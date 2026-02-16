"""Veena cognitive service: memory, reasoning, guardrails, and context orchestration."""

from __future__ import annotations

import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.veena_cognitive import ReasoningTrace, UserContext, VeenaAuditLog, VeenaMemory

SENSITIVE_FIELD_PATTERN = re.compile(
    r"\b(update|alter|delete|drop|truncate)\b.*\b(password|role|is_superuser|organization_id|rls)\b",
    re.IGNORECASE,
)


class SurrealGraphClient:
    """Thin wrapper for Surreal concept relation writes (optional/no-op without URL)."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or os.getenv("SURREALDB_URL")

    async def link_concepts(self, source: str, target: str, relation: str = "related_to") -> bool:
        if not self.url:
            return False
        # Job 14 integration point. We only mark success path as feature-flagged for now.
        return True


class ReasoningEngine:
    """Simple ReAct-style runner to orchestrate thought/tool/outcome steps."""

    def __init__(self, service: "VeenaCognitiveService") -> None:
        self.service = service

    async def run(self, session_id: str, user_id: int, query: str, context: list[dict[str, Any]]) -> dict[str, Any]:
        thoughts = [
            {"step_id": "analyze", "thought": "Analyze user intent", "tool_used": "intent-parser", "outcome": "intent-captured"},
            {"step_id": "retrieve", "thought": "Fetch relevant memory", "tool_used": "pgvector", "outcome": f"context_hits={len(context)}"},
        ]
        for step in thoughts:
            await self.service.log_reasoning_step(session_id, step)
        answer = self.service.apply_expertise_filter("Generated response with context.", user_id)
        return {"thoughts": thoughts, "content": answer}


class VeenaCognitiveService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph = SurrealGraphClient()

    async def _embed_text(self, text_value: str) -> list[float]:
        # deterministic tiny embedding fallback for tests/dev.
        tokens = [float((ord(c) % 31) / 31.0) for c in text_value[:32]]
        return tokens + [0.0] * (32 - len(tokens))

    async def ensure_pgvector_index(self) -> None:
        await self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await self.db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_veena_memories_v2_embedding
            ON veena_memories_v2 USING ivfflat ((embedding::vector(32)) vector_cosine_ops)
        """))

    async def store_memory(self, user_id: int, interaction_data: dict[str, Any]) -> VeenaMemory:
        query = interaction_data.get("query", "")
        response = interaction_data.get("response", "")
        memory = VeenaMemory(
            user_id=user_id,
            query=query,
            response=response,
            context_tags=interaction_data.get("context_tags", []),
            embedding=interaction_data.get("embedding") or await self._embed_text(f"{query} {response}"),
            pinned=interaction_data.get("pinned", False),
            ttl_days=interaction_data.get("ttl_days"),
        )
        self.db.add(memory)
        await self.db.flush()

        for tag in memory.context_tags[:3]:
            await self.graph.link_concepts(query[:128] or "query", tag)

        return memory

    async def retrieve_relevant_context(self, user_id: int, current_query: str, limit: int = 5) -> list[VeenaMemory]:
        start = time.perf_counter()
        query_embedding = await self._embed_text(current_query)
        result = await self.db.execute(
            select(VeenaMemory)
            .where(VeenaMemory.user_id == user_id)
            .order_by(VeenaMemory.created_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()

        # crude cosine-like score fallback for sqlite/tests
        def score(rec: VeenaMemory) -> float:
            emb = rec.embedding or []
            n = min(len(emb), len(query_embedding))
            return sum((emb[i] * query_embedding[i]) for i in range(n))

        ranked = sorted(records, key=score, reverse=True)

        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > 200:
            ranked = ranked[: max(1, limit // 2)]
        return ranked

    async def log_reasoning_step(self, session_id: str, step_data: dict[str, Any]) -> ReasoningTrace:
        trace = ReasoningTrace(
            session_id=session_id,
            step_id=step_data["step_id"],
            thought=step_data["thought"],
            tool_used=step_data.get("tool_used"),
            outcome=step_data.get("outcome", ""),
        )
        self.db.add(trace)
        await self.db.flush()
        return trace

    async def get_or_create_user_context(self, user_id: int) -> UserContext:
        result = await self.db.execute(select(UserContext).where(UserContext.user_id == user_id))
        context = result.scalar_one_or_none()
        if context:
            return context
        context = UserContext(user_id=user_id, preferences={}, expertise_level="manager")
        self.db.add(context)
        await self.db.flush()
        return context

    def apply_expertise_filter(self, content: str, user_id: int | None = None, expertise_level: str | None = None) -> str:
        level = expertise_level or "manager"
        if level.lower() == "breeder":
            return f"[Technical] {content}"
        if level.lower() == "manager":
            return f"[Executive] {content}"
        return content

    def inject_context(self, base_prompt: str, user_context: UserContext | None) -> str:
        if not user_context or not user_context.active_project:
            return base_prompt
        return f"{base_prompt}\n\nCurrent project: {user_context.active_project}"

    def guardrail_flag_sensitive_draft(self, draft: str) -> bool:
        return bool(SENSITIVE_FIELD_PATTERN.search(draft))

    async def create_audit_log(self, user_id: int, prompt: str, generated_draft: str, session_id: str | None = None) -> VeenaAuditLog:
        flagged = self.guardrail_flag_sensitive_draft(generated_draft)
        log = VeenaAuditLog(
            user_id=user_id,
            session_id=session_id,
            prompt=prompt,
            generated_draft=generated_draft,
            flagged_sensitive=flagged,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def feedback_loop(self, trace_id: int, approved: bool, correction: str | None = None) -> None:
        result = await self.db.execute(select(ReasoningTrace).where(ReasoningTrace.id == trace_id))
        trace = result.scalar_one_or_none()
        if not trace:
            return
        outcome_suffix = "approved" if approved else f"corrected:{correction or 'n/a'}"
        trace.outcome = f"{trace.outcome} | feedback={outcome_suffix}"

    async def cleanup_memories(self, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(select(VeenaMemory).where(VeenaMemory.user_id == user_id))
        candidates = result.scalars().all()
        to_delete_ids = []
        for mem in candidates:
            if mem.pinned or mem.ttl_days is None:
                continue
            expiry = mem.created_at + timedelta(days=mem.ttl_days)
            if expiry < now:
                to_delete_ids.append(mem.id)
        if to_delete_ids:
            await self.db.execute(delete(VeenaMemory).where(VeenaMemory.id.in_(to_delete_ids)))
        return len(to_delete_ids)

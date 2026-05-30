"""
REEVU Conversation Memory

Maintains per-conversation data context across turns, enabling follow-up
queries and progressive narrowing without re-stating everything.

Context is stored in Redis with a 2-hour TTL. When turn_count exceeds
MAX_TURNS, entity_sets are compacted (dropped) but active_filters are
always preserved.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.modules.ai.services.reevu.step_executor import ExecutionOutcome

logger = logging.getLogger(__name__)

_KEY_PREFIX = "reevu:ctx:"

# ── Follow-up and reset phrase sets ──────────────────────────────────────────

FOLLOW_UP_PHRASES: tuple[str, ...] = (
    "now", "also", "but only", "filter", "exclude", "same but",
    "what about", "show me only", "narrow", "just the", "of those",
    "from those", "among those", "of these", "from these",
)

RESET_PHRASES: tuple[str, ...] = (
    "start over", "clear filters", "reset", "new search", "forget that",
    "start fresh", "begin again",
)


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ConversationDataContext:
    """Per-conversation data context stored in Redis."""

    conversation_id: str
    entity_sets: dict[str, list[str]]   # domain → list of entity IDs
    active_filters: dict[str, Any]      # crop, trait, location, season, etc.
    last_plan_domains: list[str]        # domains from last executed plan
    last_result_summary: str | None
    turn_count: int
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "entity_sets": self.entity_sets,
            "active_filters": self.active_filters,
            "last_plan_domains": self.last_plan_domains,
            "last_result_summary": self.last_result_summary,
            "turn_count": self.turn_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationDataContext":
        return cls(
            conversation_id=data["conversation_id"],
            entity_sets=data.get("entity_sets", {}),
            active_filters=data.get("active_filters", {}),
            last_plan_domains=data.get("last_plan_domains", []),
            last_result_summary=data.get("last_result_summary"),
            turn_count=data.get("turn_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


# ── Service ───────────────────────────────────────────────────────────────────

class ConversationContextService:
    """Store and retrieve per-conversation REEVU data context via Redis.

    Usage:
        svc = ConversationContextService(redis_client=redis_client)
        ctx = await svc.get(conversation_id)
        ctx = await svc.update(conversation_id, outcome, params)
        await svc.clear(conversation_id)
    """

    CONTEXT_TTL_SECONDS: int = 7200   # 2 hours
    MAX_TURNS: int = 10

    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client

    def _key(self, conversation_id: str) -> str:
        return f"{_KEY_PREFIX}{conversation_id}"

    async def get(self, conversation_id: str) -> ConversationDataContext | None:
        """Retrieve context from Redis. Returns None on miss or when Redis unavailable."""
        if not getattr(self._redis, "is_available", False):
            return None
        try:
            data = await self._redis.get(self._key(conversation_id))
            if data is None:
                return None
            if isinstance(data, str):
                data = json.loads(data)
            return ConversationDataContext.from_dict(data)
        except Exception as exc:
            logger.warning("ConversationContextService.get failed: %s", exc)
            return None

    async def update(
        self,
        conversation_id: str,
        outcome: ExecutionOutcome,
        params: dict[str, Any],
    ) -> ConversationDataContext:
        """Update context from an execution outcome and request params.

        - Extracts entity IDs from successful step results.
        - Merges new params into existing active_filters.
        - Increments turn_count.
        - Compacts entity_sets when turn_count > MAX_TURNS.
        - Stores updated context in Redis with TTL.
        """
        # Load existing context or create fresh
        existing = await self.get(conversation_id)
        now = datetime.now(UTC)

        if existing is None:
            existing = ConversationDataContext(
                conversation_id=conversation_id,
                entity_sets={},
                active_filters={},
                last_plan_domains=[],
                last_result_summary=None,
                turn_count=0,
                created_at=now,
                updated_at=now,
            )

        # Extract entity IDs from successful steps
        new_entity_sets: dict[str, list[str]] = {}
        for step in outcome.step_results:
            if step.status != "success":
                continue
            ids = [str(eid) for eid in (step.entity_ids or []) if eid]
            if ids:
                new_entity_sets[step.domain] = ids

        # Merge active_filters (new params override old for same keys)
        merged_filters = {**existing.active_filters}
        for k, v in params.items():
            if not k.startswith("_") and v is not None:
                merged_filters[k] = v

        new_turn_count = existing.turn_count + 1

        # Compaction: when exceeding MAX_TURNS, drop entity_sets but keep filters
        if new_turn_count > self.MAX_TURNS:
            entity_sets = new_entity_sets  # only keep current turn's entities
        else:
            # Merge: new entities override old for same domain
            entity_sets = {**existing.entity_sets, **new_entity_sets}

        # Derive last_plan_domains from outcome
        last_plan_domains = list({
            step.domain for step in outcome.step_results
            if step.status == "success"
        })

        updated = ConversationDataContext(
            conversation_id=conversation_id,
            entity_sets=entity_sets,
            active_filters=merged_filters,
            last_plan_domains=last_plan_domains,
            last_result_summary=None,
            turn_count=new_turn_count,
            created_at=existing.created_at,
            updated_at=now,
        )

        # Persist to Redis
        if getattr(self._redis, "is_available", False):
            try:
                await self._redis.set(
                    self._key(conversation_id),
                    updated.to_dict(),
                    ttl_seconds=self.CONTEXT_TTL_SECONDS,
                )
            except Exception as exc:
                logger.warning("ConversationContextService.update failed to persist: %s", exc)

        return updated

    async def clear(self, conversation_id: str) -> None:
        """Delete the context for a conversation (on 'start over' command)."""
        if not getattr(self._redis, "is_available", False):
            return
        try:
            await self._redis.delete(self._key(conversation_id))
        except Exception as exc:
            logger.warning("ConversationContextService.clear failed: %s", exc)


# ── Module-level helpers (used by function_calling_service) ───────────────────

def is_follow_up_query(
    message: str,
    context: ConversationDataContext | None,
) -> bool:
    """Return True when the message is a follow-up and context has entity sets."""
    if context is None or not context.entity_sets:
        return False
    msg = message.lower()
    return any(phrase in msg for phrase in FOLLOW_UP_PHRASES)


def is_reset_query(message: str) -> bool:
    """Return True when the message requests a context reset."""
    msg = message.lower()
    return any(phrase in msg for phrase in RESET_PHRASES)

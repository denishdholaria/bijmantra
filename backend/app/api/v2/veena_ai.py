"""Veena AI orchestration endpoints with stateful reasoning trace."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.models.veena_cognitive import ReasoningTrace, VeenaMemory
from app.services.veena_cognitive_service import ReasoningEngine, VeenaCognitiveService

router = APIRouter(prefix="/veena", tags=["Veena Cognitive"], dependencies=[Depends(get_current_user)])


class ReasoningStepModel(BaseModel):
    step_id: str
    thought: str
    tool_used: str | None = None
    outcome: str


class VeenaChatRequest(BaseModel):
    session_id: str = Field(..., description="Conversation session identifier")
    query: str


class VeenaChatResponse(BaseModel):
    session_id: str
    thoughts: list[ReasoningStepModel]
    content: str
    guardrail_flagged: bool = False


class FeedbackRequest(BaseModel):
    trace_id: int
    approved: bool
    correction: str | None = None


def get_service(db: AsyncSession = Depends(get_db)) -> VeenaCognitiveService:
    return VeenaCognitiveService(db)


@router.post("/chat", response_model=VeenaChatResponse)
async def veena_chat(
    request: VeenaChatRequest,
    current_user: User = Depends(get_current_user),
    service: VeenaCognitiveService = Depends(get_service),
):
    context = await service.retrieve_relevant_context(current_user.id, request.query)
    user_context = await service.get_or_create_user_context(current_user.id)

    engine = ReasoningEngine(service)
    engine_result = await engine.run(request.session_id, current_user.id, request.query, [{"id": m.id} for m in context])

    content = service.inject_context(engine_result["content"], user_context)
    content = service.apply_expertise_filter(content, expertise_level=user_context.expertise_level)

    await service.store_memory(
        current_user.id,
        {
            "query": request.query,
            "response": content,
            "context_tags": ["veena", user_context.active_project or "general"],
        },
    )
    audit = await service.create_audit_log(current_user.id, request.query, content, request.session_id)

    return VeenaChatResponse(
        session_id=request.session_id,
        thoughts=[ReasoningStepModel(**step) for step in engine_result["thoughts"]],
        content=content,
        guardrail_flagged=audit.flagged_sensitive,
    )


@router.get("/history")
async def veena_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    memories_result = await db.execute(
        select(VeenaMemory)
        .where(VeenaMemory.user_id == current_user.id)
        .order_by(VeenaMemory.created_at.desc())
        .limit(50)
    )
    traces_result = await db.execute(
        select(ReasoningTrace)
        .where(ReasoningTrace.session_id == session_id)
        .order_by(ReasoningTrace.created_at.asc())
    )

    memories = memories_result.scalars().all()
    traces = traces_result.scalars().all()
    return {
        "session_id": session_id,
        "memories": [
            {
                "id": m.id,
                "query": m.query,
                "response": m.response,
                "context_tags": m.context_tags,
                "created_at": m.created_at,
            }
            for m in memories
        ],
        "traces": [
            {
                "id": t.id,
                "step_id": t.step_id,
                "thought": t.thought,
                "tool_used": t.tool_used,
                "outcome": t.outcome,
                "created_at": t.created_at,
            }
            for t in traces
        ],
    }


@router.post("/feedback")
async def veena_feedback(
    request: FeedbackRequest,
    service: VeenaCognitiveService = Depends(get_service),
) -> dict[str, str]:
    await service.feedback_loop(request.trace_id, request.approved, request.correction)
    return {"status": "ok"}

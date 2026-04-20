"""Hidden developer-control-plane API for optional Mem0 cloud memory."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.developer_control_plane import (
    DeveloperControlPlaneCloseoutReceiptResponse,
    DeveloperControlPlaneMissionDetailResponse,
    _closeout_receipt_response,
    _ensure_mission_state_schema_ready,
    _load_closeout_receipt,
    _load_runtime_mission_snapshot,
    _mission_detail_response,
    _require_ascii_text,
)
from app.api.deps import get_current_superuser, get_db, get_organization_id
from app.models.core import User
from app.models.developer_control_plane import DeveloperControlPlaneLearningEntry
from app.modules.ai.services.mem0_service import (
    Mem0ConfigurationError,
    Mem0DisabledError,
    Mem0Service,
    get_mem0_service,
)


DEFAULT_APP_ID = "bijmantra-dev"
DEFAULT_AGENT_ID = "developer-control-plane"


router = APIRouter(
    prefix="/developer-control-plane/mem0",
    tags=["Developer Control Plane"],
    dependencies=[Depends(get_current_superuser)],
)


class DeveloperMem0ServiceResponse(BaseModel):
    enabled: bool
    configured: bool
    host: str
    project_scoped: bool
    org_project_pair_valid: bool
    is_optional: bool = True
    is_canonical_authority: bool = False


class DeveloperMem0StatusResponse(BaseModel):
    service: DeveloperMem0ServiceResponse
    purpose: str
    detail: str


class DeveloperMem0HealthResponse(BaseModel):
    scope: DeveloperMem0ScopeResponse
    reachable: bool
    checked_at: str
    latency_ms: float | None = None
    result_count: int | None = None
    detail: str


class DeveloperMem0ScopeResponse(BaseModel):
    user_id: str
    app_id: str
    run_id: str | None = None


class DeveloperMem0AddRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    user_id: str | None = Field(default=None, min_length=1, max_length=255)
    app_id: str = Field(default=DEFAULT_APP_ID, min_length=1, max_length=255)
    run_id: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] | None = None


class DeveloperMem0AddResponse(BaseModel):
    scope: DeveloperMem0ScopeResponse
    result: dict[str, Any]


class DeveloperMem0SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=240)
    user_id: str | None = Field(default=None, min_length=1, max_length=255)
    app_id: str = Field(default=DEFAULT_APP_ID, min_length=1, max_length=255)
    run_id: str | None = Field(default=None, max_length=255)
    limit: int = Field(default=5, ge=1, le=25)
    filters: dict[str, Any] | None = None


class DeveloperMem0SearchResponse(BaseModel):
    query: str
    scope: DeveloperMem0ScopeResponse
    limit: int
    result: dict[str, Any]


class DeveloperMem0CaptureLearningRequest(BaseModel):
    user_id: str | None = Field(default=None, min_length=1, max_length=255)
    app_id: str = Field(default=DEFAULT_APP_ID, min_length=1, max_length=255)
    run_id: str | None = Field(default=None, max_length=255)


class DeveloperMem0LearningSourceResponse(BaseModel):
    learning_entry_id: int
    entry_type: str
    source_classification: str
    title: str
    summary: str
    source_lane_id: str | None = None
    queue_job_id: str | None = None
    linked_mission_id: str | None = None
    source_reference: str | None = None


class DeveloperMem0CaptureLearningResponse(BaseModel):
    scope: DeveloperMem0ScopeResponse
    source: DeveloperMem0LearningSourceResponse
    memory_text: str
    result: dict[str, Any]


class DeveloperMem0CaptureMissionRequest(BaseModel):
    user_id: str | None = Field(default=None, min_length=1, max_length=255)
    app_id: str = Field(default=DEFAULT_APP_ID, min_length=1, max_length=255)
    run_id: str | None = Field(default=None, max_length=255)


class DeveloperMem0MissionSourceResponse(BaseModel):
    mission_id: str
    objective: str
    status: str
    owner: str
    priority: str
    producer_key: str | None = None
    queue_job_id: str | None = None
    source_lane_id: str | None = None
    evidence_count: int
    blocker_count: int
    final_summary: str | None = None


class DeveloperMem0MissionCloseoutResponse(BaseModel):
    exists: bool
    queue_job_id: str | None = None
    closeout_status: str | None = None
    verification_evidence_ref: str | None = None
    artifact_count: int = 0
    command_count: int = 0


class DeveloperMem0CaptureMissionResponse(BaseModel):
    scope: DeveloperMem0ScopeResponse
    source: DeveloperMem0MissionSourceResponse
    closeout_receipt: DeveloperMem0MissionCloseoutResponse | None = None
    memory_text: str
    result: dict[str, Any]


def get_developer_mem0_service() -> Mem0Service:
    return get_mem0_service()


def _status_detail(status_payload: dict[str, Any]) -> str:
    if not status_payload["enabled"]:
        return "Mem0 is disabled for BijMantra and remains outside the canonical developer-control-plane loop."
    if not status_payload["configured"]:
        return "Mem0 is enabled in intent but the API key is missing from the runtime configuration."
    if not status_payload["org_project_pair_valid"]:
        return "MEM0_ORG_ID and MEM0_PROJECT_ID must be configured together when project scoping is used."
    if status_payload["project_scoped"]:
        return "Mem0 is ready for developer memory with explicit project scoping."
    return "Mem0 is ready for developer memory with global app-level scoping."


def _resolve_scope(
    current_user: User,
    *,
    user_id: str | None,
    app_id: str,
    run_id: str | None,
) -> DeveloperMem0ScopeResponse:
    resolved_user_id = user_id or current_user.email or f"user-{current_user.id}"
    return DeveloperMem0ScopeResponse(user_id=resolved_user_id, app_id=app_id, run_id=run_id)


def _merge_add_metadata(payload: DeveloperMem0AddRequest) -> dict[str, Any]:
    merged = dict(payload.metadata or {})
    merged.setdefault("source_surface", "developer_control_plane")
    merged.setdefault("memory_class", "developer_micro_memory")
    merged.setdefault("app_context", payload.app_id)
    if payload.category:
        merged.setdefault("category", payload.category)
    return merged


def _learning_memory_text(record: DeveloperControlPlaneLearningEntry) -> str:
    parts = [
        f"Developer control plane learning [{record.entry_type}] {record.title}.",
        f"Summary: {record.summary}",
        f"Source classification: {record.source_classification}.",
    ]
    if record.source_lane_id:
        parts.append(f"Source lane: {record.source_lane_id}.")
    if record.queue_job_id:
        parts.append(f"Queue job: {record.queue_job_id}.")
    if record.linked_mission_id:
        parts.append(f"Mission: {record.linked_mission_id}.")
    return " ".join(parts)


def _learning_metadata(record: DeveloperControlPlaneLearningEntry) -> dict[str, Any]:
    return {
        "source_surface": "developer_control_plane_learning_ledger",
        "memory_class": "developer_learning_recall",
        "learning_entry_id": record.id,
        "entry_type": record.entry_type,
        "source_classification": record.source_classification,
        "board_id": record.board_id,
        "source_lane_id": record.source_lane_id,
        "queue_job_id": record.queue_job_id,
        "linked_mission_id": record.linked_mission_id,
        "source_reference": record.source_reference,
        "evidence_refs": record.evidence_refs,
        "confidence_score": record.confidence_score,
    }


def _mission_memory_text(
    record: DeveloperControlPlaneMissionDetailResponse,
    closeout_receipt: DeveloperControlPlaneCloseoutReceiptResponse | None,
) -> str:
    parts = [
        f"Developer control plane mission outcome [{record.status}] {record.objective}.",
        f"Owner: {record.owner}.",
        f"Priority: {record.priority}.",
    ]
    if record.final_summary:
        parts.append(f"Final summary: {record.final_summary}")
    if record.queue_job_id:
        parts.append(f"Queue job: {record.queue_job_id}.")
    if record.source_lane_id:
        parts.append(f"Source lane: {record.source_lane_id}.")
    parts.append(
        "Verification passed "
        f"{record.verification.passed}, warned {record.verification.warned}, failed {record.verification.failed}."
    )
    parts.append(f"Evidence items: {record.evidence_count}. Blockers: {record.blocker_count}.")
    if closeout_receipt is not None:
        if closeout_receipt.exists:
            if closeout_receipt.closeout_status:
                parts.append(f"Closeout status: {closeout_receipt.closeout_status}.")
            if closeout_receipt.verification_evidence_ref:
                parts.append(
                    f"Verification evidence: {closeout_receipt.verification_evidence_ref}."
                )
        elif closeout_receipt.queue_job_id:
            parts.append(
                f"Closeout receipt is not yet recorded for queue job {closeout_receipt.queue_job_id}."
            )
    return " ".join(parts)


def _mission_metadata(
    record: DeveloperControlPlaneMissionDetailResponse,
    closeout_receipt: DeveloperControlPlaneCloseoutReceiptResponse | None,
) -> dict[str, Any]:
    return {
        "source_surface": "developer_control_plane_mission_state",
        "memory_class": "developer_mission_recall",
        "mission_id": record.mission_id,
        "status": record.status,
        "owner": record.owner,
        "priority": record.priority,
        "producer_key": record.producer_key,
        "queue_job_id": record.queue_job_id,
        "source_lane_id": record.source_lane_id,
        "source_board_concurrency_token": record.source_board_concurrency_token,
        "final_summary": record.final_summary,
        "subtask_total": record.subtask_total,
        "subtask_completed": record.subtask_completed,
        "assignment_total": record.assignment_total,
        "evidence_count": record.evidence_count,
        "blocker_count": record.blocker_count,
        "escalation_needed": record.escalation_needed,
        "verification": {
            "passed": record.verification.passed,
            "warned": record.verification.warned,
            "failed": record.verification.failed,
            "last_verified_at": record.verification.last_verified_at,
        },
        "evidence_refs": [item.source_path for item in record.evidence_items],
        "decision_note_count": len(record.decision_notes),
        "closeout_receipt_exists": closeout_receipt.exists if closeout_receipt else False,
        "closeout_status": closeout_receipt.closeout_status if closeout_receipt else None,
        "closeout_verification_evidence_ref": (
            closeout_receipt.verification_evidence_ref if closeout_receipt else None
        ),
        "closeout_artifact_paths": (
            [item.path for item in closeout_receipt.artifacts]
            if closeout_receipt and closeout_receipt.exists
            else []
        ),
        "closeout_command_count": (
            len(closeout_receipt.closeout_commands)
            if closeout_receipt and closeout_receipt.exists
            else 0
        ),
    }


def _mission_closeout_response(
    closeout_receipt: DeveloperControlPlaneCloseoutReceiptResponse | None,
) -> DeveloperMem0MissionCloseoutResponse | None:
    if closeout_receipt is None:
        return None

    return DeveloperMem0MissionCloseoutResponse(
        exists=closeout_receipt.exists,
        queue_job_id=closeout_receipt.queue_job_id,
        closeout_status=closeout_receipt.closeout_status,
        verification_evidence_ref=closeout_receipt.verification_evidence_ref,
        artifact_count=len(closeout_receipt.artifacts),
        command_count=len(closeout_receipt.closeout_commands),
    )


async def _get_learning_entry(
    db: AsyncSession,
    organization_id: int,
    learning_entry_id: int,
) -> DeveloperControlPlaneLearningEntry | None:
    result = await db.execute(
        select(DeveloperControlPlaneLearningEntry).where(
            DeveloperControlPlaneLearningEntry.organization_id == organization_id,
            DeveloperControlPlaneLearningEntry.id == learning_entry_id,
        )
    )
    return result.scalar_one_or_none()


def _mem0_unavailable_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, (Mem0DisabledError, Mem0ConfigurationError)):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Mem0 request failed: {exc}",
    )


@router.get("/status", response_model=DeveloperMem0StatusResponse)
async def get_developer_mem0_status(
    service: Mem0Service = Depends(get_developer_mem0_service),
) -> DeveloperMem0StatusResponse:
    status_payload = service.status()
    return DeveloperMem0StatusResponse(
        service=DeveloperMem0ServiceResponse(**status_payload),
        purpose="Developer-only cloud memory for decisions, blockers, architecture notes, and short project recall.",
        detail=_status_detail(status_payload),
    )


@router.get("/health", response_model=DeveloperMem0HealthResponse)
async def get_developer_mem0_health(
    user_id: str | None = None,
    app_id: str = DEFAULT_APP_ID,
    run_id: str | None = None,
    current_user: User = Depends(get_current_superuser),
    service: Mem0Service = Depends(get_developer_mem0_service),
) -> DeveloperMem0HealthResponse:
    scope = _resolve_scope(
        current_user,
        user_id=user_id,
        app_id=app_id,
        run_id=run_id,
    )
    try:
        health = await service.health_check(
            user_id=scope.user_id,
            agent_id=DEFAULT_AGENT_ID,
            app_id=scope.app_id,
            run_id=scope.run_id,
        )
    except Exception as exc:
        raise _mem0_unavailable_exception(exc) from exc

    return DeveloperMem0HealthResponse(scope=scope, **health)


@router.post("/memories", response_model=DeveloperMem0AddResponse)
async def add_developer_mem0_memory(
    payload: DeveloperMem0AddRequest,
    current_user: User = Depends(get_current_superuser),
    service: Mem0Service = Depends(get_developer_mem0_service),
) -> DeveloperMem0AddResponse:
    scope = _resolve_scope(
        current_user,
        user_id=payload.user_id,
        app_id=payload.app_id,
        run_id=payload.run_id,
    )
    try:
        result = await service.add_messages(
            payload.text,
            user_id=scope.user_id,
            agent_id=DEFAULT_AGENT_ID,
            app_id=scope.app_id,
            run_id=scope.run_id,
            metadata=_merge_add_metadata(payload),
        )
    except Exception as exc:
        raise _mem0_unavailable_exception(exc) from exc

    return DeveloperMem0AddResponse(scope=scope, result=result)


@router.post("/search", response_model=DeveloperMem0SearchResponse)
async def search_developer_mem0_memory(
    payload: DeveloperMem0SearchRequest,
    current_user: User = Depends(get_current_superuser),
    service: Mem0Service = Depends(get_developer_mem0_service),
) -> DeveloperMem0SearchResponse:
    scope = _resolve_scope(
        current_user,
        user_id=payload.user_id,
        app_id=payload.app_id,
        run_id=payload.run_id,
    )
    try:
        result = await service.search(
            payload.query,
            user_id=scope.user_id,
            agent_id=DEFAULT_AGENT_ID,
            app_id=scope.app_id,
            run_id=scope.run_id,
            limit=payload.limit,
            filters=payload.filters,
        )
    except Exception as exc:
        raise _mem0_unavailable_exception(exc) from exc

    return DeveloperMem0SearchResponse(
        query=payload.query,
        scope=scope,
        limit=payload.limit,
        result=result,
    )


@router.post(
    "/learnings/{learning_entry_id}/capture",
    response_model=DeveloperMem0CaptureLearningResponse,
)
async def capture_learning_entry_to_mem0(
    learning_entry_id: int,
    payload: DeveloperMem0CaptureLearningRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
    service: Mem0Service = Depends(get_developer_mem0_service),
) -> DeveloperMem0CaptureLearningResponse:
    record = await _get_learning_entry(db, organization_id, learning_entry_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning entry {learning_entry_id} was not found for this organization.",
        )

    scope = _resolve_scope(
        current_user,
        user_id=payload.user_id,
        app_id=payload.app_id,
        run_id=payload.run_id,
    )
    memory_text = _learning_memory_text(record)
    try:
        result = await service.add_messages(
            memory_text,
            user_id=scope.user_id,
            agent_id=DEFAULT_AGENT_ID,
            app_id=scope.app_id,
            run_id=scope.run_id,
            metadata=_learning_metadata(record),
        )
    except Exception as exc:
        raise _mem0_unavailable_exception(exc) from exc

    return DeveloperMem0CaptureLearningResponse(
        scope=scope,
        source=DeveloperMem0LearningSourceResponse(
            learning_entry_id=record.id,
            entry_type=record.entry_type,
            source_classification=record.source_classification,
            title=record.title,
            summary=record.summary,
            source_lane_id=record.source_lane_id,
            queue_job_id=record.queue_job_id,
            linked_mission_id=record.linked_mission_id,
            source_reference=record.source_reference,
        ),
        memory_text=memory_text,
        result=result,
    )


@router.post(
    "/missions/{mission_id}/capture",
    response_model=DeveloperMem0CaptureMissionResponse,
)
async def capture_mission_to_mem0(
    mission_id: str,
    payload: DeveloperMem0CaptureMissionRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
    service: Mem0Service = Depends(get_developer_mem0_service),
) -> DeveloperMem0CaptureMissionResponse:
    await _ensure_mission_state_schema_ready(db)
    validated_mission_id = _require_ascii_text(mission_id, "mission_id")
    snapshot = await _load_runtime_mission_snapshot(db, organization_id, validated_mission_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

    mission_detail = _mission_detail_response(snapshot)
    closeout_receipt = None
    if mission_detail.queue_job_id:
        closeout_receipt = _closeout_receipt_response(
            mission_detail.queue_job_id,
            _load_closeout_receipt(mission_detail.queue_job_id),
        )

    scope = _resolve_scope(
        current_user,
        user_id=payload.user_id,
        app_id=payload.app_id,
        run_id=payload.run_id,
    )
    memory_text = _mission_memory_text(mission_detail, closeout_receipt)
    try:
        result = await service.add_messages(
            memory_text,
            user_id=scope.user_id,
            agent_id=DEFAULT_AGENT_ID,
            app_id=scope.app_id,
            run_id=scope.run_id,
            metadata=_mission_metadata(mission_detail, closeout_receipt),
        )
    except Exception as exc:
        raise _mem0_unavailable_exception(exc) from exc

    return DeveloperMem0CaptureMissionResponse(
        scope=scope,
        source=DeveloperMem0MissionSourceResponse(
            mission_id=mission_detail.mission_id,
            objective=mission_detail.objective,
            status=mission_detail.status,
            owner=mission_detail.owner,
            priority=mission_detail.priority,
            producer_key=mission_detail.producer_key,
            queue_job_id=mission_detail.queue_job_id,
            source_lane_id=mission_detail.source_lane_id,
            evidence_count=mission_detail.evidence_count,
            blocker_count=mission_detail.blocker_count,
            final_summary=mission_detail.final_summary,
        ),
        closeout_receipt=_mission_closeout_response(closeout_receipt),
        memory_text=memory_text,
        result=result,
    )
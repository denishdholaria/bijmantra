"""Missions router for developer control plane.

Thin router — HTTP route definitions only.
Business logic lives in app.services.control_plane.mission_service.

Endpoints:
  GET  /runtime/mission-state
  POST /runtime/mission-state/bootstrap-closeout-receipt
  GET  /runtime/mission-state/{mission_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_organization_id
from app.middleware.tenant_context import get_tenant_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Request model (defined here to avoid circular imports).
# ---------------------------------------------------------------------------

class DeveloperControlPlaneMissionBootstrapRequest(BaseModel):
    queue_job_id: str = Field(..., min_length=1, max_length=256)


# ---------------------------------------------------------------------------
# Routes
# Helpers that are still in developer_control_plane.py are imported lazily
# (inside function bodies) to avoid circular imports at module load time.
# ---------------------------------------------------------------------------

@router.get("/runtime/mission-state")
async def get_runtime_mission_state(
    limit: int = 8,
    queue_job_id: str | None = None,
    source_lane_id: str | None = None,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
):
    from app.control_plane.application.mission_service import MissionService
    from app.api.bijmantra.developer.developer_control_plane import (
        _ensure_mission_state_schema_ready,
        _require_ascii_text,
    )
    await _ensure_mission_state_schema_ready(db)
    bounded_limit = max(1, min(limit, 25))
    validated_queue_job_id = (
        _require_ascii_text(queue_job_id, "queue_job_id") if queue_job_id is not None else None
    )
    validated_source_lane_id = (
        _require_ascii_text(source_lane_id, "source_lane_id")
        if source_lane_id is not None
        else None
    )
    return await MissionService(db).mission_state_response(
        organization_id,
        limit=bounded_limit,
        queue_job_id=validated_queue_job_id,
        source_lane_id=validated_source_lane_id,
    )


@router.post("/runtime/mission-state/bootstrap-closeout-receipt")
async def bootstrap_runtime_mission_state_from_closeout_receipt(
    payload: DeveloperControlPlaneMissionBootstrapRequest,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
):
    from app.api.bijmantra.developer.developer_control_plane import (
        _bootstrap_closeout_receipt_mission_state,
        _ensure_mission_state_schema_ready,
        _require_ascii_text,
        _seed_mission_state_learnings_if_ready,
    )
    from app.control_plane.application.execution_service import ExecutionService
    await _ensure_mission_state_schema_ready(db)
    validated_queue_job_id = _require_ascii_text(payload.queue_job_id, "queue_job_id")
    receipt = ExecutionService.closeout_receipt_contract_from_response(
        ExecutionService.closeout_receipt_response(
            validated_queue_job_id,
            ExecutionService.load_closeout_receipt(validated_queue_job_id),
        )
    )
    response = await _bootstrap_closeout_receipt_mission_state(
        db,
        organization_id,
        queue_job_id=validated_queue_job_id,
        closeout_receipt=receipt,
    )
    seeded_learnings = False
    if response.action in {"created", "existing"}:
        seeded_learnings = await _seed_mission_state_learnings_if_ready(db, organization_id)
    if response.action == "created" or seeded_learnings:
        await db.commit()
    return response


@router.get("/runtime/mission-state/{mission_id}")
async def get_runtime_mission_state_detail(
    mission_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
):
    from app.control_plane.application.mission_service import MissionService
    from app.api.bijmantra.developer.developer_control_plane import (
        _ensure_mission_state_schema_ready,
        _require_ascii_text,
    )
    await _ensure_mission_state_schema_ready(db)
    validated_mission_id = _require_ascii_text(mission_id, "mission_id")
    mission_service = MissionService(db)
    snapshot = await mission_service.load_runtime_mission_snapshot(organization_id, validated_mission_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return MissionService.mission_detail_response(snapshot)

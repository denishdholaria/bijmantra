"""Telemetry router for developer control plane.

Thin router — HTTP route definitions only.
Business logic lives in app.services.control_plane.telemetry_service.

Endpoints:
  GET  /overnight-queue/status
  GET  /overnight-queue/jobs/{queue_job_id}/closeout-receipt
  POST /overnight-queue/write-entry
  GET  /learnings
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_organization_id
from app.middleware.tenant_context import get_tenant_db
from app.models.core import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Request model (defined here so the parent can import it from this module,
# avoiding a circular import at module load time).
# ---------------------------------------------------------------------------

class DeveloperControlPlaneOvernightQueueWriteRequest(BaseModel):
    source_board_concurrency_token: str = Field(..., min_length=1, max_length=128)
    expected_queue_sha256: str = Field(..., min_length=1, max_length=128)
    operator_intent: str = Field(..., min_length=1, max_length=64)
    queue_entry: dict[str, Any]


# ---------------------------------------------------------------------------
# Routes
# Helpers that are still in developer_control_plane.py are imported lazily
# (inside function bodies) to avoid circular imports at module load time.
# ---------------------------------------------------------------------------

@router.get("/overnight-queue/status")
async def get_overnight_queue_status():
    from app.control_plane.orchestration.queue_materializer import QueueMaterializer
    return QueueMaterializer.overnight_queue_status_response()


@router.get("/overnight-queue/jobs/{queue_job_id}/closeout-receipt")
async def get_overnight_queue_job_closeout_receipt(queue_job_id: str):
    from app.control_plane.application.execution_service import ExecutionService
    from app.api.bijmantra.developer.developer_control_plane import (
        _require_ascii_text,
    )
    validated_queue_job_id = _require_ascii_text(queue_job_id, "queue_job_id")
    receipt = ExecutionService.load_closeout_receipt(validated_queue_job_id)
    return ExecutionService.closeout_receipt_response(validated_queue_job_id, receipt)


@router.get("/learnings")
async def list_learning_entries(
    limit: int = 25,
    entry_type: str | None = None,
    source_classification: str | None = None,
    source_lane_id: str | None = None,
    queue_job_id: str | None = None,
    linked_mission_id: str | None = None,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
):
    from app.control_plane.contracts.api_schema import (
        DeveloperControlPlaneLearningLedgerResponse,
    )
    from app.api.bijmantra.developer.developer_control_plane import (
        CONTROL_PLANE_LEARNING_ENTRY_TYPES,
        _ensure_learning_schema_ready,
        _get_learning_entries,
        _learning_entry_response,
        _require_ascii_text,
    )
    await _ensure_learning_schema_ready(db)
    bounded_limit = max(1, min(limit, 50))
    validated_entry_type = (
        _require_ascii_text(entry_type, "entry_type") if entry_type is not None else None
    )
    if (
        validated_entry_type is not None
        and validated_entry_type not in CONTROL_PLANE_LEARNING_ENTRY_TYPES
    ):
        allowed_values = ", ".join(CONTROL_PLANE_LEARNING_ENTRY_TYPES)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"entry_type must be one of: {allowed_values}",
        )

    entries = await _get_learning_entries(
        db,
        organization_id,
        entry_type=validated_entry_type,
        source_classification=(
            _require_ascii_text(source_classification, "source_classification")
            if source_classification is not None
            else None
        ),
        source_lane_id=(
            _require_ascii_text(source_lane_id, "source_lane_id")
            if source_lane_id is not None
            else None
        ),
        queue_job_id=(
            _require_ascii_text(queue_job_id, "queue_job_id")
            if queue_job_id is not None
            else None
        ),
        linked_mission_id=(
            _require_ascii_text(linked_mission_id, "linked_mission_id")
            if linked_mission_id is not None
            else None
        ),
        limit=bounded_limit,
    )
    return DeveloperControlPlaneLearningLedgerResponse(
        total_count=len(entries),
        entries=[_learning_entry_response(entry) for entry in entries],
    )


@router.post("/overnight-queue/write-entry")
async def write_overnight_queue_entry(
    payload: DeveloperControlPlaneOvernightQueueWriteRequest,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
):
    from app.control_plane.contracts.api_schema import (
        DeveloperControlPlaneOvernightQueueWriteResponse,
    )
    from app.control_plane.application.board_service import BoardService
    from app.control_plane.domain.lane import (
        find_board_lane,
        lane_has_queue_export_reviews,
    )
    from app.control_plane.domain.validation import DomainValidationError
    from app.control_plane.orchestration.queue_materializer import QueueMaterializer
    from app.control_plane.application.lane_service import LaneService
    from app.api.bijmantra.developer.developer_control_plane import (
        DEVELOPER_MASTER_BOARD_ID,
        QUEUE_WRITE_OPERATOR_INTENT,
        _best_effort_ascii_text,
        _ensure_approval_receipt_schema_ready,
        _ensure_persistence_schema_ready,
        _load_active_board_payload,
        _queue_write_conflict_detail,
        _review_gate_evidence_refs,
        _seed_approval_receipt_learnings_if_ready,
        _validate_queue_entry,
        _validate_queue_payload_shape,
    )

    await _ensure_persistence_schema_ready(db)
    await _ensure_approval_receipt_schema_ready(db)

    lane_service = LaneService(db)

    if payload.operator_intent != QUEUE_WRITE_OPERATOR_INTENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="operator_intent must acknowledge explicit queue write",
        )

    requested_queue_job_id = (
        _best_effort_ascii_text(payload.queue_entry.get("jobId"))
        if isinstance(payload.queue_entry, dict)
        else None
    )
    requested_provenance = (
        payload.queue_entry.get("provenance")
        if isinstance(payload.queue_entry, dict)
        else None
    )
    requested_source_lane_id = (
        _best_effort_ascii_text(requested_provenance.get("sourceLaneId"))
        if isinstance(requested_provenance, dict)
        else None
    )
    requested_source_board_token = _best_effort_ascii_text(
        payload.source_board_concurrency_token
    )

    current_record = await BoardService(db).get_active_board(organization_id)
    if current_record is None:
        conflict_detail = _queue_write_conflict_detail(
            "missing-active-board",
            "Queue write conflict; active board is missing for this organization",
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="queue-export",
            conflict_detail=conflict_detail,
            board_id=DEVELOPER_MASTER_BOARD_ID,
            source_lane_id=requested_source_lane_id,
            queue_job_id=requested_queue_job_id,
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    if payload.source_board_concurrency_token != current_record.canonical_board_hash:
        conflict_detail = _queue_write_conflict_detail(
            "stale-board-token",
            "Queue write conflict; source board token is stale and must be refreshed",
            current_board_concurrency_token=current_record.canonical_board_hash,
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="queue-export",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=requested_source_lane_id,
            queue_job_id=requested_queue_job_id,
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    queue_payload, _ = QueueMaterializer.load_overnight_queue_payload()
    queue_payload = _validate_queue_payload_shape(queue_payload)
    current_queue_sha256 = QueueMaterializer.queue_sha256(queue_payload)
    if payload.expected_queue_sha256 != current_queue_sha256:
        conflict_detail = _queue_write_conflict_detail(
            "queue-sha-mismatch",
            "Queue write conflict; overnight queue changed since the latest snapshot",
            current_queue_sha256=current_queue_sha256,
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="queue-export",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=requested_source_lane_id,
            queue_job_id=requested_queue_job_id,
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    existing_job_ids = {
        job.get("jobId")
        for job in queue_payload.get("jobs", [])
        if isinstance(job, dict) and isinstance(job.get("jobId"), str)
    }
    try:
        validated_queue_entry = _validate_queue_entry(payload.queue_entry, existing_job_ids)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_409_CONFLICT and isinstance(exc.detail, dict):
            await lane_service.persist_conflict_learning(
                organization_id,
                current_user,
                scope="queue-export",
                conflict_detail=exc.detail,
                board_id=current_record.board_id,
                source_lane_id=requested_source_lane_id,
                queue_job_id=requested_queue_job_id,
                source_board_concurrency_token=requested_source_board_token,
            )
        raise

    provenance = validated_queue_entry.get("provenance")
    if not isinstance(provenance, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.provenance is required for reviewed queue export",
        )

    source_lane_id = provenance.get("sourceLaneId")
    if not isinstance(source_lane_id, str) or not source_lane_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.provenance.sourceLaneId must be a non-empty string",
        )

    board_payload = _load_active_board_payload(current_record)
    try:
        lane = find_board_lane(board_payload, source_lane_id)
    except DomainValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    if lane is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer control-plane lane not found for reviewed queue export",
        )

    if not lane_has_queue_export_reviews(lane):
        conflict_detail = _queue_write_conflict_detail(
            "lane-review-missing",
            "Queue write conflict; canonical lane is missing explicit spec_review or risk_review evidence",
            source_lane_id=source_lane_id,
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="queue-export",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=source_lane_id,
            queue_job_id=validated_queue_entry["jobId"],
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    previous_queue_payload = json.loads(QueueMaterializer.serialize_queue_payload(queue_payload))
    queue_payload["jobs"] = [*queue_payload["jobs"], validated_queue_entry]
    queue_payload["updatedAt"] = datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )

    QueueMaterializer.write_overnight_queue_payload(queue_payload)
    written_queue_sha256 = QueueMaterializer.queue_sha256(queue_payload)

    try:
        approval_receipt = await lane_service.record_approval_receipt(
            organization_id,
            current_user,
            action_type=QUEUE_WRITE_OPERATOR_INTENT,
            outcome="applied",
            board_id=current_record.board_id,
            source_board_concurrency_token=payload.source_board_concurrency_token,
            source_lane_id=source_lane_id,
            queue_job_id=validated_queue_entry["jobId"],
            expected_queue_sha256=payload.expected_queue_sha256,
            resulting_queue_sha256=written_queue_sha256,
            rationale=(
                f"Write reviewed queue entry for lane {source_lane_id} into the overnight queue."
            ),
            evidence_refs=_review_gate_evidence_refs(lane, "spec_review", "risk_review"),
            summary_metadata={
                "queue_entry": {
                    "job_id": validated_queue_entry["jobId"],
                    "job_type": validated_queue_entry.get("type"),
                    "depends_on": validated_queue_entry.get("dependsOn", []),
                }
            },
        )
        await _seed_approval_receipt_learnings_if_ready(db, organization_id)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        try:
            QueueMaterializer.write_overnight_queue_payload(previous_queue_payload)
        except HTTPException as rollback_exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Approval receipt persistence failed after queue write and "
                    "overnight queue rollback did not succeed"
                ),
            ) from rollback_exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist approval receipt after queue write",
        ) from exc

    return DeveloperControlPlaneOvernightQueueWriteResponse(
        queue_sha256=written_queue_sha256,
        queue_updated_at=queue_payload["updatedAt"],
        written_job_id=validated_queue_entry["jobId"],
        replaced=False,
        approval_receipt=LaneService.approval_receipt_response(approval_receipt),
    )

"""Lanes router for developer control plane.

Thin router - HTTP route definitions only.
Business logic lives in app.services.control_plane.lane_service.

Endpoints:
  GET  /active-board
  GET  /active-board/versions
  PUT  /active-board
  POST /active-board/versions/{revision_id}/restore
  POST /active-board/prepare-completion-write
  POST /active-board/write-completion
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_organization_id
from app.middleware.tenant_context import get_tenant_db
from app.models.core import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Request models (defined here to avoid circular imports).
# ---------------------------------------------------------------------------

class DeveloperControlPlaneActiveBoardSaveRequest(BaseModel):
    canonical_board_json: str = Field(..., min_length=2)
    save_source: str = Field(..., min_length=1, max_length=64)
    concurrency_token: str | None = Field(default=None, min_length=1, max_length=64)


class DeveloperControlPlaneBoardRestoreRequest(BaseModel):
    concurrency_token: str | None = Field(default=None, min_length=1, max_length=64)


class DeveloperControlPlaneCompletionWritePreparationRequest(BaseModel):
    source_lane_id: str = Field(..., min_length=1, max_length=128)


# ---------------------------------------------------------------------------
# Routes
# Helpers that are still in developer_control_plane.py are imported lazily
# (inside function bodies) to avoid circular imports at module load time.
# ---------------------------------------------------------------------------

@router.get("/active-board")
async def get_active_board(
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
):
    from app.control_plane.application.board_service import BoardService
    from app.control_plane.contracts.api_schema import (
        DeveloperControlPlaneActiveBoardFetchResponse,
    )
    from app.api.bijmantra.developer.developer_control_plane import (
        _ensure_persistence_schema_ready,
    )
    await _ensure_persistence_schema_ready(db)
    board_service = BoardService(db)
    record = await board_service.get_active_board(organization_id)
    if record is None:
        return DeveloperControlPlaneActiveBoardFetchResponse(exists=False, record=None)
    return DeveloperControlPlaneActiveBoardFetchResponse(exists=True, record=BoardService.record_response(record))


@router.get("/active-board/versions")
async def list_active_board_versions(
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
):
    from app.control_plane.application.board_service import BoardService
    from app.control_plane.contracts.api_schema import (
        DeveloperControlPlaneBoardVersionsListResponse,
    )
    from app.api.bijmantra.developer.developer_control_plane import (
        _ensure_persistence_schema_ready,
    )
    from app.schemas.developer_control_plane import DEVELOPER_MASTER_BOARD_ID
    await _ensure_persistence_schema_ready(db)
    board_service = BoardService(db)
    current_record = await board_service.get_active_board(organization_id)
    versions = await board_service.get_board_versions(organization_id)
    current_concurrency_token = (
        current_record.canonical_board_hash if current_record is not None else None
    )
    return DeveloperControlPlaneBoardVersionsListResponse(
        board_id=DEVELOPER_MASTER_BOARD_ID,
        current_concurrency_token=current_concurrency_token,
        total_count=len(versions),
        versions=[
            BoardService.version_response(version, current_concurrency_token) for version in versions
        ],
    )


@router.put("/active-board")
async def save_active_board(
    payload: DeveloperControlPlaneActiveBoardSaveRequest,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
):
    from app.control_plane.application.board_service import BoardService
    from app.control_plane.domain.board import build_summary_metadata
    from app.api.bijmantra.developer.developer_control_plane import (
        _ensure_persistence_schema_ready,
    )
    from app.schemas.developer_control_plane import canonicalize_developer_master_board_json

    await _ensure_persistence_schema_ready(db)
    try:
        canonical_board_json, board = canonicalize_developer_master_board_json(
            payload.canonical_board_json
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid developer master board: {exc}",
        ) from exc

    board_service = BoardService(db)
    current_record = await board_service.get_active_board(organization_id)
    if current_record is not None and payload.concurrency_token != current_record.canonical_board_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": "Active board save conflict; refetch the current board before retrying",
                "current_record": BoardService.record_response(current_record).model_dump(mode="json"),
            },
        )

    current_record = await board_service.apply_active_board_state(
        organization_id,
        current_user,
        current_record,
        canonical_board_json=canonical_board_json,
        board=board,
        save_source=payload.save_source,
        summary_metadata=build_summary_metadata(board),
    )
    await db.commit()
    await db.refresh(current_record)
    return BoardService.record_response(current_record)


@router.post("/active-board/versions/{revision_id}/restore")
async def restore_active_board_version(
    revision_id: int,
    payload: DeveloperControlPlaneBoardRestoreRequest,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
):
    from app.control_plane.application.board_service import BoardService
    from app.control_plane.contracts.api_schema import (
        DeveloperControlPlaneBoardRestoreResponse,
    )
    from app.control_plane.domain.board import (
        build_summary_metadata,
        hash_canonical_board_json,
    )
    from app.control_plane.application.lane_service import LaneService
    from app.api.bijmantra.developer.developer_control_plane import (
        APPROVAL_RECEIPT_ACTION_RESTORE_VERSION,
        _ensure_approval_receipt_schema_ready,
        _ensure_persistence_schema_ready,
    )
    from app.models.developer_control_plane import DeveloperControlPlaneApprovalReceipt
    from app.schemas.developer_control_plane import canonicalize_developer_master_board_json

    await _ensure_persistence_schema_ready(db)
    await _ensure_approval_receipt_schema_ready(db)
    board_service = BoardService(db)
    lane_service = LaneService(db)
    revision = await board_service.get_board_revision(organization_id, revision_id)
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer control-plane revision not found",
        )

    current_record = await board_service.get_active_board(organization_id)
    if current_record is not None and payload.concurrency_token != current_record.canonical_board_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": "Active board save conflict; refetch the current board before retrying",
                "current_record": BoardService.record_response(current_record).model_dump(mode="json"),
            },
        )

    try:
        canonical_board_json, board = canonicalize_developer_master_board_json(
            revision.canonical_board_json
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid developer master board revision: {exc}",
        ) from exc

    restored_hash = hash_canonical_board_json(canonical_board_json)
    previous_active_concurrency_token = (
        current_record.canonical_board_hash if current_record is not None else None
    )
    if previous_active_concurrency_token == restored_hash:
        existing_receipt = await lane_service.get_latest_approval_receipt(
            organization_id,
            DeveloperControlPlaneApprovalReceipt.action_type
            == APPROVAL_RECEIPT_ACTION_RESTORE_VERSION,
            DeveloperControlPlaneApprovalReceipt.board_id == revision.board_id,
            DeveloperControlPlaneApprovalReceipt.target_revision_id == revision.id,
            DeveloperControlPlaneApprovalReceipt.resulting_board_concurrency_token
            == restored_hash,
        )
        return DeveloperControlPlaneBoardRestoreResponse(
            restored=False,
            restored_from_revision_id=revision.id,
            record=BoardService.record_response(current_record),
            approval_receipt=(
                LaneService.approval_receipt_response(existing_receipt)
                if existing_receipt is not None
                else None
            ),
        )

    restore_metadata = {
        "from_revision_id": revision.id,
        "from_concurrency_token": revision.canonical_board_hash,
        "previous_active_concurrency_token": previous_active_concurrency_token,
        "previous_active_revision_known": previous_active_concurrency_token is not None,
    }
    current_record = await board_service.apply_active_board_state(
        organization_id,
        current_user,
        current_record,
        canonical_board_json=canonical_board_json,
        board=board,
        save_source="restore-version",
        summary_metadata=build_summary_metadata(board, {"restore": restore_metadata}),
    )

    approval_receipt = await lane_service.record_approval_receipt(
        organization_id,
        current_user,
        action_type=APPROVAL_RECEIPT_ACTION_RESTORE_VERSION,
        outcome="applied",
        board_id=board.board_id,
        source_board_concurrency_token=previous_active_concurrency_token,
        resulting_board_concurrency_token=current_record.canonical_board_hash,
        target_revision_id=revision.id,
        previous_active_concurrency_token=previous_active_concurrency_token,
        rationale=f"Restore active board from immutable revision {revision.id}.",
        evidence_refs=[f"developer-control-plane:board-revision:{revision.id}"],
        summary_metadata={"restore": restore_metadata},
    )

    await db.commit()
    await db.refresh(current_record)
    return DeveloperControlPlaneBoardRestoreResponse(
        restored=True,
        restored_from_revision_id=revision.id,
        record=BoardService.record_response(current_record),
        approval_receipt=LaneService.approval_receipt_response(approval_receipt),
    )


@router.post("/active-board/prepare-completion-write")
async def prepare_active_board_completion_write(
    payload: DeveloperControlPlaneCompletionWritePreparationRequest,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
    _: User = Depends(get_current_superuser),
):
    from app.control_plane.application.board_service import BoardService
    from app.control_plane.domain.lane import find_board_lane
    from app.control_plane.domain.validation import DomainValidationError
    from app.api.bijmantra.developer.developer_control_plane import (
        _build_completion_write_preparation_response,
        _completion_write_conflict_detail,
        _ensure_persistence_schema_ready,
        _load_active_board_payload,
        _require_ascii_text,
    )
    await _ensure_persistence_schema_ready(db)

    requested_lane_id = _require_ascii_text(payload.source_lane_id, "source_lane_id")
    board_service = BoardService(db)
    current_record = await board_service.get_active_board(organization_id)
    if current_record is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_completion_write_conflict_detail(
                "missing-active-board",
                "Completion write preparation conflict; active board is missing for this organization",
            ),
        )

    board_payload = _load_active_board_payload(current_record)
    try:
        lane = find_board_lane(board_payload, requested_lane_id)
    except DomainValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    if lane is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lane {requested_lane_id} does not exist in the current active board",
        )

    return _build_completion_write_preparation_response(
        source_lane_id=requested_lane_id,
        source_board_concurrency_token=current_record.canonical_board_hash,
    )


class _CompletionWriteRequestProxy(BaseModel):
    """Proxy model for write-completion request body.

    Mirrors DeveloperControlPlaneCompletionWriteRequest from the parent module.
    FastAPI uses this for request body parsing; the handler validates the actual
    type at runtime after the lazy import resolves.
    """
    source_board_concurrency_token: str = Field(..., min_length=1, max_length=128)
    expected_queue_sha256: str = Field(..., min_length=1, max_length=128)
    operator_intent: str = Field(..., min_length=1, max_length=64)
    completion: dict


@router.post("/active-board/write-completion")
async def write_active_board_completion(
    payload: _CompletionWriteRequestProxy,
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
):
    from app.control_plane.application.board_service import BoardService
    from app.control_plane.contracts.api_schema import (
        DeveloperControlPlaneCompletionWriteRequest,
        DeveloperControlPlaneCompletionWriteResponse,
        DeveloperControlPlaneLaneCompletionPayload,
    )
    from app.control_plane.domain.board import build_summary_metadata
    from app.control_plane.domain.lane import (
        find_board_lane,
        lane_has_completion_verification_evidence,
    )
    from app.control_plane.domain.validation import DomainValidationError
    from app.control_plane.orchestration.queue_materializer import QueueMaterializer
    from app.control_plane.application.lane_service import (
        LaneService,
        build_lane_completion,
        is_same_lane_completion,
    )
    from app.control_plane.application.execution_service import ExecutionService
    from app.api.bijmantra.developer.developer_control_plane import (
        COMPLETION_WRITE_OPERATOR_INTENT,
        DEVELOPER_MASTER_BOARD_ID,
        DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
        _best_effort_ascii_text,
        _completion_write_conflict_detail,
        _deduplicate_strings,
        _ensure_approval_receipt_schema_ready,
        _ensure_mission_state_schema_ready,
        _ensure_persistence_schema_ready,
        _load_active_board_payload,
        _record_closeout_backed_mission_state,
        _review_gate_evidence_refs,
        _seed_approval_receipt_learnings_if_ready,
        _seed_mission_state_learnings_if_ready,
        _validate_completion_payload,
        _validate_queue_payload_shape,
    )
    from app.models.developer_control_plane import DeveloperControlPlaneApprovalReceipt
    import json
    from app.schemas.developer_control_plane import canonicalize_developer_master_board_json

    # Re-parse the completion field using the proper Pydantic model
    try:
        completion_obj = DeveloperControlPlaneLaneCompletionPayload(**payload.completion)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid completion payload: {exc}",
        ) from exc

    # Reconstruct as the proper request type
    try:
        typed_payload = DeveloperControlPlaneCompletionWriteRequest(
            source_board_concurrency_token=payload.source_board_concurrency_token,
            expected_queue_sha256=payload.expected_queue_sha256,
            operator_intent=payload.operator_intent,
            completion=completion_obj,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request body: {exc}",
        ) from exc

    payload = typed_payload

    await _ensure_persistence_schema_ready(db)
    await _ensure_approval_receipt_schema_ready(db)
    await _ensure_mission_state_schema_ready(db)
    lane_service = LaneService(db)
    if payload.operator_intent != COMPLETION_WRITE_OPERATOR_INTENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="operator_intent must acknowledge explicit completion write-back",
        )

    requested_lane_id = _best_effort_ascii_text(payload.completion.source_lane_id)
    requested_queue_job_id = _best_effort_ascii_text(payload.completion.queue_job_id)
    requested_source_board_token = _best_effort_ascii_text(
        payload.source_board_concurrency_token
    )

    current_record = await BoardService(db).get_active_board(organization_id)
    if current_record is None:
        conflict_detail = _completion_write_conflict_detail(
            "missing-active-board",
            "Completion write-back conflict; active board is missing for this organization",
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=DEVELOPER_MASTER_BOARD_ID,
            source_lane_id=requested_lane_id,
            queue_job_id=requested_queue_job_id,
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    queue_payload, _ = QueueMaterializer.load_overnight_queue_payload()
    queue_payload = _validate_queue_payload_shape(queue_payload)
    current_queue_sha256 = QueueMaterializer.queue_sha256(queue_payload)
    if payload.expected_queue_sha256 != current_queue_sha256:
        conflict_detail = _completion_write_conflict_detail(
            "queue-sha-mismatch",
            "Completion write-back conflict; overnight queue changed since the latest snapshot",
            current_queue_sha256=current_queue_sha256,
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=requested_lane_id,
            queue_job_id=requested_queue_job_id,
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    validated_completion = _validate_completion_payload(payload.completion)
    expected_queue_job_id = QueueMaterializer.create_lane_queue_job_id(
        validated_completion["source_lane_id"],
        payload.source_board_concurrency_token,
    )
    if validated_completion["queue_job_id"] != expected_queue_job_id:
        conflict_detail = _completion_write_conflict_detail(
            "lane-job-mismatch",
            "Completion write-back conflict; queue job id does not match the current lane and board provenance",
            expected_queue_job_id=expected_queue_job_id,
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    queue_job = QueueMaterializer.find_queue_job(queue_payload, validated_completion["queue_job_id"])
    if queue_job is None:
        conflict_detail = _completion_write_conflict_detail(
            "queue-job-missing",
            "Completion write-back conflict; queue job is missing from the current overnight queue snapshot",
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    if queue_job.get("status") != "completed":
        conflict_detail = _completion_write_conflict_detail(
            "queue-job-not-completed",
            "Completion write-back conflict; queue job must be completed before board write-back",
            current_queue_job_status=queue_job.get("status"),
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    current_closeout_receipt = ExecutionService.closeout_receipt_contract_from_response(
        ExecutionService.closeout_receipt_response(
            validated_completion["queue_job_id"],
            ExecutionService.load_closeout_receipt(validated_completion["queue_job_id"]),
        )
    )
    current_closeout_mission_id = (
        current_closeout_receipt.get("mission_id")
        if isinstance(current_closeout_receipt, dict)
        and isinstance(current_closeout_receipt.get("mission_id"), str)
        else None
    )
    requested_closeout_receipt = validated_completion["closeout_receipt"]
    if current_closeout_receipt is not None and requested_closeout_receipt is None:
        conflict_detail = _completion_write_conflict_detail(
            "closeout-receipt-required",
            "Completion write-back conflict; a stable closeout receipt exists and must be reviewed before board closure is written",
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
            linked_mission_id=current_closeout_mission_id,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    if current_closeout_receipt != requested_closeout_receipt:
        conflict_detail = _completion_write_conflict_detail(
            "closeout-receipt-mismatch",
            "Completion write-back conflict; reviewed closeout receipt does not match the latest normalized runtime evidence",
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
            linked_mission_id=current_closeout_mission_id,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    board_payload = _load_active_board_payload(current_record)
    try:
        lane = find_board_lane(board_payload, validated_completion["source_lane_id"])
    except DomainValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    if lane is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer control-plane lane not found",
        )

    if lane.get("status") == "completed":
        if is_same_lane_completion(
            lane.get("closure"),
            queue_job_id=validated_completion["queue_job_id"],
            queue_sha256=current_queue_sha256,
            source_board_concurrency_token=payload.source_board_concurrency_token,
            closure_summary=validated_completion["closure_summary"],
            evidence=validated_completion["evidence"],
            closeout_receipt=current_closeout_receipt,
        ):
            existing_receipt = await lane_service.get_latest_approval_receipt(
                organization_id,
                DeveloperControlPlaneApprovalReceipt.action_type
                == COMPLETION_WRITE_OPERATOR_INTENT,
                DeveloperControlPlaneApprovalReceipt.board_id == current_record.board_id,
                DeveloperControlPlaneApprovalReceipt.source_board_concurrency_token
                == payload.source_board_concurrency_token,
                DeveloperControlPlaneApprovalReceipt.source_lane_id
                == validated_completion["source_lane_id"],
                DeveloperControlPlaneApprovalReceipt.queue_job_id
                == validated_completion["queue_job_id"],
                DeveloperControlPlaneApprovalReceipt.resulting_board_concurrency_token
                == current_record.canonical_board_hash,
            )
            return DeveloperControlPlaneCompletionWriteResponse(
                no_op=True,
                lane_id=validated_completion["source_lane_id"],
                lane_status="completed",
                queue_job_id=validated_completion["queue_job_id"],
                queue_sha256=current_queue_sha256,
                record=BoardService.record_response(current_record),
                approval_receipt=(
                    LaneService.approval_receipt_response(existing_receipt)
                    if existing_receipt is not None
                    else None
                ),
            )
        conflict_detail = _completion_write_conflict_detail(
            "completion-overwrite-conflict",
            "Completion write-back conflict; completed lane already has different closure evidence",
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
            linked_mission_id=current_closeout_mission_id,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    if payload.source_board_concurrency_token != current_record.canonical_board_hash:
        conflict_detail = _completion_write_conflict_detail(
            "stale-board-token",
            "Completion write-back conflict; source board token is stale and must be refreshed",
            current_board_concurrency_token=current_record.canonical_board_hash,
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
            linked_mission_id=current_closeout_mission_id,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    if lane.get("status") != "active":
        conflict_detail = _completion_write_conflict_detail(
            "lane-status-conflict",
            "Completion write-back conflict; lane must be active before it can be marked completed",
            current_lane_status=lane.get("status"),
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
            linked_mission_id=current_closeout_mission_id,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    if not lane_has_completion_verification_evidence(lane):
        conflict_detail = _completion_write_conflict_detail(
            "lane-verification-missing",
            "Completion write-back conflict; canonical lane is missing explicit verification_evidence",
            current_lane_status=lane.get("status"),
        )
        await lane_service.persist_conflict_learning(
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
            linked_mission_id=current_closeout_mission_id,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)

    lane["status"] = "completed"
    lane["closure"] = build_lane_completion(
        queue_job_id=validated_completion["queue_job_id"],
        queue_sha256=current_queue_sha256,
        source_board_concurrency_token=payload.source_board_concurrency_token,
        closure_summary=validated_completion["closure_summary"],
        evidence=validated_completion["evidence"],
        closeout_receipt=current_closeout_receipt,
    )
    board_payload["version"] = DEVELOPER_MASTER_BOARD_SCHEMA_VERSION

    try:
        canonical_board_json, board = canonicalize_developer_master_board_json(
            json.dumps(board_payload)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid developer master board after completion write-back: {exc}",
        ) from exc

    board_service = BoardService(db)
    current_record = await board_service.apply_active_board_state(
        organization_id,
        current_user,
        current_record,
        canonical_board_json=canonical_board_json,
        board=board,
        save_source="write-completion",
        summary_metadata=build_summary_metadata(
            board,
            {
                "completion": {
                    "lane_id": validated_completion["source_lane_id"],
                    "queue_job_id": validated_completion["queue_job_id"],
                    "queue_sha256": current_queue_sha256,
                    "closeout_receipt_present": current_closeout_receipt is not None,
                    "closeout_receipt_recorded_at": current_closeout_receipt.get("receipt_recorded_at")
                    if current_closeout_receipt is not None
                    else None,
                    "closeout_receipt_mission_id": current_closeout_receipt.get("mission_id")
                    if current_closeout_receipt is not None
                    else None,
                    "closeout_receipt_producer_key": current_closeout_receipt.get("producer_key")
                    if current_closeout_receipt is not None
                    else None,
                    "closeout_receipt_runtime_profile_id": current_closeout_receipt.get("runtime_profile_id")
                    if current_closeout_receipt is not None
                    else None,
                    "closeout_receipt_runtime_policy_sha256": current_closeout_receipt.get("runtime_policy_sha256")
                    if current_closeout_receipt is not None
                    else None,
                }
            },
        ),
    )

    await _record_closeout_backed_mission_state(
        db,
        organization_id,
        lane_id=validated_completion["source_lane_id"],
        lane_title=lane.get("title") if isinstance(lane.get("title"), str) else None,
        queue_job_id=validated_completion["queue_job_id"],
        closure_summary=validated_completion["closure_summary"],
        closeout_receipt=current_closeout_receipt,
    )

    closeout_receipt_evidence_refs: list[str] = []
    if current_closeout_receipt is not None:
        verification_evidence_ref = current_closeout_receipt.get("verification_evidence_ref")
        if isinstance(verification_evidence_ref, str) and verification_evidence_ref.strip():
            closeout_receipt_evidence_refs.append(verification_evidence_ref)
        artifact_paths = current_closeout_receipt.get("artifact_paths")
        if isinstance(artifact_paths, list):
            closeout_receipt_evidence_refs.extend(
                item for item in artifact_paths if isinstance(item, str) and item.strip()
            )

    approval_receipt = await lane_service.record_approval_receipt(
        organization_id,
        current_user,
        action_type=COMPLETION_WRITE_OPERATOR_INTENT,
        outcome="applied",
        board_id=board.board_id,
        source_board_concurrency_token=payload.source_board_concurrency_token,
        resulting_board_concurrency_token=current_record.canonical_board_hash,
        source_lane_id=validated_completion["source_lane_id"],
        queue_job_id=validated_completion["queue_job_id"],
        expected_queue_sha256=payload.expected_queue_sha256,
        resulting_queue_sha256=current_queue_sha256,
        linked_mission_id=(
            current_closeout_receipt.get("mission_id")
            if isinstance(current_closeout_receipt, dict)
            and isinstance(current_closeout_receipt.get("mission_id"), str)
            else None
        ),
        rationale=(
            "Write reviewed completion evidence into the canonical developer control-plane "
            f"board for lane {validated_completion['source_lane_id']}."
        ),
        evidence_refs=_deduplicate_strings(
            [
                *_review_gate_evidence_refs(lane, "verification_evidence"),
                *closeout_receipt_evidence_refs,
            ]
        ),
        summary_metadata={
            "operator_evidence": validated_completion["evidence"],
            "closeout_receipt_present": current_closeout_receipt is not None,
        },
    )

    await _seed_approval_receipt_learnings_if_ready(db, organization_id)
    await _seed_mission_state_learnings_if_ready(db, organization_id)

    await db.commit()
    await db.refresh(current_record)

    return DeveloperControlPlaneCompletionWriteResponse(
        no_op=False,
        lane_id=validated_completion["source_lane_id"],
        lane_status="completed",
        queue_job_id=validated_completion["queue_job_id"],
        queue_sha256=current_queue_sha256,
        record=BoardService.record_response(current_record),
        approval_receipt=LaneService.approval_receipt_response(approval_receipt),
    )

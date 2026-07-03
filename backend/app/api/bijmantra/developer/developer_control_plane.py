"""Backend durability API for the hidden developer control-plane board.

Post-extraction maintenance note:
- Most business logic has been extracted into layered modules under
  ``app.control_plane.{domain,application,orchestration,contracts}``.
- This file retains: router definition, ``include_router`` composition,
  constants, schema re-exports, persistence-schema guards, learning-ledger
  helpers, conflict-detail builders, and backward-compatibility shims.
- New behavior should land in the appropriate extracted layer, not here.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_organization_id
from app.core.database import get_db
from app.models.core import User
from app.models.developer_control_plane import (
    DeveloperControlPlaneActiveBoard,
    DeveloperControlPlaneApprovalReceipt,
    DeveloperControlPlaneBoardRevision,
    DeveloperControlPlaneLearningEntry,
)
from app.modules.ai.services.claw_runtime_surface import (
    resolve_runtime_mission_evidence_dir,
    resolve_runtime_watchdog_state_path,
)
from app.modules.ai.services.developer_control_plane_autonomy_cycle import (
    resolve_developer_control_plane_autonomy_cycle_path,
)
from app.modules.ai.services.developer_control_plane_completion_assist import (
    resolve_developer_control_plane_completion_assist_path,
)
from app.modules.ai.services.developer_control_plane_completion_write import (
    build_developer_control_plane_completion_write_preparation_response_payload,
)
from app.modules.ai.services.orchestrator_state import (
    OrchestratorMissionStateService,
    SubtaskStatus,
    VerificationResult,
)
from app.modules.ai.services.orchestrator_state_postgres import PostgresMissionStateRepository
from app.schemas.developer_control_plane import (
    DEVELOPER_MASTER_BOARD_ID,
    DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
)
from app.control_plane.domain.validation import (
    DomainValidationError,
    DuplicateJobIdError,
    best_effort_ascii_text as _domain_best_effort_ascii_text,
    optional_ascii_text as _domain_optional_ascii_text,
    require_ascii_text as _domain_require_ascii_text,
    require_ascii_text_list as _domain_require_ascii_text_list,
    validate_completion_payload as _domain_validate_completion_payload,
    validate_queue_entry as _domain_validate_queue_entry,
    validate_queue_payload_shape as _domain_validate_queue_payload_shape,
)


router = APIRouter(
    prefix="/developer-control-plane",
    tags=["Developer Control Plane"],
    dependencies=[Depends(get_current_superuser)],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[4]
OVERNIGHT_QUEUE_PATH = REPO_ROOT / ".agent" / "jobs" / "overnight-queue.json"
MISSION_EVIDENCE_DIR = resolve_runtime_mission_evidence_dir(REPO_ROOT)
WATCHDOG_STATE_PATH = resolve_runtime_watchdog_state_path(REPO_ROOT)
AUTONOMY_CYCLE_PATH = resolve_developer_control_plane_autonomy_cycle_path(REPO_ROOT)
COMPLETION_ASSIST_PATH = resolve_developer_control_plane_completion_assist_path(REPO_ROOT)
CONTROL_SURFACE_CHECK_SCRIPT = REPO_ROOT / "scripts" / "check_control_surfaces.py"
REEVU_REAL_QUESTION_REPORT_PATH = (
    REPO_ROOT / "backend" / "test_reports" / "reevu_real_question_local.json"
)
REEVU_READINESS_CENSUS_PATH = (
    REPO_ROOT / "backend" / "test_reports" / "reevu_local_readiness_census.json"
)
REEVU_AUTHORITY_GAP_REPORT_PATH = (
    REPO_ROOT / "backend" / "test_reports" / "reevu_authority_gap_report.json"
)
QUEUE_STALENESS_WATCH_HOURS = 18
QUEUE_STALENESS_ALERT_HOURS = 36
SILENT_MONITOR_OUTPUT_ARTIFACT_PREFIX = "developer-control-plane.runtime.silent-monitors"
QUEUE_LANGUAGE = "en"
QUEUE_VOCABULARY_POLICY = "english-technical-only"
QUEUE_WRITE_OPERATOR_INTENT = "write-reviewed-queue-entry"
COMPLETION_WRITE_OPERATOR_INTENT = "write-reviewed-lane-completion"
APPROVAL_RECEIPT_ACTION_RESTORE_VERSION = "restore-active-board-version"
APPROVAL_RECEIPT_AUTHORITY_SOURCE = "developer-control-plane-api"
DEVELOPER_CONTROL_PLANE_PERSISTENCE_TABLES = (
    "developer_control_plane_active_boards",
    "developer_control_plane_board_revisions",
)
DEVELOPER_CONTROL_PLANE_APPROVAL_RECEIPT_TABLES = (
    "developer_control_plane_approval_receipts",
)
DEVELOPER_CONTROL_PLANE_APPROVAL_RECEIPT_SCHEMA_REVISION = "20260331_1100"
DEVELOPER_CONTROL_PLANE_LEARNING_TABLES = (
    "developer_control_plane_learning_entries",
)
DEVELOPER_CONTROL_PLANE_LEARNING_SCHEMA_REVISION = "20260331_1500"
CONTROL_PLANE_LEARNING_ENTRY_TYPES = (
    "pattern",
    "pitfall",
    "incident",
    "verification-learning",
)
MISSION_STATE_PERSISTENCE_TABLES = (
    "orchestrator_missions",
    "orchestrator_subtasks",
    "orchestrator_assignments",
    "orchestrator_evidence_items",
    "orchestrator_verification_runs",
    "orchestrator_decision_notes",
    "orchestrator_blockers",
)
MISSION_STATE_REQUIRED_COLUMNS = {
    "orchestrator_missions": (
        "producer_key",
        "queue_job_id",
        "source_lane_id",
        "source_board_concurrency_token",
    ),
}
# MISSION_LINKAGE_SOURCE_REQUEST_PATTERN lives in app.control_plane.domain.mission
# Import it from there if needed; do not redefine here.


# ---------------------------------------------------------------------------
# API schema models — imported from the frozen contracts layer.
# DO NOT redefine these here; the canonical source is
# app.control_plane.contracts.api_schema
# ---------------------------------------------------------------------------
from app.control_plane.contracts.api_schema import (  # noqa: E402
    DeveloperControlPlaneActiveBoardConflictResponse,
    DeveloperControlPlaneActiveBoardFetchResponse,
    DeveloperControlPlaneActiveBoardRecordResponse,
    DeveloperControlPlaneActiveBoardSaveRequest,
    DeveloperControlPlaneApprovalReceiptResponse,
    DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse,
    DeveloperControlPlaneAutonomyCycleActionResponse,
    DeveloperControlPlaneAutonomyCycleBlockedJobResponse,
    DeveloperControlPlaneAutonomyCycleCloseoutCandidateResponse,
    DeveloperControlPlaneAutonomyCycleJobErrorResponse,
    DeveloperControlPlaneAutonomyCycleResponse,
    DeveloperControlPlaneAutonomyCycleSelectedJobResponse,
    DeveloperControlPlaneAutonomyCycleWatchdogResponse,
    DeveloperControlPlaneBoardRestoreRequest,
    DeveloperControlPlaneBoardRestoreResponse,
    DeveloperControlPlaneBoardVersionResponse,
    DeveloperControlPlaneBoardVersionsListResponse,
    DeveloperControlPlaneCloseoutArtifactResponse,
    DeveloperControlPlaneCloseoutCommandResultResponse,
    DeveloperControlPlaneCloseoutReceiptResponse,
    DeveloperControlPlaneCompletionCloseoutReceiptPayload,
    DeveloperControlPlaneCompletionWritePreparationRequest,
    DeveloperControlPlaneCompletionWritePreparationResponse,
    DeveloperControlPlaneCompletionWriteRequest,
    DeveloperControlPlaneCompletionWriteResponse,
    DeveloperControlPlaneLaneCompletionPayload,
    DeveloperControlPlaneLearningEntryResponse,
    DeveloperControlPlaneLearningLedgerResponse,
    DeveloperControlPlaneMissionAssignmentResponse,
    DeveloperControlPlaneMissionBlockerResponse,
    DeveloperControlPlaneMissionBootstrapRequest,
    DeveloperControlPlaneMissionBootstrapResponse,
    DeveloperControlPlaneMissionDecisionNoteResponse,
    DeveloperControlPlaneMissionDetailResponse,
    DeveloperControlPlaneMissionEvidenceResponse,
    DeveloperControlPlaneMissionStateResponse,
    DeveloperControlPlaneMissionSubtaskResponse,
    DeveloperControlPlaneMissionSummaryResponse,
    DeveloperControlPlaneMissionVerificationRunResponse,
    DeveloperControlPlaneMissionVerificationSummaryResponse,
    DeveloperControlPlaneOvernightQueueStatusResponse,
    DeveloperControlPlaneOvernightQueueWriteRequest,
    DeveloperControlPlaneOvernightQueueWriteResponse,
    DeveloperControlPlaneRuntimeCompletionAssistResponse,
    DeveloperControlPlaneSilentMonitorEvidenceSourceResponse,
    DeveloperControlPlaneSilentMonitorResponse,
    DeveloperControlPlaneSilentMonitorsResponse,
    DeveloperControlPlaneWatchdogCompletionAssistAdvisoryResponse,
    DeveloperControlPlaneWatchdogJobResponse,
    DeveloperControlPlaneWatchdogStatusResponse,
)


# ---------------------------------------------------------------------------
# Domain-to-HTTP bridge helpers
# ---------------------------------------------------------------------------

def _raise_as_http(exc: DomainValidationError) -> None:
    """Translate a domain validation error into an HTTPException."""
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


# ---------------------------------------------------------------------------
# Extracted modules — imported here so thin routers can reach them via
# developer_control_plane.<name> without changing their import paths.
# ---------------------------------------------------------------------------
from app.api.bijmantra.developer.developer_control_plane_conflicts import (  # noqa: E402
    _completion_write_conflict_detail,
    _queue_write_conflict_detail,
)
from app.api.bijmantra.developer.developer_control_plane_learning import (  # noqa: E402
    _get_existing_learning_entry,
    _get_learning_entries,
    _learning_entry_response,
    _mission_learning_evidence_refs,
    _record_learning_entry,
    _seed_approval_receipt_learnings_if_ready,
    _seed_learning_entries,
    _seed_learning_entries_from_approval_receipts,
    _seed_learning_entries_from_mission_state,
    _seed_mission_state_learnings_if_ready,
)


def _require_ascii_text(value: Any, field_name: str) -> str:
    try:
        return _domain_require_ascii_text(value, field_name)
    except DomainValidationError as exc:
        _raise_as_http(exc)


def _require_ascii_text_list(value: Any, field_name: str, *, min_items: int = 0) -> list[str]:
    try:
        return _domain_require_ascii_text_list(value, field_name, min_items=min_items)
    except DomainValidationError as exc:
        _raise_as_http(exc)


def _optional_ascii_text(value: Any, field_name: str) -> str | None:
    try:
        return _domain_optional_ascii_text(value, field_name)
    except DomainValidationError as exc:
        _raise_as_http(exc)


def _best_effort_ascii_text(value: Any) -> str | None:
    return _domain_best_effort_ascii_text(value)


def _validate_queue_payload_shape(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return _domain_validate_queue_payload_shape(payload)
    except DomainValidationError as exc:
        _raise_as_http(exc)


def _validate_queue_entry(
    queue_entry: dict[str, Any],
    existing_job_ids: set[str],
) -> dict[str, Any]:
    try:
        return _domain_validate_queue_entry(queue_entry, existing_job_ids)
    except DuplicateJobIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_queue_write_conflict_detail(
                "duplicate-job-id",
                "Queue entry conflict; jobId already exists and create-only policy forbids overwrite",
                job_id=exc.job_id,
            ),
        ) from exc
    except DomainValidationError as exc:
        _raise_as_http(exc)


def _validate_completion_payload(
    payload: DeveloperControlPlaneLaneCompletionPayload,
) -> dict[str, Any]:
    try:
        return _domain_validate_completion_payload(payload)
    except DomainValidationError as exc:
        _raise_as_http(exc)


def _find_board_lane(board_payload: dict[str, Any], lane_id: str) -> dict[str, Any] | None:
    from app.control_plane.domain.lane import find_board_lane as _domain_find_board_lane
    try:
        return _domain_find_board_lane(board_payload, lane_id)
    except DomainValidationError as exc:
        _raise_as_http(exc)


# ---------------------------------------------------------------------------
# Persistence schema guards
# ---------------------------------------------------------------------------

async def _get_missing_required_tables(
    db: AsyncSession,
    required_tables: tuple[str, ...],
) -> list[str]:
    connection = await db.connection()

    def inspect_missing_tables(sync_connection: Any) -> list[str]:
        inspector = inspect(sync_connection)
        return [
            table_name
            for table_name in required_tables
            if not inspector.has_table(table_name)
        ]

    return await connection.run_sync(inspect_missing_tables)


async def _get_missing_persistence_tables(db: AsyncSession) -> list[str]:
    return await _get_missing_required_tables(db, DEVELOPER_CONTROL_PLANE_PERSISTENCE_TABLES)


async def _get_missing_approval_receipt_tables(db: AsyncSession) -> list[str]:
    return await _get_missing_required_tables(
        db,
        DEVELOPER_CONTROL_PLANE_APPROVAL_RECEIPT_TABLES,
    )


async def _get_missing_learning_tables(db: AsyncSession) -> list[str]:
    return await _get_missing_required_tables(
        db,
        DEVELOPER_CONTROL_PLANE_LEARNING_TABLES,
    )


async def _get_missing_mission_state_schema_requirements(
    db: AsyncSession,
) -> tuple[list[str], dict[str, list[str]]]:
    connection = await db.connection()

    def inspect_missing_requirements(
        sync_connection: Any,
    ) -> tuple[list[str], dict[str, list[str]]]:
        inspector = inspect(sync_connection)
        missing_tables = [
            table_name
            for table_name in MISSION_STATE_PERSISTENCE_TABLES
            if not inspector.has_table(table_name)
        ]
        missing_columns: dict[str, list[str]] = {}
        for table_name, required_columns in MISSION_STATE_REQUIRED_COLUMNS.items():
            if table_name in missing_tables:
                continue
            existing_columns = {
                column_info["name"] for column_info in inspector.get_columns(table_name)
            }
            absent_columns = [
                column_name
                for column_name in required_columns
                if column_name not in existing_columns
            ]
            if absent_columns:
                missing_columns[table_name] = absent_columns
        return missing_tables, missing_columns

    return await connection.run_sync(inspect_missing_requirements)


async def _ensure_persistence_schema_ready(db: AsyncSession) -> None:
    missing_tables = await _get_missing_persistence_tables(db)
    if not missing_tables:
        return

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Developer control-plane persistence schema is not ready; "
            f"missing table(s): {', '.join(sorted(missing_tables))}. "
            "Run backend alembic upgrade through revision 20260318_1500."
        ),
    )


async def _ensure_approval_receipt_schema_ready(db: AsyncSession) -> None:
    missing_tables = await _get_missing_approval_receipt_tables(db)
    if not missing_tables:
        return

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Developer control-plane approval receipt schema is not ready; "
            f"missing table(s): {', '.join(sorted(missing_tables))}. "
            "Run backend alembic upgrade through revision "
            f"{DEVELOPER_CONTROL_PLANE_APPROVAL_RECEIPT_SCHEMA_REVISION}."
        ),
    )


async def _ensure_learning_schema_ready(db: AsyncSession) -> None:
    missing_tables = await _get_missing_learning_tables(db)
    if not missing_tables:
        return

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Developer control-plane learnings ledger schema is not ready; "
            f"missing table(s): {', '.join(sorted(missing_tables))}. "
            "Run backend alembic upgrade through revision "
            f"{DEVELOPER_CONTROL_PLANE_LEARNING_SCHEMA_REVISION}."
        ),
    )


async def _ensure_mission_state_schema_ready(db: AsyncSession) -> None:
    missing_tables, missing_columns = await _get_missing_mission_state_schema_requirements(db)
    if not missing_tables and not missing_columns:
        return

    detail_parts = []
    if missing_tables:
        detail_parts.append(f"missing table(s): {', '.join(sorted(missing_tables))}")
    if missing_columns:
        missing_column_descriptions = [
            f"{table_name}.{column_name}"
            for table_name, column_names in sorted(missing_columns.items())
            for column_name in column_names
        ]
        detail_parts.append(
            f"missing column(s): {', '.join(missing_column_descriptions)}"
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Developer control-plane mission-state schema is not ready; "
            f"{'; '.join(detail_parts)}. "
            "Run backend alembic upgrade through revision 20260323_0100."
        ),
    )


# ---------------------------------------------------------------------------
# Board payload helpers (still used by thin routers)
# ---------------------------------------------------------------------------

def _load_active_board_payload(record: DeveloperControlPlaneActiveBoard) -> dict[str, Any]:
    try:
        payload = json.loads(record.canonical_board_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current active board payload is not valid JSON",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current active board payload must be a JSON object",
        )

    lanes = payload.get("lanes")
    if not isinstance(lanes, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current active board payload is missing lanes",
        )

    return payload


# ---------------------------------------------------------------------------
# Completion write preparation (used by lanes.py and dispatch_planner.py)
# ---------------------------------------------------------------------------

def _build_completion_write_preparation_response(
    *,
    source_lane_id: str,
    source_board_concurrency_token: str,
) -> DeveloperControlPlaneCompletionWritePreparationResponse:
    from app.control_plane.orchestration.queue_materializer import QueueMaterializer
    from app.control_plane.application.execution_service import ExecutionService

    queue_status = QueueMaterializer.overnight_queue_status_response()
    queue_job_id = QueueMaterializer.create_lane_queue_job_id(
        source_lane_id,
        source_board_concurrency_token,
    )
    closeout_receipt = ExecutionService.closeout_receipt_response(
        queue_job_id,
        ExecutionService.load_closeout_receipt(queue_job_id),
    )
    payload = build_developer_control_plane_completion_write_preparation_response_payload(
        source_lane_id=source_lane_id,
        source_board_concurrency_token=source_board_concurrency_token,
        expected_queue_sha256=queue_status.queue_sha256,
        queue_updated_at=queue_status.updated_at,
        queue_job_id=queue_job_id,
        queue_status=queue_status.model_dump(),
        closeout_receipt=closeout_receipt.model_dump(),
        operator_intent=COMPLETION_WRITE_OPERATOR_INTENT,
    )
    return DeveloperControlPlaneCompletionWritePreparationResponse.model_validate(payload)


# ---------------------------------------------------------------------------
# Utility helpers (used by thin routers)
# ---------------------------------------------------------------------------

def _deduplicate_strings(values: list[str]) -> list[str]:
    deduplicated: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(normalized)
    return deduplicated


def _review_gate_evidence_refs(lane: dict[str, Any], *review_gate_names: str) -> list[str]:
    review_state = lane.get("review_state")
    if not isinstance(review_state, dict):
        return []

    evidence_refs: list[str] = []
    for review_gate_name in review_gate_names:
        review_gate = review_state.get(review_gate_name)
        if not isinstance(review_gate, dict):
            continue
        gate_evidence = review_gate.get("evidence")
        if not isinstance(gate_evidence, list):
            continue
        evidence_refs.extend(
            item for item in gate_evidence if isinstance(item, str) and item.strip()
        )

    return _deduplicate_strings(evidence_refs)


# ---------------------------------------------------------------------------
# Learning ledger helpers — extracted to developer_control_plane_learning.py
# Imported above and re-exported here for backward compatibility.
# ---------------------------------------------------------------------------

# All learning-ledger functions now live in developer_control_plane_learning.py:
#   _learning_entry_response
#   _get_learning_entries
#   _get_existing_learning_entry
#   _record_learning_entry
#   _mission_learning_evidence_refs
#   _seed_learning_entries_from_approval_receipts
#   _seed_learning_entries_from_mission_state
#   _seed_learning_entries
#   _seed_approval_receipt_learnings_if_ready
#   _seed_mission_state_learnings_if_ready

# ---------------------------------------------------------------------------
# Conflict detail builders — extracted to developer_control_plane_conflicts.py
# Imported above and re-exported here for backward compatibility.
# ---------------------------------------------------------------------------

# All conflict-detail functions now live in developer_control_plane_conflicts.py:
#   _queue_write_conflict_detail
#   _completion_write_conflict_detail


# ---------------------------------------------------------------------------
# Conflict detail builders (used by thin routers)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Mission source request helpers (not yet extracted)
# ---------------------------------------------------------------------------

def _completion_mission_objective(lane_id: str, lane_title: str | None) -> str:
    if lane_title:
        return f"Reviewed closeout persistence for lane {lane_title}"
    return f"Reviewed closeout persistence for lane {lane_id}"


def _bootstrap_mission_objective(lane_id: str, lane_title: str | None) -> str:
    if lane_title:
        return f"Await canonical board closure for lane {lane_title}"
    return f"Await canonical board closure for lane {lane_id}"


def _completion_mission_source_request(
    lane_id: str,
    queue_job_id: str,
    closeout_receipt: dict[str, Any],
) -> str:
    return _mission_link_source_request(
        "explicit completion write-back",
        lane_id,
        queue_job_id,
        closeout_receipt,
    )


def _bootstrap_mission_source_request(
    lane_id: str,
    queue_job_id: str,
    closeout_receipt: dict[str, Any],
) -> str:
    return _mission_link_source_request(
        "stable closeout receipt observed",
        lane_id,
        queue_job_id,
        closeout_receipt,
    )


def _mission_link_source_request(
    event: str,
    lane_id: str,
    queue_job_id: str,
    closeout_receipt: dict[str, Any],
) -> str:
    source_request = (
        f"Developer control-plane {event} for lane {lane_id} "
        f"from queue job {queue_job_id}."
    )
    source_board_concurrency_token = closeout_receipt.get("source_board_concurrency_token")
    if isinstance(source_board_concurrency_token, str) and source_board_concurrency_token:
        source_request += (
            f" Context: source_board_concurrency_token={source_board_concurrency_token}."
        )
    return source_request


async def _lookup_active_board_lane_title(
    db: AsyncSession,
    organization_id: int,
    lane_id: str,
) -> str | None:
    from app.control_plane.application.board_service import BoardService

    current_record = await BoardService(db).get_active_board(organization_id)
    if current_record is None:
        return None

    try:
        board_payload = json.loads(current_record.canonical_board_json)
    except json.JSONDecodeError:
        return None

    lanes = board_payload.get("lanes")
    if not isinstance(lanes, list):
        return None

    lane = next(
        (
            entry
            for entry in lanes
            if isinstance(entry, dict) and entry.get("id") == lane_id
        ),
        None,
    )
    return lane.get("title") if isinstance(lane, dict) and isinstance(lane.get("title"), str) else None


def _closeout_receipt_verification_result(
    closeout_receipt: dict[str, Any],
) -> VerificationResult:
    status_value = closeout_receipt.get("closeout_status")
    if status_value == "failed":
        return VerificationResult.FAILED
    if status_value in {"passed", "skipped"}:
        return VerificationResult.PASSED
    return VerificationResult.WARN


# ---------------------------------------------------------------------------
# Mission bootstrap and closeout-backed state (not yet extracted)
# ---------------------------------------------------------------------------

async def _bootstrap_closeout_receipt_mission_state(
    db: AsyncSession,
    organization_id: int,
    *,
    queue_job_id: str,
    closeout_receipt: dict[str, Any] | None,
) -> DeveloperControlPlaneMissionBootstrapResponse:
    if closeout_receipt is None:
        return DeveloperControlPlaneMissionBootstrapResponse(action="missing-receipt", mission_id=None)

    mission_id = closeout_receipt.get("mission_id")
    if not isinstance(mission_id, str) or not mission_id:
        return DeveloperControlPlaneMissionBootstrapResponse(action="missing-mission-id", mission_id=None)

    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    existing = await service.repository.get_mission(mission_id)
    if existing is not None:
        return DeveloperControlPlaneMissionBootstrapResponse(action="existing", mission_id=mission_id)

    lane_id = (
        closeout_receipt.get("source_lane_id")
        if isinstance(closeout_receipt.get("source_lane_id"), str) and closeout_receipt.get("source_lane_id")
        else queue_job_id
    )
    lane_title = await _lookup_active_board_lane_title(db, organization_id, lane_id)
    mission = await service.register_mission(
        mission_id=mission_id,
        objective=_bootstrap_mission_objective(lane_id, lane_title),
        owner="OmShriMaatreNamaha",
        priority="p1",
        source_request=_bootstrap_mission_source_request(lane_id, queue_job_id, closeout_receipt),
        producer_key=(
            closeout_receipt.get("producer_key")
            if isinstance(closeout_receipt.get("producer_key"), str)
            else "developer-control-plane"
        ),
        queue_job_id=queue_job_id,
        source_lane_id=(
            closeout_receipt.get("source_lane_id")
            if isinstance(closeout_receipt.get("source_lane_id"), str)
            else lane_id
        ),
        source_board_concurrency_token=(
            closeout_receipt.get("source_board_concurrency_token")
            if isinstance(closeout_receipt.get("source_board_concurrency_token"), str)
            else None
        ),
    )
    closeout_receipt_path = f"runtime-artifacts/mission-evidence/{queue_job_id}/closeout.json"
    closeout_evidence = await service.record_evidence(
        mission_id=mission.id,
        kind="closeout_receipt",
        source_path=closeout_receipt_path,
        evidence_class="runtime-receipt",
        summary=f"Stable closeout receipt is available for queue job {queue_job_id}.",
    )

    verification_evidence_ref = closeout_receipt.get("verification_evidence_ref")
    if isinstance(verification_evidence_ref, str) and verification_evidence_ref:
        await service.record_evidence(
            mission_id=mission.id,
            kind="verification_evidence",
            source_path=verification_evidence_ref,
            evidence_class="runtime-verification",
            summary=f"Verification evidence is available for queue job {queue_job_id}.",
        )

    await service.record_verification_run(
        subject_id=mission.id,
        verification_type="runtime_closeout_receipt_observed",
        result=_closeout_receipt_verification_result(closeout_receipt),
        evidence_ref=closeout_evidence.id,
    )
    await service.record_decision_note(
        mission_id=mission.id,
        decision_class="stable_closeout_receipt_observed",
        rationale=(
            f"Stable runtime closeout receipt was captured for lane {lane_id} "
            f"from queue job {queue_job_id} before canonical board closure."
        ),
        authority_source="OmShriMaatreNamaha",
    )
    return DeveloperControlPlaneMissionBootstrapResponse(action="created", mission_id=mission.id)


async def _record_closeout_backed_mission_state(
    db: AsyncSession,
    organization_id: int,
    *,
    lane_id: str,
    lane_title: str | None,
    queue_job_id: str,
    closure_summary: str,
    closeout_receipt: dict[str, Any] | None,
) -> None:
    if closeout_receipt is None:
        return

    mission_id = closeout_receipt.get("mission_id")
    if not isinstance(mission_id, str) or not mission_id:
        return

    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    existing = await service.repository.get_mission(mission_id)
    if existing is None:
        mission = await service.register_mission(
            mission_id=mission_id,
            objective=_completion_mission_objective(lane_id, lane_title),
            owner="OmShriMaatreNamaha",
            priority="p1",
            source_request=_completion_mission_source_request(
                lane_id,
                queue_job_id,
                closeout_receipt,
            ),
            producer_key=(
                closeout_receipt.get("producer_key")
                if isinstance(closeout_receipt.get("producer_key"), str)
                else "developer-control-plane"
            ),
            queue_job_id=queue_job_id,
            source_lane_id=(
                closeout_receipt.get("source_lane_id")
                if isinstance(closeout_receipt.get("source_lane_id"), str)
                else lane_id
            ),
            source_board_concurrency_token=(
                closeout_receipt.get("source_board_concurrency_token")
                if isinstance(closeout_receipt.get("source_board_concurrency_token"), str)
                else None
            ),
        )
    else:
        mission = await service.repository.save_mission(
            replace(
                existing,
                objective=_completion_mission_objective(lane_id, lane_title),
                producer_key=(
                    closeout_receipt.get("producer_key")
                    if isinstance(closeout_receipt.get("producer_key"), str)
                    else existing.producer_key
                ),
                queue_job_id=queue_job_id,
                source_lane_id=(
                    closeout_receipt.get("source_lane_id")
                    if isinstance(closeout_receipt.get("source_lane_id"), str)
                    else existing.source_lane_id or lane_id
                ),
                source_board_concurrency_token=(
                    closeout_receipt.get("source_board_concurrency_token")
                    if isinstance(closeout_receipt.get("source_board_concurrency_token"), str)
                    else existing.source_board_concurrency_token
                ),
                source_request=_completion_mission_source_request(
                    lane_id,
                    queue_job_id,
                    closeout_receipt,
                ),
                updated_at=datetime.now(UTC),
            )
        )

    snapshot = await service.get_mission_snapshot(mission.id)
    subtask = await service.add_subtask(
        mission_id=mission.id,
        title="Persist reviewed closeout evidence",
        owner_role="OmVishnaveNamah",
    )
    await service.update_subtask_status(subtask.id, SubtaskStatus.COMPLETED)
    assignment = await service.assign_subtask(
        subtask_id=subtask.id,
        assigned_role="OmVishnaveNamah",
        handoff_reason="Verify reviewed runtime evidence before durable mission closeout.",
    )
    await service.complete_assignment(assignment.id)

    closeout_receipt_path = f"runtime-artifacts/mission-evidence/{queue_job_id}/closeout.json"
    existing_evidence_keys = {
        (item.kind, item.source_path)
        for item in snapshot.evidence_items
    }
    if ("closeout_receipt", closeout_receipt_path) in existing_evidence_keys:
        closeout_evidence = next(
            item
            for item in snapshot.evidence_items
            if item.kind == "closeout_receipt" and item.source_path == closeout_receipt_path
        )
    else:
        closeout_evidence = await service.record_evidence(
            subtask_id=subtask.id,
            kind="closeout_receipt",
            source_path=closeout_receipt_path,
            evidence_class="runtime-receipt",
            summary=f"Stable closeout receipt was reviewed for queue job {queue_job_id}.",
        )

    verification_evidence_ref = closeout_receipt.get("verification_evidence_ref")
    if isinstance(verification_evidence_ref, str) and verification_evidence_ref:
        if ("verification_evidence", verification_evidence_ref) not in existing_evidence_keys:
            await service.record_evidence(
                subtask_id=subtask.id,
                kind="verification_evidence",
                source_path=verification_evidence_ref,
                evidence_class="runtime-verification",
                summary=f"Verification evidence was preserved for queue job {queue_job_id}.",
            )

    await service.record_verification_run(
        subject_id=subtask.id,
        verification_type="closeout_receipt_review",
        result=VerificationResult.PASSED,
        evidence_ref=closeout_evidence.id,
    )
    await service.record_decision_note(
        mission_id=mission.id,
        decision_class="reviewed_completion_writeback",
        rationale=(
            f"Canonical board closure accepted reviewed runtime evidence for lane {lane_id} "
            f"from queue job {queue_job_id}."
        ),
        authority_source="OmShriMaatreNamaha",
    )
    await service.complete_mission(
        mission.id,
        (
            f"Canonical board closure persisted reviewed runtime provenance for lane {lane_id}. "
            f"Closure summary: {closure_summary}"
        ),
    )


# ---------------------------------------------------------------------------
# Backward-compatibility shims for external consumers
# These thin wrappers delegate to extracted modules and are kept so that
# existing lazy imports (e.g. from developer_control_plane_mem0.py,
# dispatch_planner.py) continue to resolve.  New code should import
# directly from the extracted modules.
#
# Deprecation warnings are emitted at call time (not import time) so that
# test suites and static analysis tools can still import the module without
# noise.  The warnings point to the canonical new module location.
# ---------------------------------------------------------------------------



def _load_closeout_receipt(queue_job_id: str) -> dict[str, Any] | None:
    """Shim — delegates to ExecutionService.

    .. deprecated::
        Import directly from ``app.control_plane.application.execution_service.ExecutionService``.
    """
    _warnings.warn(
        "Importing _load_closeout_receipt from developer_control_plane is deprecated. "
        "Use app.control_plane.application.execution_service.ExecutionService.load_closeout_receipt instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.application.execution_service import ExecutionService
    return ExecutionService.load_closeout_receipt(queue_job_id)


def _closeout_receipt_response(
    queue_job_id: str,
    receipt: dict[str, Any] | None,
) -> DeveloperControlPlaneCloseoutReceiptResponse:
    """Shim — delegates to ExecutionService.

    .. deprecated::
        Import directly from ``app.control_plane.application.execution_service.ExecutionService``.
    """
    _warnings.warn(
        "Importing _closeout_receipt_response from developer_control_plane is deprecated. "
        "Use app.control_plane.application.execution_service.ExecutionService.closeout_receipt_response instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.application.execution_service import ExecutionService
    return ExecutionService.closeout_receipt_response(queue_job_id, receipt)


async def _load_runtime_mission_snapshot(
    db: AsyncSession,
    organization_id: int,
    mission_id: str,
):
    """Shim — delegates to MissionService.

    .. deprecated::
        Import directly from ``app.control_plane.application.mission_service.MissionService``.
    """
    _warnings.warn(
        "Importing _load_runtime_mission_snapshot from developer_control_plane is deprecated. "
        "Use app.control_plane.application.mission_service.MissionService.load_runtime_mission_snapshot instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.application.mission_service import MissionService
    return await MissionService(db).load_runtime_mission_snapshot(organization_id, mission_id)


def _mission_detail_response(
    snapshot: Any,
) -> DeveloperControlPlaneMissionDetailResponse:
    """Shim — delegates to MissionService.

    .. deprecated::
        Import directly from ``app.control_plane.application.mission_service.MissionService``.
    """
    _warnings.warn(
        "Importing _mission_detail_response from developer_control_plane is deprecated. "
        "Use app.control_plane.application.mission_service.MissionService.mission_detail_response instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.application.mission_service import MissionService
    return MissionService.mission_detail_response(snapshot)


async def _get_active_board(
    db: AsyncSession,
    organization_id: int,
) -> DeveloperControlPlaneActiveBoard | None:
    """Shim — delegates to BoardService.

    .. deprecated::
        Import directly from ``app.control_plane.application.board_service.BoardService``.
    """
    _warnings.warn(
        "Importing _get_active_board from developer_control_plane is deprecated. "
        "Use app.control_plane.application.board_service.BoardService.get_active_board instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.application.board_service import BoardService
    return await BoardService(db).get_active_board(organization_id)


# ---------------------------------------------------------------------------
# Additional backward-compatibility re-exports for extracted modules
# These re-exports ensure that code importing domain entities, application
# services, and orchestration classes from this file continues to work.
# New code should import directly from the extracted modules.
# ---------------------------------------------------------------------------

def _get_board_versions(db: AsyncSession, organization_id: int):
    """Shim — delegates to BoardService.get_board_versions.

    .. deprecated::
        Import directly from ``app.control_plane.application.board_service.BoardService``.
    """
    _warnings.warn(
        "Importing _get_board_versions from developer_control_plane is deprecated. "
        "Use app.control_plane.application.board_service.BoardService.get_board_versions instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.application.board_service import BoardService
    return BoardService(db).get_board_versions(organization_id)


def _record_response(record: DeveloperControlPlaneActiveBoard):
    """Shim — delegates to BoardService.record_response.

    .. deprecated::
        Import directly from ``app.control_plane.application.board_service.BoardService``.
    """
    _warnings.warn(
        "Importing _record_response from developer_control_plane is deprecated. "
        "Use app.control_plane.application.board_service.BoardService.record_response instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.application.board_service import BoardService
    return BoardService.record_response(record)


def _mission_summary_response(snapshot: Any):
    """Shim — delegates to MissionService.mission_summary_response.

    .. deprecated::
        Import directly from ``app.control_plane.application.mission_service.MissionService``.
    """
    _warnings.warn(
        "Importing _mission_summary_response from developer_control_plane is deprecated. "
        "Use app.control_plane.application.mission_service.MissionService.mission_summary_response instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.application.mission_service import MissionService
    return MissionService.mission_summary_response(snapshot)


def _hash_canonical_board_json(canonical_board_json: str) -> str:
    """Shim — delegates to domain board module.

    .. deprecated::
        Import directly from ``app.control_plane.domain.board.hash_canonical_board_json``.
    """
    _warnings.warn(
        "Importing _hash_canonical_board_json from developer_control_plane is deprecated. "
        "Use app.control_plane.domain.board.hash_canonical_board_json instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.domain.board import hash_canonical_board_json
    return hash_canonical_board_json(canonical_board_json)


def _build_summary_metadata(board: Any, extra_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Shim — delegates to domain board module.

    .. deprecated::
        Import directly from ``app.control_plane.domain.board.build_summary_metadata``.
    """
    _warnings.warn(
        "Importing _build_summary_metadata from developer_control_plane is deprecated. "
        "Use app.control_plane.domain.board.build_summary_metadata instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.domain.board import build_summary_metadata
    return build_summary_metadata(board, extra_metadata)


def _has_meaningful_text(value: Any) -> bool:
    """Shim — delegates to domain lane module.

    .. deprecated::
        Import directly from ``app.control_plane.domain.lane.has_meaningful_text``.
    """
    _warnings.warn(
        "Importing _has_meaningful_text from developer_control_plane is deprecated. "
        "Use app.control_plane.domain.lane.has_meaningful_text instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.domain.lane import has_meaningful_text
    return has_meaningful_text(value)


def _has_meaningful_text_list(value: Any) -> bool:
    """Shim — delegates to domain lane module.

    .. deprecated::
        Import directly from ``app.control_plane.domain.lane.has_meaningful_text_list``.
    """
    _warnings.warn(
        "Importing _has_meaningful_text_list from developer_control_plane is deprecated. "
        "Use app.control_plane.domain.lane.has_meaningful_text_list instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.domain.lane import has_meaningful_text_list
    return has_meaningful_text_list(value)


def _has_complete_review_gate(review_gate: Any) -> bool:
    """Shim — delegates to domain lane module.

    .. deprecated::
        Import directly from ``app.control_plane.domain.lane.has_complete_review_gate``.
    """
    _warnings.warn(
        "Importing _has_complete_review_gate from developer_control_plane is deprecated. "
        "Use app.control_plane.domain.lane.has_complete_review_gate instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.domain.lane import has_complete_review_gate
    return has_complete_review_gate(review_gate)


def _lane_has_queue_export_reviews(lane: dict[str, Any]) -> bool:
    """Shim — delegates to domain lane module.

    .. deprecated::
        Import directly from ``app.control_plane.domain.lane.lane_has_queue_export_reviews``.
    """
    _warnings.warn(
        "Importing _lane_has_queue_export_reviews from developer_control_plane is deprecated. "
        "Use app.control_plane.domain.lane.lane_has_queue_export_reviews instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.domain.lane import lane_has_queue_export_reviews
    return lane_has_queue_export_reviews(lane)


def _lane_has_completion_verification_evidence(lane: dict[str, Any]) -> bool:
    """Shim — delegates to domain lane module.

    .. deprecated::
        Import directly from ``app.control_plane.domain.lane.lane_has_completion_verification_evidence``.
    """
    _warnings.warn(
        "Importing _lane_has_completion_verification_evidence from developer_control_plane is deprecated. "
        "Use app.control_plane.domain.lane.lane_has_completion_verification_evidence instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.control_plane.domain.lane import lane_has_completion_verification_evidence
    return lane_has_completion_verification_evidence(lane)


# ---------------------------------------------------------------------------
# Composition shell — include thin routers for each responsibility domain.
# These imports are at the bottom to avoid circular imports: the thin routers
# use lazy imports (inside function bodies) to reference symbols defined above.
# ---------------------------------------------------------------------------

from app.api.bijmantra.control_plane import lanes as _lanes_router_module  # noqa: E402
from app.api.bijmantra.control_plane import missions as _missions_router_module  # noqa: E402
from app.api.bijmantra.control_plane import verification as _verification_router_module  # noqa: E402
from app.api.bijmantra.control_plane import telemetry as _telemetry_router_module  # noqa: E402

router.include_router(_lanes_router_module.router)
router.include_router(_missions_router_module.router)
router.include_router(_verification_router_module.router)
router.include_router(_telemetry_router_module.router)

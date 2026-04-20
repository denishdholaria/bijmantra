"""Backend durability API for the hidden developer control-plane board.

Interim maintenance note:
- Read DEVELOPER_CONTROL_PLANE_AGENT_INDEX before adding new behavior here.
- This file is a hot control-surface module; prefer extraction-first slices instead of
    making this endpoint module the permanent landing zone for every queue, board,
    approval, learning, or runtime concern.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, ValidationError
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
from app.modules.ai.services.claw_runtime_contract import (
    normalize_runtime_reference,
    runtime_auth_store_path,
)
from app.modules.ai.services.claw_runtime_surface import (
    display_runtime_artifact_path,
    resolve_runtime_mission_evidence_dir,
    resolve_runtime_watchdog_state_path,
    runtime_watchdog_state_freshness,
)
from app.modules.ai.services.developer_control_plane_autonomy_cycle import (
    build_developer_control_plane_learning_queries,
    load_developer_control_plane_autonomy_cycle,
    resolve_developer_control_plane_autonomy_cycle_path,
    score_developer_control_plane_autonomy_action,
)
from app.modules.ai.services.developer_control_plane_completion_assist import (
    load_developer_control_plane_completion_assist,
    resolve_developer_control_plane_completion_assist_path,
)
from app.modules.ai.services.developer_control_plane_completion_write import (
    build_developer_control_plane_first_actionable_completion_write_payload,
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
    build_developer_master_board_summary,
    canonicalize_developer_master_board_json,
)
from app.services.control_plane import telemetry_service


router = APIRouter(
    prefix="/developer-control-plane",
    tags=["Developer Control Plane"],
    dependencies=[Depends(get_current_superuser)],
)

# AI agents should read this index before adding behavior to this module.
DEVELOPER_CONTROL_PLANE_AGENT_INDEX = """
agent_index_version: 2026-04-03

purpose:
- Hidden developer control-plane durability and workflow-governance API.
- Owns the authenticated HTTP contract for board state, overnight queue persistence,
    approval receipts, learning ledger reads, and closeout visibility.

current_decision:
- Keep this file authoritative for the HTTP surface and request-shape semantics.
- Do not keep expanding this module as the long-term home for every persistence,
    runtime-inspection, or closeout workflow detail.
- Continue through extraction-first slices: if a change introduces substantial new
    workflow logic, move that family into helpers or services first and keep this
    endpoint module thin.

module_map:
- Route surface: overnight queue, active board, approval receipt, learning ledger,
    closeout, and readiness endpoints.
- Local responsibilities: request and response models, file-path constants,
    endpoint guards, and orchestration glue into services or repositories.
- Growth pressure zones: queue JSON mutation, approval receipt write-back,
    mission linkage, closeout artifact inspection, and learning-ledger assembly.

edit_rules:
- Acceptable direct edits: local contract fixes, auth corrections, response-shape
    fixes, small persistence guards, and one-endpoint bug fixes.
- Extraction-first trigger: new workflow family, new runtime artifact family,
    new persistence branch, or any change that adds more than about 40 lines of
    business logic to one endpoint path.
- If a change touches queue write flow plus approval or closeout flow in the same
    slice, stop and extract shared helpers or services before continuing.
- Preserve Backend API v2 discipline: endpoint handlers stay thin and database or
    filesystem orchestration should move outward when it stops being local glue.

candidate_extraction_order:
- queue read and write helpers plus hash and staleness computation
- approval receipt and learning-ledger serialization helpers
- closeout and mission-linkage artifact inspection helpers
- board revision restore and persistence validation helpers

hotspots:
- overnight queue mutation and reviewed write-back
- approval receipt linkage and closeout state reconciliation
- learning ledger response assembly
- runtime artifact, watchdog, and mission evidence inspection
"""

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
MISSION_LINKAGE_SOURCE_REQUEST_PATTERN = re.compile(
    r"^Developer control-plane "
    r"(?P<event>explicit completion write-back|stable closeout receipt observed) for lane "
    r"(?P<lane_id>[^ ]+) from queue job (?P<queue_job_id>[^.]+)\."
    r"(?: Context: source_board_concurrency_token=(?P<board_token>[^.]+)\.)?$"
)


class DeveloperControlPlaneOvernightQueueStatusResponse(BaseModel):
    queue_path: str
    queue_sha256: str
    exists: bool
    job_count: int
    updated_at: str | None


class DeveloperControlPlaneOvernightQueueWriteRequest(BaseModel):
    source_board_concurrency_token: str = Field(..., min_length=1, max_length=128)
    expected_queue_sha256: str = Field(..., min_length=1, max_length=128)
    operator_intent: str = Field(..., min_length=1, max_length=64)
    queue_entry: dict[str, Any]


class DeveloperControlPlaneApprovalReceiptResponse(BaseModel):
    receipt_id: int
    organization_id: int
    action_type: str
    outcome: str
    authority_actor_user_id: int
    authority_actor_email: str | None = None
    authority_source: str
    board_id: str
    source_board_concurrency_token: str | None = None
    resulting_board_concurrency_token: str | None = None
    source_lane_id: str | None = None
    queue_job_id: str | None = None
    expected_queue_sha256: str | None = None
    resulting_queue_sha256: str | None = None
    target_revision_id: int | None = None
    previous_active_concurrency_token: str | None = None
    linked_mission_id: str | None = None
    rationale: str
    evidence_refs: list[str] = []
    summary_metadata: dict[str, Any] | None = None
    recorded_at: datetime


class DeveloperControlPlaneLearningEntryResponse(BaseModel):
    learning_entry_id: int
    organization_id: int
    entry_type: str
    source_classification: str
    title: str
    summary: str
    confidence_score: float | None = None
    recorded_by_user_id: int | None = None
    recorded_by_email: str | None = None
    board_id: str | None = None
    source_lane_id: str | None = None
    queue_job_id: str | None = None
    linked_mission_id: str | None = None
    approval_receipt_id: int | None = None
    source_reference: str | None = None
    evidence_refs: list[str] = []
    summary_metadata: dict[str, Any] | None = None
    recorded_at: datetime


class DeveloperControlPlaneLearningLedgerResponse(BaseModel):
    total_count: int
    entries: list[DeveloperControlPlaneLearningEntryResponse] = []


class DeveloperControlPlaneOvernightQueueWriteResponse(BaseModel):
    queue_sha256: str
    queue_updated_at: str
    written_job_id: str
    replaced: bool
    approval_receipt: DeveloperControlPlaneApprovalReceiptResponse | None = None


class DeveloperControlPlaneCloseoutCommandResultResponse(BaseModel):
    command: str
    passed: bool
    exit_code: int | None
    started_at: str | None
    finished_at: str | None
    stdout_tail: str | None
    stderr_tail: str | None


class DeveloperControlPlaneCloseoutArtifactResponse(BaseModel):
    path: str
    exists: bool
    sha256: str | None
    modified_at: str | None


class DeveloperControlPlaneCloseoutReceiptResponse(BaseModel):
    exists: bool
    queue_job_id: str
    mission_id: str | None = None
    producer_key: str | None = None
    source_lane_id: str | None = None
    source_board_concurrency_token: str | None = None
    runtime_profile_id: str | None = None
    runtime_policy_sha256: str | None = None
    closeout_status: str | None = None
    state_refresh_required: bool | None = None
    receipt_recorded_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    verification_evidence_ref: str | None = None
    queue_sha256_at_closeout: str | None = None
    closeout_commands: list[DeveloperControlPlaneCloseoutCommandResultResponse] = []
    artifacts: list[DeveloperControlPlaneCloseoutArtifactResponse] = []


class DeveloperControlPlaneCompletionCloseoutReceiptPayload(BaseModel):
    queue_job_id: str = Field(..., min_length=1, max_length=256)
    artifact_paths: list[str] = []
    mission_id: str | None = Field(default=None, min_length=1, max_length=256)
    producer_key: str | None = Field(default=None, min_length=1, max_length=128)
    source_lane_id: str | None = Field(default=None, min_length=1, max_length=128)
    source_board_concurrency_token: str | None = Field(default=None, min_length=1, max_length=128)
    runtime_profile_id: str | None = Field(default=None, min_length=1, max_length=128)
    runtime_policy_sha256: str | None = Field(default=None, min_length=1, max_length=128)
    closeout_status: str | None = Field(default=None, min_length=1, max_length=64)
    state_refresh_required: bool | None = None
    receipt_recorded_at: str | None = Field(default=None, min_length=1, max_length=64)
    verification_evidence_ref: str | None = Field(default=None, min_length=1, max_length=512)
    queue_sha256_at_closeout: str | None = Field(default=None, min_length=1, max_length=128)


class DeveloperControlPlaneWatchdogJobResponse(BaseModel):
    job_id: str
    label: str | None = None
    status: str | None = None
    started_at: str | None = None
    duration_minutes: float | None = None
    last_error: str | None = None
    consecutive_errors: int | None = None
    branch: str | None = None
    verification_passed: bool | None = None


class DeveloperControlPlaneWatchdogCompletionAssistAdvisoryResponse(BaseModel):
    authority: str = "advisory-only-derived"
    observed_from_path: str | None = None
    available: bool = False
    artifact_path: str | None = None
    status: str | None = None
    staged: bool = False
    explicit_write_required: bool = True
    message: str | None = None
    source_lane_id: str | None = None
    queue_job_id: str | None = None
    draft_source: str | None = None
    receipt_path: str | None = None
    source_endpoint: str | None = None
    autonomy_cycle_artifact_path: str | None = None
    next_action_ordering_source: str | None = None
    matched_selected_job_ids: list[str] = []


class DeveloperControlPlaneWatchdogStatusResponse(BaseModel):
    exists: bool
    state_path: str
    auth_store_exists: bool
    auth_store_path: str
    bootstrap_ready: bool
    bootstrap_status: str
    mission_evidence_dir_exists: bool
    mission_evidence_dir_path: str
    last_check: str | None = None
    state_age_seconds: int | None = None
    state_is_stale: bool = False
    gateway_healthy: bool | None = None
    total_checks: int = 0
    total_alerts: int = 0
    job_count: int = 0
    jobs: list[DeveloperControlPlaneWatchdogJobResponse] = []
    completion_assist_advisory: (
        DeveloperControlPlaneWatchdogCompletionAssistAdvisoryResponse | None
    ) = None


class DeveloperControlPlaneAutonomyCycleJobErrorResponse(BaseModel):
    last_error: str | None = None
    consecutive_errors: int | None = None


class DeveloperControlPlaneAutonomyCycleWatchdogResponse(BaseModel):
    exists: bool
    state_path: str
    last_check: str | None = None
    gateway_healthy: bool | None = None
    state_is_stale: bool = False
    total_alerts: int = 0
    job_errors: dict[str, DeveloperControlPlaneAutonomyCycleJobErrorResponse] = {}


class DeveloperControlPlaneAutonomyCycleSelectedJobResponse(BaseModel):
    job_id: str
    title: str
    source_lane_id: str | None = None
    priority: str
    primary_agent: str
    trigger_reason: str | None = None
    source_task: str | None = None


class DeveloperControlPlaneAutonomyCycleBlockedJobResponse(BaseModel):
    job_id: str
    title: str
    source_lane_id: str | None = None
    reason: str | None = None


class DeveloperControlPlaneAutonomyCycleCloseoutCandidateResponse(BaseModel):
    job_id: str
    title: str | None = None
    source_lane_id: str | None = None
    queue_status: str | None = None
    closeout_status: str | None = None
    mission_id: str | None = None
    verification_evidence_ref: str | None = None
    path: str | None = None


class DeveloperControlPlaneAutonomyCycleActionResponse(BaseModel):
    action: str
    job_id: str | None = None
    title: str | None = None
    source_lane_id: str | None = None
    reason: str | None = None
    primary_agent: str | None = None
    priority: str | None = None
    mission_id: str | None = None
    receipt_path: str | None = None
    state_path: str | None = None
    detail: dict[str, Any] | None = None


class DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse(BaseModel):
    action: str
    action_index: int
    job_id: str
    source_lane_id: str
    reason: str | None = None
    mission_id: str | None = None
    receipt_path: str | None = None
    preparation: DeveloperControlPlaneCompletionWritePreparationResponse


class DeveloperControlPlaneAutonomyCycleResponse(BaseModel):
    exists: bool
    artifact_path: str
    generated_at: str | None = None
    queue_path: str | None = None
    window: str | None = None
    max_jobs_per_run: int = 0
    status_counts: dict[str, int] = {}
    selected_job_count: int = 0
    blocked_job_count: int = 0
    closeout_candidate_count: int = 0
    next_action_count: int = 0
    next_action_ordering_source: str
    watchdog: DeveloperControlPlaneAutonomyCycleWatchdogResponse
    selected_jobs: list[DeveloperControlPlaneAutonomyCycleSelectedJobResponse] = []
    blocked_jobs: list[DeveloperControlPlaneAutonomyCycleBlockedJobResponse] = []
    closeout_candidates: list[DeveloperControlPlaneAutonomyCycleCloseoutCandidateResponse] = []
    next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse] = []
    first_actionable_completion_write: (
        DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse | None
    ) = None


class DeveloperControlPlaneRuntimeCompletionAssistResponse(BaseModel):
    exists: bool
    artifact_path: str
    generated_at: str | None = None
    status: str | None = None
    staged: bool = False
    explicit_write_required: bool = True
    message: str | None = None
    source: dict[str, Any] | None = None
    actionable_completion_write: dict[str, Any] | None = None


class DeveloperControlPlaneSilentMonitorEvidenceSourceResponse(BaseModel):
    label: str
    path: str
    observed_at: str | None = None


class DeveloperControlPlaneSilentMonitorResponse(BaseModel):
    monitor_key: str
    label: str
    state: str
    should_emit: bool = False
    summary: str
    detail: str | None = None
    observed_at: str | None = None
    refresh_cadence: str
    output_artifact: str
    mutates_authority_surfaces: bool = False
    evidence_sources: list[DeveloperControlPlaneSilentMonitorEvidenceSourceResponse] = []
    findings: list[str] = []


class DeveloperControlPlaneSilentMonitorsResponse(BaseModel):
    generated_at: str
    overall_state: str
    should_emit: bool = False
    monitors: list[DeveloperControlPlaneSilentMonitorResponse] = []


class DeveloperControlPlaneMissionVerificationSummaryResponse(BaseModel):
    passed: int
    warned: int
    failed: int
    last_verified_at: str | None = None


class DeveloperControlPlaneMissionSummaryResponse(BaseModel):
    mission_id: str
    objective: str
    status: str
    owner: str
    priority: str
    producer_key: str | None = None
    queue_job_id: str | None = None
    source_lane_id: str | None = None
    source_board_concurrency_token: str | None = None
    created_at: str
    updated_at: str
    subtask_total: int
    subtask_completed: int
    assignment_total: int
    evidence_count: int
    blocker_count: int
    escalation_needed: bool
    verification: DeveloperControlPlaneMissionVerificationSummaryResponse
    final_summary: str | None = None


class DeveloperControlPlaneMissionStateResponse(BaseModel):
    count: int = 0
    missions: list[DeveloperControlPlaneMissionSummaryResponse] = []


class DeveloperControlPlaneMissionBootstrapRequest(BaseModel):
    queue_job_id: str = Field(..., min_length=1, max_length=256)


class DeveloperControlPlaneMissionBootstrapResponse(BaseModel):
    action: str
    mission_id: str | None = None


class DeveloperControlPlaneMissionSubtaskResponse(BaseModel):
    id: str
    title: str
    status: str
    owner_role: str
    depends_on: list[str] = []
    updated_at: str


class DeveloperControlPlaneMissionAssignmentResponse(BaseModel):
    id: str
    subtask_id: str
    assigned_role: str
    handoff_reason: str
    started_at: str
    completed_at: str | None = None


class DeveloperControlPlaneMissionEvidenceResponse(BaseModel):
    id: str
    mission_id: str | None = None
    subtask_id: str | None = None
    kind: str
    evidence_class: str
    summary: str
    source_path: str
    recorded_at: str


class DeveloperControlPlaneMissionVerificationRunResponse(BaseModel):
    id: str
    subject_id: str
    verification_type: str
    result: str
    evidence_ref: str | None = None
    executed_at: str


class DeveloperControlPlaneMissionDecisionNoteResponse(BaseModel):
    id: str
    decision_class: str
    authority_source: str
    recorded_at: str


class DeveloperControlPlaneMissionBlockerResponse(BaseModel):
    id: str
    mission_id: str | None = None
    subtask_id: str | None = None
    blocker_type: str
    impact: str
    escalation_needed: bool
    recorded_at: str


class DeveloperControlPlaneMissionDetailResponse(DeveloperControlPlaneMissionSummaryResponse):
    subtasks: list[DeveloperControlPlaneMissionSubtaskResponse] = []
    assignments: list[DeveloperControlPlaneMissionAssignmentResponse] = []
    evidence_items: list[DeveloperControlPlaneMissionEvidenceResponse] = []
    verification_runs: list[DeveloperControlPlaneMissionVerificationRunResponse] = []
    decision_notes: list[DeveloperControlPlaneMissionDecisionNoteResponse] = []
    blockers: list[DeveloperControlPlaneMissionBlockerResponse] = []


class DeveloperControlPlaneLaneCompletionPayload(BaseModel):
    source_lane_id: str = Field(..., min_length=1, max_length=128)
    queue_job_id: str = Field(..., min_length=1, max_length=256)
    closure_summary: str = Field(..., min_length=1, max_length=2000)
    evidence: list[str] = Field(..., min_length=1)
    closeout_receipt: DeveloperControlPlaneCompletionCloseoutReceiptPayload | None = None


class DeveloperControlPlaneCompletionWriteRequest(BaseModel):
    source_board_concurrency_token: str = Field(..., min_length=1, max_length=128)
    expected_queue_sha256: str = Field(..., min_length=1, max_length=128)
    operator_intent: str = Field(..., min_length=1, max_length=64)
    completion: DeveloperControlPlaneLaneCompletionPayload


class DeveloperControlPlaneCompletionWritePreparationRequest(BaseModel):
    source_lane_id: str = Field(..., min_length=1, max_length=128)


class DeveloperControlPlaneCompletionWritePreparationResponse(BaseModel):
    source_lane_id: str
    queue_job_id: str
    draft_source: str
    queue_status: DeveloperControlPlaneOvernightQueueStatusResponse
    closeout_receipt: DeveloperControlPlaneCloseoutReceiptResponse
    prepared_request: DeveloperControlPlaneCompletionWriteRequest


class DeveloperControlPlaneCompletionWriteResponse(BaseModel):
    no_op: bool
    lane_id: str
    lane_status: str
    queue_job_id: str
    queue_sha256: str
    record: DeveloperControlPlaneActiveBoardRecordResponse
    approval_receipt: DeveloperControlPlaneApprovalReceiptResponse | None = None


class DeveloperControlPlaneActiveBoardRecordResponse(BaseModel):
    id: int
    organization_id: int
    board_id: str
    schema_version: str
    visibility: str
    canonical_board_json: str
    concurrency_token: str
    updated_by_user_id: int
    updated_at: datetime
    save_source: str
    summary_metadata: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeveloperControlPlaneActiveBoardFetchResponse(BaseModel):
    exists: bool
    record: DeveloperControlPlaneActiveBoardRecordResponse | None


class DeveloperControlPlaneActiveBoardSaveRequest(BaseModel):
    canonical_board_json: str = Field(..., min_length=2)
    save_source: str = Field(..., min_length=1, max_length=64)
    concurrency_token: str | None = Field(default=None, min_length=1, max_length=64)


class DeveloperControlPlaneActiveBoardConflictResponse(BaseModel):
    detail: str
    current_record: DeveloperControlPlaneActiveBoardRecordResponse


class DeveloperControlPlaneBoardVersionResponse(BaseModel):
    revision_id: int
    schema_version: str
    visibility: str
    concurrency_token: str
    created_at: datetime
    saved_by_user_id: int
    save_source: str
    summary_metadata: dict[str, Any] | None
    is_current: bool


class DeveloperControlPlaneBoardVersionsListResponse(BaseModel):
    board_id: str
    current_concurrency_token: str | None
    total_count: int
    versions: list[DeveloperControlPlaneBoardVersionResponse]


class DeveloperControlPlaneBoardRestoreRequest(BaseModel):
    concurrency_token: str | None = Field(default=None, min_length=1, max_length=64)


class DeveloperControlPlaneBoardRestoreResponse(BaseModel):
    restored: bool
    restored_from_revision_id: int
    record: DeveloperControlPlaneActiveBoardRecordResponse
    approval_receipt: DeveloperControlPlaneApprovalReceiptResponse | None = None


def _require_ascii_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a non-empty string",
        )
    if not value.isascii():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must use ASCII-only English technical vocabulary",
        )
    return value


def _require_ascii_text_list(value: Any, field_name: str, *, min_items: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < min_items:
        minimum = f" with at least {min_items} item(s)" if min_items else ""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a list{minimum}",
        )
    return [_require_ascii_text(item, f"{field_name}[{index}]") for index, item in enumerate(value)]


def _optional_ascii_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_ascii_text(value, field_name)


def _best_effort_ascii_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip() and value.isascii():
        return value.strip()
    return None


def _has_meaningful_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_meaningful_text_list(value: Any) -> bool:
    return isinstance(value, list) and any(_has_meaningful_text(item) for item in value)


def _has_complete_review_gate(review_gate: Any) -> bool:
    return (
        isinstance(review_gate, dict)
        and _has_meaningful_text(review_gate.get("reviewed_by"))
        and _has_meaningful_text(review_gate.get("summary"))
        and _has_meaningful_text(review_gate.get("reviewed_at"))
        and _has_meaningful_text_list(review_gate.get("evidence"))
    )


def _lane_has_queue_export_reviews(lane: dict[str, Any]) -> bool:
    review_state = lane.get("review_state")
    if not isinstance(review_state, dict):
        return False

    return _has_complete_review_gate(review_state.get("spec_review")) and _has_complete_review_gate(
        review_state.get("risk_review")
    )


def _lane_has_completion_verification_evidence(lane: dict[str, Any]) -> bool:
    review_state = lane.get("review_state")
    if not isinstance(review_state, dict):
        return False

    return _has_complete_review_gate(review_state.get("verification_evidence"))


def _default_queue_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "updatedAt": None,
        "language": QUEUE_LANGUAGE,
        "vocabularyPolicy": QUEUE_VOCABULARY_POLICY,
        "defaults": {
            "window": "nightly",
            "stateRefreshRequired": True,
            "closeoutCommands": ["make update-state"],
            "maxJobsPerRun": 2,
        },
        "jobs": [],
    }


def _queue_sha256(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


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


def _load_overnight_queue_payload() -> tuple[dict[str, Any], bool]:
    if not OVERNIGHT_QUEUE_PATH.exists():
        return _default_queue_payload(), False

    try:
        payload = json.loads(OVERNIGHT_QUEUE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        malformed = _default_queue_payload()
        malformed["malformed_artifact"] = True
        malformed["error"] = str(exc)
        return malformed, False

    if not isinstance(payload, dict):
        malformed = _default_queue_payload()
        malformed["malformed_artifact"] = True
        malformed["error"] = "Overnight queue payload must be a JSON object"
        return malformed, False

    return payload, True


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


def _load_closeout_receipt(queue_job_id: str) -> dict[str, Any] | None:
    return telemetry_service.load_closeout_receipt(queue_job_id, MISSION_EVIDENCE_DIR)


def _load_watchdog_state_payload() -> dict[str, Any] | None:
    return telemetry_service.load_watchdog_state_payload(WATCHDOG_STATE_PATH)


def _relative_repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _parse_monitor_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def _trim_monitor_detail(value: str | None, limit: int = 280) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.split())
    if not normalized:
        return None

    if len(normalized) <= limit:
        return normalized

    return f"{normalized[: limit - 3].rstrip()}..."


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, str)]


def _load_optional_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"Unable to read {_relative_repo_path(path)}: {exc}"

    if not isinstance(payload, dict):
        return None, f"{_relative_repo_path(path)} must be a JSON object"

    return payload, None


def _build_silent_monitor_response(
    *,
    monitor_key: str,
    label: str,
    state: str,
    summary: str,
    detail: str | None,
    observed_at: str | None,
    refresh_cadence: str,
    evidence_sources: list[DeveloperControlPlaneSilentMonitorEvidenceSourceResponse],
    findings: list[str],
) -> DeveloperControlPlaneSilentMonitorResponse:
    return DeveloperControlPlaneSilentMonitorResponse(
        monitor_key=monitor_key,
        label=label,
        state=state,
        should_emit=state != "healthy",
        summary=summary,
        detail=detail,
        observed_at=observed_at,
        refresh_cadence=refresh_cadence,
        output_artifact=f"{SILENT_MONITOR_OUTPUT_ARTIFACT_PREFIX}.{monitor_key}",
        mutates_authority_surfaces=False,
        evidence_sources=evidence_sources,
        findings=findings,
    )


def _overnight_queue_status_response() -> DeveloperControlPlaneOvernightQueueStatusResponse:
    queue_payload, exists = _load_overnight_queue_payload()
    queue_payload = _validate_queue_payload_shape(queue_payload)
    response_dict = telemetry_service.build_overnight_queue_status_response(
        queue_payload,
        exists,
        _queue_sha256(queue_payload),
        OVERNIGHT_QUEUE_PATH,
        REPO_ROOT,
    )
    return DeveloperControlPlaneOvernightQueueStatusResponse(**response_dict)


def _queue_staleness_monitor(
    queue_status: DeveloperControlPlaneOvernightQueueStatusResponse,
) -> DeveloperControlPlaneSilentMonitorResponse:
    evidence_sources = [
        DeveloperControlPlaneSilentMonitorEvidenceSourceResponse(
            label="Overnight queue status",
            path=queue_status.queue_path,
            observed_at=queue_status.updated_at,
        )
    ]

    if not queue_status.exists:
        return _build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="alert",
            summary="The derived overnight queue file is missing.",
            detail="Execution export cannot be sampled until .agent/jobs/overnight-queue.json exists again.",
            observed_at=None,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=["overnight-queue.missing"],
        )

    if not queue_status.updated_at:
        return _build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="watch",
            summary="The overnight queue exists but does not advertise an updatedAt timestamp.",
            detail=f"Queue hash {queue_status.queue_sha256}; sampled job count {queue_status.job_count}.",
            observed_at=None,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=["overnight-queue.updated-at-missing"],
        )

    updated_at = _parse_monitor_timestamp(queue_status.updated_at)
    if updated_at is None:
        return _build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="watch",
            summary="The overnight queue timestamp is present but could not be parsed.",
            detail=f"Queue hash {queue_status.queue_sha256}; raw updatedAt value {queue_status.updated_at!r}.",
            observed_at=queue_status.updated_at,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=["overnight-queue.updated-at-invalid"],
        )

    age_seconds = max(0.0, (datetime.now(UTC) - updated_at).total_seconds())
    age_hours = age_seconds / 3600
    detail = (
        f"Queue hash {queue_status.queue_sha256}; {queue_status.job_count} sampled jobs; "
        f"age {age_hours:.1f}h."
    )

    if age_hours >= QUEUE_STALENESS_ALERT_HOURS:
        return _build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="alert",
            summary="The overnight queue snapshot is older than the nightly freshness window.",
            detail=detail,
            observed_at=queue_status.updated_at,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=[f"overnight-queue.age-hours>={QUEUE_STALENESS_ALERT_HOURS}"],
        )

    if age_hours >= QUEUE_STALENESS_WATCH_HOURS:
        return _build_silent_monitor_response(
            monitor_key="queue-staleness",
            label="Queue staleness",
            state="watch",
            summary="The overnight queue snapshot is aging toward staleness.",
            detail=detail,
            observed_at=queue_status.updated_at,
            refresh_cadence="Nightly and immediately after each reviewed queue export",
            evidence_sources=evidence_sources,
            findings=[f"overnight-queue.age-hours>={QUEUE_STALENESS_WATCH_HOURS}"],
        )

    return _build_silent_monitor_response(
        monitor_key="queue-staleness",
        label="Queue staleness",
        state="healthy",
        summary="The overnight queue snapshot looks fresh for the current nightly cadence.",
        detail=detail,
        observed_at=queue_status.updated_at,
        refresh_cadence="Nightly and immediately after each reviewed queue export",
        evidence_sources=evidence_sources,
        findings=[],
    )


def _control_surface_drift_monitor() -> DeveloperControlPlaneSilentMonitorResponse:
    observed_at = datetime.now(UTC).isoformat()
    evidence_sources = [
        DeveloperControlPlaneSilentMonitorEvidenceSourceResponse(
            label="Canonical control-surface checker",
            path=_relative_repo_path(CONTROL_SURFACE_CHECK_SCRIPT),
            observed_at=observed_at,
        )
    ]

    if not CONTROL_SURFACE_CHECK_SCRIPT.exists():
        return _build_silent_monitor_response(
            monitor_key="control-surface-drift",
            label="Control-surface drift",
            state="missing",
            summary="The canonical control-surface checker is missing.",
            detail=f"Expected script {_relative_repo_path(CONTROL_SURFACE_CHECK_SCRIPT)} could not be found.",
            observed_at=observed_at,
            refresh_cadence="Before operator handoff and after control-plane contract changes",
            evidence_sources=evidence_sources,
            findings=["control-surfaces.check-script-missing"],
        )

    try:
        completed = subprocess.run(
            [sys.executable, str(CONTROL_SURFACE_CHECK_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return _build_silent_monitor_response(
            monitor_key="control-surface-drift",
            label="Control-surface drift",
            state="alert",
            summary="The control-surface checker timed out.",
            detail=_trim_monitor_detail(str(exc)),
            observed_at=observed_at,
            refresh_cadence="Before operator handoff and after control-plane contract changes",
            evidence_sources=evidence_sources,
            findings=["control-surfaces.check-timeout"],
        )
    except OSError as exc:
        return _build_silent_monitor_response(
            monitor_key="control-surface-drift",
            label="Control-surface drift",
            state="alert",
            summary="The control-surface checker could not be executed.",
            detail=_trim_monitor_detail(str(exc)),
            observed_at=observed_at,
            refresh_cadence="Before operator handoff and after control-plane contract changes",
            evidence_sources=evidence_sources,
            findings=["control-surfaces.check-execution-failed"],
        )

    command_output = _trim_monitor_detail(completed.stderr or completed.stdout)
    if completed.returncode == 0:
        return _build_silent_monitor_response(
            monitor_key="control-surface-drift",
            label="Control-surface drift",
            state="healthy",
            summary="The canonical control-surface checker reports no structural drift.",
            detail=command_output,
            observed_at=observed_at,
            refresh_cadence="Before operator handoff and after control-plane contract changes",
            evidence_sources=evidence_sources,
            findings=[],
        )

    return _build_silent_monitor_response(
        monitor_key="control-surface-drift",
        label="Control-surface drift",
        state="alert",
        summary="The canonical control-surface checker detected drift or structural damage.",
        detail=command_output,
        observed_at=observed_at,
        refresh_cadence="Before operator handoff and after control-plane contract changes",
        evidence_sources=evidence_sources,
        findings=["control-surfaces.drift-detected"],
    )


def _reevu_readiness_monitor() -> DeveloperControlPlaneSilentMonitorResponse:
    real_question_report, real_question_error = _load_optional_json_object(
        REEVU_REAL_QUESTION_REPORT_PATH
    )
    readiness_census, readiness_census_error = _load_optional_json_object(
        REEVU_READINESS_CENSUS_PATH
    )
    authority_gap_report, authority_gap_error = _load_optional_json_object(
        REEVU_AUTHORITY_GAP_REPORT_PATH
    )

    evidence_sources: list[DeveloperControlPlaneSilentMonitorEvidenceSourceResponse] = []
    for label, path, payload in (
        ("REEVU real-question benchmark", REEVU_REAL_QUESTION_REPORT_PATH, real_question_report),
        ("REEVU local readiness census", REEVU_READINESS_CENSUS_PATH, readiness_census),
        ("REEVU authority gap report", REEVU_AUTHORITY_GAP_REPORT_PATH, authority_gap_report),
    ):
        evidence_sources.append(
            DeveloperControlPlaneSilentMonitorEvidenceSourceResponse(
                label=label,
                path=_relative_repo_path(path),
                observed_at=payload.get("generated_at") if isinstance(payload, dict) else None,
            )
        )

    missing_artifacts = [
        _relative_repo_path(path)
        for path, payload, error in (
            (REEVU_REAL_QUESTION_REPORT_PATH, real_question_report, real_question_error),
            (REEVU_READINESS_CENSUS_PATH, readiness_census, readiness_census_error),
            (REEVU_AUTHORITY_GAP_REPORT_PATH, authority_gap_report, authority_gap_error),
        )
        if payload is None and error is None
    ]
    artifact_errors = [
        error
        for error in (real_question_error, readiness_census_error, authority_gap_error)
        if error is not None
    ]

    if missing_artifacts:
        return _build_silent_monitor_response(
            monitor_key="reevu-readiness",
            label="REEVU readiness",
            state="missing",
            summary="One or more REEVU readiness artifacts are missing.",
            detail="Missing artifacts: " + ", ".join(missing_artifacts),
            observed_at=None,
            refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
            evidence_sources=evidence_sources,
            findings=[f"missing:{path}" for path in missing_artifacts],
        )

    if artifact_errors:
        return _build_silent_monitor_response(
            monitor_key="reevu-readiness",
            label="REEVU readiness",
            state="alert",
            summary="One or more REEVU readiness artifacts could not be read.",
            detail=_trim_monitor_detail("; ".join(artifact_errors)),
            observed_at=None,
            refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
            evidence_sources=evidence_sources,
            findings=["reevu.readiness-artifact-read-failed"],
        )

    runtime_status = (
        real_question_report.get("runtime_status")
        if isinstance(real_question_report.get("runtime_status"), str)
        else None
    )
    passed_cases = (
        real_question_report.get("passed_cases")
        if isinstance(real_question_report.get("passed_cases"), int)
        else None
    )
    total_cases = (
        real_question_report.get("total_cases")
        if isinstance(real_question_report.get("total_cases"), int)
        else None
    )
    pass_rate = (
        float(real_question_report.get("pass_rate"))
        if isinstance(real_question_report.get("pass_rate"), (int, float))
        else None
    )
    benchmark_ready_org_ids = _string_list(readiness_census.get("benchmark_ready_organization_ids"))
    if not benchmark_ready_org_ids and isinstance(
        readiness_census.get("benchmark_ready_organization_ids"), list
    ):
        benchmark_ready_org_ids = [
            str(item) for item in readiness_census.get("benchmark_ready_organization_ids") if isinstance(item, int)
        ]
    overall_gap_status = (
        authority_gap_report.get("overall_gap_status")
        if isinstance(authority_gap_report.get("overall_gap_status"), str)
        else None
    )
    blockers = _string_list(authority_gap_report.get("selected_local_org_blockers"))
    if not blockers:
        blockers = _string_list(authority_gap_report.get("common_blockers_across_blocked_orgs"))

    observed_candidates = [
        payload.get("generated_at")
        for payload in (real_question_report, readiness_census, authority_gap_report)
        if isinstance(payload.get("generated_at"), str)
    ]
    observed_at = max(observed_candidates, default=None)
    benchmark_ready_count = len(benchmark_ready_org_ids)
    ready_local_orgs = [
        organization
        for organization in readiness_census.get("organizations", [])
        if isinstance(organization, dict)
        and organization.get("runtime_status") == "ready"
        and isinstance(organization.get("organization_id"), int)
    ]
    least_blocked_local_organization = (
        readiness_census.get("least_blocked_local_organization")
        if isinstance(readiness_census.get("least_blocked_local_organization"), dict)
        else None
    )
    pass_summary = (
        f"{passed_cases}/{total_cases} real-question cases passed"
        if passed_cases is not None and total_cases is not None
        else "real-question pass rate unavailable"
    )
    detail_parts = [
        pass_summary,
        f"runtime status {runtime_status or 'unknown'}",
        f"benchmark-ready local orgs {benchmark_ready_count}",
        f"gap status {overall_gap_status or 'unknown'}",
    ]
    if blockers:
        detail_parts.append("blockers: " + ", ".join(blockers[:3]))
    if ready_local_orgs:
        ready_org_labels = ", ".join(
            f"{organization.get('organization_id')} ({organization.get('organization_name') or 'unnamed'})"
            for organization in ready_local_orgs[:3]
        )
        detail_parts.append("ready local orgs: " + ready_org_labels)
    if isinstance(least_blocked_local_organization, dict):
        least_blocked_id = least_blocked_local_organization.get("organization_id")
        least_blocked_name = least_blocked_local_organization.get("organization_name") or "unnamed"
        least_blocked_blockers = _string_list(
            least_blocked_local_organization.get("readiness_blockers")
        )
        detail_parts.append(
            f"least-blocked local org {least_blocked_id} ({least_blocked_name})"
        )
        if least_blocked_blockers:
            detail_parts.append(
                "least-blocked blockers: " + ", ".join(least_blocked_blockers[:3])
            )
    detail = "; ".join(detail_parts) + "."

    if runtime_status == "ready" and benchmark_ready_count > 0 and overall_gap_status in {
        "ready",
        "benchmark-ready",
        "benchmark_ready",
    }:
        state = "watch" if pass_rate is not None and pass_rate < 0.8 else "healthy"
        summary = (
            "REEVU readiness artifacts are present and benchmark-ready local evidence exists."
            if state == "healthy"
            else "REEVU readiness artifacts are present, but benchmark pass rate still needs attention."
        )
        findings = [] if state == "healthy" else ["reevu.pass-rate-below-target"]
        return _build_silent_monitor_response(
            monitor_key="reevu-readiness",
            label="REEVU readiness",
            state=state,
            summary=summary,
            detail=detail,
            observed_at=observed_at,
            refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
            evidence_sources=evidence_sources,
            findings=findings,
        )

    return _build_silent_monitor_response(
        monitor_key="reevu-readiness",
        label="REEVU readiness",
        state="alert",
        summary="REEVU readiness is degraded for the current local evidence set.",
        detail=detail,
        observed_at=observed_at,
        refresh_cadence="After REEVU readiness census, benchmark, or authority-gap regeneration",
        evidence_sources=evidence_sources,
        findings=blockers[:5],
    )


def _derive_silent_monitor_overall_state(
    monitors: list[DeveloperControlPlaneSilentMonitorResponse],
) -> str:
    state_priority = {
        "alert": 4,
        "missing": 3,
        "watch": 2,
        "healthy": 1,
    }
    highest_state = "healthy"
    highest_priority = 0
    for monitor in monitors:
        priority = state_priority.get(monitor.state, 0)
        if priority > highest_priority:
            highest_priority = priority
            highest_state = monitor.state

    return highest_state


def _closeout_receipt_response(
    queue_job_id: str,
    receipt: dict[str, Any] | None,
) -> DeveloperControlPlaneCloseoutReceiptResponse:
    response_dict = telemetry_service.build_closeout_receipt_response(
        queue_job_id,
        receipt,
        MISSION_EVIDENCE_DIR,
        REPO_ROOT,
    )
    return DeveloperControlPlaneCloseoutReceiptResponse(**response_dict)


def _watchdog_status_response(
    watchdog_state: dict[str, Any] | None,
) -> DeveloperControlPlaneWatchdogStatusResponse:
    response_dict = telemetry_service.build_watchdog_status_response(
        watchdog_state,
        WATCHDOG_STATE_PATH,
        MISSION_EVIDENCE_DIR,
        REPO_ROOT,
    )
    return DeveloperControlPlaneWatchdogStatusResponse(**response_dict)


def _load_autonomy_cycle_payload() -> dict[str, Any] | None:
    return telemetry_service.load_autonomy_cycle_payload(AUTONOMY_CYCLE_PATH)


def _load_completion_assist_payload() -> dict[str, Any] | None:
    return telemetry_service.load_completion_assist_payload(COMPLETION_ASSIST_PATH)


def _completion_assist_response(
    payload: dict[str, Any] | None,
) -> DeveloperControlPlaneRuntimeCompletionAssistResponse:
    response_dict = telemetry_service.build_completion_assist_response(
        payload,
        COMPLETION_ASSIST_PATH,
        REPO_ROOT,
    )
    return DeveloperControlPlaneRuntimeCompletionAssistResponse(**response_dict)


def _autonomy_cycle_response(
    payload: dict[str, Any] | None,
) -> DeveloperControlPlaneAutonomyCycleResponse:
    artifact_path = (
        str(AUTONOMY_CYCLE_PATH.relative_to(REPO_ROOT))
        if AUTONOMY_CYCLE_PATH.is_relative_to(REPO_ROOT)
        else str(AUTONOMY_CYCLE_PATH)
    )

    if payload is None:
        return DeveloperControlPlaneAutonomyCycleResponse(
            exists=False,
            artifact_path=artifact_path,
            next_action_ordering_source="artifact",
            watchdog=DeveloperControlPlaneAutonomyCycleWatchdogResponse(
                exists=False,
                state_path="runtime-artifacts/watchdog-state.json",
            ),
        )

    def _source_lane_id(item: dict[str, Any]) -> str | None:
        source_lane_id = item.get("sourceLaneId")
        if isinstance(source_lane_id, str) and source_lane_id:
            return source_lane_id

        provenance = item.get("provenance")
        if isinstance(provenance, dict):
            provenance_source_lane_id = provenance.get("sourceLaneId")
            if isinstance(provenance_source_lane_id, str) and provenance_source_lane_id:
                return provenance_source_lane_id

        return None

    watchdog_payload = payload.get("watchdog") if isinstance(payload.get("watchdog"), dict) else {}
    normalized_job_errors: dict[str, DeveloperControlPlaneAutonomyCycleJobErrorResponse] = {}
    job_errors = watchdog_payload.get("jobErrors")
    if isinstance(job_errors, dict):
        for job_id, detail in job_errors.items():
            if isinstance(job_id, str) and isinstance(detail, dict):
                normalized_job_errors[job_id] = DeveloperControlPlaneAutonomyCycleJobErrorResponse(
                    last_error=detail.get("lastError")
                    if isinstance(detail.get("lastError"), str)
                    else None,
                    consecutive_errors=detail.get("consecutiveErrors")
                    if isinstance(detail.get("consecutiveErrors"), int)
                    else None,
                )

    selected_jobs: list[DeveloperControlPlaneAutonomyCycleSelectedJobResponse] = []
    if isinstance(payload.get("selectedJobs"), list):
        for item in payload["selectedJobs"]:
            if isinstance(item, dict) and isinstance(item.get("jobId"), str):
                selected_jobs.append(
                    DeveloperControlPlaneAutonomyCycleSelectedJobResponse(
                        job_id=item["jobId"],
                        title=item.get("title") if isinstance(item.get("title"), str) else item["jobId"],
                        source_lane_id=_source_lane_id(item),
                        priority=item.get("priority") if isinstance(item.get("priority"), str) else "p3",
                        primary_agent=(
                            item.get("primaryAgent") if isinstance(item.get("primaryAgent"), str) else "Unknown"
                        ),
                        trigger_reason=(
                            item.get("triggerReason") if isinstance(item.get("triggerReason"), str) else None
                        ),
                        source_task=item.get("sourceTask") if isinstance(item.get("sourceTask"), str) else None,
                    )
                )

    blocked_jobs: list[DeveloperControlPlaneAutonomyCycleBlockedJobResponse] = []
    if isinstance(payload.get("blockedJobs"), list):
        for item in payload["blockedJobs"]:
            if isinstance(item, dict) and isinstance(item.get("jobId"), str):
                blocked_jobs.append(
                    DeveloperControlPlaneAutonomyCycleBlockedJobResponse(
                        job_id=item["jobId"],
                        title=item.get("title") if isinstance(item.get("title"), str) else item["jobId"],
                        source_lane_id=_source_lane_id(item),
                        reason=item.get("reason") if isinstance(item.get("reason"), str) else None,
                    )
                )

    closeout_candidates: list[DeveloperControlPlaneAutonomyCycleCloseoutCandidateResponse] = []
    if isinstance(payload.get("closeoutCandidates"), list):
        for item in payload["closeoutCandidates"]:
            if isinstance(item, dict) and isinstance(item.get("jobId"), str):
                closeout_candidates.append(
                    DeveloperControlPlaneAutonomyCycleCloseoutCandidateResponse(
                        job_id=item["jobId"],
                        title=item.get("title") if isinstance(item.get("title"), str) else None,
                        source_lane_id=_source_lane_id(item),
                        queue_status=item.get("queueStatus")
                        if isinstance(item.get("queueStatus"), str)
                        else None,
                        closeout_status=item.get("closeoutStatus")
                        if isinstance(item.get("closeoutStatus"), str)
                        else None,
                        mission_id=item.get("missionId") if isinstance(item.get("missionId"), str) else None,
                        verification_evidence_ref=(
                            item.get("verificationEvidenceRef")
                            if isinstance(item.get("verificationEvidenceRef"), str)
                            else None
                        ),
                        path=item.get("path") if isinstance(item.get("path"), str) else None,
                    )
                )

    next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse] = []
    if isinstance(payload.get("nextActions"), list):
        for item in payload["nextActions"]:
            if isinstance(item, dict) and isinstance(item.get("action"), str):
                next_actions.append(
                    DeveloperControlPlaneAutonomyCycleActionResponse(
                        action=item["action"],
                        job_id=item.get("jobId") if isinstance(item.get("jobId"), str) else None,
                        title=item.get("title") if isinstance(item.get("title"), str) else None,
                        source_lane_id=_source_lane_id(item),
                        reason=item.get("reason") if isinstance(item.get("reason"), str) else None,
                        primary_agent=(
                            item.get("primaryAgent") if isinstance(item.get("primaryAgent"), str) else None
                        ),
                        priority=item.get("priority") if isinstance(item.get("priority"), str) else None,
                        mission_id=item.get("missionId") if isinstance(item.get("missionId"), str) else None,
                        receipt_path=(
                            item.get("receiptPath") if isinstance(item.get("receiptPath"), str) else None
                        ),
                        state_path=item.get("statePath") if isinstance(item.get("statePath"), str) else None,
                        detail=item.get("detail") if isinstance(item.get("detail"), dict) else None,
                    )
                )

    status_counts = payload.get("statusCounts") if isinstance(payload.get("statusCounts"), dict) else {}
    normalized_status_counts = {
        key: value for key, value in status_counts.items() if isinstance(key, str) and isinstance(value, int)
    }

    return DeveloperControlPlaneAutonomyCycleResponse(
        exists=True,
        artifact_path=artifact_path,
        generated_at=payload.get("generatedAt") if isinstance(payload.get("generatedAt"), str) else None,
        queue_path=payload.get("queuePath") if isinstance(payload.get("queuePath"), str) else None,
        window=payload.get("window") if isinstance(payload.get("window"), str) else None,
        max_jobs_per_run=payload.get("maxJobsPerRun") if isinstance(payload.get("maxJobsPerRun"), int) else 0,
        status_counts=normalized_status_counts,
        selected_job_count=(
            payload.get("selectedJobCount") if isinstance(payload.get("selectedJobCount"), int) else 0
        ),
        blocked_job_count=(
            payload.get("blockedJobCount") if isinstance(payload.get("blockedJobCount"), int) else 0
        ),
        closeout_candidate_count=(
            payload.get("closeoutCandidateCount")
            if isinstance(payload.get("closeoutCandidateCount"), int)
            else 0
        ),
        next_action_count=(
            payload.get("nextActionCount") if isinstance(payload.get("nextActionCount"), int) else 0
        ),
        next_action_ordering_source=(
            payload.get("nextActionOrderingSource")
            if isinstance(payload.get("nextActionOrderingSource"), str)
            else "artifact"
        ),
        watchdog=DeveloperControlPlaneAutonomyCycleWatchdogResponse(
            exists=watchdog_payload.get("exists") is True,
            state_path=(
                watchdog_payload.get("statePath")
                if isinstance(watchdog_payload.get("statePath"), str)
                else "runtime-artifacts/watchdog-state.json"
            ),
            last_check=(
                watchdog_payload.get("lastCheck")
                if isinstance(watchdog_payload.get("lastCheck"), str)
                else None
            ),
            gateway_healthy=(
                watchdog_payload.get("gatewayHealthy")
                if isinstance(watchdog_payload.get("gatewayHealthy"), bool)
                else None
            ),
            state_is_stale=watchdog_payload.get("stateIsStale") is True,
            total_alerts=(
                watchdog_payload.get("totalAlerts")
                if isinstance(watchdog_payload.get("totalAlerts"), int)
                else 0
            ),
            job_errors=normalized_job_errors,
        ),
        selected_jobs=selected_jobs,
        blocked_jobs=blocked_jobs,
        closeout_candidates=closeout_candidates,
        next_actions=next_actions,
    )


async def _memory_biased_autonomy_cycle_next_actions(
    db: AsyncSession,
    organization_id: int,
    next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse],
) -> tuple[list[DeveloperControlPlaneAutonomyCycleActionResponse], str]:
    if not next_actions:
        return next_actions, "artifact"

    try:
        if await _get_missing_learning_tables(db):
            return next_actions, "artifact"

        ranked_actions: list[
            tuple[int, int, DeveloperControlPlaneAutonomyCycleActionResponse]
        ] = []
        ordering_sources: set[str] = set()
        for index, action in enumerate(next_actions):
            learning_queries = build_developer_control_plane_learning_queries(
                source_lane_id=action.source_lane_id,
                queue_job_id=action.job_id,
                linked_mission_id=action.mission_id,
                limit=3,
            )
            primary_match_mode = learning_queries[0][0] if learning_queries else "none"
            matched_entries: list[DeveloperControlPlaneLearningEntry] = []
            resolved_match_mode = "none"

            for match_mode, query in learning_queries:
                matched_entries = await _get_learning_entries(
                    db,
                    organization_id,
                    entry_type=None,
                    source_classification=None,
                    source_lane_id=query.get("source_lane_id"),
                    queue_job_id=query.get("queue_job_id"),
                    linked_mission_id=query.get("linked_mission_id"),
                    limit=query.get("limit", 3),
                )
                if matched_entries:
                    resolved_match_mode = match_mode
                    break

            score = score_developer_control_plane_autonomy_action(
                action_type=action.action,
                priority=action.priority,
                learning_entries=matched_entries,
                match_mode=resolved_match_mode,
                primary_match_mode=primary_match_mode,
            )
            if score > 0 and resolved_match_mode != "none":
                ordering_sources.add(
                    "canonical-learning-exact-runtime"
                    if resolved_match_mode == primary_match_mode
                    else "canonical-learning-fallback"
                )
            ranked_actions.append((score, index, action))

        if not any(score > 0 for score, _, _ in ranked_actions):
            return next_actions, "artifact"

        return (
            [
                action
                for _, _, action in sorted(
                    ranked_actions,
                    key=lambda item: (-item[0], item[1]),
                )
            ],
            (
                "canonical-learning-exact-runtime"
                if "canonical-learning-exact-runtime" in ordering_sources
                else "canonical-learning-fallback"
            ),
        )
    except Exception:
        return next_actions, "artifact"


async def _hydrate_autonomy_cycle_completion_write_preparations(
    db: AsyncSession,
    organization_id: int,
    next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse],
) -> list[DeveloperControlPlaneAutonomyCycleActionResponse]:
    if not next_actions:
        return next_actions

    current_record = await _get_active_board(db, organization_id)
    if current_record is None:
        return next_actions

    try:
        board_payload = _load_active_board_payload(current_record)
    except HTTPException:
        return next_actions

    hydrated_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse] = []
    for action in next_actions:
        if action.action != "prepare-completion-write-back" or not action.source_lane_id:
            hydrated_actions.append(action)
            continue

        if _find_board_lane(board_payload, action.source_lane_id) is None:
            hydrated_actions.append(action)
            continue

        try:
            preparation = _build_completion_write_preparation_response(
                source_lane_id=action.source_lane_id,
                source_board_concurrency_token=current_record.canonical_board_hash,
            )
        except HTTPException:
            hydrated_actions.append(action)
            continue

        detail = dict(action.detail or {})
        detail["completionWritePreparation"] = preparation.model_dump()
        hydrated_actions.append(action.model_copy(update={"detail": detail}))

    return hydrated_actions


def _resolve_first_actionable_completion_write(
    next_actions: list[DeveloperControlPlaneAutonomyCycleActionResponse],
) -> DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse | None:
    payload = build_developer_control_plane_first_actionable_completion_write_payload(
        next_actions
    )
    if payload is None:
        return None

    try:
        return DeveloperControlPlaneAutonomyCycleActionableCompletionWriteResponse.model_validate(
            payload
        )
    except ValidationError:
        return None


def _mission_summary_response(
    snapshot: Any,
) -> DeveloperControlPlaneMissionSummaryResponse:
    linkage = _mission_linkage(snapshot.mission)
    passed = sum(1 for item in snapshot.verification_runs if item.result.value == "passed")
    warned = sum(1 for item in snapshot.verification_runs if item.result.value == "warn")
    failed = sum(1 for item in snapshot.verification_runs if item.result.value == "failed")
    last_verified_at = max(
        (item.executed_at for item in snapshot.verification_runs),
        default=None,
    )
    subtask_completed = sum(
        1 for item in snapshot.subtasks if item.status.value == "completed"
    )
    return DeveloperControlPlaneMissionSummaryResponse(
        mission_id=snapshot.mission.id,
        objective=snapshot.mission.objective,
        status=snapshot.mission.status.value,
        owner=snapshot.mission.owner,
        priority=snapshot.mission.priority,
        producer_key=snapshot.mission.producer_key,
        queue_job_id=linkage["queue_job_id"] if linkage is not None else None,
        source_lane_id=linkage["source_lane_id"] if linkage is not None else None,
        source_board_concurrency_token=(
            linkage["source_board_concurrency_token"] if linkage is not None else None
        ),
        created_at=snapshot.mission.created_at.isoformat(),
        updated_at=snapshot.mission.updated_at.isoformat(),
        subtask_total=len(snapshot.subtasks),
        subtask_completed=subtask_completed,
        assignment_total=len(snapshot.assignments),
        evidence_count=len(snapshot.evidence_items),
        blocker_count=len(snapshot.blockers),
        escalation_needed=any(item.escalation_needed for item in snapshot.blockers),
        verification=DeveloperControlPlaneMissionVerificationSummaryResponse(
            passed=passed,
            warned=warned,
            failed=failed,
            last_verified_at=last_verified_at.isoformat() if last_verified_at else None,
        ),
        final_summary=snapshot.mission.final_summary,
    )


def _mission_detail_response(
    snapshot: Any,
) -> DeveloperControlPlaneMissionDetailResponse:
    summary = _mission_summary_response(snapshot)
    runtime_root = MISSION_EVIDENCE_DIR.parent
    return DeveloperControlPlaneMissionDetailResponse(
        **summary.model_dump(),
        subtasks=[
            DeveloperControlPlaneMissionSubtaskResponse(
                id=item.id,
                title=item.title,
                status=item.status.value,
                owner_role=item.owner_role,
                depends_on=list(item.depends_on),
                updated_at=item.updated_at.isoformat(),
            )
            for item in snapshot.subtasks
        ],
        assignments=[
            DeveloperControlPlaneMissionAssignmentResponse(
                id=item.id,
                subtask_id=item.subtask_id,
                assigned_role=item.assigned_role,
                handoff_reason=item.handoff_reason,
                started_at=item.started_at.isoformat(),
                completed_at=item.completed_at.isoformat() if item.completed_at else None,
            )
            for item in snapshot.assignments
        ],
        evidence_items=[
            DeveloperControlPlaneMissionEvidenceResponse(
                id=item.id,
                mission_id=item.mission_id,
                subtask_id=item.subtask_id,
                kind=item.kind,
                evidence_class=item.evidence_class,
                summary=item.summary,
                source_path=normalize_runtime_reference(REPO_ROOT, runtime_root, item.source_path)
                or item.source_path,
                recorded_at=item.recorded_at.isoformat(),
            )
            for item in snapshot.evidence_items
        ],
        verification_runs=[
            DeveloperControlPlaneMissionVerificationRunResponse(
                id=item.id,
                subject_id=item.subject_id,
                verification_type=item.verification_type,
                result=item.result.value,
                evidence_ref=item.evidence_ref,
                executed_at=item.executed_at.isoformat(),
            )
            for item in snapshot.verification_runs
        ],
        decision_notes=[
            DeveloperControlPlaneMissionDecisionNoteResponse(
                id=item.id,
                decision_class=item.decision_class,
                authority_source=item.authority_source,
                recorded_at=item.recorded_at.isoformat(),
            )
            for item in snapshot.decision_notes
        ],
        blockers=[
            DeveloperControlPlaneMissionBlockerResponse(
                id=item.id,
                mission_id=item.mission_id,
                subtask_id=item.subtask_id,
                blocker_type=item.blocker_type,
                impact=item.impact,
                escalation_needed=item.escalation_needed,
                recorded_at=item.recorded_at.isoformat(),
            )
            for item in snapshot.blockers
        ],
    )


async def _load_runtime_mission_snapshot(
    db: AsyncSession,
    organization_id: int,
    mission_id: str,
):
    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    mission = await service.repository.get_mission(mission_id)
    if mission is None or mission.owner != "OmShriMaatreNamaha":
        return None
    return await service.get_mission_snapshot(mission_id)


async def _mission_state_response(
    db: AsyncSession,
    organization_id: int,
    *,
    limit: int,
    queue_job_id: str | None = None,
    source_lane_id: str | None = None,
) -> DeveloperControlPlaneMissionStateResponse:
    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    relevant_missions = await service.repository.list_missions(
        owner="OmShriMaatreNamaha",
        queue_job_id=queue_job_id,
        source_lane_id=source_lane_id,
    )

    if (queue_job_id is not None or source_lane_id is not None) and not relevant_missions:
        fallback_missions = await service.repository.list_missions(owner="OmShriMaatreNamaha")
        filtered_missions = []
        for mission in fallback_missions:
            linkage = _mission_linkage(mission)
            if linkage is None:
                continue
            if queue_job_id is not None and linkage["queue_job_id"] != queue_job_id:
                continue
            if source_lane_id is not None and linkage["source_lane_id"] != source_lane_id:
                continue
            filtered_missions.append(mission)
        relevant_missions = filtered_missions

    relevant_missions.sort(key=lambda item: (item.updated_at, item.id), reverse=True)

    summaries: list[DeveloperControlPlaneMissionSummaryResponse] = []
    for mission in relevant_missions[:limit]:
        snapshot = await service.get_mission_snapshot(mission.id)
        summaries.append(_mission_summary_response(snapshot))

    return DeveloperControlPlaneMissionStateResponse(count=len(summaries), missions=summaries)


def _validate_queue_payload_shape(payload: dict[str, Any]) -> dict[str, Any]:
    defaults = payload.get("defaults")
    jobs = payload.get("jobs")

    if payload.get("language") != QUEUE_LANGUAGE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Overnight queue payload must declare language=en",
        )
    if payload.get("vocabularyPolicy") != QUEUE_VOCABULARY_POLICY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Overnight queue payload must declare vocabularyPolicy=english-technical-only",
        )
    if not isinstance(defaults, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Overnight queue payload defaults must be an object",
        )
    if not isinstance(jobs, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Overnight queue payload jobs must be a list",
        )

    return payload


def _validate_queue_entry(
    queue_entry: dict[str, Any],
    existing_job_ids: set[str],
) -> dict[str, Any]:
    required_keys = (
        "jobId",
        "title",
        "status",
        "priority",
        "primaryAgent",
        "supportAgents",
        "executionMode",
        "autonomousTrigger",
        "dependsOn",
        "goal",
        "lane",
        "successCriteria",
        "verification",
    )
    for key in required_keys:
        if key not in queue_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"queue_entry is missing required key: {key}",
            )

    job_id = _require_ascii_text(queue_entry["jobId"], "queue_entry.jobId")
    if job_id in existing_job_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_queue_write_conflict_detail(
                "duplicate-job-id",
                "Queue entry conflict; jobId already exists and create-only policy forbids overwrite",
                job_id=job_id,
            ),
        )

    if queue_entry["status"] != "queued":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.status must be queued",
        )
    if queue_entry["priority"] != "p2":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.priority must be p2",
        )
    if queue_entry["executionMode"] != "same-control-plane":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.executionMode must be same-control-plane",
        )

    _require_ascii_text(queue_entry["title"], "queue_entry.title")
    _require_ascii_text(queue_entry["primaryAgent"], "queue_entry.primaryAgent")
    _require_ascii_text(queue_entry["goal"], "queue_entry.goal")
    _require_ascii_text_list(queue_entry["supportAgents"], "queue_entry.supportAgents")
    depends_on = _require_ascii_text_list(queue_entry["dependsOn"], "queue_entry.dependsOn")
    success_criteria = _require_ascii_text_list(
        queue_entry["successCriteria"],
        "queue_entry.successCriteria",
        min_items=1,
    )

    for dependency in depends_on:
        if dependency not in existing_job_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"queue_entry.dependsOn references unknown jobId: {dependency}",
            )

    autonomous_trigger = queue_entry["autonomousTrigger"]
    if not isinstance(autonomous_trigger, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.autonomousTrigger must be an object",
        )
    if autonomous_trigger.get("type") != "overnight-window":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.autonomousTrigger.type must be overnight-window",
        )
    if autonomous_trigger.get("window") != "nightly":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.autonomousTrigger.window must be nightly",
        )
    if autonomous_trigger.get("enabled") is not True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.autonomousTrigger.enabled must be true",
        )

    verification = queue_entry["verification"]
    if not isinstance(verification, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.verification must be an object",
        )
    verification_commands = _require_ascii_text_list(
        verification.get("commands"),
        "queue_entry.verification.commands",
    )
    if verification.get("stateRefreshRequired") is not True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.verification.stateRefreshRequired must be true",
        )

    lane = queue_entry["lane"]
    if not isinstance(lane, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="queue_entry.lane must be an object",
        )
    lane_objective = _require_ascii_text(lane.get("objective"), "queue_entry.lane.objective")
    lane_inputs = _require_ascii_text_list(lane.get("inputs"), "queue_entry.lane.inputs")
    lane_outputs = _require_ascii_text_list(lane.get("outputs"), "queue_entry.lane.outputs")
    lane_dependencies = _require_ascii_text_list(
        lane.get("dependencies"),
        "queue_entry.lane.dependencies",
    )
    lane_completion_criteria = _require_ascii_text_list(
        lane.get("completion_criteria"),
        "queue_entry.lane.completion_criteria",
        min_items=1,
    )
    provenance = queue_entry.get("provenance")
    validated_provenance = None
    if provenance is not None:
        if not isinstance(provenance, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="queue_entry.provenance must be an object",
            )

        required_provenance_keys = (
            "candidateVersion",
            "exportedAt",
            "boardId",
            "boardTitle",
            "sourceBoardConcurrencyToken",
            "sourceLaneId",
            "precedence",
        )
        for key in required_provenance_keys:
            if key not in provenance:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"queue_entry.provenance is missing required key: {key}",
                )

        precedence = provenance["precedence"]
        if not isinstance(precedence, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="queue_entry.provenance.precedence must be an object",
            )
        if precedence.get("canonicalPlanningSource") != "active-board":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "queue_entry.provenance.precedence."
                    "canonicalPlanningSource must be active-board"
                ),
            )
        if precedence.get("derivedExecutionSurface") != "overnight-queue":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "queue_entry.provenance.precedence."
                    "derivedExecutionSurface must be overnight-queue"
                ),
            )
        if precedence.get("exportDisposition") != "manual-candidate-only":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "queue_entry.provenance.precedence."
                    "exportDisposition must be manual-candidate-only"
                ),
            )
        if precedence.get("conflictResolution") != "board-wins-no-silent-overwrite":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "queue_entry.provenance.precedence."
                    "conflictResolution must be board-wins-no-silent-overwrite"
                ),
            )
        if precedence.get("staleIfSourceBoardChanges") is not True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "queue_entry.provenance.precedence."
                    "staleIfSourceBoardChanges must be true"
                ),
            )

        validated_provenance = {
            "candidateVersion": _require_ascii_text(
                provenance["candidateVersion"],
                "queue_entry.provenance.candidateVersion",
            ),
            "exportedAt": _require_ascii_text(
                provenance["exportedAt"],
                "queue_entry.provenance.exportedAt",
            ),
            "boardId": _require_ascii_text(
                provenance["boardId"],
                "queue_entry.provenance.boardId",
            ),
            "boardTitle": _require_ascii_text(
                provenance["boardTitle"],
                "queue_entry.provenance.boardTitle",
            ),
            "sourceBoardConcurrencyToken": _require_ascii_text(
                provenance["sourceBoardConcurrencyToken"],
                "queue_entry.provenance.sourceBoardConcurrencyToken",
            ),
            "sourceLaneId": _require_ascii_text(
                provenance["sourceLaneId"],
                "queue_entry.provenance.sourceLaneId",
            ),
            "precedence": {
                "canonicalPlanningSource": "active-board",
                "derivedExecutionSurface": "overnight-queue",
                "exportDisposition": "manual-candidate-only",
                "conflictResolution": "board-wins-no-silent-overwrite",
                "staleIfSourceBoardChanges": True,
            },
        }

    validated_entry = {
        "jobId": job_id,
        "title": queue_entry["title"],
        "status": "queued",
        "priority": "p2",
        "primaryAgent": queue_entry["primaryAgent"],
        "supportAgents": queue_entry["supportAgents"],
        "executionMode": "same-control-plane",
        "autonomousTrigger": {
            "type": "overnight-window",
            "window": "nightly",
            "enabled": True,
        },
        "dependsOn": depends_on,
        "goal": queue_entry["goal"],
        "lane": {
            "objective": lane_objective,
            "inputs": lane_inputs,
            "outputs": lane_outputs,
            "dependencies": lane_dependencies,
            "completion_criteria": lane_completion_criteria,
        },
        "successCriteria": success_criteria,
        "verification": {
            "commands": verification_commands,
            "stateRefreshRequired": True,
        },
    }

    if validated_provenance is not None:
        validated_entry["provenance"] = validated_provenance

    return validated_entry


def _serialize_queue_payload(payload: dict[str, Any]) -> str:
    stable_payload = {
        "version": payload.get("version", 1),
        "updatedAt": payload.get("updatedAt"),
        "language": payload.get("language", QUEUE_LANGUAGE),
        "vocabularyPolicy": payload.get("vocabularyPolicy", QUEUE_VOCABULARY_POLICY),
        "defaults": payload.get("defaults", _default_queue_payload()["defaults"]),
        "jobs": payload.get("jobs", []),
    }
    return f"{json.dumps(stable_payload, indent=2, ensure_ascii=True)}\n"


def _write_overnight_queue_payload(payload: dict[str, Any]) -> None:
    try:
        OVERNIGHT_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        OVERNIGHT_QUEUE_PATH.write_text(_serialize_queue_payload(payload), encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to write overnight queue file",
        ) from exc


def _record_response(
    record: DeveloperControlPlaneActiveBoard,
) -> DeveloperControlPlaneActiveBoardRecordResponse:
    return DeveloperControlPlaneActiveBoardRecordResponse(
        id=record.id,
        organization_id=record.organization_id,
        board_id=record.board_id,
        schema_version=record.schema_version,
        visibility=record.visibility,
        canonical_board_json=record.canonical_board_json,
        concurrency_token=record.canonical_board_hash,
        updated_by_user_id=record.updated_by_user_id,
        updated_at=record.updated_at,
        save_source=record.save_source,
        summary_metadata=record.summary_metadata,
        created_at=record.created_at,
    )


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


def _approval_receipt_response(
    record: DeveloperControlPlaneApprovalReceipt,
) -> DeveloperControlPlaneApprovalReceiptResponse:
    return DeveloperControlPlaneApprovalReceiptResponse(
        receipt_id=record.id,
        organization_id=record.organization_id,
        action_type=record.action_type,
        outcome=record.outcome,
        authority_actor_user_id=record.authority_actor_user_id,
        authority_actor_email=record.authority_actor_email,
        authority_source=record.authority_source,
        board_id=record.board_id,
        source_board_concurrency_token=record.source_board_concurrency_token,
        resulting_board_concurrency_token=record.resulting_board_concurrency_token,
        source_lane_id=record.source_lane_id,
        queue_job_id=record.queue_job_id,
        expected_queue_sha256=record.expected_queue_sha256,
        resulting_queue_sha256=record.resulting_queue_sha256,
        target_revision_id=record.target_revision_id,
        previous_active_concurrency_token=record.previous_active_concurrency_token,
        linked_mission_id=record.linked_mission_id,
        rationale=record.rationale,
        evidence_refs=record.evidence_refs,
        summary_metadata=record.summary_metadata,
        recorded_at=record.created_at,
    )


async def _get_latest_approval_receipt(
    db: AsyncSession,
    organization_id: int,
    *conditions: Any,
) -> DeveloperControlPlaneApprovalReceipt | None:
    result = await db.execute(
        select(DeveloperControlPlaneApprovalReceipt)
        .where(
            DeveloperControlPlaneApprovalReceipt.organization_id == organization_id,
            *conditions,
        )
        .order_by(
            DeveloperControlPlaneApprovalReceipt.created_at.desc(),
            DeveloperControlPlaneApprovalReceipt.id.desc(),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _record_approval_receipt(
    db: AsyncSession,
    organization_id: int,
    current_user: User,
    *,
    action_type: str,
    outcome: str,
    board_id: str,
    rationale: str,
    evidence_refs: list[str],
    source_board_concurrency_token: str | None = None,
    resulting_board_concurrency_token: str | None = None,
    source_lane_id: str | None = None,
    queue_job_id: str | None = None,
    expected_queue_sha256: str | None = None,
    resulting_queue_sha256: str | None = None,
    target_revision_id: int | None = None,
    previous_active_concurrency_token: str | None = None,
    linked_mission_id: str | None = None,
    summary_metadata: dict[str, Any] | None = None,
) -> DeveloperControlPlaneApprovalReceipt:
    receipt = DeveloperControlPlaneApprovalReceipt(
        organization_id=organization_id,
        action_type=action_type,
        outcome=outcome,
        authority_actor_user_id=current_user.id,
        authority_actor_email=getattr(current_user, "email", None),
        authority_source=APPROVAL_RECEIPT_AUTHORITY_SOURCE,
        board_id=board_id,
        source_board_concurrency_token=source_board_concurrency_token,
        resulting_board_concurrency_token=resulting_board_concurrency_token,
        source_lane_id=source_lane_id,
        queue_job_id=queue_job_id,
        expected_queue_sha256=expected_queue_sha256,
        resulting_queue_sha256=resulting_queue_sha256,
        target_revision_id=target_revision_id,
        previous_active_concurrency_token=previous_active_concurrency_token,
        linked_mission_id=linked_mission_id,
        rationale=rationale,
        evidence_refs=_deduplicate_strings(evidence_refs),
        summary_metadata=summary_metadata,
    )
    db.add(receipt)
    await db.flush()
    return receipt


def _learning_entry_response(
    record: DeveloperControlPlaneLearningEntry,
) -> DeveloperControlPlaneLearningEntryResponse:
    return DeveloperControlPlaneLearningEntryResponse(
        learning_entry_id=record.id,
        organization_id=record.organization_id,
        entry_type=record.entry_type,
        source_classification=record.source_classification,
        title=record.title,
        summary=record.summary,
        confidence_score=record.confidence_score,
        recorded_by_user_id=record.recorded_by_user_id,
        recorded_by_email=record.recorded_by_email,
        board_id=record.board_id,
        source_lane_id=record.source_lane_id,
        queue_job_id=record.queue_job_id,
        linked_mission_id=record.linked_mission_id,
        approval_receipt_id=record.approval_receipt_id,
        source_reference=record.source_reference,
        evidence_refs=record.evidence_refs,
        summary_metadata=record.summary_metadata,
        recorded_at=record.created_at,
    )


async def _get_learning_entries(
    db: AsyncSession,
    organization_id: int,
    *,
    entry_type: str | None = None,
    source_classification: str | None = None,
    source_lane_id: str | None = None,
    queue_job_id: str | None = None,
    linked_mission_id: str | None = None,
    limit: int = 25,
) -> list[DeveloperControlPlaneLearningEntry]:
    conditions = [DeveloperControlPlaneLearningEntry.organization_id == organization_id]
    if entry_type is not None:
        conditions.append(DeveloperControlPlaneLearningEntry.entry_type == entry_type)
    if source_classification is not None:
        conditions.append(
            DeveloperControlPlaneLearningEntry.source_classification == source_classification
        )
    if source_lane_id is not None:
        conditions.append(DeveloperControlPlaneLearningEntry.source_lane_id == source_lane_id)
    if queue_job_id is not None:
        conditions.append(DeveloperControlPlaneLearningEntry.queue_job_id == queue_job_id)
    if linked_mission_id is not None:
        conditions.append(
            DeveloperControlPlaneLearningEntry.linked_mission_id == linked_mission_id
        )

    result = await db.execute(
        select(DeveloperControlPlaneLearningEntry)
        .where(*conditions)
        .order_by(
            DeveloperControlPlaneLearningEntry.created_at.desc(),
            DeveloperControlPlaneLearningEntry.id.desc(),
        )
        .limit(limit)
    )
    return list(result.scalars().all())


async def _get_existing_learning_entry(
    db: AsyncSession,
    organization_id: int,
    *,
    entry_type: str,
    source_classification: str,
    source_reference: str | None,
    board_id: str | None,
    source_lane_id: str | None,
    queue_job_id: str | None,
    linked_mission_id: str | None,
    approval_receipt_id: int | None,
) -> DeveloperControlPlaneLearningEntry | None:
    conditions = [
        DeveloperControlPlaneLearningEntry.organization_id == organization_id,
        DeveloperControlPlaneLearningEntry.entry_type == entry_type,
        DeveloperControlPlaneLearningEntry.source_classification == source_classification,
    ]

    optional_string_fields = {
        DeveloperControlPlaneLearningEntry.source_reference: source_reference,
        DeveloperControlPlaneLearningEntry.board_id: board_id,
        DeveloperControlPlaneLearningEntry.source_lane_id: source_lane_id,
        DeveloperControlPlaneLearningEntry.queue_job_id: queue_job_id,
        DeveloperControlPlaneLearningEntry.linked_mission_id: linked_mission_id,
    }
    for field, value in optional_string_fields.items():
        if value is None:
            conditions.append(field.is_(None))
        else:
            conditions.append(field == value)

    if approval_receipt_id is None:
        conditions.append(DeveloperControlPlaneLearningEntry.approval_receipt_id.is_(None))
    else:
        conditions.append(DeveloperControlPlaneLearningEntry.approval_receipt_id == approval_receipt_id)

    result = await db.execute(
        select(DeveloperControlPlaneLearningEntry)
        .where(*conditions)
        .order_by(
            DeveloperControlPlaneLearningEntry.created_at.desc(),
            DeveloperControlPlaneLearningEntry.id.desc(),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _record_learning_entry(
    db: AsyncSession,
    organization_id: int,
    *,
    entry_type: str,
    source_classification: str,
    title: str,
    summary: str,
    confidence_score: float | None,
    recorded_by_user_id: int | None,
    recorded_by_email: str | None,
    board_id: str | None,
    source_lane_id: str | None,
    queue_job_id: str | None,
    linked_mission_id: str | None,
    approval_receipt_id: int | None,
    source_reference: str | None,
    evidence_refs: list[str],
    summary_metadata: dict[str, Any] | None,
) -> tuple[DeveloperControlPlaneLearningEntry, bool]:
    validated_entry_type = _require_ascii_text(entry_type, "learning.entry_type")
    if validated_entry_type not in CONTROL_PLANE_LEARNING_ENTRY_TYPES:
        allowed_values = ", ".join(CONTROL_PLANE_LEARNING_ENTRY_TYPES)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"learning.entry_type must be one of: {allowed_values}",
        )

    if confidence_score is not None and not 0 <= confidence_score <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="learning.confidence_score must be between 0 and 1",
        )

    validated_source_classification = _require_ascii_text(
        source_classification,
        "learning.source_classification",
    )
    validated_title = _require_ascii_text(title, "learning.title")
    validated_summary = _require_ascii_text(summary, "learning.summary")
    validated_recorded_by_email = _optional_ascii_text(
        recorded_by_email,
        "learning.recorded_by_email",
    )
    validated_board_id = _optional_ascii_text(board_id, "learning.board_id")
    validated_source_lane_id = _optional_ascii_text(
        source_lane_id,
        "learning.source_lane_id",
    )
    validated_queue_job_id = _optional_ascii_text(queue_job_id, "learning.queue_job_id")
    validated_linked_mission_id = _optional_ascii_text(
        linked_mission_id,
        "learning.linked_mission_id",
    )
    validated_source_reference = _optional_ascii_text(
        source_reference,
        "learning.source_reference",
    )
    validated_evidence_refs = _deduplicate_strings(
        _require_ascii_text_list(evidence_refs, "learning.evidence_refs", min_items=0)
    )

    existing_entry = await _get_existing_learning_entry(
        db,
        organization_id,
        entry_type=validated_entry_type,
        source_classification=validated_source_classification,
        source_reference=validated_source_reference,
        board_id=validated_board_id,
        source_lane_id=validated_source_lane_id,
        queue_job_id=validated_queue_job_id,
        linked_mission_id=validated_linked_mission_id,
        approval_receipt_id=approval_receipt_id,
    )
    if existing_entry is not None:
        return existing_entry, False

    entry = DeveloperControlPlaneLearningEntry(
        organization_id=organization_id,
        entry_type=validated_entry_type,
        source_classification=validated_source_classification,
        title=validated_title,
        summary=validated_summary,
        confidence_score=confidence_score,
        recorded_by_user_id=recorded_by_user_id,
        recorded_by_email=validated_recorded_by_email,
        board_id=validated_board_id,
        source_lane_id=validated_source_lane_id,
        queue_job_id=validated_queue_job_id,
        linked_mission_id=validated_linked_mission_id,
        approval_receipt_id=approval_receipt_id,
        source_reference=validated_source_reference,
        evidence_refs=validated_evidence_refs,
        summary_metadata=summary_metadata,
    )
    db.add(entry)
    await db.flush()
    return entry, True


def _mission_learning_evidence_refs(snapshot: Any, *, include_passed_runs: bool) -> list[str]:
    evidence_refs: list[str] = []
    for item in snapshot.verification_runs:
        if not include_passed_runs and item.result.value == "passed":
            continue
        if isinstance(item.evidence_ref, str) and item.evidence_ref.strip() and item.evidence_ref.isascii():
            evidence_refs.append(item.evidence_ref)
    for item in snapshot.evidence_items:
        if isinstance(item.source_path, str) and item.source_path.strip() and item.source_path.isascii():
            evidence_refs.append(item.source_path)
    if not evidence_refs:
        evidence_refs.append(f"developer-control-plane:mission:{snapshot.mission.id}")
    return _deduplicate_strings(evidence_refs)


def _learning_conflict_entry_type(reason: str) -> str:
    if reason in {"closeout-receipt-mismatch", "completion-overwrite-conflict"}:
        return "incident"
    return "pitfall"


def _learning_conflict_target(
    source_lane_id: str | None,
    queue_job_id: str | None,
) -> str:
    if source_lane_id is not None:
        return f"lane {source_lane_id}"
    if queue_job_id is not None:
        return f"queue job {queue_job_id}"
    return "developer control plane"


def _learning_conflict_title(
    scope: str,
    reason: str,
    source_lane_id: str | None,
    queue_job_id: str | None,
) -> str:
    scope_label = "Queue export" if scope == "queue-export" else "Completion write-back"
    return f"{scope_label} conflict {reason} for {_learning_conflict_target(source_lane_id, queue_job_id)}"


def _learning_conflict_summary(conflict_detail: dict[str, Any]) -> str:
    detail_message = conflict_detail.get("detail")
    remediation_message = conflict_detail.get("remediation_message")
    summary_parts = []
    if isinstance(detail_message, str) and detail_message.strip():
        summary_parts.append(detail_message.strip().rstrip("."))
    if isinstance(remediation_message, str) and remediation_message.strip():
        summary_parts.append(f"Remediation: {remediation_message.strip()}")
    return " ".join(summary_parts)


def _learning_conflict_evidence_refs(
    *,
    board_id: str | None,
    source_lane_id: str | None,
    queue_job_id: str | None,
    source_board_concurrency_token: str | None,
    conflict_detail: dict[str, Any],
) -> list[str]:
    evidence_refs: list[str] = []
    if board_id is not None:
        evidence_refs.append(f"developer-control-plane:board:{board_id}")
    if source_lane_id is not None:
        evidence_refs.append(f"developer-control-plane:lane:{source_lane_id}")
    if queue_job_id is not None:
        evidence_refs.append(f"developer-control-plane:queue-job:{queue_job_id}")
    if source_board_concurrency_token is not None:
        evidence_refs.append(
            f"developer-control-plane:board-token:{source_board_concurrency_token}"
        )
    current_queue_sha256 = conflict_detail.get("current_queue_sha256")
    if (
        isinstance(current_queue_sha256, str)
        and current_queue_sha256.strip()
        and current_queue_sha256.isascii()
    ):
        evidence_refs.append(f"developer-control-plane:queue-sha:{current_queue_sha256}")
    return _deduplicate_strings(evidence_refs)


async def _persist_conflict_learning(
    db: AsyncSession,
    organization_id: int,
    current_user: User,
    *,
    scope: str,
    conflict_detail: dict[str, Any],
    board_id: str | None,
    source_lane_id: str | None,
    queue_job_id: str | None,
    source_board_concurrency_token: str | None,
    linked_mission_id: str | None = None,
) -> None:
    reason = conflict_detail.get("conflict_reason")
    if not isinstance(reason, str) or not reason:
        return

    normalized_board_id = _best_effort_ascii_text(board_id)
    normalized_source_lane_id = _best_effort_ascii_text(source_lane_id)
    normalized_queue_job_id = _best_effort_ascii_text(queue_job_id)
    normalized_board_token = _best_effort_ascii_text(source_board_concurrency_token)
    normalized_linked_mission_id = _best_effort_ascii_text(linked_mission_id)
    summary = _learning_conflict_summary(conflict_detail)
    if not summary:
        return

    summary_metadata = {
        key: value
        for key, value in conflict_detail.items()
        if key != "detail"
    }
    summary_metadata["conflict_scope"] = scope
    if normalized_board_token is not None:
        summary_metadata["source_board_concurrency_token"] = normalized_board_token

    try:
        await _record_learning_entry(
            db,
            organization_id,
            entry_type=_learning_conflict_entry_type(reason),
            source_classification="queue-conflict",
            title=_learning_conflict_title(
                scope,
                reason,
                normalized_source_lane_id,
                normalized_queue_job_id,
            ),
            summary=summary,
            confidence_score=0.95 if _learning_conflict_entry_type(reason) == "incident" else 0.9,
            recorded_by_user_id=current_user.id,
            recorded_by_email=getattr(current_user, "email", None),
            board_id=normalized_board_id,
            source_lane_id=normalized_source_lane_id,
            queue_job_id=normalized_queue_job_id,
            linked_mission_id=normalized_linked_mission_id,
            approval_receipt_id=None,
            source_reference=(
                f"queue-conflict:{scope}:{reason}:"
                f"{normalized_source_lane_id or '-'}:{normalized_queue_job_id or '-'}:"
                f"{normalized_board_token or '-'}"
            ),
            evidence_refs=_learning_conflict_evidence_refs(
                board_id=normalized_board_id,
                source_lane_id=normalized_source_lane_id,
                queue_job_id=normalized_queue_job_id,
                source_board_concurrency_token=normalized_board_token,
                conflict_detail=conflict_detail,
            ),
            summary_metadata=summary_metadata,
        )
        await db.commit()
    except Exception:
        await db.rollback()


async def _seed_learning_entries_from_approval_receipts(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    if await _get_missing_approval_receipt_tables(db):
        return False

    result = await db.execute(
        select(DeveloperControlPlaneApprovalReceipt)
        .where(DeveloperControlPlaneApprovalReceipt.organization_id == organization_id)
        .order_by(
            DeveloperControlPlaneApprovalReceipt.created_at.asc(),
            DeveloperControlPlaneApprovalReceipt.id.asc(),
        )
    )

    created_any = False
    for receipt in result.scalars().all():
        lane_id = receipt.source_lane_id or "unknown-lane"
        queue_job_id = receipt.queue_job_id or "unknown-job"
        if receipt.action_type == QUEUE_WRITE_OPERATOR_INTENT:
            _, created = await _record_learning_entry(
                db,
                organization_id,
                entry_type="pattern",
                source_classification="accepted-review",
                title=f"Accepted review enabled queue export for lane {lane_id}",
                summary=(
                    f"Explicit spec_review and risk_review evidence supported queue export for "
                    f"lane {lane_id} into queue job {queue_job_id} without weakening board-wins precedence."
                ),
                confidence_score=0.93,
                recorded_by_user_id=receipt.authority_actor_user_id,
                recorded_by_email=receipt.authority_actor_email,
                board_id=receipt.board_id,
                source_lane_id=receipt.source_lane_id,
                queue_job_id=receipt.queue_job_id,
                linked_mission_id=receipt.linked_mission_id,
                approval_receipt_id=receipt.id,
                source_reference=f"approval-receipt:{receipt.id}:accepted-review",
                evidence_refs=receipt.evidence_refs,
                summary_metadata={
                    "seed_source": "approval-receipt",
                    "approval_receipt_action": receipt.action_type,
                    "approval_receipt_outcome": receipt.outcome,
                    "queue_sha256": receipt.resulting_queue_sha256,
                },
            )
            created_any = created_any or created
            continue

        if receipt.action_type != COMPLETION_WRITE_OPERATOR_INTENT:
            continue

        receipt_metadata = receipt.summary_metadata if isinstance(receipt.summary_metadata, dict) else {}
        closeout_receipt_present = receipt_metadata.get("closeout_receipt_present") is True
        _, created = await _record_learning_entry(
            db,
            organization_id,
            entry_type="pattern",
            source_classification="reviewed-completion-writeback",
            title=f"Reviewed completion write-back closed lane {lane_id}",
            summary=(
                f"Explicit reviewed completion write-back persisted canonical closure for lane "
                f"{lane_id} from queue job {queue_job_id} without weakening board-wins precedence."
                + (
                    " Runtime closeout receipt evidence stayed attached to the accepted closure path."
                    if closeout_receipt_present
                    else " The canonical board remained the accepted closure authority."
                )
            ),
            confidence_score=0.94,
            recorded_by_user_id=receipt.authority_actor_user_id,
            recorded_by_email=receipt.authority_actor_email,
            board_id=receipt.board_id,
            source_lane_id=receipt.source_lane_id,
            queue_job_id=receipt.queue_job_id,
            linked_mission_id=receipt.linked_mission_id,
            approval_receipt_id=receipt.id,
            source_reference=f"approval-receipt:{receipt.id}:reviewed-completion-writeback",
            evidence_refs=receipt.evidence_refs,
            summary_metadata={
                "seed_source": "approval-receipt",
                "approval_receipt_action": receipt.action_type,
                "approval_receipt_outcome": receipt.outcome,
                "queue_sha256": receipt.resulting_queue_sha256,
                "closeout_receipt_present": closeout_receipt_present,
            },
        )
        created_any = created_any or created

    return created_any


async def _seed_learning_entries_from_mission_state(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    missing_tables, missing_columns = await _get_missing_mission_state_schema_requirements(db)
    if missing_tables or missing_columns:
        return False

    service = OrchestratorMissionStateService(
        PostgresMissionStateRepository(db, organization_id=organization_id)
    )
    missions = await service.repository.list_missions(owner="OmShriMaatreNamaha")

    created_any = False
    for mission in missions:
        snapshot = await service.get_mission_snapshot(mission.id)
        summary = _mission_summary_response(snapshot)
        mission_evidence_refs = _mission_learning_evidence_refs(
            snapshot,
            include_passed_runs=True,
        )
        regression_evidence_refs = _mission_learning_evidence_refs(
            snapshot,
            include_passed_runs=False,
        )

        if any(
            item.decision_class == "stable_closeout_receipt_observed"
            for item in snapshot.decision_notes
        ):
            _, created = await _record_learning_entry(
                db,
                organization_id,
                entry_type="pattern",
                source_classification="stable-closeout-receipt",
                title=f"Stable closeout receipt observed for mission {snapshot.mission.id}",
                summary=(
                    f"Stable closeout receipt evidence was observed for queue job "
                    f"{summary.queue_job_id or snapshot.mission.id} before canonical board closure, "
                    "so later review can reuse the same runtime provenance."
                ),
                confidence_score=0.88,
                recorded_by_user_id=None,
                recorded_by_email=None,
                board_id=DEVELOPER_MASTER_BOARD_ID,
                source_lane_id=summary.source_lane_id,
                queue_job_id=summary.queue_job_id,
                linked_mission_id=snapshot.mission.id,
                approval_receipt_id=None,
                source_reference=f"mission:{snapshot.mission.id}:stable-closeout-receipt",
                evidence_refs=mission_evidence_refs,
                summary_metadata={
                    "seed_source": "mission-state",
                    "producer_key": summary.producer_key,
                    "mission_status": summary.status,
                    "decision_classes": [
                        item.decision_class for item in snapshot.decision_notes
                    ],
                },
            )
            created_any = created_any or created

        if summary.verification.failed or summary.verification.warned:
            _, created = await _record_learning_entry(
                db,
                organization_id,
                entry_type="verification-learning",
                source_classification="benchmark-regression",
                title=f"Mission verification regression for {snapshot.mission.id}",
                summary=(
                    f"Mission {snapshot.mission.id} currently has {summary.verification.failed} failed "
                    f"and {summary.verification.warned} warning verification runs; reuse this regression "
                    "evidence before promoting similar control-plane changes."
                ),
                confidence_score=0.86,
                recorded_by_user_id=None,
                recorded_by_email=None,
                board_id=DEVELOPER_MASTER_BOARD_ID,
                source_lane_id=summary.source_lane_id,
                queue_job_id=summary.queue_job_id,
                linked_mission_id=snapshot.mission.id,
                approval_receipt_id=None,
                source_reference=(
                    f"mission:{snapshot.mission.id}:verification-regression:"
                    f"{summary.verification.failed}:{summary.verification.warned}"
                ),
                evidence_refs=regression_evidence_refs,
                summary_metadata={
                    "seed_source": "mission-state",
                    "producer_key": summary.producer_key,
                    "mission_status": summary.status,
                    "verification": summary.verification.model_dump(),
                },
            )
            created_any = created_any or created

    return created_any


async def _seed_learning_entries(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    if await _get_missing_learning_tables(db):
        return False

    created_from_receipts = await _seed_learning_entries_from_approval_receipts(
        db,
        organization_id,
    )
    created_from_missions = await _seed_learning_entries_from_mission_state(
        db,
        organization_id,
    )
    return created_from_receipts or created_from_missions


async def _seed_approval_receipt_learnings_if_ready(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    if await _get_missing_learning_tables(db):
        return False
    return await _seed_learning_entries_from_approval_receipts(db, organization_id)


async def _seed_mission_state_learnings_if_ready(
    db: AsyncSession,
    organization_id: int,
) -> bool:
    if await _get_missing_learning_tables(db):
        return False
    return await _seed_learning_entries_from_mission_state(db, organization_id)


def _queue_write_conflict_detail(
    reason: str, detail: str, **extra: Any
) -> dict[str, Any]:
    remediation_message = {
        "lane-review-missing": (
            "Update the canonical lane with explicit spec_review and risk_review evidence, "
            "save the shared board, then retry queue export from the current board token."
        ),
        "missing-active-board": (
            "Restore or resave the shared active board first. Queue writes stay blocked "
            "until shared board provenance exists."
        ),
        "stale-board-token": (
            "Refresh the shared board state, confirm the selected lane still "
            "materializes to the intended queue entry, then retry with the current "
            "board token."
        ),
        "queue-sha-mismatch": (
            "Refresh queue status, compare the latest queue hash shown here, then retry "
            "only if the reviewed queue entry is still valid."
        ),
        "duplicate-job-id": (
            "Do not overwrite. Inspect whether the existing queued job already "
            "represents this lane and token pair, or regenerate from a newer board token "
            "if the board changed."
        ),
    }[reason]
    refresh_targets = {
        "lane-review-missing": ["active-board"],
        "missing-active-board": ["active-board"],
        "stale-board-token": ["active-board"],
        "queue-sha-mismatch": ["overnight-queue"],
        "duplicate-job-id": ["overnight-queue", "active-board"],
    }[reason]
    retry_permitted_after_refresh = {
        "lane-review-missing": False,
        "missing-active-board": True,
        "stale-board-token": True,
        "queue-sha-mismatch": True,
        "duplicate-job-id": False,
    }[reason]

    return {
        "detail": detail,
        "conflict_reason": reason,
        "remediation_message": remediation_message,
        "refresh_targets": refresh_targets,
        "retry_permitted_after_refresh": retry_permitted_after_refresh,
        **extra,
    }


def _completion_write_conflict_detail(
    reason: str, detail: str, **extra: Any
) -> dict[str, Any]:
    remediation_message = {
        "lane-verification-missing": (
            "Attach canonical verification_evidence to the lane, save the shared board, "
            "and retry completion write-back only after the reviewed verification gate "
            "is visible."
        ),
        "missing-active-board": (
            "Restore or resave the shared active board first. Completion write-back "
            "stays blocked until shared board provenance exists."
        ),
        "queue-sha-mismatch": (
            "Refresh queue status, confirm the current queue hash and the reviewed "
            "completion target, then retry only if the same job still applies."
        ),
        "queue-job-missing": (
            "The reviewed queue job is no longer present in the current queue snapshot. "
            "Refresh queue status and verify the job id before retrying."
        ),
        "queue-job-not-completed": (
            "Wait until the reviewed queue job reaches completed status before writing "
            "closure evidence back into the board."
        ),
        "closeout-receipt-required": (
            "Refresh the reviewed closeout receipt and retry only after the normalized "
            "receipt is visible in the control plane. Runtime-backed lanes should not be "
            "closed from freeform evidence alone."
        ),
        "closeout-receipt-mismatch": (
            "Refresh the reviewed closeout receipt, compare the latest normalized runtime "
            "evidence, and retry only if the receipt still matches the queue job being "
            "closed."
        ),
        "lane-job-mismatch": (
            "Refresh the shared board state and use the deterministic lane job id for the "
            "selected lane and board token. Do not apply completion evidence to a "
            "mismatched job."
        ),
        "stale-board-token": (
            "Refresh the shared board state, confirm the lane is still the intended "
            "completion target, then retry with the current board token."
        ),
        "lane-status-conflict": (
            "Only active lanes can move to completed in this slice. Review the current "
            "lane status and avoid forcing completion onto a non-active lane."
        ),
        "completion-overwrite-conflict": (
            "This lane already has different closure evidence. Review the current board "
            "record instead of overwriting closure data implicitly."
        ),
    }[reason]
    refresh_targets = {
        "lane-verification-missing": ["active-board"],
        "missing-active-board": ["active-board"],
        "queue-sha-mismatch": ["overnight-queue"],
        "queue-job-missing": ["overnight-queue"],
        "queue-job-not-completed": ["overnight-queue", "closeout-receipt"],
        "closeout-receipt-required": ["closeout-receipt", "overnight-queue"],
        "closeout-receipt-mismatch": ["closeout-receipt", "overnight-queue"],
        "lane-job-mismatch": ["active-board", "overnight-queue"],
        "stale-board-token": ["active-board"],
        "lane-status-conflict": ["active-board"],
        "completion-overwrite-conflict": ["active-board"],
    }[reason]
    retry_permitted_after_refresh = {
        "lane-verification-missing": False,
        "missing-active-board": True,
        "queue-sha-mismatch": True,
        "queue-job-missing": False,
        "queue-job-not-completed": True,
        "closeout-receipt-required": True,
        "closeout-receipt-mismatch": True,
        "lane-job-mismatch": True,
        "stale-board-token": True,
        "lane-status-conflict": False,
        "completion-overwrite-conflict": False,
    }[reason]

    return {
        "detail": detail,
        "conflict_reason": reason,
        "remediation_message": remediation_message,
        "refresh_targets": refresh_targets,
        "retry_permitted_after_refresh": retry_permitted_after_refresh,
        **extra,
    }


def _queue_token_suffix(source_board_concurrency_token: str) -> str:
    normalized = "".join(
        character
        for character in source_board_concurrency_token.lower()
        if character.isascii() and character.isalnum()
    )[:8]
    return normalized or "unknown000"


def _create_lane_queue_job_id(source_lane_id: str, source_board_concurrency_token: str) -> str:
    return f"overnight-lane-{source_lane_id}-{_queue_token_suffix(source_board_concurrency_token)}"


def _find_queue_job(queue_payload: dict[str, Any], queue_job_id: str) -> dict[str, Any] | None:
    for job in queue_payload.get("jobs", []):
        if isinstance(job, dict) and job.get("jobId") == queue_job_id:
            return job
    return None


def _find_board_lane(board_payload: dict[str, Any], lane_id: str) -> dict[str, Any] | None:
    lanes = board_payload.get("lanes")
    if not isinstance(lanes, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current active board payload is missing lanes",
        )

    return next(
        (
            entry
            for entry in lanes
            if isinstance(entry, dict) and entry.get("id") == lane_id
        ),
        None,
    )


def _build_completion_write_preparation_response(
    *,
    source_lane_id: str,
    source_board_concurrency_token: str,
) -> DeveloperControlPlaneCompletionWritePreparationResponse:
    queue_status = _overnight_queue_status_response()
    queue_job_id = _create_lane_queue_job_id(
        source_lane_id,
        source_board_concurrency_token,
    )
    closeout_receipt = _closeout_receipt_response(
        queue_job_id,
        _load_closeout_receipt(queue_job_id),
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


def _validate_completion_payload(
    payload: DeveloperControlPlaneLaneCompletionPayload,
) -> dict[str, Any]:
    validated_closeout_receipt = None
    if payload.closeout_receipt is not None:
        validated_closeout_receipt = _build_closeout_receipt_contract(
            queue_job_id=_require_ascii_text(
                payload.closeout_receipt.queue_job_id,
                "completion.closeout_receipt.queue_job_id",
            ),
            artifact_paths=_require_ascii_text_list(
                payload.closeout_receipt.artifact_paths,
                "completion.closeout_receipt.artifact_paths",
                min_items=0,
            ),
            mission_id=_optional_ascii_text(
                payload.closeout_receipt.mission_id,
                "completion.closeout_receipt.mission_id",
            ),
            producer_key=_optional_ascii_text(
                payload.closeout_receipt.producer_key,
                "completion.closeout_receipt.producer_key",
            ),
            source_lane_id=_optional_ascii_text(
                payload.closeout_receipt.source_lane_id,
                "completion.closeout_receipt.source_lane_id",
            ),
            source_board_concurrency_token=_optional_ascii_text(
                payload.closeout_receipt.source_board_concurrency_token,
                "completion.closeout_receipt.source_board_concurrency_token",
            ),
            runtime_profile_id=_optional_ascii_text(
                payload.closeout_receipt.runtime_profile_id,
                "completion.closeout_receipt.runtime_profile_id",
            ),
            runtime_policy_sha256=_optional_ascii_text(
                payload.closeout_receipt.runtime_policy_sha256,
                "completion.closeout_receipt.runtime_policy_sha256",
            ),
            closeout_status=_optional_ascii_text(
                payload.closeout_receipt.closeout_status,
                "completion.closeout_receipt.closeout_status",
            ),
            state_refresh_required=payload.closeout_receipt.state_refresh_required,
            receipt_recorded_at=_optional_ascii_text(
                payload.closeout_receipt.receipt_recorded_at,
                "completion.closeout_receipt.receipt_recorded_at",
            ),
            verification_evidence_ref=_optional_ascii_text(
                payload.closeout_receipt.verification_evidence_ref,
                "completion.closeout_receipt.verification_evidence_ref",
            ),
            queue_sha256_at_closeout=_optional_ascii_text(
                payload.closeout_receipt.queue_sha256_at_closeout,
                "completion.closeout_receipt.queue_sha256_at_closeout",
            ),
        )

    return {
        "source_lane_id": _require_ascii_text(payload.source_lane_id, "completion.source_lane_id"),
        "queue_job_id": _require_ascii_text(payload.queue_job_id, "completion.queue_job_id"),
        "closure_summary": _require_ascii_text(
            payload.closure_summary,
            "completion.closure_summary",
        ),
        "evidence": _require_ascii_text_list(payload.evidence, "completion.evidence", min_items=1),
        "closeout_receipt": validated_closeout_receipt,
    }


def _build_closeout_receipt_contract(
    *,
    queue_job_id: str,
    artifact_paths: list[str],
    mission_id: str | None = None,
    producer_key: str | None = None,
    source_lane_id: str | None = None,
    source_board_concurrency_token: str | None = None,
    runtime_profile_id: str | None = None,
    runtime_policy_sha256: str | None = None,
    closeout_status: str | None = None,
    state_refresh_required: bool | None = None,
    receipt_recorded_at: str | None = None,
    verification_evidence_ref: str | None = None,
    queue_sha256_at_closeout: str | None = None,
) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "queue_job_id": queue_job_id,
        "artifact_paths": artifact_paths,
    }
    if mission_id is not None:
        contract["mission_id"] = mission_id
    if producer_key is not None:
        contract["producer_key"] = producer_key
    if source_lane_id is not None:
        contract["source_lane_id"] = source_lane_id
    if source_board_concurrency_token is not None:
        contract["source_board_concurrency_token"] = source_board_concurrency_token
    if runtime_profile_id is not None:
        contract["runtime_profile_id"] = runtime_profile_id
    if runtime_policy_sha256 is not None:
        contract["runtime_policy_sha256"] = runtime_policy_sha256
    if closeout_status is not None:
        contract["closeout_status"] = closeout_status
    if state_refresh_required is not None:
        contract["state_refresh_required"] = state_refresh_required
    if receipt_recorded_at is not None:
        contract["receipt_recorded_at"] = receipt_recorded_at
    if verification_evidence_ref is not None:
        contract["verification_evidence_ref"] = verification_evidence_ref
    if queue_sha256_at_closeout is not None:
        contract["queue_sha256_at_closeout"] = queue_sha256_at_closeout
    return contract


def _closeout_receipt_contract_from_response(
    receipt: DeveloperControlPlaneCloseoutReceiptResponse,
) -> dict[str, Any] | None:
    if not receipt.exists:
        return None

    return _build_closeout_receipt_contract(
        queue_job_id=receipt.queue_job_id,
        artifact_paths=[artifact.path for artifact in receipt.artifacts if artifact.exists],
        mission_id=receipt.mission_id,
        producer_key=receipt.producer_key,
        source_lane_id=receipt.source_lane_id,
        source_board_concurrency_token=receipt.source_board_concurrency_token,
        runtime_profile_id=receipt.runtime_profile_id,
        runtime_policy_sha256=receipt.runtime_policy_sha256,
        closeout_status=receipt.closeout_status,
        state_refresh_required=receipt.state_refresh_required,
        receipt_recorded_at=receipt.receipt_recorded_at,
        verification_evidence_ref=receipt.verification_evidence_ref,
        queue_sha256_at_closeout=receipt.queue_sha256_at_closeout,
    )


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


def _parse_completion_source_request(
    source_request: str | None,
) -> dict[str, str | None] | None:
    if not source_request:
        return None

    match = MISSION_LINKAGE_SOURCE_REQUEST_PATTERN.match(source_request.strip())
    if match is None:
        return None

    return {
        "source_lane_id": match.group("lane_id"),
        "queue_job_id": match.group("queue_job_id"),
        "source_board_concurrency_token": match.group("board_token"),
    }


def _mission_linkage(mission: Any) -> dict[str, str | None] | None:
    queue_job_id = mission.queue_job_id if isinstance(mission.queue_job_id, str) else None
    source_lane_id = mission.source_lane_id if isinstance(mission.source_lane_id, str) else None
    source_board_concurrency_token = (
        mission.source_board_concurrency_token
        if isinstance(mission.source_board_concurrency_token, str)
        else None
    )

    if (
        queue_job_id is not None
        or source_lane_id is not None
        or source_board_concurrency_token is not None
    ):
        return {
            "queue_job_id": queue_job_id,
            "source_lane_id": source_lane_id,
            "source_board_concurrency_token": source_board_concurrency_token,
        }

    return _parse_completion_source_request(mission.source_request)


async def _lookup_active_board_lane_title(
    db: AsyncSession,
    organization_id: int,
    lane_id: str,
) -> str | None:
    current_record = await _get_active_board(db, organization_id)
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


def _build_lane_completion(
    *,
    queue_job_id: str,
    queue_sha256: str,
    source_board_concurrency_token: str,
    closure_summary: str,
    evidence: list[str],
    closeout_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    completion = {
        "queue_job_id": queue_job_id,
        "queue_sha256": queue_sha256,
        "source_board_concurrency_token": source_board_concurrency_token,
        "closure_summary": closure_summary,
        "evidence": evidence,
        "completed_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
    }
    if closeout_receipt is not None:
        completion["closeout_receipt"] = closeout_receipt
    return completion


def _is_same_lane_completion(
    existing_closure: Any,
    *,
    queue_job_id: str,
    queue_sha256: str,
    source_board_concurrency_token: str,
    closure_summary: str,
    evidence: list[str],
    closeout_receipt: dict[str, Any] | None,
) -> bool:
    return (
        isinstance(existing_closure, dict)
        and existing_closure.get("queue_job_id") == queue_job_id
        and existing_closure.get("queue_sha256") == queue_sha256
        and existing_closure.get("source_board_concurrency_token") == source_board_concurrency_token
        and existing_closure.get("closure_summary") == closure_summary
        and existing_closure.get("evidence") == evidence
        and existing_closure.get("closeout_receipt") == closeout_receipt
    )


async def _get_active_board(
    db: AsyncSession,
    organization_id: int,
) -> DeveloperControlPlaneActiveBoard | None:
    result = await db.execute(
        select(DeveloperControlPlaneActiveBoard).where(
            DeveloperControlPlaneActiveBoard.organization_id == organization_id,
            DeveloperControlPlaneActiveBoard.board_id == DEVELOPER_MASTER_BOARD_ID,
        )
    )
    return result.scalar_one_or_none()


async def _get_board_versions(
    db: AsyncSession,
    organization_id: int,
) -> list[DeveloperControlPlaneBoardRevision]:
    result = await db.execute(
        select(DeveloperControlPlaneBoardRevision)
        .where(
            DeveloperControlPlaneBoardRevision.organization_id == organization_id,
            DeveloperControlPlaneBoardRevision.board_id == DEVELOPER_MASTER_BOARD_ID,
        )
        .order_by(
            DeveloperControlPlaneBoardRevision.created_at.desc(),
            DeveloperControlPlaneBoardRevision.id.desc(),
        )
    )
    return list(result.scalars().all())


async def _get_board_revision(
    db: AsyncSession,
    organization_id: int,
    revision_id: int,
) -> DeveloperControlPlaneBoardRevision | None:
    result = await db.execute(
        select(DeveloperControlPlaneBoardRevision).where(
            DeveloperControlPlaneBoardRevision.id == revision_id,
            DeveloperControlPlaneBoardRevision.organization_id == organization_id,
            DeveloperControlPlaneBoardRevision.board_id == DEVELOPER_MASTER_BOARD_ID,
        )
    )
    return result.scalar_one_or_none()


def _hash_canonical_board_json(canonical_board_json: str) -> str:
    return hashlib.sha256(canonical_board_json.encode("utf-8")).hexdigest()


def _version_response(
    record: DeveloperControlPlaneBoardRevision,
    current_concurrency_token: str | None,
) -> DeveloperControlPlaneBoardVersionResponse:
    return DeveloperControlPlaneBoardVersionResponse(
        revision_id=record.id,
        schema_version=record.schema_version,
        visibility=record.visibility,
        concurrency_token=record.canonical_board_hash,
        created_at=record.created_at,
        saved_by_user_id=record.saved_by_user_id,
        save_source=record.save_source,
        summary_metadata=record.summary_metadata,
        is_current=current_concurrency_token == record.canonical_board_hash,
    )


def _build_summary_metadata(
    board: Any,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary_metadata = build_developer_master_board_summary(board)
    if extra_metadata is not None:
        summary_metadata = {**summary_metadata, **extra_metadata}
    return summary_metadata


async def _apply_active_board_state(
    db: AsyncSession,
    organization_id: int,
    current_user: User,
    current_record: DeveloperControlPlaneActiveBoard | None,
    *,
    canonical_board_json: str,
    board: Any,
    save_source: str,
    summary_metadata: dict[str, Any],
) -> DeveloperControlPlaneActiveBoard:
    previous_board_hash = current_record.canonical_board_hash if current_record is not None else None
    board_hash = _hash_canonical_board_json(canonical_board_json)

    if current_record is None:
        current_record = DeveloperControlPlaneActiveBoard(
            organization_id=organization_id,
            board_id=board.board_id,
            schema_version=board.version,
            visibility=board.visibility,
            canonical_board_json=canonical_board_json,
            canonical_board_hash=board_hash,
            updated_by_user_id=current_user.id,
            save_source=save_source,
            summary_metadata=summary_metadata,
        )
        db.add(current_record)
    else:
        current_record.schema_version = board.version
        current_record.visibility = board.visibility
        current_record.canonical_board_json = canonical_board_json
        current_record.canonical_board_hash = board_hash
        current_record.updated_by_user_id = current_user.id
        current_record.save_source = save_source
        current_record.summary_metadata = summary_metadata

    await db.flush()

    if previous_board_hash != board_hash:
        db.add(
            DeveloperControlPlaneBoardRevision(
                organization_id=organization_id,
                board_id=board.board_id,
                schema_version=board.version,
                visibility=board.visibility,
                canonical_board_json=canonical_board_json,
                canonical_board_hash=board_hash,
                saved_by_user_id=current_user.id,
                save_source=save_source,
                summary_metadata=summary_metadata,
            )
        )

    return current_record


@router.get("/active-board", response_model=DeveloperControlPlaneActiveBoardFetchResponse)
async def get_active_board(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    await _ensure_persistence_schema_ready(db)
    record = await _get_active_board(db, organization_id)
    if record is None:
        return DeveloperControlPlaneActiveBoardFetchResponse(exists=False, record=None)

    return DeveloperControlPlaneActiveBoardFetchResponse(exists=True, record=_record_response(record))


@router.get(
    "/overnight-queue/status",
    response_model=DeveloperControlPlaneOvernightQueueStatusResponse,
)
async def get_overnight_queue_status():
    return _overnight_queue_status_response()


@router.get(
    "/runtime/watchdog-status",
    response_model=DeveloperControlPlaneWatchdogStatusResponse,
)
async def get_runtime_watchdog_status():
    return _watchdog_status_response(_load_watchdog_state_payload())


@router.get(
    "/runtime/autonomy-cycle",
    response_model=DeveloperControlPlaneAutonomyCycleResponse,
)
async def get_runtime_autonomy_cycle(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    response = _autonomy_cycle_response(_load_autonomy_cycle_payload())
    if response.exists is not True:
        return response

    response.next_actions, response.next_action_ordering_source = (
        await _memory_biased_autonomy_cycle_next_actions(
        db,
        organization_id,
        response.next_actions,
        )
    )
    response.next_actions = await _hydrate_autonomy_cycle_completion_write_preparations(
        db,
        organization_id,
        response.next_actions,
    )
    response.first_actionable_completion_write = _resolve_first_actionable_completion_write(
        response.next_actions
    )
    return response


@router.get(
    "/runtime/completion-assist",
    response_model=DeveloperControlPlaneRuntimeCompletionAssistResponse,
)
async def get_runtime_completion_assist():
    return _completion_assist_response(_load_completion_assist_payload())


@router.get(
    "/runtime/silent-monitors",
    response_model=DeveloperControlPlaneSilentMonitorsResponse,
)
async def get_runtime_silent_monitors():
    queue_status = _overnight_queue_status_response()
    monitors = [
        _queue_staleness_monitor(queue_status),
        _control_surface_drift_monitor(),
        _reevu_readiness_monitor(),
    ]
    return DeveloperControlPlaneSilentMonitorsResponse(
        generated_at=datetime.now(UTC).isoformat(),
        overall_state=_derive_silent_monitor_overall_state(monitors),
        should_emit=any(monitor.should_emit for monitor in monitors),
        monitors=monitors,
    )


@router.get(
    "/runtime/mission-state",
    response_model=DeveloperControlPlaneMissionStateResponse,
)
async def get_runtime_mission_state(
    limit: int = 8,
    queue_job_id: str | None = None,
    source_lane_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
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
    return await _mission_state_response(
        db,
        organization_id,
        limit=bounded_limit,
        queue_job_id=validated_queue_job_id,
        source_lane_id=validated_source_lane_id,
    )


@router.post(
    "/runtime/mission-state/bootstrap-closeout-receipt",
    response_model=DeveloperControlPlaneMissionBootstrapResponse,
)
async def bootstrap_runtime_mission_state_from_closeout_receipt(
    payload: DeveloperControlPlaneMissionBootstrapRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    await _ensure_mission_state_schema_ready(db)
    validated_queue_job_id = _require_ascii_text(payload.queue_job_id, "queue_job_id")
    receipt = _closeout_receipt_contract_from_response(
        _closeout_receipt_response(
            validated_queue_job_id,
            _load_closeout_receipt(validated_queue_job_id),
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


@router.get(
    "/runtime/mission-state/{mission_id}",
    response_model=DeveloperControlPlaneMissionDetailResponse,
)
async def get_runtime_mission_state_detail(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    await _ensure_mission_state_schema_ready(db)
    validated_mission_id = _require_ascii_text(mission_id, "mission_id")
    snapshot = await _load_runtime_mission_snapshot(db, organization_id, validated_mission_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return _mission_detail_response(snapshot)


@router.get(
    "/learnings",
    response_model=DeveloperControlPlaneLearningLedgerResponse,
)
async def list_learning_entries(
    limit: int = 25,
    entry_type: str | None = None,
    source_classification: str | None = None,
    source_lane_id: str | None = None,
    queue_job_id: str | None = None,
    linked_mission_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
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


@router.get(
    "/overnight-queue/jobs/{queue_job_id}/closeout-receipt",
    response_model=DeveloperControlPlaneCloseoutReceiptResponse,
)
async def get_overnight_queue_job_closeout_receipt(queue_job_id: str):
    validated_queue_job_id = _require_ascii_text(queue_job_id, "queue_job_id")
    receipt = _load_closeout_receipt(validated_queue_job_id)
    return _closeout_receipt_response(validated_queue_job_id, receipt)


@router.get(
    "/active-board/versions",
    response_model=DeveloperControlPlaneBoardVersionsListResponse,
)
async def list_active_board_versions(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    await _ensure_persistence_schema_ready(db)
    current_record = await _get_active_board(db, organization_id)
    versions = await _get_board_versions(db, organization_id)
    current_concurrency_token = (
        current_record.canonical_board_hash if current_record is not None else None
    )

    return DeveloperControlPlaneBoardVersionsListResponse(
        board_id=DEVELOPER_MASTER_BOARD_ID,
        current_concurrency_token=current_concurrency_token,
        total_count=len(versions),
        versions=[
            _version_response(version, current_concurrency_token) for version in versions
        ],
    )


@router.put(
    "/active-board",
    response_model=DeveloperControlPlaneActiveBoardRecordResponse,
    responses={status.HTTP_409_CONFLICT: {"model": DeveloperControlPlaneActiveBoardConflictResponse}},
)
async def save_active_board(
    payload: DeveloperControlPlaneActiveBoardSaveRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
):
    await _ensure_persistence_schema_ready(db)
    try:
        canonical_board_json, board = canonicalize_developer_master_board_json(payload.canonical_board_json)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid developer master board: {exc}",
        ) from exc

    current_record = await _get_active_board(db, organization_id)
    if current_record is not None and payload.concurrency_token != current_record.canonical_board_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": "Active board save conflict; refetch the current board before retrying",
                "current_record": _record_response(current_record).model_dump(mode="json"),
            },
        )

    current_record = await _apply_active_board_state(
        db,
        organization_id,
        current_user,
        current_record,
        canonical_board_json=canonical_board_json,
        board=board,
        save_source=payload.save_source,
        summary_metadata=_build_summary_metadata(board),
    )
    await db.commit()
    await db.refresh(current_record)
    return _record_response(current_record)


@router.post(
    "/active-board/versions/{revision_id}/restore",
    response_model=DeveloperControlPlaneBoardRestoreResponse,
    responses={status.HTTP_409_CONFLICT: {"model": DeveloperControlPlaneActiveBoardConflictResponse}},
)
async def restore_active_board_version(
    revision_id: int,
    payload: DeveloperControlPlaneBoardRestoreRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
):
    await _ensure_persistence_schema_ready(db)
    await _ensure_approval_receipt_schema_ready(db)
    revision = await _get_board_revision(db, organization_id, revision_id)
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer control-plane revision not found",
        )

    current_record = await _get_active_board(db, organization_id)
    if current_record is not None and payload.concurrency_token != current_record.canonical_board_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": "Active board save conflict; refetch the current board before retrying",
                "current_record": _record_response(current_record).model_dump(mode="json"),
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

    restored_hash = _hash_canonical_board_json(canonical_board_json)
    previous_active_concurrency_token = (
        current_record.canonical_board_hash if current_record is not None else None
    )
    if previous_active_concurrency_token == restored_hash:
        existing_receipt = await _get_latest_approval_receipt(
            db,
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
            record=_record_response(current_record),
            approval_receipt=(
                _approval_receipt_response(existing_receipt)
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
    current_record = await _apply_active_board_state(
        db,
        organization_id,
        current_user,
        current_record,
        canonical_board_json=canonical_board_json,
        board=board,
        save_source="restore-version",
        summary_metadata=_build_summary_metadata(board, {"restore": restore_metadata}),
    )

    approval_receipt = await _record_approval_receipt(
        db,
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
        record=_record_response(current_record),
        approval_receipt=_approval_receipt_response(approval_receipt),
    )


@router.post(
    "/overnight-queue/write-entry",
    response_model=DeveloperControlPlaneOvernightQueueWriteResponse,
)
async def write_overnight_queue_entry(
    payload: DeveloperControlPlaneOvernightQueueWriteRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
):
    await _ensure_persistence_schema_ready(db)
    await _ensure_approval_receipt_schema_ready(db)
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

    current_record = await _get_active_board(db, organization_id)
    if current_record is None:
        conflict_detail = _queue_write_conflict_detail(
            "missing-active-board",
            "Queue write conflict; active board is missing for this organization",
        )
        await _persist_conflict_learning(
            db,
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
        await _persist_conflict_learning(
            db,
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

    queue_payload, _ = _load_overnight_queue_payload()
    queue_payload = _validate_queue_payload_shape(queue_payload)
    current_queue_sha256 = _queue_sha256(queue_payload)
    if payload.expected_queue_sha256 != current_queue_sha256:
        conflict_detail = _queue_write_conflict_detail(
            "queue-sha-mismatch",
            "Queue write conflict; overnight queue changed since the latest snapshot",
            current_queue_sha256=current_queue_sha256,
        )
        await _persist_conflict_learning(
            db,
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
            await _persist_conflict_learning(
                db,
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
    lane = _find_board_lane(board_payload, source_lane_id)
    if lane is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer control-plane lane not found for reviewed queue export",
        )

    if not _lane_has_queue_export_reviews(lane):
        conflict_detail = _queue_write_conflict_detail(
            "lane-review-missing",
            "Queue write conflict; canonical lane is missing explicit spec_review or risk_review evidence",
            source_lane_id=source_lane_id,
        )
        await _persist_conflict_learning(
            db,
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

    previous_queue_payload = json.loads(_serialize_queue_payload(queue_payload))
    queue_payload["jobs"] = [*queue_payload["jobs"], validated_queue_entry]
    queue_payload["updatedAt"] = datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )

    _write_overnight_queue_payload(queue_payload)
    written_queue_sha256 = _queue_sha256(queue_payload)

    try:
        approval_receipt = await _record_approval_receipt(
            db,
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
            _write_overnight_queue_payload(previous_queue_payload)
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
        approval_receipt=_approval_receipt_response(approval_receipt),
    )


@router.post(
    "/active-board/prepare-completion-write",
    response_model=DeveloperControlPlaneCompletionWritePreparationResponse,
)
async def prepare_active_board_completion_write(
    payload: DeveloperControlPlaneCompletionWritePreparationRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    _: User = Depends(get_current_superuser),
):
    await _ensure_persistence_schema_ready(db)

    requested_lane_id = _require_ascii_text(payload.source_lane_id, "source_lane_id")
    current_record = await _get_active_board(db, organization_id)
    if current_record is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_completion_write_conflict_detail(
                "missing-active-board",
                "Completion write preparation conflict; active board is missing for this organization",
            ),
        )

    board_payload = _load_active_board_payload(current_record)
    if _find_board_lane(board_payload, requested_lane_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lane {requested_lane_id} does not exist in the current active board",
        )

    return _build_completion_write_preparation_response(
        source_lane_id=requested_lane_id,
        source_board_concurrency_token=current_record.canonical_board_hash,
    )


@router.post(
    "/active-board/write-completion",
    response_model=DeveloperControlPlaneCompletionWriteResponse,
)
async def write_active_board_completion(
    payload: DeveloperControlPlaneCompletionWriteRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_superuser),
):
    await _ensure_persistence_schema_ready(db)
    await _ensure_approval_receipt_schema_ready(db)
    await _ensure_mission_state_schema_ready(db)
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

    current_record = await _get_active_board(db, organization_id)
    if current_record is None:
        conflict_detail = _completion_write_conflict_detail(
            "missing-active-board",
            "Completion write-back conflict; active board is missing for this organization",
        )
        await _persist_conflict_learning(
            db,
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=DEVELOPER_MASTER_BOARD_ID,
            source_lane_id=requested_lane_id,
            queue_job_id=requested_queue_job_id,
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    queue_payload, _ = _load_overnight_queue_payload()
    queue_payload = _validate_queue_payload_shape(queue_payload)
    current_queue_sha256 = _queue_sha256(queue_payload)
    if payload.expected_queue_sha256 != current_queue_sha256:
        conflict_detail = _completion_write_conflict_detail(
            "queue-sha-mismatch",
            "Completion write-back conflict; overnight queue changed since the latest snapshot",
            current_queue_sha256=current_queue_sha256,
        )
        await _persist_conflict_learning(
            db,
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=requested_lane_id,
            queue_job_id=requested_queue_job_id,
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    validated_completion = _validate_completion_payload(payload.completion)
    expected_queue_job_id = _create_lane_queue_job_id(
        validated_completion["source_lane_id"],
        payload.source_board_concurrency_token,
    )
    if validated_completion["queue_job_id"] != expected_queue_job_id:
        conflict_detail = _completion_write_conflict_detail(
            "lane-job-mismatch",
            "Completion write-back conflict; queue job id does not match the current lane and board provenance",
            expected_queue_job_id=expected_queue_job_id,
        )
        await _persist_conflict_learning(
            db,
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    queue_job = _find_queue_job(queue_payload, validated_completion["queue_job_id"])
    if queue_job is None:
        conflict_detail = _completion_write_conflict_detail(
            "queue-job-missing",
            "Completion write-back conflict; queue job is missing from the current overnight queue snapshot",
        )
        await _persist_conflict_learning(
            db,
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )
    if queue_job.get("status") != "completed":
        conflict_detail = _completion_write_conflict_detail(
            "queue-job-not-completed",
            "Completion write-back conflict; queue job must be completed before board write-back",
            current_queue_job_status=queue_job.get("status"),
        )
        await _persist_conflict_learning(
            db,
            organization_id,
            current_user,
            scope="completion-writeback",
            conflict_detail=conflict_detail,
            board_id=current_record.board_id,
            source_lane_id=validated_completion["source_lane_id"],
            queue_job_id=validated_completion["queue_job_id"],
            source_board_concurrency_token=requested_source_board_token,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    current_closeout_receipt = _closeout_receipt_contract_from_response(
        _closeout_receipt_response(
            validated_completion["queue_job_id"],
            _load_closeout_receipt(validated_completion["queue_job_id"]),
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
        await _persist_conflict_learning(
            db,
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )
    if current_closeout_receipt != requested_closeout_receipt:
        conflict_detail = _completion_write_conflict_detail(
            "closeout-receipt-mismatch",
            "Completion write-back conflict; reviewed closeout receipt does not match the latest normalized runtime evidence",
        )
        await _persist_conflict_learning(
            db,
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    board_payload = _load_active_board_payload(current_record)
    lane = _find_board_lane(board_payload, validated_completion["source_lane_id"])
    if lane is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer control-plane lane not found",
        )

    if lane.get("status") == "completed":
        if _is_same_lane_completion(
            lane.get("closure"),
            queue_job_id=validated_completion["queue_job_id"],
            queue_sha256=current_queue_sha256,
            source_board_concurrency_token=payload.source_board_concurrency_token,
            closure_summary=validated_completion["closure_summary"],
            evidence=validated_completion["evidence"],
            closeout_receipt=current_closeout_receipt,
        ):
            existing_receipt = await _get_latest_approval_receipt(
                db,
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
                record=_record_response(current_record),
                approval_receipt=(
                    _approval_receipt_response(existing_receipt)
                    if existing_receipt is not None
                    else None
                ),
            )
        conflict_detail = _completion_write_conflict_detail(
            "completion-overwrite-conflict",
            "Completion write-back conflict; completed lane already has different closure evidence",
        )
        await _persist_conflict_learning(
            db,
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
        await _persist_conflict_learning(
            db,
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    if lane.get("status") != "active":
        conflict_detail = _completion_write_conflict_detail(
            "lane-status-conflict",
            "Completion write-back conflict; lane must be active before it can be marked completed",
            current_lane_status=lane.get("status"),
        )
        await _persist_conflict_learning(
            db,
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    if not _lane_has_completion_verification_evidence(lane):
        conflict_detail = _completion_write_conflict_detail(
            "lane-verification-missing",
            "Completion write-back conflict; canonical lane is missing explicit verification_evidence",
            current_lane_status=lane.get("status"),
        )
        await _persist_conflict_learning(
            db,
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    lane["status"] = "completed"
    lane["closure"] = _build_lane_completion(
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

    current_record = await _apply_active_board_state(
        db,
        organization_id,
        current_user,
        current_record,
        canonical_board_json=canonical_board_json,
        board=board,
        save_source="write-completion",
        summary_metadata=_build_summary_metadata(
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

    approval_receipt = await _record_approval_receipt(
        db,
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
        record=_record_response(current_record),
        approval_receipt=_approval_receipt_response(approval_receipt),
    )

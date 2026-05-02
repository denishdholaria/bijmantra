"""Frozen API schemas for the developer control-plane.

This module contains ALL Pydantic request/response models that external
consumers depend on — most critically the BeingBijMantra VS Code extension
(autonomy bridge).

DO NOT modify field names, field types, or nesting structures without
following the breaking-change process defined in Requirement 2 of the
control-plane kernel extraction spec.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Queue status and write
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Approval receipt
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Learning ledger
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Queue write response
# ---------------------------------------------------------------------------

class DeveloperControlPlaneOvernightQueueWriteResponse(BaseModel):
    queue_sha256: str
    queue_updated_at: str
    written_job_id: str
    replaced: bool
    approval_receipt: DeveloperControlPlaneApprovalReceiptResponse | None = None


# ---------------------------------------------------------------------------
# Closeout receipt
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Completion closeout receipt payload
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Autonomy cycle
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Active board
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Lane completion
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Autonomy cycle actionable completion write (depends on preparation response)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Runtime completion assist
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Silent monitors
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Mission state
# ---------------------------------------------------------------------------

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

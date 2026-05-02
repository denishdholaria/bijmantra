import { ApiError } from '@/lib/api-errors'
import { apiClient } from '@/lib/api-client'

export type DeveloperControlPlaneActiveBoardRecord = {
  id: number
  organization_id: number
  board_id: string
  schema_version: string
  visibility: string
  canonical_board_json: string
  concurrency_token: string
  updated_by_user_id: number
  updated_at: string
  save_source: string
  summary_metadata: Record<string, unknown> | null
  created_at: string
}

export type DeveloperControlPlaneActiveBoardFetchResponse = {
  exists: boolean
  record: DeveloperControlPlaneActiveBoardRecord | null
}

export type DeveloperControlPlaneBoardVersion = {
  revision_id: number
  schema_version: string
  visibility: string
  concurrency_token: string
  created_at: string
  saved_by_user_id: number
  save_source: string
  summary_metadata: Record<string, unknown> | null
  is_current: boolean
}

export type DeveloperControlPlaneBoardVersionsListResponse = {
  board_id: string
  current_concurrency_token: string | null
  total_count: number
  versions: DeveloperControlPlaneBoardVersion[]
}

export type DeveloperControlPlaneBoardRestoreResponse = {
  restored: boolean
  restored_from_revision_id: number
  record: DeveloperControlPlaneActiveBoardRecord
  approval_receipt: DeveloperControlPlaneApprovalReceipt | null
}

export type DeveloperControlPlaneOvernightQueueStatusResponse = {
  queue_path: string
  queue_sha256: string
  exists: boolean
  job_count: number
  updated_at: string | null
}

export type DeveloperControlPlaneCloseoutCommandResult = {
  command: string
  passed: boolean
  exit_code: number | null
  started_at: string | null
  finished_at: string | null
  stdout_tail: string | null
  stderr_tail: string | null
}

export type DeveloperControlPlaneCloseoutArtifact = {
  path: string
  exists: boolean
  sha256: string | null
  modified_at: string | null
}

export type DeveloperControlPlaneCloseoutReceiptResponse = {
  exists: boolean
  queue_job_id: string
  mission_id?: string | null
  producer_key?: string | null
  source_lane_id?: string | null
  source_board_concurrency_token?: string | null
  runtime_profile_id?: string | null
  runtime_policy_sha256?: string | null
  closeout_status: string | null
  state_refresh_required: boolean | null
  receipt_recorded_at: string | null
  started_at: string | null
  finished_at: string | null
  verification_evidence_ref: string | null
  queue_sha256_at_closeout: string | null
  closeout_commands: DeveloperControlPlaneCloseoutCommandResult[]
  artifacts: DeveloperControlPlaneCloseoutArtifact[]
}

export type DeveloperControlPlaneWatchdogJob = {
  job_id: string
  label: string | null
  status: string | null
  started_at: string | null
  duration_minutes: number | null
  last_error: string | null
  consecutive_errors: number | null
  branch: string | null
  verification_passed: boolean | null
}

export type DeveloperControlPlaneWatchdogCompletionAssistAdvisory = {
  authority: string
  observed_from_path: string | null
  available: boolean
  artifact_path: string | null
  status: string | null
  staged: boolean
  explicit_write_required: boolean
  message: string | null
  source_lane_id: string | null
  queue_job_id: string | null
  draft_source: string | null
  receipt_path: string | null
  source_endpoint: string | null
  autonomy_cycle_artifact_path: string | null
  next_action_ordering_source: string | null
  matched_selected_job_ids: string[]
}

export type DeveloperControlPlaneWatchdogStatusResponse = {
  exists: boolean
  state_path: string
  auth_store_exists: boolean
  auth_store_path: string
  bootstrap_ready: boolean
  bootstrap_status: string
  mission_evidence_dir_exists: boolean
  mission_evidence_dir_path: string
  last_check: string | null
  state_age_seconds?: number | null
  state_is_stale?: boolean
  gateway_healthy: boolean | null
  total_checks: number
  total_alerts: number
  job_count: number
  jobs: DeveloperControlPlaneWatchdogJob[]
  completion_assist_advisory?: DeveloperControlPlaneWatchdogCompletionAssistAdvisory | null
}

export type DeveloperControlPlaneAutonomyCycleJobError = {
  last_error: string | null
  consecutive_errors: number | null
}

export type DeveloperControlPlaneAutonomyCycleWatchdog = {
  exists: boolean
  state_path: string
  last_check: string | null
  gateway_healthy: boolean | null
  state_is_stale: boolean
  total_alerts: number
  job_errors: Record<string, DeveloperControlPlaneAutonomyCycleJobError>
}

export type DeveloperControlPlaneAutonomyCycleSelectedJob = {
  job_id: string
  title: string
  source_lane_id: string | null
  priority: string
  primary_agent: string
  trigger_reason: string | null
  source_task: string | null
}

export type DeveloperControlPlaneAutonomyCycleBlockedJob = {
  job_id: string
  title: string
  source_lane_id: string | null
  reason: string | null
}

export type DeveloperControlPlaneAutonomyCycleCloseoutCandidate = {
  job_id: string
  title: string | null
  source_lane_id: string | null
  queue_status: string | null
  closeout_status: string | null
  mission_id: string | null
  verification_evidence_ref: string | null
  path: string | null
}

export type DeveloperControlPlaneAutonomyCycleAction = {
  action: string
  job_id: string | null
  title: string | null
  source_lane_id: string | null
  reason: string | null
  primary_agent: string | null
  priority: string | null
  mission_id: string | null
  receipt_path: string | null
  state_path: string | null
  detail: Record<string, unknown> | null
}

export type DeveloperControlPlaneAutonomyCycleActionableCompletionWrite = {
  action: string
  action_index: number
  job_id: string
  source_lane_id: string
  reason: string | null
  mission_id: string | null
  receipt_path: string | null
  preparation: DeveloperControlPlaneCompletionWritePreparationResponse
}

export type DeveloperControlPlaneAutonomyCycleOrderingSource =
  | 'artifact'
  | 'canonical-learning-exact-runtime'
  | 'canonical-learning-fallback'

export type DeveloperControlPlaneAutonomyCycleResponse = {
  exists: boolean
  artifact_path: string
  generated_at: string | null
  queue_path: string | null
  window: string | null
  max_jobs_per_run: number
  status_counts: Record<string, number>
  selected_job_count: number
  blocked_job_count: number
  closeout_candidate_count: number
  next_action_count: number
  next_action_ordering_source: DeveloperControlPlaneAutonomyCycleOrderingSource
  watchdog: DeveloperControlPlaneAutonomyCycleWatchdog
  selected_jobs: DeveloperControlPlaneAutonomyCycleSelectedJob[]
  blocked_jobs: DeveloperControlPlaneAutonomyCycleBlockedJob[]
  closeout_candidates: DeveloperControlPlaneAutonomyCycleCloseoutCandidate[]
  next_actions: DeveloperControlPlaneAutonomyCycleAction[]
  first_actionable_completion_write: DeveloperControlPlaneAutonomyCycleActionableCompletionWrite | null
}

export type DeveloperControlPlaneRuntimeCompletionAssistResponse = {
  exists: boolean
  artifact_path: string
  generated_at: string | null
  status: string | null
  staged: boolean
  explicit_write_required: boolean
  message: string | null
  source: {
    endpoint: string
    autonomy_cycle_artifact_path: string | null
    autonomy_cycle_generated_at: string | null
    next_action_ordering_source: string | null
  } | null
  actionable_completion_write: {
    action: string
    actionIndex: number
    jobId: string
    sourceLaneId: string
    reason: string | null
    missionId: string | null
    receiptPath: string | null
    draftSource: DeveloperControlPlaneCompletionWritePreparationResponse['draft_source']
    queueStatus: DeveloperControlPlaneOvernightQueueStatusResponse
    closeoutReceipt: DeveloperControlPlaneCloseoutReceiptResponse
    preparedRequest: DeveloperControlPlaneCompletionWriteRequest
  } | null
}

export type DeveloperControlPlaneSilentMonitorState = 'healthy' | 'watch' | 'alert' | 'missing'

export type DeveloperControlPlaneSilentMonitorEvidenceSource = {
  label: string
  path: string
  observed_at: string | null
}

export type DeveloperControlPlaneSilentMonitor = {
  monitor_key: string
  label: string
  state: DeveloperControlPlaneSilentMonitorState
  should_emit: boolean
  summary: string
  detail: string | null
  observed_at: string | null
  refresh_cadence: string
  output_artifact: string
  mutates_authority_surfaces: boolean
  evidence_sources: DeveloperControlPlaneSilentMonitorEvidenceSource[]
  findings: string[]
}

export type DeveloperControlPlaneSilentMonitorsResponse = {
  generated_at: string
  overall_state: DeveloperControlPlaneSilentMonitorState
  should_emit: boolean
  monitors: DeveloperControlPlaneSilentMonitor[]
}

export type DeveloperControlPlaneMissionVerificationSummary = {
  passed: number
  warned: number
  failed: number
  last_verified_at: string | null
}

export type DeveloperControlPlaneMissionSummary = {
  mission_id: string
  objective: string
  status: string
  owner: string
  priority: string
  producer_key: string | null
  queue_job_id?: string | null
  source_lane_id?: string | null
  source_board_concurrency_token?: string | null
  created_at: string
  updated_at: string
  subtask_total: number
  subtask_completed: number
  assignment_total: number
  evidence_count: number
  blocker_count: number
  escalation_needed: boolean
  verification: DeveloperControlPlaneMissionVerificationSummary
  final_summary: string | null
}

export type DeveloperControlPlaneMissionStateResponse = {
  count: number
  missions: DeveloperControlPlaneMissionSummary[]
}

export type DeveloperControlPlaneLearningEntryType =
  | 'pattern'
  | 'pitfall'
  | 'incident'
  | 'verification-learning'

export type DeveloperControlPlaneLearningEntry = {
  learning_entry_id: number
  organization_id: number
  entry_type: DeveloperControlPlaneLearningEntryType
  source_classification: string
  title: string
  summary: string
  confidence_score: number | null
  recorded_by_user_id: number | null
  recorded_by_email: string | null
  board_id: string | null
  source_lane_id: string | null
  queue_job_id: string | null
  linked_mission_id: string | null
  approval_receipt_id: number | null
  source_reference: string | null
  evidence_refs: string[]
  summary_metadata: Record<string, unknown> | null
  recorded_at: string
}

export type DeveloperControlPlaneLearningLedgerResponse = {
  total_count: number
  entries: DeveloperControlPlaneLearningEntry[]
}

export type DeveloperControlPlaneMissionBootstrapResponse = {
  action: string
  mission_id: string | null
}

type DeveloperControlPlaneMissionStateQuery = {
  limit?: number
  queueJobId?: string | null
  sourceLaneId?: string | null
}

type DeveloperControlPlaneLearningLedgerQuery = {
  limit?: number
  entryType?: DeveloperControlPlaneLearningEntryType | null
  sourceClassification?: string | null
  sourceLaneId?: string | null
  queueJobId?: string | null
  linkedMissionId?: string | null
}

export type DeveloperControlPlaneMissionSubtask = {
  id: string
  title: string
  status: string
  owner_role: string
  depends_on: string[]
  updated_at: string
}

export type DeveloperControlPlaneMissionAssignment = {
  id: string
  subtask_id: string
  assigned_role: string
  handoff_reason: string
  started_at: string
  completed_at: string | null
}

export type DeveloperControlPlaneMissionEvidence = {
  id: string
  mission_id: string | null
  subtask_id: string | null
  kind: string
  evidence_class: string
  summary: string
  source_path: string
  recorded_at: string
}

export type DeveloperControlPlaneMissionVerificationRun = {
  id: string
  subject_id: string
  verification_type: string
  result: string
  evidence_ref: string | null
  executed_at: string
}

export type DeveloperControlPlaneMissionDecisionNote = {
  id: string
  decision_class: string
  authority_source: string
  recorded_at: string
}

export type DeveloperControlPlaneMissionBlocker = {
  id: string
  mission_id: string | null
  subtask_id: string | null
  blocker_type: string
  impact: string
  escalation_needed: boolean
  recorded_at: string
}

export type DeveloperControlPlaneMissionDetailResponse =
  DeveloperControlPlaneMissionSummary & {
    subtasks: DeveloperControlPlaneMissionSubtask[]
    assignments: DeveloperControlPlaneMissionAssignment[]
    evidence_items: DeveloperControlPlaneMissionEvidence[]
    verification_runs: DeveloperControlPlaneMissionVerificationRun[]
    decision_notes: DeveloperControlPlaneMissionDecisionNote[]
    blockers: DeveloperControlPlaneMissionBlocker[]
  }

export type DeveloperControlPlaneIndigenousBrainDefinition = {
  status: string
  summary: string
  authority_boundary: string
  current_role: string
}

export type DeveloperControlPlaneIndigenousBrainBoardSignal = {
  available: boolean
  board_id: string | null
  title: string | null
  lane_count: number
  status_counts: Record<string, number>
  active_lane_count: number
  blocked_lane_count: number
  active_lane_ids: string[]
  blocked_lane_ids: string[]
  lanes_missing_review: string[]
  lanes_pending_closure: string[]
  primary_orchestrator: string | null
  updated_at: string | null
  detail: string | null
}

export type DeveloperControlPlaneIndigenousBrainQueueSignal = {
  exists: boolean
  queue_path: string
  queue_sha256: string | null
  job_count: number
  updated_at: string | null
  age_hours: number | null
  is_stale: boolean
  stale_threshold_hours: number
  top_job_ids: string[]
  detail: string | null
}

export type DeveloperControlPlaneIndigenousBrainMissionSummary = {
  mission_id: string
  objective: string
  status: string
  queue_job_id: string | null
  source_lane_id: string | null
  updated_at: string
}

export type DeveloperControlPlaneIndigenousBrainMissionSignal = {
  available: boolean
  total_count: number
  active_count: number
  blocked_count: number
  escalation_count: number
  recent: DeveloperControlPlaneIndigenousBrainMissionSummary[]
  detail: string | null
}

export type DeveloperControlPlaneIndigenousBrainLearningSummary = {
  learning_entry_id: number
  entry_type: string
  source_classification: string
  title: string
  summary: string
  source_lane_id: string | null
  queue_job_id: string | null
  recorded_at: string
}

export type DeveloperControlPlaneIndigenousBrainLearningSignal = {
  available: boolean
  total_count: number
  recent: DeveloperControlPlaneIndigenousBrainLearningSummary[]
  detail: string | null
}

export type DeveloperControlPlaneIndigenousBrainProjectBrainSignal = {
  available: boolean
  base_url: string
  query: string
  source_match_count: number
  projection_match_count: number
  node_match_count: number
  provenance_trail_count: number
  notable_source_paths: string[]
  notable_node_titles: string[]
  detail: string | null
}

export type DeveloperControlPlaneIndigenousBrainMem0Signal = {
  enabled: boolean
  configured: boolean
  ready: boolean
  host: string
  project_scoped: boolean
  org_project_pair_valid: boolean
  detail: string | null
}

export type DeveloperControlPlaneIndigenousBrainRecommendedFocus = {
  source: string
  lane_id: string
  title: string
  status: string
  objective: string
  reason: string
  dependencies: string[]
}

export type DeveloperControlPlaneIndigenousBrainBlocker = {
  key: string
  severity: string
  surface: string
  summary: string
  recommended_action: string
}

export type DeveloperControlPlaneIndigenousBrainBriefResponse = {
  generated_at: string
  indigenous_brain: DeveloperControlPlaneIndigenousBrainDefinition
  worldview_summary: string
  board: DeveloperControlPlaneIndigenousBrainBoardSignal
  queue: DeveloperControlPlaneIndigenousBrainQueueSignal
  missions: DeveloperControlPlaneIndigenousBrainMissionSignal
  learnings: DeveloperControlPlaneIndigenousBrainLearningSignal
  project_brain: DeveloperControlPlaneIndigenousBrainProjectBrainSignal
  mem0: DeveloperControlPlaneIndigenousBrainMem0Signal
  recommended_focus: DeveloperControlPlaneIndigenousBrainRecommendedFocus | null
  blockers: DeveloperControlPlaneIndigenousBrainBlocker[]
  missing_capabilities: string[]
}

export type DeveloperControlPlaneOvernightQueueWriteRequest = {
  source_board_concurrency_token: string
  expected_queue_sha256: string
  operator_intent: 'write-reviewed-queue-entry'
  queue_entry: Record<string, unknown>
}

export type DeveloperControlPlaneApprovalReceipt = {
  receipt_id: number
  organization_id: number
  action_type: string
  outcome: string
  authority_actor_user_id: number
  authority_actor_email?: string | null
  authority_source: string
  board_id: string
  source_board_concurrency_token?: string | null
  resulting_board_concurrency_token?: string | null
  source_lane_id?: string | null
  queue_job_id?: string | null
  expected_queue_sha256?: string | null
  resulting_queue_sha256?: string | null
  target_revision_id?: number | null
  previous_active_concurrency_token?: string | null
  linked_mission_id?: string | null
  rationale: string
  evidence_refs: string[]
  summary_metadata: Record<string, unknown> | null
  recorded_at: string
}

export type DeveloperControlPlaneOvernightQueueWriteResponse = {
  queue_sha256: string
  queue_updated_at: string
  written_job_id: string
  replaced: boolean
  approval_receipt: DeveloperControlPlaneApprovalReceipt | null
}

export type DeveloperControlPlaneCompletionWriteRequest = {
  source_board_concurrency_token: string
  expected_queue_sha256: string
  operator_intent: 'write-reviewed-lane-completion'
  completion: {
    source_lane_id: string
    queue_job_id: string
    closure_summary: string
    evidence: string[]
    closeout_receipt?: {
      queue_job_id: string
      artifact_paths: string[]
      mission_id: string | null
      producer_key: string | null
      source_lane_id: string | null
      source_board_concurrency_token: string | null
      runtime_profile_id: string | null
      runtime_policy_sha256: string | null
      closeout_status: string | null
      state_refresh_required: boolean | null
      receipt_recorded_at: string | null
      verification_evidence_ref: string | null
      queue_sha256_at_closeout: string | null
    }
  }
}

export type DeveloperControlPlaneCompletionWritePreparationRequest = {
  source_lane_id: string
}

export type DeveloperControlPlaneCompletionWritePreparationResponse = {
  source_lane_id: string
  queue_job_id: string
  draft_source: 'queue-snapshot' | 'stable-closeout-receipt'
  queue_status: DeveloperControlPlaneOvernightQueueStatusResponse
  closeout_receipt: DeveloperControlPlaneCloseoutReceiptResponse
  prepared_request: DeveloperControlPlaneCompletionWriteRequest
}

export type DeveloperControlPlaneCompletionWriteResponse = {
  no_op: boolean
  lane_id: string
  lane_status: string
  queue_job_id: string
  queue_sha256: string
  record: DeveloperControlPlaneActiveBoardRecord
  approval_receipt: DeveloperControlPlaneApprovalReceipt | null
}

export type DeveloperControlPlaneOvernightQueueConflictReason =
  | 'missing-active-board'
  | 'stale-board-token'
  | 'queue-sha-mismatch'
  | 'lane-review-missing'
  | 'duplicate-job-id'

export type DeveloperControlPlaneConflictRefreshTarget =
  | 'active-board'
  | 'overnight-queue'
  | 'closeout-receipt'

export type DeveloperControlPlaneOvernightQueueConflictDetail = {
  detail: string
  conflict_reason?: DeveloperControlPlaneOvernightQueueConflictReason
  remediation_message?: string
  refresh_targets?: DeveloperControlPlaneConflictRefreshTarget[]
  retry_permitted_after_refresh?: boolean
  current_board_concurrency_token?: string
  current_queue_sha256?: string
  job_id?: string
}

export type DeveloperControlPlaneCompletionConflictReason =
  | 'missing-active-board'
  | 'stale-board-token'
  | 'queue-sha-mismatch'
  | 'queue-job-missing'
  | 'queue-job-not-completed'
  | 'lane-verification-missing'
  | 'closeout-receipt-required'
  | 'closeout-receipt-mismatch'
  | 'lane-job-mismatch'
  | 'lane-status-conflict'
  | 'completion-overwrite-conflict'

export type DeveloperControlPlaneCompletionConflictDetail = {
  detail: string
  conflict_reason?: DeveloperControlPlaneCompletionConflictReason
  remediation_message?: string
  refresh_targets?: DeveloperControlPlaneConflictRefreshTarget[]
  retry_permitted_after_refresh?: boolean
  current_board_concurrency_token?: string
  current_queue_sha256?: string
  expected_queue_job_id?: string
  current_queue_job_status?: string
  current_lane_status?: string
}

type DeveloperControlPlaneActiveBoardSaveRequest = {
  canonical_board_json: string
  save_source: string
  concurrency_token: string | null
}

export type DeveloperControlPlanePersistenceErrorKind = 'generic' | 'schema-not-ready'

export type DeveloperControlPlanePersistenceErrorSummary = {
  kind: DeveloperControlPlanePersistenceErrorKind
  message: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((entry) => typeof entry === 'string')
}

function isActiveBoardRecord(value: unknown): value is DeveloperControlPlaneActiveBoardRecord {
  return (
    isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.organization_id === 'number' &&
    typeof value.board_id === 'string' &&
    typeof value.schema_version === 'string' &&
    typeof value.visibility === 'string' &&
    typeof value.canonical_board_json === 'string' &&
    typeof value.concurrency_token === 'string' &&
    typeof value.updated_by_user_id === 'number' &&
    typeof value.updated_at === 'string' &&
    typeof value.save_source === 'string' &&
    typeof value.created_at === 'string'
  )
}

function isOvernightQueueConflictDetail(
  value: unknown
): value is DeveloperControlPlaneOvernightQueueConflictDetail {
  return (
    isRecord(value) &&
    typeof value.detail === 'string' &&
    (value.conflict_reason === undefined || typeof value.conflict_reason === 'string') &&
    (value.remediation_message === undefined || typeof value.remediation_message === 'string') &&
    (value.refresh_targets === undefined || isStringArray(value.refresh_targets)) &&
    (value.retry_permitted_after_refresh === undefined ||
      typeof value.retry_permitted_after_refresh === 'boolean') &&
    (value.current_board_concurrency_token === undefined ||
      typeof value.current_board_concurrency_token === 'string') &&
    (value.current_queue_sha256 === undefined || typeof value.current_queue_sha256 === 'string') &&
    (value.job_id === undefined || typeof value.job_id === 'string')
  )
}

function isCompletionConflictDetail(
  value: unknown
): value is DeveloperControlPlaneCompletionConflictDetail {
  return (
    isRecord(value) &&
    typeof value.detail === 'string' &&
    (value.conflict_reason === undefined || typeof value.conflict_reason === 'string') &&
    (value.remediation_message === undefined || typeof value.remediation_message === 'string') &&
    (value.refresh_targets === undefined || isStringArray(value.refresh_targets)) &&
    (value.retry_permitted_after_refresh === undefined ||
      typeof value.retry_permitted_after_refresh === 'boolean') &&
    (value.current_board_concurrency_token === undefined ||
      typeof value.current_board_concurrency_token === 'string') &&
    (value.current_queue_sha256 === undefined || typeof value.current_queue_sha256 === 'string') &&
    (value.expected_queue_job_id === undefined || typeof value.expected_queue_job_id === 'string') &&
    (value.current_queue_job_status === undefined || typeof value.current_queue_job_status === 'string') &&
    (value.current_lane_status === undefined || typeof value.current_lane_status === 'string')
  )
}

export async function fetchDeveloperControlPlaneActiveBoard() {
  return apiClient.get<DeveloperControlPlaneActiveBoardFetchResponse>(
    '/api/v2/developer-control-plane/active-board'
  )
}

export async function fetchDeveloperControlPlaneActiveBoardVersions() {
  return apiClient.get<DeveloperControlPlaneBoardVersionsListResponse>(
    '/api/v2/developer-control-plane/active-board/versions'
  )
}

export async function restoreDeveloperControlPlaneActiveBoardVersion(
  revisionId: number,
  concurrencyToken: string | null
) {
  return apiClient.post<DeveloperControlPlaneBoardRestoreResponse>(
    `/api/v2/developer-control-plane/active-board/versions/${revisionId}/restore`,
    {
      concurrency_token: concurrencyToken,
    }
  )
}

export async function saveDeveloperControlPlaneActiveBoard(
  payload: DeveloperControlPlaneActiveBoardSaveRequest
) {
  return apiClient.put<DeveloperControlPlaneActiveBoardRecord>(
    '/api/v2/developer-control-plane/active-board',
    payload
  )
}

export async function fetchDeveloperControlPlaneOvernightQueueStatus() {
  return apiClient.get<DeveloperControlPlaneOvernightQueueStatusResponse>(
    '/api/v2/developer-control-plane/overnight-queue/status'
  )
}

export async function fetchDeveloperControlPlaneCloseoutReceipt(queueJobId: string) {
  return apiClient.get<DeveloperControlPlaneCloseoutReceiptResponse>(
    `/api/v2/developer-control-plane/overnight-queue/jobs/${encodeURIComponent(queueJobId)}/closeout-receipt`
  )
}

export async function fetchDeveloperControlPlaneWatchdogStatus() {
  return apiClient.get<DeveloperControlPlaneWatchdogStatusResponse>(
    '/api/v2/developer-control-plane/runtime/watchdog-status'
  )
}

export async function fetchDeveloperControlPlaneAutonomyCycle() {
  return apiClient.get<DeveloperControlPlaneAutonomyCycleResponse>(
    '/api/v2/developer-control-plane/runtime/autonomy-cycle'
  )
}

export async function fetchDeveloperControlPlaneSilentMonitors() {
  return apiClient.get<DeveloperControlPlaneSilentMonitorsResponse>(
    '/api/v2/developer-control-plane/runtime/silent-monitors'
  )
}

export async function fetchDeveloperControlPlaneMissionState(
  query: DeveloperControlPlaneMissionStateQuery = {}
) {
  const searchParams = new URLSearchParams()
  searchParams.set('limit', String(query.limit ?? 8))
  if (query.queueJobId) {
    searchParams.set('queue_job_id', query.queueJobId)
  }
  if (query.sourceLaneId) {
    searchParams.set('source_lane_id', query.sourceLaneId)
  }

  return apiClient.get<DeveloperControlPlaneMissionStateResponse>(
    `/api/v2/developer-control-plane/runtime/mission-state?${searchParams.toString()}`
  )
}

export async function fetchDeveloperControlPlaneMissionDetail(missionId: string) {
  return apiClient.get<DeveloperControlPlaneMissionDetailResponse>(
    `/api/v2/developer-control-plane/runtime/mission-state/${encodeURIComponent(missionId)}`
  )
}

export async function fetchDeveloperControlPlaneIndigenousBrainBrief(
  projectBrainQuery?: string | null
) {
  const searchParams = new URLSearchParams()
  if (projectBrainQuery) {
    searchParams.set('project_brain_query', projectBrainQuery)
  }

  const suffix = searchParams.size > 0 ? `?${searchParams.toString()}` : ''

  return apiClient.get<DeveloperControlPlaneIndigenousBrainBriefResponse>(
    `/api/v2/developer-control-plane/indigenous-brain/brief${suffix}`
  )
}

export async function fetchDeveloperControlPlaneLearnings(
  query: DeveloperControlPlaneLearningLedgerQuery = {}
) {
  const searchParams = new URLSearchParams()
  searchParams.set('limit', String(query.limit ?? 12))
  if (query.entryType) {
    searchParams.set('entry_type', query.entryType)
  }
  if (query.sourceClassification) {
    searchParams.set('source_classification', query.sourceClassification)
  }
  if (query.sourceLaneId) {
    searchParams.set('source_lane_id', query.sourceLaneId)
  }
  if (query.queueJobId) {
    searchParams.set('queue_job_id', query.queueJobId)
  }
  if (query.linkedMissionId) {
    searchParams.set('linked_mission_id', query.linkedMissionId)
  }

  return apiClient.get<DeveloperControlPlaneLearningLedgerResponse>(
    `/api/v2/developer-control-plane/learnings?${searchParams.toString()}`
  )
}

export async function bootstrapDeveloperControlPlaneMissionStateFromCloseoutReceipt(
  queueJobId: string
) {
  return apiClient.post<DeveloperControlPlaneMissionBootstrapResponse>(
    '/api/v2/developer-control-plane/runtime/mission-state/bootstrap-closeout-receipt',
    { queue_job_id: queueJobId }
  )
}

export async function writeDeveloperControlPlaneOvernightQueueEntry(
  payload: DeveloperControlPlaneOvernightQueueWriteRequest
) {
  return apiClient.post<DeveloperControlPlaneOvernightQueueWriteResponse>(
    '/api/v2/developer-control-plane/overnight-queue/write-entry',
    payload
  )
}

export async function writeDeveloperControlPlaneLaneCompletion(
  payload: DeveloperControlPlaneCompletionWriteRequest
) {
  return apiClient.post<DeveloperControlPlaneCompletionWriteResponse>(
    '/api/v2/developer-control-plane/active-board/write-completion',
    payload
  )
}

export async function prepareDeveloperControlPlaneLaneCompletionWrite(
  payload: DeveloperControlPlaneCompletionWritePreparationRequest
) {
  return apiClient.post<DeveloperControlPlaneCompletionWritePreparationResponse>(
    '/api/v2/developer-control-plane/active-board/prepare-completion-write',
    payload
  )
}

export async function fetchDeveloperControlPlaneRuntimeCompletionAssist() {
  return apiClient.get<DeveloperControlPlaneRuntimeCompletionAssistResponse>(
    '/api/v2/developer-control-plane/runtime/completion-assist'
  )
}

export function getDeveloperControlPlaneConflictRecord(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null
  }

  const detail = (error.responseData as { detail?: unknown } | undefined)?.detail
  if (!isRecord(detail)) {
    return null
  }

  const currentRecord = detail.current_record
  return isActiveBoardRecord(currentRecord) ? currentRecord : null
}

export function getDeveloperControlPlaneOvernightQueueConflictDetail(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null
  }

  const detail = (error.responseData as { detail?: unknown } | undefined)?.detail
  return isOvernightQueueConflictDetail(detail) ? detail : null
}

export function getDeveloperControlPlaneCompletionConflictDetail(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null
  }

  const detail = (error.responseData as { detail?: unknown } | undefined)?.detail
  return isCompletionConflictDetail(detail) ? detail : null
}

export function getDeveloperControlPlanePersistenceErrorMessage(error: unknown) {
  return getDeveloperControlPlanePersistenceErrorSummary(error).message
}

export function getDeveloperControlPlanePersistenceErrorSummary(
  error: unknown
): DeveloperControlPlanePersistenceErrorSummary {
  if (!(error instanceof Error)) {
    return {
      kind: 'generic',
      message: 'Developer control-plane persistence failed',
    }
  }

  if (error instanceof ApiError) {
    const detail = (error.responseData as { detail?: unknown } | undefined)?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : isRecord(detail) && typeof detail.detail === 'string'
          ? detail.detail
          : error.getUserMessage()

    if (
      error.statusCode === 503 &&
      message.startsWith('Developer control-plane persistence schema is not ready;')
    ) {
      return {
        kind: 'schema-not-ready',
        message,
      }
    }

    return {
      kind: 'generic',
      message,
    }
  }

  return {
    kind: 'generic',
    message: error.message || 'Developer control-plane persistence failed',
  }
}

export function isDeveloperControlPlaneConflictError(error: unknown) {
  return error instanceof ApiError && error.statusCode === 409
}

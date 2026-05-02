import type { ChangeEvent } from 'react'

import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, ApiErrorType } from '@/lib/api-errors'
import {
  canonicalizeDeveloperMasterBoardJson,
  createDefaultDeveloperMasterBoardJson,
  parseDeveloperMasterBoard,
  serializeDeveloperMasterBoard,
} from '../contracts/board'
import { createDeveloperLaneQueueJobId } from '../contracts/dispatch'
import type {
  DeveloperControlPlaneActiveBoardRecord,
  DeveloperControlPlaneBoardVersion,
  DeveloperControlPlaneBoardVersionsListResponse,
  DeveloperControlPlaneCompletionWritePreparationResponse,
} from '../api/activeBoard'
import { useDevMasterBoardStore } from '../state'
import { useControlPlaneController } from './useControlPlaneController'

const activeBoardApiMocks = vi.hoisted(() => ({
  bootstrapDeveloperControlPlaneMissionStateFromCloseoutReceipt: vi.fn(),
  fetchDeveloperControlPlaneAutonomyCycle: vi.fn(),
  fetchDeveloperControlPlaneRuntimeCompletionAssist: vi.fn(),
  fetchDeveloperControlPlaneIndigenousBrainBrief: vi.fn(),
  fetchDeveloperControlPlaneActiveBoard: vi.fn(),
  fetchDeveloperControlPlaneActiveBoardVersions: vi.fn(),
  fetchDeveloperControlPlaneCloseoutReceipt: vi.fn(),
  fetchDeveloperControlPlaneLearnings: vi.fn(),
  fetchDeveloperControlPlaneMissionDetail: vi.fn(),
  fetchDeveloperControlPlaneMissionState: vi.fn(),
  fetchDeveloperControlPlaneOvernightQueueStatus: vi.fn(),
  prepareDeveloperControlPlaneLaneCompletionWrite: vi.fn(),
  fetchDeveloperControlPlaneSilentMonitors: vi.fn(),
  fetchDeveloperControlPlaneWatchdogStatus: vi.fn(),
  restoreDeveloperControlPlaneActiveBoardVersion: vi.fn(),
  saveDeveloperControlPlaneActiveBoard: vi.fn(),
  writeDeveloperControlPlaneLaneCompletion: vi.fn(),
  writeDeveloperControlPlaneOvernightQueueEntry: vi.fn(),
  getDeveloperControlPlaneConflictRecord: vi.fn(),
  getDeveloperControlPlaneCompletionConflictDetail: vi.fn(),
  getDeveloperControlPlaneOvernightQueueConflictDetail: vi.fn(),
  getDeveloperControlPlanePersistenceErrorSummary: vi.fn(),
  isDeveloperControlPlaneConflictError: vi.fn(),
  getDeveloperControlPlanePersistenceErrorMessage: vi.fn(),
}))

vi.mock('../api/activeBoard', () => ({
  bootstrapDeveloperControlPlaneMissionStateFromCloseoutReceipt:
    activeBoardApiMocks.bootstrapDeveloperControlPlaneMissionStateFromCloseoutReceipt,
  fetchDeveloperControlPlaneAutonomyCycle:
    activeBoardApiMocks.fetchDeveloperControlPlaneAutonomyCycle,
  fetchDeveloperControlPlaneRuntimeCompletionAssist:
    activeBoardApiMocks.fetchDeveloperControlPlaneRuntimeCompletionAssist,
  fetchDeveloperControlPlaneIndigenousBrainBrief:
    activeBoardApiMocks.fetchDeveloperControlPlaneIndigenousBrainBrief,
  fetchDeveloperControlPlaneActiveBoard: activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard,
  fetchDeveloperControlPlaneActiveBoardVersions:
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoardVersions,
  fetchDeveloperControlPlaneCloseoutReceipt:
    activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt,
  fetchDeveloperControlPlaneLearnings:
    activeBoardApiMocks.fetchDeveloperControlPlaneLearnings,
  fetchDeveloperControlPlaneMissionDetail:
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionDetail,
  fetchDeveloperControlPlaneMissionState:
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionState,
  fetchDeveloperControlPlaneOvernightQueueStatus:
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus,
  prepareDeveloperControlPlaneLaneCompletionWrite:
    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite,
  fetchDeveloperControlPlaneSilentMonitors:
    activeBoardApiMocks.fetchDeveloperControlPlaneSilentMonitors,
  fetchDeveloperControlPlaneWatchdogStatus:
    activeBoardApiMocks.fetchDeveloperControlPlaneWatchdogStatus,
  restoreDeveloperControlPlaneActiveBoardVersion:
    activeBoardApiMocks.restoreDeveloperControlPlaneActiveBoardVersion,
  saveDeveloperControlPlaneActiveBoard: activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard,
  writeDeveloperControlPlaneLaneCompletion:
    activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion,
  writeDeveloperControlPlaneOvernightQueueEntry:
    activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry,
  getDeveloperControlPlaneConflictRecord: activeBoardApiMocks.getDeveloperControlPlaneConflictRecord,
  getDeveloperControlPlaneCompletionConflictDetail:
    activeBoardApiMocks.getDeveloperControlPlaneCompletionConflictDetail,
  getDeveloperControlPlaneOvernightQueueConflictDetail:
    activeBoardApiMocks.getDeveloperControlPlaneOvernightQueueConflictDetail,
  getDeveloperControlPlanePersistenceErrorSummary:
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorSummary,
  isDeveloperControlPlaneConflictError: activeBoardApiMocks.isDeveloperControlPlaneConflictError,
  getDeveloperControlPlanePersistenceErrorMessage:
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage,
}))

function createActiveBoardRecord(
  canonicalBoardJson: string,
  overrides: Partial<DeveloperControlPlaneActiveBoardRecord> = {}
): DeveloperControlPlaneActiveBoardRecord {
  return {
    id: 1,
    organization_id: 1,
    board_id: 'bijmantra-app-development-master-board',
    schema_version: '1.0.0',
    visibility: 'internal-superuser',
    canonical_board_json: canonicalBoardJson,
    concurrency_token: 'token-1',
    updated_by_user_id: 1,
    updated_at: '2026-03-18T10:00:00.000Z',
    save_source: 'hidden-route-ui',
    summary_metadata: null,
    created_at: '2026-03-18T09:00:00.000Z',
    ...overrides,
  }
}

function createBoardVersion(
  revisionId: number,
  overrides: Partial<DeveloperControlPlaneBoardVersion> = {}
): DeveloperControlPlaneBoardVersion {
  return {
    revision_id: revisionId,
    schema_version: '1.0.0',
    visibility: 'internal-superuser',
    concurrency_token: `token-${revisionId}`,
    created_at: '2026-03-18T11:00:00.000Z',
    saved_by_user_id: 1,
    save_source: 'hidden-route-ui',
    summary_metadata: null,
    is_current: false,
    ...overrides,
  }
}

function createPreparedCompletionWriteResponse(
  overrides: Record<string, unknown> = {},
  completionOverrides: Record<string, unknown> = {},
  closeoutReceiptOverrides: Record<string, unknown> = {},
  queueStatusOverrides: Record<string, unknown> = {}
): DeveloperControlPlaneCompletionWritePreparationResponse {
  const queueStatus = {
    queue_path: '.agent/jobs/overnight-queue.json',
    queue_sha256: 'queue-sha-1',
    exists: true,
    job_count: 2,
    updated_at: '2026-03-18T11:30:00.000Z',
    ...queueStatusOverrides,
  }

  const closeoutReceipt = {
    exists: false,
    queue_job_id: 'overnight-lane-control-plane-sharedto',
    mission_id: null,
    producer_key: null,
    source_lane_id: null,
    source_board_concurrency_token: null,
    runtime_profile_id: null,
    runtime_policy_sha256: null,
    closeout_status: null,
    state_refresh_required: null,
    receipt_recorded_at: null,
    started_at: null,
    finished_at: null,
    verification_evidence_ref: null,
    queue_sha256_at_closeout: null,
    closeout_commands: [],
    artifacts: [],
    ...closeoutReceiptOverrides,
  }

  return {
    source_lane_id: 'control-plane',
    queue_job_id: 'overnight-lane-control-plane-sharedto',
    draft_source: 'queue-snapshot',
    queue_status: queueStatus,
    closeout_receipt: closeoutReceipt,
    prepared_request: {
      source_board_concurrency_token: 'shared-token-1',
      expected_queue_sha256: queueStatus.queue_sha256,
      operator_intent: 'write-reviewed-lane-completion',
      completion: {
        source_lane_id: 'control-plane',
        queue_job_id: 'overnight-lane-control-plane-sharedto',
        closure_summary:
          'Reviewed closeout for lane control-plane after queue completion and canonical queue refresh.',
        evidence: [
          'Reviewed queue job overnight-lane-control-plane-sharedto before explicit board write-back.',
          `Queue snapshot hash at reviewed closeout: ${queueStatus.queue_sha256}.`,
          'Board token used for reviewed closeout: shared-token-1.',
          `Queue status reviewed at ${queueStatus.updated_at}.`,
        ],
        closeout_receipt: closeoutReceipt.exists
          ? {
              queue_job_id: closeoutReceipt.queue_job_id,
              artifact_paths: closeoutReceipt.artifacts
                .filter((artifact: { exists: boolean }) => artifact.exists)
                .map((artifact: { path: string }) => artifact.path),
              mission_id: closeoutReceipt.mission_id,
              producer_key: closeoutReceipt.producer_key,
              source_lane_id: closeoutReceipt.source_lane_id,
              source_board_concurrency_token: closeoutReceipt.source_board_concurrency_token,
              runtime_profile_id: closeoutReceipt.runtime_profile_id,
              runtime_policy_sha256: closeoutReceipt.runtime_policy_sha256,
              closeout_status: closeoutReceipt.closeout_status,
              state_refresh_required: closeoutReceipt.state_refresh_required,
              receipt_recorded_at: closeoutReceipt.receipt_recorded_at,
              verification_evidence_ref: closeoutReceipt.verification_evidence_ref,
              queue_sha256_at_closeout: closeoutReceipt.queue_sha256_at_closeout,
            }
          : undefined,
        ...completionOverrides,
      },
    },
    ...overrides,
  }
}

function createBoardVersionsRecord(
  versions: DeveloperControlPlaneBoardVersion[],
  overrides: Partial<DeveloperControlPlaneBoardVersionsListResponse> = {}
): DeveloperControlPlaneBoardVersionsListResponse {
  return {
    board_id: 'bijmantra-app-development-master-board',
    current_concurrency_token: versions.find((version) => version.is_current)?.concurrency_token ?? null,
    total_count: versions.length,
    versions,
    ...overrides,
  }
}

describe('useControlPlaneController', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    useDevMasterBoardStore.setState({
      rawBoardJson: createDefaultDeveloperMasterBoardJson(),
      lastUpdatedAt: '2026-03-18T00:00:00.000Z',
      hasHydrated: true,
      storageAvailable: true,
      backendHydrationState: 'idle',
      saveState: 'idle',
      backendConcurrencyToken: null,
      backendLastSyncedAt: null,
      lastPersistedBoardJson: null,
      hasUnsavedChanges: false,
      persistenceError: null,
      persistenceErrorKind: 'generic',
      conflictRecord: null,
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({ exists: false, record: null })
    activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard.mockImplementation(
      async ({ canonical_board_json, concurrency_token }) =>
        createActiveBoardRecord(canonical_board_json, {
          concurrency_token: concurrency_token ?? 'token-1',
          updated_at: '2026-03-18T11:00:00.000Z',
        })
    )
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockResolvedValue({
      queue_path: '.agent/jobs/overnight-queue.json',
      queue_sha256: 'queue-sha-1',
      exists: true,
      job_count: 2,
      updated_at: '2026-03-18T11:30:00.000Z',
    })
    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockResolvedValue(
      createPreparedCompletionWriteResponse()
    )
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoardVersions.mockResolvedValue(
      createBoardVersionsRecord([
        createBoardVersion(1, {
          concurrency_token: 'token-1',
          is_current: true,
        }),
      ])
    )
    activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt.mockResolvedValue({
      exists: false,
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      closeout_status: null,
      state_refresh_required: null,
      receipt_recorded_at: null,
      started_at: null,
      finished_at: null,
      verification_evidence_ref: null,
      queue_sha256_at_closeout: null,
      closeout_commands: [],
      artifacts: [],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneLearnings.mockResolvedValue({
      total_count: 0,
      entries: [],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneWatchdogStatus.mockResolvedValue({
      exists: true,
      state_path: 'runtime-artifacts/watchdog-state.json',
      auth_store_exists: true,
      auth_store_path: 'runtime-artifacts/agents/main/agent/auth-profiles.json',
      bootstrap_ready: true,
      bootstrap_status: 'ready',
      mission_evidence_dir_exists: false,
      mission_evidence_dir_path: 'runtime-artifacts/mission-evidence',
      last_check: '2026-03-20T08:29:26.506880+00:00',
      gateway_healthy: true,
      total_checks: 1,
      total_alerts: 0,
      job_count: 1,
      jobs: [
        {
          job_id: 'overnight-lane-control-plane-sharedto',
          label: 'bijmantra:overnight-lane-control-plane-sharedto',
          status: 'completed',
          started_at: '2026-03-20T08:00:00+00:00',
          duration_minutes: 5,
          last_error: '',
          consecutive_errors: 0,
          branch: 'auto/overnight-lane-control-plane-sharedto',
          verification_passed: true,
        },
      ],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneAutonomyCycle.mockResolvedValue({
      exists: true,
      artifact_path:
        '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
      generated_at: '2026-04-05T11:10:24.399975+00:00',
      queue_path: '.agent/jobs/overnight-queue.json',
      window: 'nightly',
      max_jobs_per_run: 2,
      status_counts: { queued: 9 },
      selected_job_count: 1,
      blocked_job_count: 1,
      closeout_candidate_count: 0,
      next_action_count: 1,
      watchdog: {
        exists: true,
        state_path: 'runtime-artifacts/watchdog-state.json',
        last_check: '2026-04-05T10:00:00Z',
        gateway_healthy: true,
        state_is_stale: false,
        total_alerts: 0,
        job_errors: {},
      },
      selected_jobs: [
        {
          job_id: 'overnight-lane-control-plane-sharedto',
          title: 'Control Plane Queue Job',
          priority: 'p1',
          primary_agent: 'OmShriMaatreNamaha',
          trigger_reason: 'overnight-window:nightly',
          source_task: '.ai/tasks/example.md',
        },
      ],
      blocked_jobs: [
        {
          job_id: 'blocked-job',
          title: 'Blocked Job',
          reason: 'trigger-disabled',
        },
      ],
      closeout_candidates: [],
      next_actions: [
        {
          action: 'dispatch-queue-job',
          job_id: 'overnight-lane-control-plane-sharedto',
          title: 'Control Plane Queue Job',
          reason: 'overnight-window:nightly',
          primary_agent: 'OmShriMaatreNamaha',
          priority: 'p1',
          mission_id: null,
          receipt_path: null,
          state_path: null,
          detail: null,
        },
      ],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneRuntimeCompletionAssist.mockResolvedValue({
      exists: true,
      artifact_path:
        '.github/docs/architecture/tracking/developer-control-plane-completion-assist.json',
      generated_at: '2026-04-06T12:05:00+00:00',
      status: 'staged',
      staged: true,
      explicit_write_required: true,
      message:
        'Staged reviewed completion assist for lane control-plane. This artifact does not perform explicit board write-back.',
      source: {
        endpoint: 'http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle',
        autonomy_cycle_artifact_path:
          '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
        autonomy_cycle_generated_at: '2026-04-05T11:10:24.399975+00:00',
        next_action_ordering_source: 'artifact',
      },
      actionable_completion_write: {
        action: 'prepare-completion-write-back',
        actionIndex: 0,
        jobId: 'overnight-lane-control-plane-sharedto',
        sourceLaneId: 'control-plane',
        reason: 'stable closeout ready for explicit board write-back',
        missionId: 'runtime-mission-control-plane-sharedto',
        receiptPath: 'runtime-artifacts/mission-evidence/job/closeout.json',
        draftSource: 'stable-closeout-receipt',
        queueStatus: {
          queue_path: '.agent/jobs/overnight-queue.json',
          queue_sha256: 'queue-sha-1',
          exists: true,
          job_count: 1,
          updated_at: '2026-03-20T08:29:00+00:00',
        },
        closeoutReceipt: {
          exists: true,
          queue_job_id: 'overnight-lane-control-plane-sharedto',
          mission_id: 'runtime-mission-control-plane-sharedto',
          producer_key: 'openclaw-runtime',
          source_lane_id: 'control-plane',
          source_board_concurrency_token: 'shared-token-1',
          runtime_profile_id: 'bijmantra-bca-local-verify',
          runtime_policy_sha256: 'policy-sha-1234',
          closeout_status: 'passed',
          state_refresh_required: true,
          receipt_recorded_at: '2026-03-20T08:05:00+00:00',
          started_at: '2026-03-20T08:00:00+00:00',
          finished_at: '2026-03-20T08:04:00+00:00',
          verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
          queue_sha256_at_closeout: 'queue-sha-closeout-77',
          closeout_commands: [],
          artifacts: [],
        },
        preparedRequest: {
          source_board_concurrency_token: 'shared-token-1',
          expected_queue_sha256: 'queue-sha-1',
          operator_intent: 'write-reviewed-lane-completion',
          completion: {
            source_lane_id: 'control-plane',
            queue_job_id: 'overnight-lane-control-plane-sharedto',
            closure_summary:
              'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.',
            evidence: [
              'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.',
            ],
            closeout_receipt: {
              queue_job_id: 'overnight-lane-control-plane-sharedto',
              artifact_paths: [],
              mission_id: 'runtime-mission-control-plane-sharedto',
              producer_key: 'openclaw-runtime',
              source_lane_id: 'control-plane',
              source_board_concurrency_token: 'shared-token-1',
              runtime_profile_id: 'bijmantra-bca-local-verify',
              runtime_policy_sha256: 'policy-sha-1234',
              closeout_status: 'passed',
              state_refresh_required: true,
              receipt_recorded_at: '2026-03-20T08:05:00+00:00',
              verification_evidence_ref:
                'runtime-artifacts/mission-evidence/job/verification_1.json',
              queue_sha256_at_closeout: 'queue-sha-closeout-77',
            },
          },
        },
      },
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneSilentMonitors.mockResolvedValue({
      generated_at: '2026-03-31T12:20:00.000Z',
      overall_state: 'alert',
      should_emit: true,
      monitors: [
        {
          monitor_key: 'queue-staleness',
          label: 'Queue staleness',
          state: 'healthy',
          should_emit: false,
          summary: 'The overnight queue snapshot looks fresh for the current nightly cadence.',
          detail: 'Queue hash queue-sha-1; 2 sampled jobs; age 0.3h.',
          observed_at: '2026-03-31T12:00:00.000Z',
          refresh_cadence: 'Nightly and immediately after each reviewed queue export',
          output_artifact: 'developer-control-plane.runtime.silent-monitors.queue-staleness',
          mutates_authority_surfaces: false,
          evidence_sources: [
            {
              label: 'Overnight queue status',
              path: '.agent/jobs/overnight-queue.json',
              observed_at: '2026-03-31T12:00:00.000Z',
            },
          ],
          findings: [],
        },
        {
          monitor_key: 'control-surface-drift',
          label: 'Control-surface drift',
          state: 'healthy',
          should_emit: false,
          summary: 'The canonical control-surface checker reports no structural drift.',
          detail: 'Control surfaces are structurally valid and aligned with the current repo layout.',
          observed_at: '2026-03-31T12:20:00.000Z',
          refresh_cadence: 'Before operator handoff and after control-plane contract changes',
          output_artifact:
            'developer-control-plane.runtime.silent-monitors.control-surface-drift',
          mutates_authority_surfaces: false,
          evidence_sources: [
            {
              label: 'Canonical control-surface checker',
              path: 'scripts/check_control_surfaces.py',
              observed_at: '2026-03-31T12:20:00.000Z',
            },
          ],
          findings: [],
        },
        {
          monitor_key: 'reevu-readiness',
          label: 'REEVU readiness',
          state: 'alert',
          should_emit: true,
          summary: 'REEVU readiness is degraded for the current local evidence set.',
          detail:
            '3/14 real-question cases passed; runtime status blocked; benchmark-ready local orgs 0; gap status no_benchmark_ready_local_org; blockers: observations.empty, bio_gwas_runs.empty, bio_qtls.missing_or_inaccessible.',
          observed_at: '2026-03-31T12:20:00.000Z',
          refresh_cadence:
            'After REEVU readiness census, benchmark, or authority-gap regeneration',
          output_artifact: 'developer-control-plane.runtime.silent-monitors.reevu-readiness',
          mutates_authority_surfaces: false,
          evidence_sources: [
            {
              label: 'REEVU authority gap report',
              path: 'backend/test_reports/reevu_authority_gap_report.json',
              observed_at: '2026-03-31T12:20:00.000Z',
            },
          ],
          findings: [
            'observations.empty',
            'bio_gwas_runs.empty',
            'bio_qtls.missing_or_inaccessible',
          ],
        },
      ],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionState.mockResolvedValue({
      count: 1,
      missions: [
        {
          mission_id: 'mission-1',
          objective: 'Control-plane reviewed dispatch runtime inspection',
          status: 'completed',
          owner: 'OmShriMaatreNamaha',
          priority: 'p1',
          producer_key: 'chaitanya',
          queue_job_id: null,
          source_lane_id: null,
          source_board_concurrency_token: null,
          created_at: '2026-03-20T08:00:00+00:00',
          updated_at: '2026-03-20T08:05:00+00:00',
          subtask_total: 1,
          subtask_completed: 1,
          assignment_total: 1,
          evidence_count: 1,
          blocker_count: 1,
          escalation_needed: true,
          verification: {
            passed: 1,
            warned: 0,
            failed: 0,
            last_verified_at: '2026-03-20T08:04:00+00:00',
          },
          final_summary: 'Runtime watchdog and durable mission-state inspection recorded.',
        },
      ],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionDetail.mockResolvedValue({
      mission_id: 'mission-1',
      objective: 'Control-plane reviewed dispatch runtime inspection',
      status: 'completed',
      owner: 'OmShriMaatreNamaha',
      priority: 'p1',
      producer_key: 'chaitanya',
      queue_job_id: null,
      source_lane_id: null,
      source_board_concurrency_token: null,
      created_at: '2026-03-20T08:00:00+00:00',
      updated_at: '2026-03-20T08:05:00+00:00',
      subtask_total: 1,
      subtask_completed: 1,
      assignment_total: 1,
      evidence_count: 1,
      blocker_count: 1,
      escalation_needed: true,
      verification: {
        passed: 1,
        warned: 0,
        failed: 0,
        last_verified_at: '2026-03-20T08:04:00+00:00',
      },
      final_summary: 'Runtime watchdog and durable mission-state inspection recorded.',
      subtasks: [
        {
          id: 'subtask-1',
          title: 'Inspect watchdog and mission evidence alignment',
          status: 'completed',
          owner_role: 'OmVishnaveNamah',
          depends_on: [],
          updated_at: '2026-03-20T08:03:00+00:00',
        },
      ],
      assignments: [
        {
          id: 'assignment-1',
          subtask_id: 'subtask-1',
          assigned_role: 'OmVishnaveNamah',
          handoff_reason: 'Validate runtime truth before pilot closeout',
          started_at: '2026-03-20T08:01:00+00:00',
          completed_at: '2026-03-20T08:02:00+00:00',
        },
      ],
      evidence_items: [
        {
          id: 'evidence-1',
          mission_id: 'mission-1',
          subtask_id: 'subtask-1',
          kind: 'runtime_watchdog',
          evidence_class: 'runtime-status',
          summary: 'Watchdog completed the reviewed queue job.',
          source_path: 'runtime-artifacts/watchdog-state.json',
          recorded_at: '2026-03-20T08:03:30+00:00',
        },
      ],
      verification_runs: [
        {
          id: 'verification-1',
          subject_id: 'subtask-1',
          verification_type: 'runtime_watchdog',
          result: 'passed',
          evidence_ref: 'evidence-1',
          executed_at: '2026-03-20T08:04:00+00:00',
        },
      ],
      decision_notes: [
        {
          id: 'decision-1',
          decision_class: 'reviewed_dispatch',
          authority_source: 'OmShriMaatreNamaha',
          recorded_at: '2026-03-20T08:04:30+00:00',
        },
      ],
      blockers: [
        {
          id: 'blocker-1',
          mission_id: 'mission-1',
          subtask_id: null,
          blocker_type: 'missing_closeout_receipt',
          impact: 'Stable runtime closeout receipt is not yet present.',
          escalation_needed: true,
          recorded_at: '2026-03-20T08:04:45+00:00',
        },
      ],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneIndigenousBrainBrief.mockResolvedValue({
      generated_at: '2026-04-05T10:30:00.000Z',
      indigenous_brain: {
        status: 'bootstrapped',
        summary: 'Backend-native world model for the developer control plane.',
        authority_boundary:
          'It synthesizes canonical board, queue, mission, learning, and optional project-brain signals without becoming a new authority source.',
        current_role: 'Turn scattered internal control-plane surfaces into one actionable brief.',
      },
      worldview_summary:
        'Indigenous Brain is now defined as the native control-plane world model rather than a second authority store.',
      board: {
        available: false,
        board_id: null,
        title: null,
        lane_count: 0,
        status_counts: {},
        active_lane_count: 0,
        blocked_lane_count: 0,
        active_lane_ids: [],
        blocked_lane_ids: [],
        lanes_missing_review: [],
        lanes_pending_closure: [],
        primary_orchestrator: null,
        updated_at: null,
        detail: 'No shared active board is persisted yet.',
      },
      queue: {
        exists: true,
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        job_count: 2,
        updated_at: '2026-03-18T11:30:00.000Z',
        age_hours: 0.2,
        is_stale: false,
        stale_threshold_hours: 18,
        top_job_ids: ['overnight-lane-control-plane-sharedto'],
        detail: null,
      },
      missions: {
        available: true,
        total_count: 1,
        active_count: 0,
        blocked_count: 0,
        escalation_count: 1,
        recent: [
          {
            mission_id: 'mission-1',
            objective: 'Control-plane reviewed dispatch runtime inspection',
            status: 'completed',
            queue_job_id: null,
            source_lane_id: null,
            updated_at: '2026-03-20T08:05:00+00:00',
          },
        ],
        detail: null,
      },
      learnings: {
        available: true,
        total_count: 0,
        recent: [],
        detail: null,
      },
      project_brain: {
        available: false,
        base_url: 'http://127.0.0.1:8083',
        query: 'developer control plane world model mission state learning queue project brain',
        source_match_count: 0,
        projection_match_count: 0,
        node_match_count: 0,
        provenance_trail_count: 0,
        notable_source_paths: [],
        notable_node_titles: [],
        detail: 'Project-brain sidecar is not currently reachable.',
      },
      mem0: {
        enabled: false,
        configured: false,
        ready: false,
        host: 'https://api.mem0.ai',
        project_scoped: false,
        org_project_pair_valid: true,
        detail:
          'Mem0 is disabled. It remains an optional external episodic-memory adapter, not part of the canonical self-building loop yet.',
      },
      recommended_focus: null,
      blockers: [],
      missing_capabilities: [],
    })
    activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry.mockResolvedValue({
      queue_sha256: 'queue-sha-2',
      queue_updated_at: '2026-03-18T11:31:00.000Z',
      written_job_id: 'overnight-lane-platform-runtime-token1',
      replaced: false,
      approval_receipt: {
        receipt_id: 41,
        recorded_at: '2026-03-18T11:31:05.000Z',
      },
    })
    const completedBoard = parseDeveloperMasterBoard(createDefaultDeveloperMasterBoardJson())
    const completedControlPlaneLane = completedBoard.lanes.find((lane) => lane.id === 'control-plane')

    if (!completedControlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    completedControlPlaneLane.status = 'completed'
    completedControlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      queue_sha256: 'queue-sha-1',
      source_board_concurrency_token: 'token-completed-1',
      closure_summary: 'Completion evidence was reviewed and accepted.',
      evidence: ['Focused tests passed', 'Queue job completed'],
      completed_at: '2026-03-18T11:32:00.000Z',
    }
    activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion.mockResolvedValue({
      no_op: false,
      lane_id: 'control-plane',
      lane_status: 'completed',
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      queue_sha256: 'queue-sha-1',
      approval_receipt: {
        receipt_id: 52,
        recorded_at: '2026-03-18T11:32:05.000Z',
      },
      record: createActiveBoardRecord(serializeDeveloperMasterBoard(completedBoard), {
        concurrency_token: 'token-completed-1',
        updated_at: '2026-03-18T11:32:00.000Z',
      }),
    })
    activeBoardApiMocks.restoreDeveloperControlPlaneActiveBoardVersion.mockResolvedValue({
      restored: true,
      restored_from_revision_id: 1,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'token-restored-1',
        updated_at: '2026-03-18T11:33:00.000Z',
      }),
      approval_receipt: {
        receipt_id: 81,
        recorded_at: '2026-03-18T11:33:05.000Z',
      },
    })
    activeBoardApiMocks.getDeveloperControlPlaneConflictRecord.mockReturnValue(null)
    activeBoardApiMocks.getDeveloperControlPlaneCompletionConflictDetail.mockReturnValue(null)
    activeBoardApiMocks.getDeveloperControlPlaneOvernightQueueConflictDetail.mockReturnValue(null)
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorSummary.mockImplementation(
      (error: unknown) => ({
        kind: 'generic',
        message:
          error instanceof Error
            ? error.message
            : 'Developer control-plane persistence failed',
      })
    )
    activeBoardApiMocks.isDeveloperControlPlaneConflictError.mockReturnValue(false)
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockImplementation(
      (error: unknown) => (error instanceof Error ? error.message : 'Developer control-plane persistence failed')
    )
    activeBoardApiMocks.bootstrapDeveloperControlPlaneMissionStateFromCloseoutReceipt.mockResolvedValue(
      {
        action: 'existing',
        mission_id: 'mission-1',
      }
    )
    vi.restoreAllMocks()
  })

  it('hydrates from the shared backend board when a record already exists', async () => {
    const remoteBoardJson = canonicalizeDeveloperMasterBoardJson(`{
      "title": "Remote Shared Board",
      "board_id": "bijmantra-app-development-master-board",
      "version": "1.0.0",
      "visibility": "internal-superuser",
      "continuous_operation_goal": "Remote goal",
      "intent": "Remote intent",
      "control_plane": {
        "operating_cadence": [],
        "evidence_sources": [],
        "primary_orchestrator": "OmShriMaatreNamaha"
      },
      "agent_roles": [],
      "lanes": [],
      "orchestration_contract": {
        "coordination_rules": [],
        "execution_loop": [],
        "canonical_outputs": [],
        "canonical_inputs": []
      }
    }`)
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(remoteBoardJson, { concurrency_token: 'remote-token' }),
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    expect(result.current.rawBoardJson).toBe(remoteBoardJson)
    expect(activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard).not.toHaveBeenCalled()
  })

  it('surfaces schema-readiness failures as an explicit persistence state', async () => {
    const schemaMessage =
      'Developer control-plane persistence schema is not ready; missing table(s): developer_control_plane_board_revisions. Run backend alembic upgrade through revision 20260318_1500.'
    const schemaError = new ApiError(
      schemaMessage,
      ApiErrorType.SERVICE_UNAVAILABLE,
      503,
      { message: schemaMessage }
    )

    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockRejectedValue(schemaError)
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorSummary.mockReturnValue({
      kind: 'schema-not-ready',
      message: schemaMessage,
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(schemaMessage)

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared persistence schema incomplete')
    })

    expect(result.current.persistenceStatus.description).toBe(schemaMessage)
  })

  it('surfaces bootstrap save schema failures as an explicit persistence state', async () => {
    const schemaMessage =
      'Developer control-plane persistence schema is not ready; missing table(s): developer_control_plane_board_revisions. Run backend alembic upgrade through revision 20260318_1500.'
    const schemaError = new ApiError(
      schemaMessage,
      ApiErrorType.SERVICE_UNAVAILABLE,
      503,
      { message: schemaMessage }
    )

    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({ exists: false, record: null })
    activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard.mockRejectedValue(schemaError)
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorSummary.mockReturnValue({
      kind: 'schema-not-ready',
      message: schemaMessage,
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(schemaMessage)

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared persistence schema incomplete')
    })

    expect(result.current.persistenceStatus.description).toBe(schemaMessage)
  })

  it('creates a lane and applies owner and subplan updates through the canonical board store', async () => {
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.handleCreateLane()
    })

    expect(result.current.selectedLane?.id).toMatch(/^new-lane-4-/)
    expect(result.current.activeTab).toBe('planner')

    act(() => {
      result.current.setExtraOwnersInput('Agent Alpha, Agent Beta')
    })

    act(() => {
      result.current.handleAddExtraOwners()
    })

    act(() => {
      result.current.handleAddSubplan()
    })

    const board = parseDeveloperMasterBoard(useDevMasterBoardStore.getState().rawBoardJson)
    const newLane = board.lanes.find((lane) => lane.id === result.current.selectedLane?.id)

    expect(newLane?.owners).toEqual(
      expect.arrayContaining(['OmShriMaatreNamaha', 'Agent Alpha', 'Agent Beta'])
    )
    expect(newLane?.subplans).toHaveLength(1)
    expect(result.current.extraOwnersInput).toBe('')

    await waitFor(() => {
      expect(activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard).toHaveBeenCalled()
    }, { timeout: 2000 })

    expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
  })

  it('does not write a queue entry when owner state makes the selected lane structurally blocked', async () => {
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await waitFor(() => {
      expect(result.current.queueStatusState).toBe('ready')
    })

    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockClear()

    act(() => {
      result.current.updateLaneField('owners', [])
    })

    expect(result.current.selectedLaneAnalysis?.readiness).toBe('blocked')
    expect(result.current.selectedLaneAnalysis?.structuralWarnings).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'missing-owners', severity: 'blocking' }),
      ])
    )

    await act(async () => {
      await result.current.handleWriteQueueEntry()
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus).not.toHaveBeenCalled()
    expect(activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry).not.toHaveBeenCalled()
  })

  it('refreshes runtime watchdog state alongside queue status', async () => {
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.refreshQueueStatus()
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneAutonomyCycle).toHaveBeenCalled()
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneRuntimeCompletionAssist).toHaveBeenCalled()
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneWatchdogStatus).toHaveBeenCalled()
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneSilentMonitors).toHaveBeenCalled()
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneMissionState).toHaveBeenCalled()
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneMissionDetail).toHaveBeenCalledWith(
      'mission-1'
    )
    expect(result.current.runtimeWatchdogState).toBe('ready')
    expect(result.current.runtimeWatchdogRecord?.job_count).toBe(1)
    expect(result.current.runtimeWatchdogRecord?.jobs[0]?.verification_passed).toBe(true)
    expect(result.current.runtimeAutonomyCycleState).toBe('ready')
    expect(result.current.runtimeAutonomyCycleRecord?.next_action_count).toBe(1)
    expect(result.current.runtimeAutonomyCycleRecord?.next_actions[0]?.action).toBe(
      'dispatch-queue-job'
    )
    expect(result.current.runtimeCompletionAssistState).toBe('ready')
    expect(result.current.runtimeCompletionAssistRecord?.status).toBe('staged')
    expect(
      result.current.runtimeCompletionAssistRecord?.actionable_completion_write?.sourceLaneId
    ).toBe('control-plane')
    expect(result.current.silentMonitorsState).toBe('ready')
    expect(result.current.silentMonitorsRecord?.overall_state).toBe('alert')
    expect(
      result.current.silentMonitorsRecord?.monitors.find(
        (monitor) => monitor.monitor_key === 'reevu-readiness'
      )?.state
    ).toBe('alert')
    expect(result.current.missionStateState).toBe('ready')
    expect(result.current.missionStateRecord?.count).toBe(1)
    expect(result.current.missionDetailState).toBe('ready')
    expect(result.current.missionDetailRecord?.evidence_items[0]?.source_path).toBe(
      'runtime-artifacts/watchdog-state.json'
    )
  })

  it('keeps stable closeout receipt loading read-only', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt.mockResolvedValue({
      exists: true,
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      mission_id: 'runtime-mission-control-plane-sharedto',
      producer_key: 'openclaw-runtime',
      source_lane_id: 'control-plane',
      source_board_concurrency_token: 'shared-token-1',
      runtime_profile_id: 'bijmantra-bca-local-verify',
      runtime_policy_sha256: 'policy-sha-1234',
      closeout_status: 'passed',
      state_refresh_required: true,
      receipt_recorded_at: '2026-03-20T08:05:00+00:00',
      started_at: '2026-03-20T08:00:00+00:00',
      finished_at: '2026-03-20T08:04:00+00:00',
      verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
      queue_sha256_at_closeout: 'queue-sha-closeout-77',
      closeout_commands: [],
      artifacts: [],
    })
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.refreshQueueStatus()
    })

    expect(
      activeBoardApiMocks.bootstrapDeveloperControlPlaneMissionStateFromCloseoutReceipt
    ).not.toHaveBeenCalled()
    expect(result.current.closeoutReceiptRecord?.mission_id).toBe(
      'runtime-mission-control-plane-sharedto'
    )
  })

  it('prefers the selected lane runtime mission id when loading durable mission detail', async () => {
    const board = parseDeveloperMasterBoard(createDefaultDeveloperMasterBoardJson())
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      queue_sha256: 'queue-sha-1',
      source_board_concurrency_token: 'shared-token-1',
      closure_summary: 'Reviewed runtime evidence was accepted.',
      evidence: ['Focused tests passed'],
      completed_at: '2026-03-20T08:06:00+00:00',
      closeout_receipt: {
        queue_job_id: 'overnight-lane-control-plane-sharedto',
        artifact_paths: ['metrics.json'],
        mission_id: 'runtime-mission-control-plane-sharedto',
        producer_key: 'openclaw-runtime',
        source_lane_id: 'control-plane',
        source_board_concurrency_token: 'shared-token-1',
        runtime_profile_id: 'bijmantra-bca-local-verify',
        runtime_policy_sha256: 'policy-sha-1234',
        closeout_status: 'passed',
        state_refresh_required: true,
        receipt_recorded_at: '2026-03-20T08:05:00+00:00',
        verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
        queue_sha256_at_closeout: 'queue-sha-closeout-77',
      },
    }

    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(serializeDeveloperMasterBoard(board), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionState.mockResolvedValue({
      count: 2,
      missions: [
        {
          mission_id: 'mission-latest',
          objective: 'Unrelated latest mission',
          status: 'completed',
          owner: 'OmShriMaatreNamaha',
          priority: 'p2',
          producer_key: 'chaitanya',
          queue_job_id: null,
          source_lane_id: null,
          source_board_concurrency_token: null,
          created_at: '2026-03-20T09:00:00+00:00',
          updated_at: '2026-03-20T09:05:00+00:00',
          subtask_total: 1,
          subtask_completed: 1,
          assignment_total: 1,
          evidence_count: 1,
          blocker_count: 0,
          escalation_needed: false,
          verification: {
            passed: 1,
            warned: 0,
            failed: 0,
            last_verified_at: '2026-03-20T09:04:00+00:00',
          },
          final_summary: 'Latest unrelated mission.',
        },
        {
          mission_id: 'runtime-mission-control-plane-sharedto',
          objective: 'Reviewed closeout persistence for lane Control Plane Lane',
          status: 'completed',
          owner: 'OmShriMaatreNamaha',
          priority: 'p1',
          producer_key: 'openclaw-runtime',
          queue_job_id: 'overnight-lane-control-plane-sharedto',
          source_lane_id: 'control-plane',
          source_board_concurrency_token: 'shared-token-1',
          created_at: '2026-03-20T08:00:00+00:00',
          updated_at: '2026-03-20T08:05:00+00:00',
          subtask_total: 1,
          subtask_completed: 1,
          assignment_total: 1,
          evidence_count: 2,
          blocker_count: 0,
          escalation_needed: false,
          verification: {
            passed: 1,
            warned: 0,
            failed: 0,
            last_verified_at: '2026-03-20T08:04:00+00:00',
          },
          final_summary: 'Linked mission detail should win.',
        },
      ],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionDetail.mockResolvedValue({
      mission_id: 'runtime-mission-control-plane-sharedto',
      objective: 'Reviewed closeout persistence for lane Control Plane Lane',
      status: 'completed',
      owner: 'OmShriMaatreNamaha',
      priority: 'p1',
      producer_key: 'openclaw-runtime',
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      source_lane_id: 'control-plane',
      source_board_concurrency_token: 'shared-token-1',
      created_at: '2026-03-20T08:00:00+00:00',
      updated_at: '2026-03-20T08:05:00+00:00',
      subtask_total: 1,
      subtask_completed: 1,
      assignment_total: 1,
      evidence_count: 2,
      blocker_count: 0,
      escalation_needed: false,
      verification: {
        passed: 1,
        warned: 0,
        failed: 0,
        last_verified_at: '2026-03-20T08:04:00+00:00',
      },
      final_summary: 'Linked mission detail should win.',
      subtasks: [],
      assignments: [],
      evidence_items: [],
      verification_runs: [],
      decision_notes: [],
      blockers: [],
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await waitFor(() => {
      expect(activeBoardApiMocks.fetchDeveloperControlPlaneMissionDetail).toHaveBeenCalledWith(
        'runtime-mission-control-plane-sharedto'
      )
    })

    expect(result.current.selectedLane?.closure?.closeout_receipt?.mission_id).toBe(
      'runtime-mission-control-plane-sharedto'
    )
    expect(result.current.missionDetailRecord?.mission_id).toBe(
      'runtime-mission-control-plane-sharedto'
    )
  })

  it('uses server-side mission-state filtering when the linked mission falls outside the live feed window', async () => {
    const board = parseDeveloperMasterBoard(createDefaultDeveloperMasterBoardJson())
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      queue_sha256: 'queue-sha-1',
      source_board_concurrency_token: 'shared-token-1',
      closure_summary: 'Reviewed runtime evidence was accepted.',
      evidence: ['Focused tests passed'],
      completed_at: '2026-03-20T08:06:00+00:00',
      closeout_receipt: {
        queue_job_id: 'overnight-lane-control-plane-sharedto',
        artifact_paths: ['metrics.json'],
        mission_id: 'runtime-mission-control-plane-sharedto',
        producer_key: 'openclaw-runtime',
        source_lane_id: 'control-plane',
        source_board_concurrency_token: 'shared-token-1',
        runtime_profile_id: 'bijmantra-bca-local-verify',
        runtime_policy_sha256: 'policy-sha-1234',
        closeout_status: 'passed',
        state_refresh_required: true,
        receipt_recorded_at: '2026-03-20T08:05:00+00:00',
        verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
        queue_sha256_at_closeout: 'queue-sha-closeout-77',
      },
    }

    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(serializeDeveloperMasterBoard(board), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionState
      .mockResolvedValueOnce({
        count: 1,
        missions: [
          {
            mission_id: 'mission-latest',
            objective: 'Unrelated latest mission',
            status: 'completed',
            owner: 'OmShriMaatreNamaha',
            priority: 'p2',
            producer_key: 'chaitanya',
            queue_job_id: null,
            source_lane_id: null,
            source_board_concurrency_token: null,
            created_at: '2026-03-20T09:00:00+00:00',
            updated_at: '2026-03-20T09:05:00+00:00',
            subtask_total: 1,
            subtask_completed: 1,
            assignment_total: 1,
            evidence_count: 1,
            blocker_count: 0,
            escalation_needed: false,
            verification: {
              passed: 1,
              warned: 0,
              failed: 0,
              last_verified_at: '2026-03-20T09:04:00+00:00',
            },
            final_summary: 'Latest unrelated mission.',
          },
        ],
      })
      .mockResolvedValueOnce({
        count: 1,
        missions: [
          {
            mission_id: 'runtime-mission-control-plane-sharedto',
            objective: 'Reviewed closeout persistence for lane Control Plane Lane',
            status: 'completed',
            owner: 'OmShriMaatreNamaha',
            priority: 'p1',
            producer_key: 'openclaw-runtime',
            queue_job_id: 'overnight-lane-control-plane-sharedto',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'shared-token-1',
            created_at: '2026-03-20T08:00:00+00:00',
            updated_at: '2026-03-20T08:05:00+00:00',
            subtask_total: 1,
            subtask_completed: 1,
            assignment_total: 1,
            evidence_count: 2,
            blocker_count: 0,
            escalation_needed: false,
            verification: {
              passed: 1,
              warned: 0,
              failed: 0,
              last_verified_at: '2026-03-20T08:04:00+00:00',
            },
            final_summary: 'Linked mission detail should win.',
          },
        ],
      })
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionDetail.mockResolvedValue({
      mission_id: 'runtime-mission-control-plane-sharedto',
      objective: 'Reviewed closeout persistence for lane Control Plane Lane',
      status: 'completed',
      owner: 'OmShriMaatreNamaha',
      priority: 'p1',
      producer_key: 'openclaw-runtime',
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      source_lane_id: 'control-plane',
      source_board_concurrency_token: 'shared-token-1',
      created_at: '2026-03-20T08:00:00+00:00',
      updated_at: '2026-03-20T08:05:00+00:00',
      subtask_total: 1,
      subtask_completed: 1,
      assignment_total: 1,
      evidence_count: 2,
      blocker_count: 0,
      escalation_needed: false,
      verification: {
        passed: 1,
        warned: 0,
        failed: 0,
        last_verified_at: '2026-03-20T08:04:00+00:00',
      },
      final_summary: 'Linked mission detail should win.',
      subtasks: [],
      assignments: [],
      evidence_items: [],
      verification_runs: [],
      decision_notes: [],
      blockers: [],
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await waitFor(() => {
      expect(activeBoardApiMocks.fetchDeveloperControlPlaneMissionDetail).toHaveBeenCalledWith(
        'runtime-mission-control-plane-sharedto'
      )
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneMissionState).toHaveBeenCalledWith({
      limit: 1,
      queueJobId: 'overnight-lane-control-plane-sharedto',
      sourceLaneId: 'control-plane',
    })
    expect(result.current.missionStateRecord?.count).toBe(2)
    expect(
      result.current.missionStateRecord?.missions.some(
        (mission) => mission.mission_id === 'runtime-mission-control-plane-sharedto'
      )
    ).toBe(true)
    expect(result.current.missionDetailRecord?.mission_id).toBe(
      'runtime-mission-control-plane-sharedto'
    )
  })

  it('writes validation_basis edits through the canonical board store', async () => {
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.updateValidationBasisField('owner', 'OmShriMaatreNamaha')
      result.current.updateValidationBasisField('summary', 'Operator-reviewed validation basis is now current.')
      result.current.updateValidationBasisField('evidence', ['evidence/a', 'evidence/b'])
      result.current.updateValidationBasisField('last_reviewed_at', '2026-03-18T21:00:00.000Z')
    })

    const board = parseDeveloperMasterBoard(useDevMasterBoardStore.getState().rawBoardJson)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    expect(controlPlaneLane?.validation_basis).toEqual({
      owner: 'OmShriMaatreNamaha',
      summary: 'Operator-reviewed validation basis is now current.',
      evidence: ['evidence/a', 'evidence/b'],
      last_reviewed_at: '2026-03-18T21:00:00.000Z',
    })
    expect(result.current.selectedLane?.id).toBe('control-plane')

    act(() => {
      result.current.updateValidationBasisField('owner', '')
      result.current.updateValidationBasisField('summary', '')
      result.current.updateValidationBasisField('evidence', [])
      result.current.updateValidationBasisField('last_reviewed_at', '')
    })

    const clearedBoard = parseDeveloperMasterBoard(useDevMasterBoardStore.getState().rawBoardJson)
    const clearedLane = clearedBoard.lanes.find((lane) => lane.id === 'control-plane')
    expect(clearedLane?.validation_basis).toBeUndefined()
  })

  it('writes review_state edits through the canonical board store', async () => {
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.updateReviewStateField('spec_review', 'reviewed_by', 'OmShriMaatreNamaha')
      result.current.updateReviewStateField('spec_review', 'summary', 'Spec review is now current.')
      result.current.updateReviewStateField('spec_review', 'evidence', ['review/a', 'review/b'])
      result.current.updateReviewStateField('spec_review', 'reviewed_at', '2026-03-31T09:30:00.000Z')
    })

    const board = parseDeveloperMasterBoard(useDevMasterBoardStore.getState().rawBoardJson)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    expect(controlPlaneLane?.review_state?.spec_review).toEqual({
      reviewed_by: 'OmShriMaatreNamaha',
      summary: 'Spec review is now current.',
      evidence: ['review/a', 'review/b'],
      reviewed_at: '2026-03-31T09:30:00.000Z',
    })

    act(() => {
      result.current.updateReviewStateField('spec_review', 'reviewed_by', '')
      result.current.updateReviewStateField('spec_review', 'summary', '')
      result.current.updateReviewStateField('spec_review', 'evidence', [])
      result.current.updateReviewStateField('spec_review', 'reviewed_at', '')
    })

    const clearedBoard = parseDeveloperMasterBoard(useDevMasterBoardStore.getState().rawBoardJson)
    const clearedLane = clearedBoard.lanes.find((lane) => lane.id === 'control-plane')
    expect(clearedLane?.review_state?.spec_review).toBeUndefined()
  })

  it('loads immutable board history and restores a prior revision from the planner workflow', async () => {
    const sharedBoard = createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
      concurrency_token: 'shared-token-1',
    })
    const restoredBoard = parseDeveloperMasterBoard(createDefaultDeveloperMasterBoardJson())

    restoredBoard.title = 'Restored Shared Board'

    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: sharedBoard,
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoardVersions
      .mockResolvedValueOnce(
        createBoardVersionsRecord(
          [
            createBoardVersion(8, {
              concurrency_token: 'shared-token-8',
              created_at: '2026-03-31T10:00:00.000Z',
              is_current: true,
            }),
            createBoardVersion(7, {
              concurrency_token: 'shared-token-7',
              created_at: '2026-03-31T09:45:00.000Z',
            }),
          ],
          { current_concurrency_token: 'shared-token-8' }
        )
      )
      .mockResolvedValueOnce(
        createBoardVersionsRecord(
          [
            createBoardVersion(9, {
              concurrency_token: 'shared-token-9',
              save_source: 'hidden-route-restore',
              created_at: '2026-03-31T10:06:00.000Z',
              is_current: true,
            }),
            createBoardVersion(8, {
              concurrency_token: 'shared-token-8',
              created_at: '2026-03-31T10:00:00.000Z',
            }),
          ],
          { current_concurrency_token: 'shared-token-9' }
        )
      )
    activeBoardApiMocks.restoreDeveloperControlPlaneActiveBoardVersion.mockResolvedValue({
      restored: true,
      restored_from_revision_id: 7,
      record: createActiveBoardRecord(serializeDeveloperMasterBoard(restoredBoard), {
        concurrency_token: 'shared-token-9',
        updated_at: '2026-03-31T10:06:00.000Z',
      }),
      approval_receipt: {
        receipt_id: 91,
        recorded_at: '2026-03-31T10:06:05.000Z',
      },
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.setActiveTab('planner')
    })

    await waitFor(() => {
      expect(activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoardVersions).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(
        result.current.boardVersionsRecord?.versions.find((version) => version.is_current)
          ?.revision_id
      ).toBe(8)
    })

    await act(async () => {
      await result.current.handleRestoreBoardVersion(7)
    })

    expect(activeBoardApiMocks.restoreDeveloperControlPlaneActiveBoardVersion).toHaveBeenCalledWith(
      7,
      'shared-token-1'
    )

    await waitFor(() => {
      expect(result.current.boardRestoreState).toBe('restored')
    })

    expect(result.current.parsedBoard?.title).toBe('Restored Shared Board')
    expect(result.current.boardVersionsRecord?.versions.find((version) => version.is_current)?.revision_id).toBe(9)
    expect(result.current.lastBoardRestoreResult).toMatchObject({
      status: 'restored',
      restored: true,
      restoredFromRevisionId: 7,
      currentBoardConcurrencyToken: 'shared-token-9',
      previousBoardConcurrencyToken: 'shared-token-1',
      approvalReceiptId: 91,
      approvalReceiptRecordedAt: '2026-03-31T10:06:05.000Z',
    })
  })

  it('loads overview learnings and supports scoped lane refreshes', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionState.mockResolvedValue({
      count: 0,
      missions: [],
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneLearnings
      .mockResolvedValueOnce({
        total_count: 1,
        entries: [
          {
            learning_entry_id: 401,
            organization_id: 1,
            entry_type: 'pattern',
            source_classification: 'approval-receipt',
            title: 'Reviewed queue export pattern',
            summary: 'Accepted approval receipts can be reused as canonical queue-export evidence.',
            confidence_score: 0.86,
            recorded_by_user_id: 1,
            recorded_by_email: 'ops@bijmantra.org',
            board_id: 'bijmantra-app-development-master-board',
            source_lane_id: 'control-plane',
            queue_job_id: 'overnight-lane-control-plane-shared-token-1',
            linked_mission_id: null,
            approval_receipt_id: 44,
            source_reference: 'approval-receipt-44',
            evidence_refs: ['receipt:44'],
            summary_metadata: null,
            recorded_at: '2026-03-31T12:10:00.000Z',
          },
        ],
      })
      .mockResolvedValueOnce({
        total_count: 1,
        entries: [
          {
            learning_entry_id: 402,
            organization_id: 1,
            entry_type: 'verification-learning',
            source_classification: 'mission-state',
            title: 'Lane-scoped verification reminder',
            summary: 'Control-plane verification evidence should be refreshed before completion write-back.',
            confidence_score: 0.91,
            recorded_by_user_id: 1,
            recorded_by_email: 'ops@bijmantra.org',
            board_id: 'bijmantra-app-development-master-board',
            source_lane_id: 'control-plane',
            queue_job_id: null,
            linked_mission_id: 'mission-control-plane-1',
            approval_receipt_id: null,
            source_reference: 'mission:mission-control-plane-1',
            evidence_refs: ['mission:mission-control-plane-1'],
            summary_metadata: null,
            recorded_at: '2026-03-31T12:15:00.000Z',
          },
        ],
      })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await waitFor(() => {
      expect(result.current.learningLedgerState).toBe('ready')
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneLearnings).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        limit: 6,
        entryType: null,
        sourceLaneId: null,
        queueJobId: null,
      })
    )
    expect(result.current.learningLedgerRecord?.entries[0]?.title).toBe(
      'Reviewed queue export pattern'
    )

    await act(async () => {
      await result.current.loadLearnings({
        limit: 6,
        sourceLaneId: 'control-plane',
      })
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneLearnings).toHaveBeenLastCalledWith(
      expect.objectContaining({
        limit: 6,
        sourceLaneId: 'control-plane',
      })
    )
    expect(result.current.learningLedgerQuery).toMatchObject({
      sourceLaneId: 'control-plane',
    })
    expect(result.current.learningLedgerRecord?.entries[0]?.title).toBe(
      'Lane-scoped verification reminder'
    )
  })

  it('creates collision-safe lane and subplan ids after deletes', async () => {
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.handleCreateLane()
    })

    const firstCreatedLaneId = result.current.selectedLane?.id

    expect(firstCreatedLaneId).toMatch(/^new-lane-4-/)

    act(() => {
      result.current.handleDeleteLane()
    })

    act(() => {
      result.current.handleCreateLane()
    })

    const secondCreatedLaneId = result.current.selectedLane?.id

    expect(secondCreatedLaneId).toMatch(/^new-lane-4-/)
    expect(secondCreatedLaneId).not.toBe(firstCreatedLaneId)

    act(() => {
      result.current.handleAddSubplan()
    })

    act(() => {
      result.current.handleAddSubplan()
    })

    const firstSubplanIds = result.current.selectedLane?.subplans.map((subplan) => subplan.id) ?? []

    expect(firstSubplanIds).toHaveLength(2)
    expect(firstSubplanIds[0]).toMatch(/^subplan-1-/)
    expect(firstSubplanIds[1]).toMatch(/^subplan-2-/)

    act(() => {
      result.current.handleDeleteSubplan(firstSubplanIds[0] ?? '')
    })

    act(() => {
      result.current.handleAddSubplan()
    })

    const nextSubplanIds = result.current.selectedLane?.subplans.map((subplan) => subplan.id) ?? []

    expect(nextSubplanIds).toHaveLength(2)
    expect(nextSubplanIds[0]).toBe(firstSubplanIds[1])
    expect(nextSubplanIds[1]).toMatch(/^subplan-2-/)
    expect(nextSubplanIds[1]).not.toBe(firstSubplanIds[0])
    expect(nextSubplanIds[1]).not.toBe(firstSubplanIds[1])
  })

  it('surfaces a shared-board conflict instead of silently overwriting a newer backend record', async () => {
    const remoteBoard = createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
      concurrency_token: 'remote-token-1',
    })
    const currentRemoteBoard = createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
      concurrency_token: 'remote-token-2',
      updated_at: '2026-03-18T12:00:00.000Z',
    })

    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: remoteBoard,
    })
    const conflictError = new ApiError(
      'HTTP 409',
      ApiErrorType.CONFLICT,
      409,
      {
        detail: {
          detail: 'Active board save conflict; refetch the current board before retrying',
          current_record: currentRemoteBoard,
        },
      } as any,
      { statusCode: 409 }
    )
    activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard.mockRejectedValue(conflictError)
    activeBoardApiMocks.getDeveloperControlPlaneConflictRecord.mockReturnValue(currentRemoteBoard)
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Active board save conflict; refetch the current board before retrying'
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.handleCreateLane()
    })

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared board conflict')
    }, { timeout: 2000 })

    expect(activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard).toHaveBeenCalledWith(
      expect.objectContaining({ concurrency_token: 'remote-token-1' })
    )
  })

  it('exports, imports, and resets canonical board JSON through controller actions', async () => {
    const createObjectURL = vi.fn(() => 'blob:board')
    const revokeObjectURL = vi.fn()
    const click = vi.fn()
    let exportedBlobParts: BlobPart[] = []

    class CapturingBlob extends Blob {
      constructor(blobParts: BlobPart[], options?: BlobPropertyBag) {
        super(blobParts, options)
        exportedBlobParts = blobParts
      }
    }

    vi.stubGlobal('navigator', {
      clipboard: {
        writeText: vi.fn(),
      },
    })
    vi.stubGlobal('Blob', CapturingBlob)

    window.URL.createObjectURL = vi.fn((blob: Blob) => {
      return createObjectURL()
    })
    window.URL.revokeObjectURL = revokeObjectURL
    vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      if (tagName === 'a') {
        const anchor = document.createElementNS('http://www.w3.org/1999/xhtml', 'a')
        anchor.click = click
        return anchor
      }

      return document.createElementNS('http://www.w3.org/1999/xhtml', tagName)
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.handleExport()
    })

    expect(createObjectURL).toHaveBeenCalledTimes(1)
    expect(click).toHaveBeenCalledTimes(1)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:board')

    const importedJson = '{\n  "title": "Imported Board",\n  "board_id": "bijmantra-app-development-master-board",\n  "version": "1.0.0",\n  "visibility": "internal-superuser",\n  "continuous_operation_goal": "Imported goal",\n  "intent": "Imported intent",\n  "control_plane": {\n    "operating_cadence": [],\n    "evidence_sources": [],\n    "primary_orchestrator": "OmShriMaatreNamaha"\n  },\n  "agent_roles": [],\n  "lanes": [],\n  "orchestration_contract": {\n    "coordination_rules": [],\n    "execution_loop": [],\n    "canonical_outputs": [],\n    "canonical_inputs": []\n  }\n}'

    const importEvent = {
      target: {
        files: [
          {
            text: async () => importedJson,
          },
        ],
        value: 'pending',
      },
    } as unknown as ChangeEvent<HTMLInputElement>

    await act(async () => {
      await result.current.handleImport(importEvent)
    })

    expect(useDevMasterBoardStore.getState().rawBoardJson).toBe(
      canonicalizeDeveloperMasterBoardJson(importedJson)
    )
    expect(importEvent.target.value).toBe('')

    act(() => {
      result.current.handleExport()
    })

    expect(exportedBlobParts).toHaveLength(1)
    expect(String(exportedBlobParts[0])).toBe(
      canonicalizeDeveloperMasterBoardJson(importedJson)
    )

    act(() => {
      result.current.resetBoard()
    })

    expect(useDevMasterBoardStore.getState().rawBoardJson).toContain('BijMantra Developer Control Plane')
  })

  it('bootstraps the first shared board automatically when no remote record exists', async () => {
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    expect(activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard).toHaveBeenCalledWith(
      expect.objectContaining({
        save_source: 'hidden-route-bootstrap',
        concurrency_token: null,
      })
    )
    expect(result.current.queueCandidate?.sourceBoardConcurrencyToken).toBe('token-1')
    expect(result.current.queueEntryMaterialization.entry).not.toBeNull()
  })

  it('does not copy a queue candidate while shared board bootstrap is still pending', async () => {
    const writeText = vi.fn()
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText,
      },
    })
    activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard.mockImplementation(
      () => new Promise(() => {})
    )

    const { result } = renderHook(() => useControlPlaneController())

    expect(result.current.queueCandidate).toBeNull()

    await act(async () => {
      await result.current.handleCopyQueueCandidate()
    })

    expect(writeText).not.toHaveBeenCalled()
  })

  it('does not copy a queue entry while shared board bootstrap is still pending', async () => {
    const writeText = vi.fn()
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText,
      },
    })
    activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard.mockImplementation(
      () => new Promise(() => {})
    )

    const { result } = renderHook(() => useControlPlaneController())

    expect(result.current.queueEntryMaterialization.entry).toBeNull()

    await act(async () => {
      await result.current.handleCopyQueueEntry()
    })

    expect(writeText).not.toHaveBeenCalled()
  })

  it('copies a queue candidate once the shared active board token exists', async () => {
    const writeText = vi.fn()
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText,
      },
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    expect(result.current.queueCandidate?.sourceBoardConcurrencyToken).toBe('shared-token-1')

    await act(async () => {
      await result.current.handleCopyQueueCandidate()
    })

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining('"sourceBoardConcurrencyToken": "shared-token-1"')
    )
  })

  it('copies a queue-native entry once shared active board token exists', async () => {
    const writeText = vi.fn()
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText,
      },
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    expect(result.current.queueEntryMaterialization.entry).not.toBeNull()

    await act(async () => {
      await result.current.handleCopyQueueEntry()
    })

    expect(writeText).toHaveBeenCalledWith(expect.stringContaining('"status": "queued"'))
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining('"priority": "p2"'))
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining('"executionMode": "same-control-plane"')
    )
  })

  it('does not write a queue entry while shared board bootstrap is still pending', async () => {
    activeBoardApiMocks.saveDeveloperControlPlaneActiveBoard.mockImplementation(
      () => new Promise(() => {})
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus).toHaveBeenCalled()
    })

    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockClear()

    await act(async () => {
      await result.current.handleWriteQueueEntry()
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus).not.toHaveBeenCalled()
    expect(activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry).not.toHaveBeenCalled()
    expect(result.current.queueWriteState).toBe('idle')
  })

  it('writes a queue entry when shared board provenance exists', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        exists: true,
        job_count: 2,
        updated_at: '2026-03-18T11:30:00.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-2',
        exists: true,
        job_count: 3,
        updated_at: '2026-03-18T11:31:00.000Z',
      })
    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await waitFor(() => {
      expect(result.current.queueStatusState).toBe('ready')
    })

    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockReset()
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        exists: true,
        job_count: 2,
        updated_at: '2026-03-18T11:30:00.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-2',
        exists: true,
        job_count: 3,
        updated_at: '2026-03-18T11:31:00.000Z',
      })

    await act(async () => {
      await result.current.handleWriteQueueEntry()
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus).toHaveBeenCalledTimes(2)
    expect(activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry).toHaveBeenCalledWith(
      expect.objectContaining({
        source_board_concurrency_token: 'shared-token-1',
        expected_queue_sha256: 'queue-sha-1',
        operator_intent: 'write-reviewed-queue-entry',
      })
    )
    expect(result.current.queueWriteState).toBe('written')
    expect(result.current.queueStatusRecord?.queue_sha256).toBe('queue-sha-2')
    expect(result.current.queueStatusRecord?.job_count).toBe(3)
    expect(result.current.lastQueueWriteResult).toMatchObject({
      status: 'written',
      writtenJobId: 'overnight-lane-platform-runtime-token1',
      previousQueueSha256: 'queue-sha-1',
      currentQueueSha256: 'queue-sha-2',
      queueUpdatedAt: '2026-03-18T11:31:00.000Z',
      approvalReceiptId: 41,
      approvalReceiptRecordedAt: '2026-03-18T11:31:05.000Z',
    })
  })

  it('surfaces queue sha conflict remediation and refreshed queue status', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        exists: true,
        job_count: 2,
        updated_at: '2026-03-18T11:30:00.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-9',
        exists: true,
        job_count: 4,
        updated_at: '2026-03-18T11:35:00.000Z',
      })
    activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry.mockRejectedValue(
      new ApiError(
        'HTTP 409',
        ApiErrorType.CONFLICT,
        409,
        {
          detail: {
            detail: 'Queue write conflict; overnight queue changed since the latest snapshot',
            conflict_reason: 'queue-sha-mismatch',
            remediation_message:
              'Refresh queue status, compare the latest queue hash shown here, then retry only if the reviewed queue entry is still valid.',
            refresh_targets: ['overnight-queue'],
            retry_permitted_after_refresh: true,
            current_queue_sha256: 'queue-sha-9',
          },
        } as any,
        { statusCode: 409 }
      )
    )
    activeBoardApiMocks.isDeveloperControlPlaneConflictError.mockReturnValue(true)
    activeBoardApiMocks.getDeveloperControlPlaneOvernightQueueConflictDetail.mockReturnValue({
      detail: 'Queue write conflict; overnight queue changed since the latest snapshot',
      conflict_reason: 'queue-sha-mismatch',
      remediation_message:
        'Refresh queue status, compare the latest queue hash shown here, then retry only if the reviewed queue entry is still valid.',
      refresh_targets: ['overnight-queue'],
      retry_permitted_after_refresh: true,
      current_queue_sha256: 'queue-sha-9',
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Queue write conflict; overnight queue changed since the latest snapshot'
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await waitFor(() => {
      expect(result.current.queueStatusState).toBe('ready')
    })

    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockReset()
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        exists: true,
        job_count: 2,
        updated_at: '2026-03-18T11:30:00.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-9',
        exists: true,
        job_count: 4,
        updated_at: '2026-03-18T11:35:00.000Z',
      })

    await act(async () => {
      await result.current.handleWriteQueueEntry()
    })

    expect(result.current.queueWriteState).toBe('conflict')
    expect(result.current.queueStatusRecord?.queue_sha256).toBe('queue-sha-9')
    expect(result.current.lastQueueWriteResult).toMatchObject({
      status: 'conflict',
      previousQueueSha256: 'queue-sha-1',
      currentQueueSha256: 'queue-sha-9',
      conflictReason: 'queue-sha-mismatch',
      remediationMessage:
        'Refresh queue status, compare the latest queue hash shown here, then retry only if the reviewed queue entry is still valid.',
      refreshTargets: ['overnight-queue'],
      retryPermittedAfterRefresh: true,
    })
  })

  it('surfaces stale board token remediation without mutating board state', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-1',
        }),
      })
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-2',
        }),
      })
    activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry.mockRejectedValue(
      new ApiError(
        'HTTP 409',
        ApiErrorType.CONFLICT,
        409,
        {
          detail: {
            detail: 'Queue write conflict; source board token is stale and must be refreshed',
            conflict_reason: 'stale-board-token',
            remediation_message:
              'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.',
            refresh_targets: ['active-board'],
            retry_permitted_after_refresh: true,
            current_board_concurrency_token: 'shared-token-2',
          },
        } as any,
        { statusCode: 409 }
      )
    )
    activeBoardApiMocks.isDeveloperControlPlaneConflictError.mockReturnValue(true)
    activeBoardApiMocks.getDeveloperControlPlaneOvernightQueueConflictDetail.mockReturnValue({
      detail: 'Queue write conflict; source board token is stale and must be refreshed',
      conflict_reason: 'stale-board-token',
      remediation_message:
        'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.',
      refresh_targets: ['active-board'],
      retry_permitted_after_refresh: true,
      current_board_concurrency_token: 'shared-token-2',
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Queue write conflict; source board token is stale and must be refreshed'
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.handleWriteQueueEntry()
    })

    expect(result.current.queueWriteState).toBe('conflict')
    expect(result.current.lastQueueWriteResult).toMatchObject({
      status: 'conflict',
      conflictReason: 'stale-board-token',
      currentBoardConcurrencyToken: 'shared-token-2',
      remediationMessage:
        'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.',
      refreshTargets: ['active-board'],
      retryPermittedAfterRefresh: true,
    })
    expect(useDevMasterBoardStore.getState().backendConcurrencyToken).toBe('shared-token-1')

    await act(async () => {
      await result.current.handleRefreshRecommendedTargets(['active-board'])
    })

    expect(useDevMasterBoardStore.getState().backendConcurrencyToken).toBe('shared-token-2')
  })

  it('refreshes active board before queue-linked targets so derived queue evidence uses the latest token', async () => {
    const refreshedBoardToken = 'shared-token-9'
    const refreshedBoardJson = createDefaultDeveloperMasterBoardJson()
    const refreshedQueueJobId = createDeveloperLaneQueueJobId('control-plane', refreshedBoardToken)

    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-1',
        }),
      })
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(refreshedBoardJson, {
          concurrency_token: refreshedBoardToken,
        }),
      })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await waitFor(() => {
      expect(result.current.queueStatusState).toBe('ready')
    })

    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockClear()
    activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt.mockClear()
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockResolvedValue({
      queue_path: '.agent/jobs/overnight-queue.json',
      queue_sha256: 'queue-sha-9',
      exists: true,
      job_count: 4,
      updated_at: '2026-03-18T11:39:00.000Z',
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt.mockResolvedValue({
      exists: true,
      queue_job_id: refreshedQueueJobId,
      closeout_status: 'passed',
      state_refresh_required: true,
      receipt_recorded_at: '2026-03-18T11:40:00.000Z',
      started_at: '2026-03-18T11:39:30.000Z',
      finished_at: '2026-03-18T11:39:50.000Z',
      verification_evidence_ref:
        'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
      queue_sha256_at_closeout: 'queue-sha-9',
      closeout_commands: [],
      artifacts: [],
    })

    await act(async () => {
      await result.current.handleRefreshRecommendedTargets(['active-board', 'overnight-queue'])
    })

    expect(result.current.queueStatusRecord?.queue_sha256).toBe('queue-sha-9')
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt).toHaveBeenCalledWith(
      refreshedQueueJobId
    )
  })

  it('refreshes and retries queue writes with the latest shared board token when retry is permitted', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-1',
        }),
      })
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-2',
        }),
      })

    activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry
      .mockRejectedValueOnce(
        new ApiError(
          'HTTP 409',
          ApiErrorType.CONFLICT,
          409,
          {
            detail: {
              detail:
                'Queue write conflict; source board token is stale and must be refreshed',
              conflict_reason: 'stale-board-token',
              remediation_message:
                'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.',
              refresh_targets: ['active-board'],
              retry_permitted_after_refresh: true,
              current_board_concurrency_token: 'shared-token-2',
            },
          } as any,
          { statusCode: 409 }
        )
      )
      .mockResolvedValueOnce({
        queue_sha256: 'queue-sha-2',
        queue_updated_at: '2026-03-18T11:31:30.000Z',
        written_job_id: 'overnight-lane-control-plane-shared-token-2',
      })
    activeBoardApiMocks.isDeveloperControlPlaneConflictError.mockReturnValue(true)
    activeBoardApiMocks.getDeveloperControlPlaneOvernightQueueConflictDetail.mockReturnValue({
      detail: 'Queue write conflict; source board token is stale and must be refreshed',
      conflict_reason: 'stale-board-token',
      remediation_message:
        'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.',
      refresh_targets: ['active-board'],
      retry_permitted_after_refresh: true,
      current_board_concurrency_token: 'shared-token-2',
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Queue write conflict; source board token is stale and must be refreshed'
    )
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        exists: true,
        job_count: 2,
        updated_at: '2026-03-18T11:30:00.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        exists: true,
        job_count: 2,
        updated_at: '2026-03-18T11:30:15.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-2',
        exists: true,
        job_count: 3,
        updated_at: '2026-03-18T11:31:00.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-2',
        exists: true,
        job_count: 3,
        updated_at: '2026-03-18T11:31:30.000Z',
      })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.handleWriteQueueEntry()
    })

    expect(result.current.queueWriteState).toBe('conflict')

    await act(async () => {
      await result.current.handleRefreshAndRetryQueueWrite()
    })

    expect(activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry).toHaveBeenLastCalledWith(
      expect.objectContaining({
        source_board_concurrency_token: 'shared-token-2',
      })
    )
    expect(result.current.queueWriteState).toBe('written')
    expect(result.current.lastQueueWriteResult).toMatchObject({
      status: 'written',
      writtenJobId: 'overnight-lane-control-plane-shared-token-2',
    })
  })

  it('does not retry a queue write when active-board refresh fails', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-1',
        }),
      })
      .mockRejectedValueOnce(new Error('backend unavailable'))

    activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry.mockRejectedValueOnce(
      new ApiError(
        'HTTP 409',
        ApiErrorType.CONFLICT,
        409,
        {
          details: {
            detail: 'Queue write conflict; source board token is stale and must be refreshed',
            conflict_reason: 'stale-board-token',
            remediation_message:
              'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.',
            refresh_targets: ['active-board'],
            retry_permitted_after_refresh: true,
            current_board_concurrency_token: 'shared-token-2',
          },
        },
        { statusCode: 409 }
      )
    )
    activeBoardApiMocks.isDeveloperControlPlaneConflictError.mockReturnValue(true)
    activeBoardApiMocks.getDeveloperControlPlaneOvernightQueueConflictDetail.mockReturnValue({
      conflict_reason: 'stale-board-token',
      remediation_message:
        'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.',
      refresh_targets: ['active-board'],
      retry_permitted_after_refresh: true,
      current_board_concurrency_token: 'shared-token-2',
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Queue write conflict; source board token is stale and must be refreshed'
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.handleWriteQueueEntry()
    })

    expect(result.current.queueWriteState).toBe('conflict')

    await act(async () => {
      await result.current.handleRefreshAndRetryQueueWrite()
    })

    expect(activeBoardApiMocks.writeDeveloperControlPlaneOvernightQueueEntry).toHaveBeenCalledTimes(1)
    expect(result.current.queueWriteState).toBe('conflict')
  })

  it('writes lane completion back into the shared board after explicit review', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.setCompletionClosureSummary('Completion evidence was reviewed and accepted.')
      result.current.setCompletionEvidenceInput('Focused tests passed\nQueue job completed')
    })

    await act(async () => {
      await result.current.handleWriteLaneCompletion()
    })

    expect(activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion).toHaveBeenCalledWith(
      expect.objectContaining({
        source_board_concurrency_token: 'shared-token-1',
        operator_intent: 'write-reviewed-lane-completion',
        completion: expect.objectContaining({
          source_lane_id: 'control-plane',
        }),
      })
    )
    expect(result.current.completionWriteState).toBe('written')
    expect(result.current.lastCompletionWriteResult).toMatchObject({
      status: 'written',
      laneId: 'control-plane',
      laneStatus: 'completed',
      noOp: false,
      approvalReceiptId: 52,
      approvalReceiptRecordedAt: '2026-03-18T11:32:05.000Z',
      nextRecommendedLaneId: 'platform-runtime',
      nextRecommendedLaneTitle: 'App Runtime and Developer Surface Capabilities',
    })
    expect(useDevMasterBoardStore.getState().backendConcurrencyToken).toBe('token-completed-1')
  })

  it('submits the normalized closeout receipt with completion write-back when available', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockResolvedValue(
      createPreparedCompletionWriteResponse(
        { draft_source: 'stable-closeout-receipt' },
        {
          closure_summary:
            'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.',
          evidence: [
            'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.',
            'Watchdog closeout queue hash: queue-sha-closeout-77.',
            'Board token used for reviewed closeout: shared-token-1.',
            'Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.',
            'Verification evidence referenced by closeout receipt: runtime-artifacts/mission-evidence/job/verification_1.json.',
            'Closeout artifact refreshed: metrics.json.',
            'Stable closeout receipt recorded at 2026-03-19T12:05:00.000Z.',
          ],
          closeout_receipt: {
            queue_job_id: 'overnight-lane-control-plane-sharedto',
            artifact_paths: ['metrics.json'],
            mission_id: 'runtime-mission-control-plane-sharedto',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'shared-token-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-1234',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-19T12:05:00.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-closeout-77',
          },
        },
        {
          exists: true,
          queue_job_id: 'overnight-lane-control-plane-sharedto',
          mission_id: 'runtime-mission-control-plane-sharedto',
          producer_key: 'openclaw-runtime',
          source_lane_id: 'control-plane',
          source_board_concurrency_token: 'shared-token-1',
          runtime_profile_id: 'bijmantra-bca-local-verify',
          runtime_policy_sha256: 'policy-sha-1234',
          closeout_status: 'passed',
          state_refresh_required: true,
          receipt_recorded_at: '2026-03-19T12:05:00.000Z',
          started_at: '2026-03-19T12:03:00.000Z',
          finished_at: '2026-03-19T12:04:00.000Z',
          verification_evidence_ref:
            'runtime-artifacts/mission-evidence/job/verification_1.json',
          queue_sha256_at_closeout: 'queue-sha-closeout-77',
          closeout_commands: [],
          artifacts: [
            {
              path: 'metrics.json',
              exists: true,
              sha256: 'abc123',
              modified_at: '2026-03-19T12:04:30.000Z',
            },
          ],
        }
      )
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.setCompletionClosureSummary('Completion evidence was reviewed and accepted.')
      result.current.setCompletionEvidenceInput('Focused tests passed\nQueue job completed')
    })

    await act(async () => {
      await result.current.handleWriteLaneCompletion()
    })

    expect(activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion).toHaveBeenCalledWith(
      expect.objectContaining({
        completion: expect.objectContaining({
          closeout_receipt: {
            queue_job_id: 'overnight-lane-control-plane-sharedto',
            artifact_paths: ['metrics.json'],
            mission_id: 'runtime-mission-control-plane-sharedto',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'shared-token-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-1234',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-19T12:05:00.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-closeout-77',
          },
        }),
      })
    )
  })

  it('drafts completion write-back details from the current queue snapshot', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockResolvedValue({
      queue_path: '.agent/jobs/overnight-queue.json',
      queue_sha256: 'queue-sha-77',
      exists: true,
      job_count: 3,
      updated_at: '2026-03-19T12:00:00.000Z',
    })
    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockResolvedValue(
      createPreparedCompletionWriteResponse(
        {},
        {
          closure_summary:
            'Reviewed closeout for lane control-plane after queue completion and canonical queue refresh.',
          evidence: [
            'Reviewed queue job overnight-lane-control-plane-sharedto before explicit board write-back.',
            'Queue snapshot hash at reviewed closeout: queue-sha-77.',
            'Board token used for reviewed closeout: shared-token-1.',
            'Queue status reviewed at 2026-03-19T12:00:00.000Z.',
          ],
        },
        {},
        {
          queue_sha256: 'queue-sha-77',
          updated_at: '2026-03-19T12:00:00.000Z',
          job_count: 3,
        }
      )
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.refreshQueueStatus()
    })

    expect(result.current.closeoutReceiptState).toBe('missing')
    expect(result.current.closeoutReceiptRecord?.exists).toBe(false)

    await act(async () => {
      await result.current.handleDraftLaneCompletionFromCurrentState()
    })

    expect(result.current.completionClosureSummary).toBe(
      'Reviewed closeout for lane control-plane after queue completion and canonical queue refresh.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Reviewed queue job overnight-lane-control-plane-sharedto before explicit board write-back.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Queue snapshot hash at reviewed closeout: queue-sha-77.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Board token used for reviewed closeout: shared-token-1.'
    )
    expect(result.current.completionEvidenceInput).toContain('Queue status reviewed at ')
  })

  it('drafts completion write-back details from the watchdog closeout receipt when available', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockResolvedValue({
      queue_path: '.agent/jobs/overnight-queue.json',
      queue_sha256: 'queue-sha-77',
      exists: true,
      job_count: 3,
      updated_at: '2026-03-19T12:00:00.000Z',
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt.mockResolvedValue({
      exists: true,
      queue_job_id: 'overnight-lane-control-plane-sharedto',
      mission_id: 'runtime-mission-control-plane-sharedto',
      producer_key: 'openclaw-runtime',
      source_lane_id: 'control-plane',
      source_board_concurrency_token: 'shared-token-1',
      runtime_profile_id: 'bijmantra-bca-local-verify',
      runtime_policy_sha256: 'policy-sha-1234',
      closeout_status: 'passed',
      state_refresh_required: true,
      receipt_recorded_at: '2026-03-19T12:05:00.000Z',
      started_at: '2026-03-19T12:03:00.000Z',
      finished_at: '2026-03-19T12:04:00.000Z',
      verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
      queue_sha256_at_closeout: 'queue-sha-closeout-77',
      closeout_commands: [],
      artifacts: [
        {
          path: 'metrics.json',
          exists: true,
          sha256: 'abc123',
          modified_at: '2026-03-19T12:04:30.000Z',
        },
      ],
    })
    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockResolvedValue(
      createPreparedCompletionWriteResponse(
        { draft_source: 'stable-closeout-receipt' },
        {
          closure_summary:
            'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.',
          evidence: [
            'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.',
            'Watchdog closeout queue hash: queue-sha-closeout-77.',
            'Board token used for reviewed closeout: shared-token-1.',
            'Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.',
            'Verification evidence referenced by closeout receipt: runtime-artifacts/mission-evidence/job/verification_1.json.',
            'Closeout artifact refreshed: metrics.json.',
            'Stable closeout receipt recorded at 2026-03-19T12:05:00.000Z.',
          ],
          closeout_receipt: {
            queue_job_id: 'overnight-lane-control-plane-sharedto',
            artifact_paths: ['metrics.json'],
            mission_id: 'runtime-mission-control-plane-sharedto',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'shared-token-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-1234',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-19T12:05:00.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-closeout-77',
          },
        },
        {
          exists: true,
          queue_job_id: 'overnight-lane-control-plane-sharedto',
          mission_id: 'runtime-mission-control-plane-sharedto',
          producer_key: 'openclaw-runtime',
          source_lane_id: 'control-plane',
          source_board_concurrency_token: 'shared-token-1',
          runtime_profile_id: 'bijmantra-bca-local-verify',
          runtime_policy_sha256: 'policy-sha-1234',
          closeout_status: 'passed',
          state_refresh_required: true,
          receipt_recorded_at: '2026-03-19T12:05:00.000Z',
          started_at: '2026-03-19T12:03:00.000Z',
          finished_at: '2026-03-19T12:04:00.000Z',
          verification_evidence_ref:
            'runtime-artifacts/mission-evidence/job/verification_1.json',
          queue_sha256_at_closeout: 'queue-sha-closeout-77',
          closeout_commands: [],
          artifacts: [
            {
              path: 'metrics.json',
              exists: true,
              sha256: 'abc123',
              modified_at: '2026-03-19T12:04:30.000Z',
            },
          ],
        },
        {
          queue_sha256: 'queue-sha-77',
          updated_at: '2026-03-19T12:00:00.000Z',
          job_count: 3,
        }
      )
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.refreshQueueStatus()
    })

    expect(result.current.closeoutReceiptState).toBe('available')
    expect(result.current.closeoutReceiptRecord?.closeout_status).toBe('passed')

    await act(async () => {
      await result.current.handleDraftLaneCompletionFromCurrentState()
    })

    expect(result.current.completionClosureSummary).toBe(
      'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Watchdog closeout queue hash: queue-sha-closeout-77.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Verification evidence referenced by closeout receipt: runtime-artifacts/mission-evidence/job/verification_1.json.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Closeout artifact refreshed: metrics.json.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Stable closeout receipt recorded at 2026-03-19T12:05:00.000Z.'
    )
  })

  it('focuses a requested lane and drafts completion write-back from its closeout candidate evidence', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockResolvedValue({
      queue_path: '.agent/jobs/overnight-queue.json',
      queue_sha256: 'queue-sha-77',
      exists: true,
      job_count: 3,
      updated_at: '2026-03-19T12:00:00.000Z',
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt.mockImplementation(
      async (queueJobId: string) => {
        if (queueJobId === createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1')) {
          return {
            exists: true,
            queue_job_id: queueJobId,
            mission_id: 'runtime-mission-platform-runtime-sharedto',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'platform-runtime',
            source_board_concurrency_token: 'shared-token-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-5678',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-19T13:05:00.000Z',
            started_at: '2026-03-19T13:03:00.000Z',
            finished_at: '2026-03-19T13:04:00.000Z',
            verification_evidence_ref:
              'runtime-artifacts/mission-evidence/platform-runtime/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-closeout-99',
            closeout_commands: [],
            artifacts: [
              {
                path: 'metrics.json',
                exists: true,
                sha256: 'abc123',
                modified_at: '2026-03-19T13:04:30.000Z',
              },
            ],
          }
        }

        return {
          exists: false,
          queue_job_id: queueJobId,
          closeout_status: null,
          state_refresh_required: null,
          receipt_recorded_at: null,
          started_at: null,
          finished_at: null,
          verification_evidence_ref: null,
          queue_sha256_at_closeout: null,
          closeout_commands: [],
          artifacts: [],
        }
      }
    )
    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockImplementation(
      async ({ source_lane_id }: { source_lane_id: string }) => {
        if (source_lane_id === 'platform-runtime') {
          return createPreparedCompletionWriteResponse(
            {
              source_lane_id: 'platform-runtime',
              queue_job_id: createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1'),
              draft_source: 'stable-closeout-receipt',
            },
            {
              source_lane_id: 'platform-runtime',
              queue_job_id: createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1'),
              closure_summary:
                'Reviewed platform-runtime closeout receipt (passed) after watchdog completion and canonical queue refresh.',
              evidence: [
                `Reviewed queue job ${createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1')} using watchdog closeout receipt before explicit board write-back.`,
                'Watchdog closeout queue hash: queue-sha-closeout-99.',
                'Board token used for reviewed closeout: shared-token-1.',
                'Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.',
                'Verification evidence referenced by closeout receipt: runtime-artifacts/mission-evidence/platform-runtime/verification_1.json.',
                'Closeout artifact refreshed: metrics.json.',
                'Stable closeout receipt recorded at 2026-03-19T13:05:00.000Z.',
              ],
              closeout_receipt: {
                queue_job_id: createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1'),
                artifact_paths: ['metrics.json'],
                mission_id: 'runtime-mission-platform-runtime-sharedto',
                producer_key: 'openclaw-runtime',
                source_lane_id: 'platform-runtime',
                source_board_concurrency_token: 'shared-token-1',
                runtime_profile_id: 'bijmantra-bca-local-verify',
                runtime_policy_sha256: 'policy-sha-5678',
                closeout_status: 'passed',
                state_refresh_required: true,
                receipt_recorded_at: '2026-03-19T13:05:00.000Z',
                verification_evidence_ref:
                  'runtime-artifacts/mission-evidence/platform-runtime/verification_1.json',
                queue_sha256_at_closeout: 'queue-sha-closeout-99',
              },
            },
            {
              exists: true,
              queue_job_id: createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1'),
              mission_id: 'runtime-mission-platform-runtime-sharedto',
              producer_key: 'openclaw-runtime',
              source_lane_id: 'platform-runtime',
              source_board_concurrency_token: 'shared-token-1',
              runtime_profile_id: 'bijmantra-bca-local-verify',
              runtime_policy_sha256: 'policy-sha-5678',
              closeout_status: 'passed',
              state_refresh_required: true,
              receipt_recorded_at: '2026-03-19T13:05:00.000Z',
              started_at: '2026-03-19T13:03:00.000Z',
              finished_at: '2026-03-19T13:04:00.000Z',
              verification_evidence_ref:
                'runtime-artifacts/mission-evidence/platform-runtime/verification_1.json',
              queue_sha256_at_closeout: 'queue-sha-closeout-99',
              closeout_commands: [],
              artifacts: [
                {
                  path: 'metrics.json',
                  exists: true,
                  sha256: 'abc123',
                  modified_at: '2026-03-19T13:04:30.000Z',
                },
              ],
            },
            {
              queue_sha256: 'queue-sha-77',
              updated_at: '2026-03-19T12:00:00.000Z',
              job_count: 3,
            }
          )
        }

        return createPreparedCompletionWriteResponse()
      }
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.handleDraftLaneCompletionForLane('platform-runtime')
    })

    await waitFor(() => {
      expect(result.current.selectedLane?.id).toBe('platform-runtime')
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt).toHaveBeenCalledWith(
      createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1')
    )
    expect(result.current.completionClosureSummary).toBe(
      'Reviewed platform-runtime closeout receipt (passed) after watchdog completion and canonical queue refresh.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Reviewed queue job overnight-lane-platform-runtime-sharedto using watchdog closeout receipt before explicit board write-back.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.'
    )
  })

  it('hydrates completion draft state directly from an embedded runtime preparation packet', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })

    const embeddedPreparation: DeveloperControlPlaneCompletionWritePreparationResponse =
      createPreparedCompletionWriteResponse(
        { draft_source: 'stable-closeout-receipt' },
        {
          closure_summary:
            'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.',
          evidence: [
            'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.',
            'Watchdog closeout queue hash: queue-sha-closeout-77.',
            'Board token used for reviewed closeout: shared-token-1.',
            'Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.',
            'Verification evidence referenced by closeout receipt: runtime-artifacts/mission-evidence/job/verification_1.json.',
            'Closeout artifact refreshed: metrics.json.',
            'Stable closeout receipt recorded at 2026-03-19T12:05:00.000Z.',
          ],
          closeout_receipt: {
            queue_job_id: 'overnight-lane-control-plane-sharedto',
            artifact_paths: ['metrics.json'],
            mission_id: 'runtime-mission-control-plane-sharedto',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'shared-token-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-1234',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-19T12:05:00.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-closeout-77',
          },
        },
        {
          exists: true,
          queue_job_id: 'overnight-lane-control-plane-sharedto',
          mission_id: 'runtime-mission-control-plane-sharedto',
          producer_key: 'openclaw-runtime',
          source_lane_id: 'control-plane',
          source_board_concurrency_token: 'shared-token-1',
          runtime_profile_id: 'bijmantra-bca-local-verify',
          runtime_policy_sha256: 'policy-sha-1234',
          closeout_status: 'passed',
          state_refresh_required: true,
          receipt_recorded_at: '2026-03-19T12:05:00.000Z',
          started_at: '2026-03-19T12:03:00.000Z',
          finished_at: '2026-03-19T12:04:00.000Z',
          verification_evidence_ref:
            'runtime-artifacts/mission-evidence/job/verification_1.json',
          queue_sha256_at_closeout: 'queue-sha-closeout-77',
          closeout_commands: [],
          artifacts: [
            {
              path: 'metrics.json',
              exists: true,
              sha256: 'abc123',
              modified_at: '2026-03-19T12:04:30.000Z',
            },
          ],
        },
        {
          queue_sha256: 'queue-sha-77',
          updated_at: '2026-03-19T12:00:00.000Z',
          job_count: 3,
        }
      )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockClear()

    await act(async () => {
      await result.current.handleDraftLaneCompletionForLane('control-plane', embeddedPreparation)
    })

    expect(activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite).not.toHaveBeenCalled()
    expect(result.current.closeoutReceiptState).toBe('available')
    expect(result.current.queueStatusRecord?.queue_sha256).toBe('queue-sha-77')
    expect(result.current.completionClosureSummary).toBe(
      'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.'
    )
  })

  it('reuses an embedded runtime preparation packet when drafting from the current selected lane state', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })

    const embeddedPreparation: DeveloperControlPlaneCompletionWritePreparationResponse =
      createPreparedCompletionWriteResponse(
        { draft_source: 'stable-closeout-receipt' },
        {
          closure_summary:
            'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.',
          evidence: [
            'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.',
            'Watchdog closeout queue hash: queue-sha-closeout-77.',
            'Board token used for reviewed closeout: shared-token-1.',
            'Runtime profile recorded by closeout receipt: bijmantra-bca-local-verify.',
            'Verification evidence referenced by closeout receipt: runtime-artifacts/mission-evidence/job/verification_1.json.',
            'Closeout artifact refreshed: metrics.json.',
            'Stable closeout receipt recorded at 2026-03-19T12:05:00.000Z.',
          ],
          closeout_receipt: {
            queue_job_id: 'overnight-lane-control-plane-sharedto',
            artifact_paths: ['metrics.json'],
            mission_id: 'runtime-mission-control-plane-sharedto',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'shared-token-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-1234',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-19T12:05:00.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/job/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-closeout-77',
          },
        },
        {
          exists: true,
          queue_job_id: 'overnight-lane-control-plane-sharedto',
          mission_id: 'runtime-mission-control-plane-sharedto',
          producer_key: 'openclaw-runtime',
          source_lane_id: 'control-plane',
          source_board_concurrency_token: 'shared-token-1',
          runtime_profile_id: 'bijmantra-bca-local-verify',
          runtime_policy_sha256: 'policy-sha-1234',
          closeout_status: 'passed',
          state_refresh_required: true,
          receipt_recorded_at: '2026-03-19T12:05:00.000Z',
          started_at: '2026-03-19T12:03:00.000Z',
          finished_at: '2026-03-19T12:04:00.000Z',
          verification_evidence_ref:
            'runtime-artifacts/mission-evidence/job/verification_1.json',
          queue_sha256_at_closeout: 'queue-sha-closeout-77',
          closeout_commands: [],
          artifacts: [
            {
              path: 'metrics.json',
              exists: true,
              sha256: 'abc123',
              modified_at: '2026-03-19T12:04:30.000Z',
            },
          ],
        },
        {
          queue_sha256: 'queue-sha-77',
          updated_at: '2026-03-19T12:00:00.000Z',
          job_count: 3,
        }
      )

    activeBoardApiMocks.fetchDeveloperControlPlaneAutonomyCycle.mockResolvedValue({
      exists: true,
      artifact_path:
        '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
      generated_at: '2026-04-05T11:10:24.399975+00:00',
      queue_path: '.agent/jobs/overnight-queue.json',
      window: 'nightly',
      max_jobs_per_run: 2,
      status_counts: { completed: 1 },
      selected_job_count: 0,
      blocked_job_count: 0,
      closeout_candidate_count: 1,
      next_action_count: 1,
      next_action_ordering_source: 'artifact',
      watchdog: {
        exists: true,
        state_path: 'runtime-artifacts/watchdog-state.json',
        last_check: '2026-04-05T10:00:00Z',
        gateway_healthy: true,
        state_is_stale: false,
        total_alerts: 0,
        job_errors: {},
      },
      selected_jobs: [],
      blocked_jobs: [],
      closeout_candidates: [],
      next_actions: [
        {
          action: 'prepare-completion-write-back',
          job_id: 'overnight-lane-control-plane-sharedto',
          title: 'Runtime Job',
          source_lane_id: 'control-plane',
          reason: 'stable closeout ready for explicit board write-back',
          primary_agent: null,
          priority: null,
          mission_id: 'runtime-mission-control-plane-sharedto',
          receipt_path: 'runtime-artifacts/mission-evidence/job/closeout.json',
          state_path: null,
          detail: {
            queueStatus: 'completed',
            closeoutStatus: 'passed',
            verificationEvidenceRef:
              'runtime-artifacts/mission-evidence/job/verification_1.json',
            completionWritePreparation: embeddedPreparation,
          },
        },
      ],
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.refreshQueueStatus()
    })

    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockClear()

    await act(async () => {
      await result.current.handleDraftLaneCompletionFromCurrentState()
    })

    expect(activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite).not.toHaveBeenCalled()
    expect(result.current.runtimeAutonomyCycleRecord?.next_actions[0]?.action).toBe(
      'prepare-completion-write-back'
    )
    expect(result.current.closeoutReceiptState).toBe('available')
    expect(result.current.queueStatusRecord?.queue_sha256).toBe('queue-sha-77')
    expect(result.current.completionClosureSummary).toBe(
      'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.'
    )
  })

  it('falls back to the staged completion-assist packet when the autonomy-cycle artifact has no embedded preparation', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })

    activeBoardApiMocks.fetchDeveloperControlPlaneAutonomyCycle.mockResolvedValue({
      exists: true,
      artifact_path:
        '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
      generated_at: '2026-04-05T11:10:24.399975+00:00',
      queue_path: '.agent/jobs/overnight-queue.json',
      window: 'nightly',
      max_jobs_per_run: 2,
      status_counts: { completed: 1 },
      selected_job_count: 0,
      blocked_job_count: 0,
      closeout_candidate_count: 0,
      next_action_count: 0,
      next_action_ordering_source: 'artifact',
      watchdog: {
        exists: true,
        state_path: 'runtime-artifacts/watchdog-state.json',
        last_check: '2026-04-05T10:00:00Z',
        gateway_healthy: true,
        state_is_stale: false,
        total_alerts: 0,
        job_errors: {},
      },
      selected_jobs: [],
      blocked_jobs: [],
      closeout_candidates: [],
      next_actions: [],
      first_actionable_completion_write: null,
    })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.refreshQueueStatus()
    })

    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockClear()

    await act(async () => {
      await result.current.handleDraftLaneCompletionFromCurrentState()
    })

    expect(activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite).not.toHaveBeenCalled()
    expect(result.current.runtimeAutonomyCycleRecord?.next_action_count).toBe(0)
    expect(result.current.runtimeCompletionAssistRecord?.status).toBe('staged')
    expect(
      result.current.runtimeCompletionAssistRecord?.actionable_completion_write?.sourceLaneId
    ).toBe('control-plane')
    expect(result.current.queueStatusRecord?.queue_sha256).toBe('queue-sha-1')
    expect(result.current.closeoutReceiptState).toBe('available')
    expect(result.current.completionClosureSummary).toBe(
      'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Reviewed queue job overnight-lane-control-plane-sharedto using watchdog closeout receipt before explicit board write-back.'
    )
  })

  it('falls back to the current queue snapshot when closeout receipt fetch fails', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus.mockResolvedValue({
      queue_path: '.agent/jobs/overnight-queue.json',
      queue_sha256: 'queue-sha-77',
      exists: true,
      job_count: 3,
      updated_at: '2026-03-19T12:00:00.000Z',
    })
    activeBoardApiMocks.fetchDeveloperControlPlaneCloseoutReceipt.mockRejectedValue(
      new Error('receipt unavailable')
    )
    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite.mockResolvedValue(
      createPreparedCompletionWriteResponse(
        {},
        {
          closure_summary:
            'Reviewed closeout for lane control-plane after queue completion and canonical queue refresh.',
          evidence: [
            'Reviewed queue job overnight-lane-control-plane-sharedto before explicit board write-back.',
            'Queue snapshot hash at reviewed closeout: queue-sha-77.',
            'Board token used for reviewed closeout: shared-token-1.',
            'Queue status reviewed at 2026-03-19T12:00:00.000Z.',
          ],
        },
        {},
        {
          queue_sha256: 'queue-sha-77',
          updated_at: '2026-03-19T12:00:00.000Z',
          job_count: 3,
        }
      )
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    await act(async () => {
      await result.current.refreshQueueStatus()
    })

    expect(result.current.queueStatusState).toBe('ready')
    expect(result.current.closeoutReceiptState).toBe('error')
    expect(result.current.closeoutReceiptError).toBe('receipt unavailable')

    await act(async () => {
      await result.current.handleDraftLaneCompletionFromCurrentState()
    })

    expect(result.current.completionClosureSummary).toBe(
      'Reviewed closeout for lane control-plane after queue completion and canonical queue refresh.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Reviewed queue job overnight-lane-control-plane-sharedto before explicit board write-back.'
    )
    expect(result.current.completionEvidenceInput).toContain(
      'Queue snapshot hash at reviewed closeout: queue-sha-77.'
    )
  })

  it('surfaces completion write conflict remediation for stale board tokens', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard.mockResolvedValue({
      exists: true,
      record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
        concurrency_token: 'shared-token-1',
      }),
    })
    activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion.mockRejectedValue(
      new ApiError(
        'HTTP 409',
        ApiErrorType.CONFLICT,
        409,
        {
          detail: {
            detail: 'Completion write-back conflict; source board token is stale and must be refreshed',
            conflict_reason: 'stale-board-token',
            remediation_message:
              'Refresh the shared board state, confirm the lane is still the intended completion target, then retry with the current board token.',
            refresh_targets: ['active-board'],
            retry_permitted_after_refresh: true,
            current_board_concurrency_token: 'shared-token-2',
          },
        } as any,
        { statusCode: 409 }
      )
    )
    activeBoardApiMocks.isDeveloperControlPlaneConflictError.mockReturnValue(true)
    activeBoardApiMocks.getDeveloperControlPlaneCompletionConflictDetail.mockReturnValue({
      detail: 'Completion write-back conflict; source board token is stale and must be refreshed',
      conflict_reason: 'stale-board-token',
      remediation_message:
        'Refresh the shared board state, confirm the lane is still the intended completion target, then retry with the current board token.',
      refresh_targets: ['active-board'],
      retry_permitted_after_refresh: true,
      current_board_concurrency_token: 'shared-token-2',
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Completion write-back conflict; source board token is stale and must be refreshed'
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.setCompletionClosureSummary('Completion evidence was reviewed and accepted.')
      result.current.setCompletionEvidenceInput('Focused tests passed\nQueue job completed')
    })

    await act(async () => {
      await result.current.handleWriteLaneCompletion()
    })

    expect(result.current.completionWriteState).toBe('conflict')
    expect(result.current.lastCompletionWriteResult).toMatchObject({
      status: 'conflict',
      conflictReason: 'stale-board-token',
      currentBoardConcurrencyToken: 'shared-token-2',
      remediationMessage:
        'Refresh the shared board state, confirm the lane is still the intended completion target, then retry with the current board token.',
      refreshTargets: ['active-board'],
      retryPermittedAfterRefresh: true,
    })
  })

  it('refreshes and retries completion write-back with the latest shared board token when retry is permitted', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-1',
        }),
      })
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-2',
        }),
      })
    activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion
      .mockRejectedValueOnce(
        new ApiError(
          'HTTP 409',
          ApiErrorType.CONFLICT,
          409,
          {
            detail: {
              detail:
                'Completion write-back conflict; source board token is stale and must be refreshed',
              conflict_reason: 'stale-board-token',
              remediation_message:
                'Refresh the shared board state and queue snapshot, confirm runtime evidence still matches, then retry completion write-back with the current board token.',
              refresh_targets: ['active-board', 'overnight-queue'],
              retry_permitted_after_refresh: true,
              current_board_concurrency_token: 'shared-token-2',
              current_queue_sha256: 'queue-sha-2',
              current_lane_status: 'active',
            },
          } as any,
          { statusCode: 409 }
        )
      )
      .mockResolvedValueOnce({
        no_op: false,
        lane_id: 'control-plane',
        lane_status: 'completed',
        queue_job_id: createDeveloperLaneQueueJobId('control-plane', 'shared-token-2'),
        queue_sha256: 'queue-sha-2',
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-2',
        }),
      })
    activeBoardApiMocks.isDeveloperControlPlaneConflictError.mockReturnValue(true)
    activeBoardApiMocks.getDeveloperControlPlaneCompletionConflictDetail.mockReturnValue({
      detail:
        'Completion write-back conflict; source board token is stale and must be refreshed',
      conflict_reason: 'stale-board-token',
      remediation_message:
        'Refresh the shared board state and queue snapshot, confirm runtime evidence still matches, then retry completion write-back with the current board token.',
      refresh_targets: ['active-board', 'overnight-queue'],
      retry_permitted_after_refresh: true,
      current_board_concurrency_token: 'shared-token-2',
      current_queue_sha256: 'queue-sha-2',
      current_lane_status: 'active',
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Completion write-back conflict; source board token is stale and must be refreshed'
    )
    activeBoardApiMocks.prepareDeveloperControlPlaneLaneCompletionWrite
      .mockResolvedValueOnce(
        createPreparedCompletionWriteResponse(
          {},
          {},
          {},
          {
            queue_sha256: 'queue-sha-1',
            updated_at: '2026-03-18T11:30:00.000Z',
            job_count: 2,
          }
        )
      )
      .mockResolvedValueOnce(
        (() => {
          const prepared = createPreparedCompletionWriteResponse(
            {
              queue_job_id: createDeveloperLaneQueueJobId('control-plane', 'shared-token-2'),
            },
            {
              queue_job_id: createDeveloperLaneQueueJobId('control-plane', 'shared-token-2'),
            },
            {},
            {
              queue_sha256: 'queue-sha-2',
              updated_at: '2026-03-18T11:31:00.000Z',
              job_count: 3,
            }
          )

          return {
            ...prepared,
            prepared_request: {
              ...prepared.prepared_request,
              source_board_concurrency_token: 'shared-token-2',
              expected_queue_sha256: 'queue-sha-2',
              completion: {
                ...prepared.prepared_request.completion,
                queue_job_id: createDeveloperLaneQueueJobId('control-plane', 'shared-token-2'),
              },
            },
          }
        })()
      )
    activeBoardApiMocks.fetchDeveloperControlPlaneOvernightQueueStatus
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        exists: true,
        job_count: 2,
        updated_at: '2026-03-18T11:30:00.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-1',
        exists: true,
        job_count: 2,
        updated_at: '2026-03-18T11:30:15.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-2',
        exists: true,
        job_count: 3,
        updated_at: '2026-03-18T11:31:00.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-2',
        exists: true,
        job_count: 3,
        updated_at: '2026-03-18T11:31:15.000Z',
      })
      .mockResolvedValueOnce({
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-2',
        exists: true,
        job_count: 3,
        updated_at: '2026-03-18T11:31:30.000Z',
      })

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.setCompletionClosureSummary('Completion evidence was reviewed and accepted.')
      result.current.setCompletionEvidenceInput('Focused tests passed\nQueue job completed')
    })

    await act(async () => {
      await result.current.handleWriteLaneCompletion()
    })

    expect(result.current.completionWriteState).toBe('conflict')

    await act(async () => {
      await result.current.handleRefreshAndRetryLaneCompletion()
    })

    expect(activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion).toHaveBeenLastCalledWith(
      expect.objectContaining({
        source_board_concurrency_token: 'shared-token-2',
        completion: expect.objectContaining({
          queue_job_id: createDeveloperLaneQueueJobId('control-plane', 'shared-token-2'),
        }),
      })
    )
    expect(result.current.completionWriteState).toBe('written')
    expect(result.current.lastCompletionWriteResult).toMatchObject({
      status: 'written',
      currentBoardConcurrencyToken: 'shared-token-2',
    })
  })

  it('does not retry completion write-back when active-board refresh fails', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneActiveBoard
      .mockResolvedValueOnce({
        exists: true,
        record: createActiveBoardRecord(createDefaultDeveloperMasterBoardJson(), {
          concurrency_token: 'shared-token-1',
        }),
      })
      .mockRejectedValueOnce(new Error('backend unavailable'))

    activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion.mockRejectedValueOnce(
      new ApiError(
        'HTTP 409',
        ApiErrorType.CONFLICT,
        409,
        {
          details: {
            detail:
              'Completion write-back conflict; source board token is stale and must be refreshed',
            conflict_reason: 'stale-board-token',
            remediation_message:
              'Refresh the shared board state, confirm the lane is still the intended completion target, then retry with the current board token.',
            refresh_targets: ['active-board'],
            retry_permitted_after_refresh: true,
            current_board_concurrency_token: 'shared-token-2',
          },
        },
        { statusCode: 409 }
      )
    )
    activeBoardApiMocks.isDeveloperControlPlaneConflictError.mockReturnValue(true)
    activeBoardApiMocks.getDeveloperControlPlaneCompletionConflictDetail.mockReturnValue({
      conflict_reason: 'stale-board-token',
      remediation_message:
        'Refresh the shared board state, confirm the lane is still the intended completion target, then retry with the current board token.',
      refresh_targets: ['active-board'],
      retry_permitted_after_refresh: true,
      current_board_concurrency_token: 'shared-token-2',
    })
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Completion write-back conflict; source board token is stale and must be refreshed'
    )

    const { result } = renderHook(() => useControlPlaneController())

    await waitFor(() => {
      expect(result.current.persistenceStatus.label).toBe('Shared backend persistence active')
    })

    act(() => {
      result.current.setCompletionClosureSummary('Completion evidence was reviewed and accepted.')
      result.current.setCompletionEvidenceInput('Focused tests passed\nQueue job completed')
    })

    await act(async () => {
      await result.current.handleWriteLaneCompletion()
    })

    expect(result.current.completionWriteState).toBe('conflict')

    await act(async () => {
      await result.current.handleRefreshAndRetryLaneCompletion()
    })

    expect(activeBoardApiMocks.writeDeveloperControlPlaneLaneCompletion).toHaveBeenCalledTimes(1)
    expect(result.current.completionWriteState).toBe('conflict')
  })
})

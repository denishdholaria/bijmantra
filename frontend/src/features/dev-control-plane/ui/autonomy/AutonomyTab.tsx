import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TabsContent } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

import type { DeveloperBoardLane } from '../../contracts/board'
import type {
  DeveloperBoardAutonomyAnalysis,
  DeveloperLaneAutonomyAnalysis,
  DeveloperLaneReadiness,
} from '../../contracts/autonomy'
import type {
  DeveloperLaneDispatchPacket,
  DeveloperLaneQueueCandidate,
  DeveloperLaneQueueEntry,
} from '../../contracts/dispatch'
import type {
  DeveloperControlPlaneAutonomyCycleResponse,
  DeveloperControlPlaneCloseoutReceiptResponse,
  DeveloperControlPlaneCompletionWritePreparationResponse,
  DeveloperControlPlaneConflictRefreshTarget,
  DeveloperControlPlaneMissionStateResponse,
  DeveloperControlPlaneOvernightQueueStatusResponse,
  DeveloperControlPlaneRuntimeCompletionAssistResponse,
  DeveloperControlPlaneWatchdogJob,
  DeveloperControlPlaneWatchdogStatusResponse,
} from '../../api/activeBoard'
import { AutonomyCycleCard } from './AutonomyCycleCard'
import { CompletionAssistCard } from './CompletionAssistCard'
import { DecisionMemoryCard } from './DecisionMemoryCard'
import {
  buildReviewedDispatchPilotChecks,
  countBlockingReviewedDispatchPilotChecks,
  hasReviewedCompletionVerificationEvidence,
  hasReviewedDispatchReviewGates,
  type ReviewedDispatchPilotCheck,
} from '../../reviewedDispatch'
import type { DeveloperControlPlanePersistenceStatus } from '../../state/selectors'
import { getSelectedLaneMissionSummary } from '../missionLinking'
import { useDecisionMemory } from './useDecisionMemory'

type QueueWriteResult = {
  status: 'written' | 'conflict' | 'error'
  message: string
  writtenJobId: string | null
  previousQueueSha256: string | null
  currentQueueSha256: string | null
  queueUpdatedAt: string | null
  approvalReceiptId?: number | null
  approvalReceiptRecordedAt?: string | null
  conflictReason: string | null
  remediationMessage: string | null
  refreshTargets: DeveloperControlPlaneConflictRefreshTarget[]
  retryPermittedAfterRefresh: boolean | null
  currentBoardConcurrencyToken: string | null
  conflictJobId: string | null
}

type CompletionWriteResult = {
  status: 'written' | 'conflict' | 'error'
  message: string
  noOp: boolean
  laneId: string | null
  laneStatus: string | null
  queueJobId: string | null
  queueSha256: string | null
  approvalReceiptId?: number | null
  approvalReceiptRecordedAt?: string | null
  conflictReason: string | null
  remediationMessage: string | null
  refreshTargets: DeveloperControlPlaneConflictRefreshTarget[]
  retryPermittedAfterRefresh: boolean | null
  currentBoardConcurrencyToken: string | null
  currentQueueSha256: string | null
  currentLaneStatus: string | null
  nextRecommendedLaneId?: string | null
  nextRecommendedLaneTitle?: string | null
}

type NextRecommendedLaneQueueGuidance = {
  tone: 'pending' | 'ready'
  message: string
  refreshQueueStatusRecommended?: boolean
  refreshTargetsRecommended?: DeveloperControlPlaneConflictRefreshTarget[]
}

type AutonomyTabProps = {
  jsonError: string | null
  autonomyAnalysis: DeveloperBoardAutonomyAnalysis | null
  persistenceStatus: DeveloperControlPlanePersistenceStatus
  recommendedLane: DeveloperBoardLane | null
  selectedLane: DeveloperBoardLane | null
  selectedLaneAnalysis: DeveloperLaneAutonomyAnalysis | null
  dispatchPacket: DeveloperLaneDispatchPacket | null
  queueCandidate: DeveloperLaneQueueCandidate | null
  queueEntry: DeveloperLaneQueueEntry | null
  unresolvedQueueDependencyLaneIds: string[]
  selectedLaneQueueJobId: string | null
  queueWriteState: 'idle' | 'writing' | 'written' | 'conflict' | 'error'
  completionWriteState: 'idle' | 'writing' | 'written' | 'conflict' | 'error'
  queueStatusState: 'idle' | 'loading' | 'ready' | 'error'
  queueStatusRecord: DeveloperControlPlaneOvernightQueueStatusResponse | null
  queueStatusError: string | null
  queueStatusLastRefreshedAt: string | null
  closeoutReceiptState: 'idle' | 'loading' | 'available' | 'missing' | 'error'
  closeoutReceiptRecord: DeveloperControlPlaneCloseoutReceiptResponse | null
  closeoutReceiptError: string | null
  closeoutReceiptLastCheckedAt: string | null
  missionStateState?: 'idle' | 'loading' | 'ready' | 'error'
  missionStateRecord?: DeveloperControlPlaneMissionStateResponse | null
  runtimeWatchdogState?: 'idle' | 'loading' | 'ready' | 'error'
  runtimeWatchdogRecord?: DeveloperControlPlaneWatchdogStatusResponse | null
  runtimeWatchdogError?: string | null
  runtimeWatchdogLastCheckedAt?: string | null
  runtimeAutonomyCycleState?: 'idle' | 'loading' | 'ready' | 'missing' | 'error'
  runtimeAutonomyCycleRecord?: DeveloperControlPlaneAutonomyCycleResponse | null
  runtimeAutonomyCycleError?: string | null
  runtimeAutonomyCycleLastCheckedAt?: string | null
  runtimeCompletionAssistState?: 'idle' | 'loading' | 'ready' | 'missing' | 'error'
  runtimeCompletionAssistRecord?: DeveloperControlPlaneRuntimeCompletionAssistResponse | null
  runtimeCompletionAssistError?: string | null
  runtimeCompletionAssistLastCheckedAt?: string | null
  lastQueueWriteResult: QueueWriteResult | null
  completionClosureSummary: string
  completionEvidenceInput: string
  lastCompletionWriteResult: CompletionWriteResult | null
  onSelectLane: (laneId: string) => void
  onPromoteLane: (laneId: string) => void
  onCopyDispatchPacket: () => Promise<void> | void
  onCopyQueueCandidate: () => Promise<void> | void
  onCopyQueueEntry: () => Promise<void> | void
  onRefreshQueueStatus: () => Promise<unknown> | void
  onRefreshRecommendedTargets?: (
    targets: DeveloperControlPlaneConflictRefreshTarget[]
  ) => Promise<unknown> | void
  onRefreshAndRetryQueueWrite?: () => Promise<unknown> | void
  onRefreshAndRetryLaneCompletion?: () => Promise<unknown> | void
  onCompletionClosureSummaryChange: (value: string) => void
  onCompletionEvidenceInputChange: (value: string) => void
  onDraftLaneCompletionFromCurrentState: () => void
  onDraftLaneCompletionForLane?: (
    laneId: string,
    prepared?: DeveloperControlPlaneCompletionWritePreparationResponse | null
  ) => Promise<void> | void
  onWriteLaneCompletion: () => Promise<void> | void
  onWriteQueueEntry: () => Promise<void> | void
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return 'Not available'
  }

  return new Date(value).toLocaleString()
}

function formatRefreshTarget(target: DeveloperControlPlaneConflictRefreshTarget) {
  if (target === 'active-board') {
    return 'Active board'
  }

  if (target === 'overnight-queue') {
    return 'Overnight queue'
  }

  if (target === 'closeout-receipt') {
    return 'Closeout receipt'
  }

  return target
}

function readinessTone(readiness: DeveloperLaneReadiness) {
  return readiness === 'ready'
    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    : readiness === 'completed'
      ? 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
    : readiness === 'watch'
      ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
      : 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
}

function warningTone(severity: 'blocking' | 'advisory') {
  return severity === 'blocking'
    ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
    : 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
}

function statusTone(status: DeveloperBoardLane['status']) {
  return status === 'active'
    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    : status === 'watch'
      ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
      : status === 'blocked'
        ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
        : 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function closeoutReceiptTone(state: AutonomyTabProps['closeoutReceiptState']) {
  return state === 'available'
    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    : state === 'missing'
      ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
      : state === 'error'
        ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
        : state === 'loading'
          ? 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
          : 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function closeoutReceiptDescription(
  state: AutonomyTabProps['closeoutReceiptState'],
  queueJobId: string | null
) {
  if (state === 'available') {
    return 'Stable closeout receipt found. Draft closeout will prefer watchdog evidence for this queue job.'
  }

  if (state === 'missing') {
    return 'No stable closeout receipt is present yet. Draft closeout will fall back to the refreshed queue snapshot.'
  }

  if (state === 'error') {
    return 'Closeout receipt lookup failed. Draft closeout will retry receipt fetch and otherwise fall back to the refreshed queue snapshot.'
  }

  if (state === 'loading') {
    return 'Checking whether runtime produced a stable closeout receipt for the selected queue job.'
  }

  if (!queueJobId) {
    return 'Select a lane with a shared board token to derive the deterministic queue job id.'
  }

  return 'Refresh queue status to check whether runtime already published a stable closeout receipt for this queue job.'
}

function runtimeWatchdogTone(
  state: NonNullable<AutonomyTabProps['runtimeWatchdogState']>,
  mismatch: boolean,
  record: DeveloperControlPlaneWatchdogStatusResponse | null
) {
  if (mismatch) {
    return 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
  }

  if (state === 'ready' && record?.state_is_stale) {
    return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
  }

  if (state === 'ready' && record?.bootstrap_ready && record.gateway_healthy) {
    return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
  }

  if (state === 'ready') {
    return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
  }

  if (state === 'error') {
    return 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
  }

  if (state === 'loading') {
    return 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
  }

  return 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function findSelectedRuntimeWatchdogJob(
  record: DeveloperControlPlaneWatchdogStatusResponse | null,
  queueJobId: string | null
) {
  if (!record || !queueJobId) {
    return null
  }

  return record.jobs.find((job) => job.job_id === queueJobId) ?? null
}

function runtimeWatchdogDescription(
  state: NonNullable<AutonomyTabProps['runtimeWatchdogState']>,
  record: DeveloperControlPlaneWatchdogStatusResponse | null,
  queueJobId: string | null,
  selectedRuntimeJob: DeveloperControlPlaneWatchdogJob | null,
  closeoutReceiptState: AutonomyTabProps['closeoutReceiptState'],
  mismatch: boolean
) {
  if (mismatch) {
    return 'Watchdog marked the selected queue job completed and verified, but the stable closeout receipt is still missing. Treat runtime closeout as incomplete until mission evidence is written.'
  }

  if (state === 'error') {
    return 'Runtime watchdog state could not be loaded. Refresh queue status before trusting reviewed runtime state.'
  }

  if (state === 'loading') {
    return 'Refreshing live runtime watchdog state for the selected queue job.'
  }

  if (!queueJobId) {
    return 'Select a lane with a deterministic queue job id to cross-check runtime watchdog status.'
  }

  if (state === 'ready' && record && !record.bootstrap_ready) {
    return 'Runtime bootstrap is blocked because the auth store is missing. Seed runtime auth before expecting reviewed queue projection.'
  }

  if (state === 'ready' && record?.state_is_stale) {
    return 'Runtime watchdog state is stale. Refresh or rerun the watchdog before trusting gateway health or selected queue-job status.'
  }

  if (state === 'ready' && selectedRuntimeJob) {
    if (closeoutReceiptState === 'available') {
      return 'Runtime watchdog status and the stable closeout receipt are aligned for the selected queue job.'
    }

    return `Runtime watchdog is tracking the selected queue job with status ${selectedRuntimeJob.status ?? 'unknown'}.`
  }

  if (state === 'ready') {
    return 'No runtime watchdog job matches the selected queue job yet. Refresh after runtime starts writing watchdog state.'
  }

  return 'Refresh queue status to load the current runtime watchdog state.'
}

function runtimeWatchdogCompletionAssistSummary(
  advisory: DeveloperControlPlaneWatchdogStatusResponse['completion_assist_advisory']
) {
  if (!advisory) {
    return null
  }

  if (advisory.available && advisory.staged) {
    return advisory.source_lane_id
      ? `Completion assist advisory is staged for lane ${advisory.source_lane_id} and still needs explicit write-back review.`
      : 'Completion assist advisory is staged and still needs explicit write-back review.'
  }

  if (advisory.available) {
    return 'Completion assist advisory is present but not staged for write-back.'
  }

  return 'Completion assist advisory is currently idle.'
}

function pilotCheckTone(check: ReviewedDispatchPilotCheck) {
  if (check.passed) {
    return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
  }

  return check.blocking
    ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
    : 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
}

type TimelineStageState = 'complete' | 'active' | 'pending' | 'warning'

type TimelineStage = {
  id: string
  label: string
  state: TimelineStageState
  detail: string
}

function timelineStageTone(state: TimelineStageState) {
  return state === 'complete'
    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    : state === 'active'
      ? 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
      : state === 'warning'
        ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
        : 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function durableMissionTone(
  missionStateState: NonNullable<AutonomyTabProps['missionStateState']>,
  missionSnapshotReady: boolean,
  closurePending: boolean,
  receiptAvailable: boolean
) {
  if (missionSnapshotReady && closurePending) {
    return 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
  }

  if (missionSnapshotReady) {
    return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
  }

  if (missionStateState === 'error') {
    return 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
  }

  if (missionStateState === 'loading' || (receiptAvailable && missionStateState !== 'ready')) {
    return 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
  }

  if (receiptAvailable) {
    return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
  }

  return 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function buildAutonomyEvidenceTimeline(
  selectedLane: DeveloperBoardLane | null,
  selectedLaneQueueJobId: string | null,
  queueStatusState: AutonomyTabProps['queueStatusState'],
  queueStatusRecord: DeveloperControlPlaneOvernightQueueStatusResponse | null,
  runtimeWatchdogState: NonNullable<AutonomyTabProps['runtimeWatchdogState']>,
  runtimeWatchdogSnapshotStale: boolean,
  selectedRuntimeWatchdogJob: DeveloperControlPlaneWatchdogJob | null,
  closeoutReceiptState: AutonomyTabProps['closeoutReceiptState'],
  closeoutReceiptRecord: DeveloperControlPlaneCloseoutReceiptResponse | null,
  runtimeEvidenceMismatch: boolean,
  missionStateState: NonNullable<AutonomyTabProps['missionStateState']>,
  durableMissionSnapshot: ReturnType<typeof getSelectedLaneMissionSummary>
): TimelineStage[] {
  const boardStage: TimelineStage = !selectedLane
    ? {
        id: 'board',
        label: 'Canonical board lane',
        state: 'pending',
        detail: 'Select a lane to establish the canonical planning source for this execution chain.',
      }
    : {
        id: 'board',
        label: 'Canonical board lane',
        state: selectedLane.closure ? 'complete' : 'active',
        detail: selectedLane.closure
          ? `Lane ${selectedLane.id} has persisted closure evidence in the canonical board.`
          : `Lane ${selectedLane.id} is the active planning source for reviewed execution tracking.`,
      }

  const queueStage: TimelineStage = selectedLaneQueueJobId && queueStatusState === 'ready' && queueStatusRecord
    ? {
        id: 'queue',
        label: 'Reviewed queue snapshot',
        state: 'complete',
        detail: `Queue ${queueStatusRecord.queue_sha256} is loaded for deterministic job ${selectedLaneQueueJobId}.`,
      }
    : selectedLaneQueueJobId
      ? {
          id: 'queue',
          label: 'Reviewed queue snapshot',
          state: queueStatusState === 'error' ? 'warning' : queueStatusState === 'loading' ? 'active' : 'pending',
          detail:
            queueStatusState === 'error'
              ? 'Queue inspection failed; refresh before trusting reviewed execution state.'
              : queueStatusState === 'loading'
                ? 'Refreshing the shared queue snapshot for the selected lane.'
                : `Queue job ${selectedLaneQueueJobId} is derived, but the queue snapshot is not loaded yet.`,
        }
      : {
          id: 'queue',
          label: 'Reviewed queue snapshot',
          state: 'pending',
          detail: 'A deterministic queue job id will appear after lane selection and shared token derivation.',
        }

  const runtimeStage: TimelineStage = runtimeWatchdogSnapshotStale
    ? {
        id: 'runtime',
        label: 'Runtime execution',
        state: 'warning',
        detail: 'Runtime watchdog snapshot is stale. Refresh or rerun the watchdog before trusting execution state.',
      }
    : runtimeEvidenceMismatch
    ? {
        id: 'runtime',
        label: 'Runtime execution',
        state: 'warning',
        detail: 'Runtime watchdog reports verified completion, but stable receipt evidence is still missing.',
      }
    : runtimeWatchdogState === 'ready' && selectedRuntimeWatchdogJob?.status === 'completed' && selectedRuntimeWatchdogJob.verification_passed === true
      ? {
          id: 'runtime',
          label: 'Runtime execution',
          state: 'complete',
          detail: `Watchdog verified runtime completion for ${selectedRuntimeWatchdogJob.job_id}.`,
        }
      : runtimeWatchdogState === 'ready' && selectedRuntimeWatchdogJob
        ? {
            id: 'runtime',
            label: 'Runtime execution',
            state: 'active',
            detail: `Watchdog is tracking ${selectedRuntimeWatchdogJob.job_id} with status ${selectedRuntimeWatchdogJob.status ?? 'unknown'}.`,
          }
        : {
            id: 'runtime',
            label: 'Runtime execution',
            state: runtimeWatchdogState === 'error' ? 'warning' : runtimeWatchdogState === 'loading' ? 'active' : 'pending',
            detail:
              runtimeWatchdogState === 'error'
                ? 'Runtime watchdog inspection failed.'
                : runtimeWatchdogState === 'loading'
                  ? 'Refreshing runtime watchdog state.'
                  : 'Runtime watchdog has not yet produced a matching execution signal.',
          }

  const receiptStage: TimelineStage = closeoutReceiptState === 'available' && closeoutReceiptRecord?.exists
    ? {
        id: 'receipt',
        label: 'Stable closeout receipt',
        state: 'complete',
        detail: `Stable receipt${closeoutReceiptRecord.runtime_profile_id ? ` via ${closeoutReceiptRecord.runtime_profile_id}` : ''} was recorded for ${closeoutReceiptRecord.queue_job_id}.`,
      }
    : {
        id: 'receipt',
        label: 'Stable closeout receipt',
        state:
          closeoutReceiptState === 'error'
            ? 'warning'
            : closeoutReceiptState === 'loading'
              ? 'active'
              : closeoutReceiptState === 'missing' && runtimeEvidenceMismatch
                ? 'warning'
                : 'pending',
        detail:
          closeoutReceiptState === 'error'
            ? 'Stable closeout receipt lookup failed.'
            : closeoutReceiptState === 'loading'
              ? 'Checking whether runtime already published stable closeout evidence.'
              : closeoutReceiptState === 'missing'
                ? 'Stable closeout receipt is not available yet.'
                : 'Stable closeout receipt will appear here once runtime writes mission evidence.',
      }

    const missionStage: TimelineStage = durableMissionSnapshot && !selectedLane?.closure
      ? {
          id: 'mission',
          label: 'Durable mission snapshot',
          state: 'active',
          detail: `Receipt observed. Durable mission ${durableMissionSnapshot.mission_id} is active for ${durableMissionSnapshot.queue_job_id ?? selectedLaneQueueJobId ?? selectedLane?.id ?? 'the selected lane'}, and canonical board closure is still pending.`,
        }
      : durableMissionSnapshot
        ? {
            id: 'mission',
            label: 'Durable mission snapshot',
            state: 'complete',
            detail: `Durable mission ${durableMissionSnapshot.mission_id} is aligned to the reviewed execution chain.`,
          }
        : closeoutReceiptState === 'available' && closeoutReceiptRecord?.exists
          ? {
              id: 'mission',
              label: 'Durable mission snapshot',
              state: missionStateState === 'error' ? 'warning' : missionStateState === 'loading' ? 'active' : 'pending',
              detail:
                missionStateState === 'error'
                  ? 'Stable receipt is present, but the durable mission snapshot could not be loaded.'
                  : missionStateState === 'loading'
                    ? 'Stable receipt is present; waiting for durable mission snapshot refresh.'
                    : 'Stable receipt is present, but the durable mission snapshot is not visible yet.',
            }
          : {
              id: 'mission',
              label: 'Durable mission snapshot',
              state: 'pending',
              detail: 'Durable mission snapshot appears after receipt observation or explicit completion write-back.',
            }

  const closureStage: TimelineStage = selectedLane?.closure?.closeout_receipt
    ? {
        id: 'closure',
        label: 'Canonical board closure',
        state: 'complete',
        detail: `Canonical board closure persists reviewed runtime provenance for ${selectedLane.closure.queue_job_id}.`,
      }
    : selectedLane?.closure
      ? {
          id: 'closure',
          label: 'Canonical board closure',
          state: 'active',
          detail: `Canonical board closure exists for ${selectedLane.closure.queue_job_id}, but no stable runtime subset was persisted.`,
        }
      : selectedLane?.status === 'completed'
        ? {
            id: 'closure',
            label: 'Canonical board closure',
            state: 'warning',
            detail: 'Lane is marked completed, but persisted closure evidence is missing.',
          }
        : {
            id: 'closure',
            label: 'Canonical board closure',
            state: 'pending',
            detail:
              durableMissionSnapshot && closeoutReceiptState === 'available' && closeoutReceiptRecord?.exists
                ? 'Stable receipt and durable mission snapshot are present, but explicit reviewed completion write-back is still the closure authority.'
                : 'Canonical board closure will be written only after explicit reviewed completion write-back.',
          }

  return [boardStage, queueStage, runtimeStage, receiptStage, missionStage, closureStage]
}

function deriveNextRecommendedLaneQueueGuidance(
  recommendedLane: DeveloperBoardLane | null,
  recommendedLaneAnalysis: DeveloperLaneAutonomyAnalysis | null,
  lastCompletionWriteResult: CompletionWriteResult | null,
  persistenceStatus: DeveloperControlPlanePersistenceStatus,
  queueStatusState: AutonomyTabProps['queueStatusState'],
  queueStatusRecord: DeveloperControlPlaneOvernightQueueStatusResponse | null
): NextRecommendedLaneQueueGuidance | null {
  if (
    !recommendedLane ||
    !recommendedLaneAnalysis ||
    recommendedLane.id !== lastCompletionWriteResult?.nextRecommendedLaneId
  ) {
    return null
  }

  if (recommendedLane.status !== 'active') {
    return {
      tone: 'pending' as const,
      message: 'Promote this lane to active before staging the next reviewed queue entry.',
    }
  }

  if (recommendedLane.id !== 'platform-runtime') {
    return {
      tone: 'pending' as const,
      message:
        'Reviewed queue staging remains restricted to platform-runtime for the first bounded pilot.',
    }
  }

  if (recommendedLane.dependencies.length > 0) {
    return {
      tone: 'pending' as const,
      message: `Dependencies still declared: ${recommendedLane.dependencies.join(', ')}.`,
    }
  }

  if (!hasReviewedDispatchReviewGates(recommendedLane)) {
    return {
      tone: 'pending' as const,
      message: 'Add explicit spec and risk review gates before staging the next reviewed queue entry.',
    }
  }

  if (recommendedLaneAnalysis.readiness !== 'ready') {
    return {
      tone: 'pending' as const,
      message: `Current readiness is ${recommendedLaneAnalysis.readiness}; clear blocking drift before continuing.`,
    }
  }

  if (persistenceStatus.tone !== 'synced') {
    return {
      tone: 'pending' as const,
      message: 'Shared canonical board must be active before staging the next reviewed queue entry.',
      refreshTargetsRecommended: ['active-board'],
    }
  }

  if (!(queueStatusState === 'ready' && queueStatusRecord)) {
    return {
      tone: 'pending' as const,
      message:
        'Refresh queue status before staging the next reviewed queue entry so the preflight hash is explicit.',
      refreshQueueStatusRecommended: true,
    }
  }

  return {
    tone: 'ready' as const,
    message: 'Reviewed queue staging is ready after you focus this lane.',
  }
}

export function AutonomyTab({
  jsonError,
  autonomyAnalysis,
  persistenceStatus,
  recommendedLane,
  selectedLane,
  selectedLaneAnalysis,
  dispatchPacket,
  queueCandidate,
  queueEntry,
  unresolvedQueueDependencyLaneIds,
  selectedLaneQueueJobId,
  queueWriteState,
  completionWriteState,
  queueStatusState,
  queueStatusRecord,
  queueStatusError,
  queueStatusLastRefreshedAt,
  closeoutReceiptState,
  closeoutReceiptRecord,
  closeoutReceiptError,
  closeoutReceiptLastCheckedAt,
  missionStateState = 'idle',
  missionStateRecord = null,
  runtimeWatchdogState = 'idle',
  runtimeWatchdogRecord = null,
  runtimeWatchdogError = null,
  runtimeWatchdogLastCheckedAt = null,
  runtimeAutonomyCycleState = 'idle',
  runtimeAutonomyCycleRecord = null,
  runtimeAutonomyCycleError = null,
  runtimeAutonomyCycleLastCheckedAt = null,
  runtimeCompletionAssistState = 'idle',
  runtimeCompletionAssistRecord = null,
  runtimeCompletionAssistError = null,
  runtimeCompletionAssistLastCheckedAt = null,
  lastQueueWriteResult,
  completionClosureSummary,
  completionEvidenceInput,
  lastCompletionWriteResult,
  onSelectLane,
  onPromoteLane,
  onCopyDispatchPacket,
  onCopyQueueCandidate,
  onCopyQueueEntry,
  onRefreshQueueStatus,
  onRefreshRecommendedTargets,
  onRefreshAndRetryQueueWrite,
  onRefreshAndRetryLaneCompletion,
  onCompletionClosureSummaryChange,
  onCompletionEvidenceInputChange,
  onDraftLaneCompletionFromCurrentState,
  onDraftLaneCompletionForLane,
  onWriteLaneCompletion,
  onWriteQueueEntry,
}: AutonomyTabProps) {
  const selectedLaneMissionSummary = getSelectedLaneMissionSummary({
    selectedLane,
    missionStateRecord,
    closeoutReceiptRecord,
    selectedLaneQueueJobId,
  })
  const decisionMemory = useDecisionMemory({
    enabled: persistenceStatus.tone === 'synced',
    sourceLaneId: selectedLane?.id ?? closeoutReceiptRecord?.source_lane_id ?? null,
    queueJobId: selectedLaneQueueJobId ?? closeoutReceiptRecord?.queue_job_id ?? null,
    linkedMissionId: selectedLaneMissionSummary?.mission_id ?? closeoutReceiptRecord?.mission_id ?? null,
  })
  const reviewedDispatchPilotChecks = buildReviewedDispatchPilotChecks(
    persistenceStatus,
    selectedLane,
    selectedLaneAnalysis,
    queueStatusState,
    queueStatusRecord,
    {
      state: decisionMemory.state,
      record: decisionMemory.record,
      error: decisionMemory.error,
    }
  )

  const blockingPilotChecks = countBlockingReviewedDispatchPilotChecks(reviewedDispatchPilotChecks)
  const selectedRuntimeWatchdogJob = findSelectedRuntimeWatchdogJob(
    runtimeWatchdogRecord,
    selectedLaneQueueJobId
  )
  const recommendedLaneAnalysis = recommendedLane
    ? autonomyAnalysis?.laneAnalyses.find((lane) => lane.laneId === recommendedLane.id) ?? null
    : null
  const nextRecommendedLaneQueueGuidance = deriveNextRecommendedLaneQueueGuidance(
    recommendedLane,
    recommendedLaneAnalysis,
    lastCompletionWriteResult,
    persistenceStatus,
    queueStatusState,
    queueStatusRecord
  )
  const runtimeWatchdogSnapshotStale =
    runtimeWatchdogState === 'ready' && runtimeWatchdogRecord?.state_is_stale === true
  const runtimeEvidenceMismatch =
    !runtimeWatchdogSnapshotStale &&
    closeoutReceiptState === 'missing' &&
    selectedRuntimeWatchdogJob?.status === 'completed' &&
    selectedRuntimeWatchdogJob.verification_passed === true
  const runtimeCompletionAssistAdvisory = runtimeWatchdogRecord?.completion_assist_advisory ?? null
  const runtimeCompletionAssistSummary = runtimeWatchdogCompletionAssistSummary(
    runtimeCompletionAssistAdvisory
  )
  const durableMissionClosurePending =
    selectedLaneMissionSummary !== null &&
    !selectedLane?.closure &&
    closeoutReceiptState === 'available' &&
    closeoutReceiptRecord?.exists === true
  const autonomyEvidenceTimeline = buildAutonomyEvidenceTimeline(
    selectedLane,
    selectedLaneQueueJobId,
    queueStatusState,
    queueStatusRecord,
    runtimeWatchdogState,
    runtimeWatchdogSnapshotStale,
    selectedRuntimeWatchdogJob,
    closeoutReceiptState,
    closeoutReceiptRecord,
    runtimeEvidenceMismatch,
    missionStateState,
    selectedLaneMissionSummary
  )

  return (
    <TabsContent value="autonomy" className="space-y-4">
      {jsonError || !autonomyAnalysis ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Autonomy analysis is unavailable until the canonical board JSON is valid.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Autonomous Dispatch</CardTitle>
                <CardDescription>
                  Deterministic board analysis for next-lane selection, structural drift detection, and dispatch preparation.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-2xl border border-emerald-300/50 bg-emerald-50/70 p-4 dark:border-emerald-700/40 dark:bg-emerald-950/20">
                  <div className="text-xs uppercase tracking-[0.24em] text-emerald-700 dark:text-emerald-300">
                    Recommended Next Lane
                  </div>
                  {recommendedLane ? (
                    <div className="mt-3 space-y-3">
                      <div>
                        <div className="text-lg font-semibold text-foreground">{recommendedLane.title}</div>
                        <div className="mt-1 text-sm text-muted-foreground">{recommendedLane.objective}</div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button size="sm" onClick={() => onSelectLane(recommendedLane.id)}>
                          Focus lane
                        </Button>
                        {recommendedLane.status === 'planned' && (
                          <Button size="sm" variant="outline" onClick={() => onPromoteLane(recommendedLane.id)}>
                            Promote to active
                          </Button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="mt-3 text-sm text-muted-foreground">
                      No lane is ready for autonomous dispatch yet. Clear blockers or complete missing execution fields first.
                    </div>
                  )}
                </div>

                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  <Card className="border-border/70">
                    <CardContent className="p-4">
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Ready Lanes</div>
                      <div className="mt-2 text-2xl font-semibold">{autonomyAnalysis.readyLaneIds.length}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-border/70">
                    <CardContent className="p-4">
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Blocked Lanes</div>
                      <div className="mt-2 text-2xl font-semibold">{autonomyAnalysis.blockedLaneIds.length}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-border/70">
                    <CardContent className="p-4">
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Blocking Drift</div>
                      <div className="mt-2 text-2xl font-semibold">{autonomyAnalysis.blockingStructuralWarningCount}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-border/70">
                    <CardContent className="p-4">
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Advisory Drift</div>
                      <div className="mt-2 text-2xl font-semibold">{autonomyAnalysis.advisoryStructuralWarningCount}</div>
                    </CardContent>
                  </Card>
                </div>

                <div className="rounded-2xl border border-border/70 bg-muted/20 p-4 space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Reviewed Dispatch Pilot Preflight</div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        Explicit gate checklist for the first allowlisted platform-runtime pilot before queue write and runtime projection.
                      </div>
                    </div>
                    <Badge className={cn('capitalize', blockingPilotChecks === 0 ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300' : 'bg-rose-500/15 text-rose-700 dark:text-rose-300')}>
                      {blockingPilotChecks === 0 ? 'ready' : 'blocked'}
                    </Badge>
                  </div>

                  <div className="space-y-3">
                    {reviewedDispatchPilotChecks.map((check) => (
                      <div key={check.id} className="rounded-xl border border-border/60 bg-background/70 p-3 text-sm">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge className={cn('capitalize', pilotCheckTone(check))}>
                            {check.passed ? 'pass' : check.blocking ? 'blocking' : 'advisory'}
                          </Badge>
                          <span className="font-medium text-foreground">{check.label}</span>
                        </div>
                        <div className="mt-2 text-muted-foreground">{check.detail}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Recommendations</CardTitle>
                <CardDescription>
                  Board-level guidance derived from execution readiness, dependency references, and missing contract fields.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {autonomyAnalysis.systemRecommendations.map((recommendation) => (
                  <div key={recommendation} className="rounded-xl border border-border/70 bg-muted/20 px-3 py-3 text-sm text-muted-foreground">
                    {recommendation}
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Structural Drift Warnings</CardTitle>
                <CardDescription>
                  Board-derived warning taxonomy for missing ownership, completion discipline, orphaned dependencies, and other drift signals that should be visible before dispatch.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {autonomyAnalysis.driftedLaneIds.length === 0 ? (
                  <div className="rounded-xl border border-border/70 bg-muted/20 px-3 py-3 text-sm text-muted-foreground">
                    No explicit structural drift warnings are currently derived from the canonical board.
                  </div>
                ) : (
                  autonomyAnalysis.laneAnalyses
                    .filter((lane) => lane.structuralWarnings.length > 0)
                    .map((lane) => (
                      <div key={lane.laneId} className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{lane.laneId}</div>
                            <div className="mt-1 font-medium text-foreground">{lane.title}</div>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Badge className={cn('capitalize', statusTone(lane.status))}>{lane.status}</Badge>
                            <Badge className={cn('capitalize', readinessTone(lane.readiness))}>{lane.readiness}</Badge>
                          </div>
                        </div>
                        <div className="mt-3 space-y-3">
                          {lane.structuralWarnings.map((warning) => (
                            <div key={`${lane.laneId}-${warning.code}`} className="rounded-xl border border-border/60 bg-background/80 p-3 text-sm">
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge className={cn('capitalize', warningTone(warning.severity))}>{warning.severity}</Badge>
                                <span className="font-medium text-foreground">{warning.message}</span>
                              </div>
                              <div className="mt-2 text-muted-foreground">{warning.remediation}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Lane Readiness Matrix</CardTitle>
                <CardDescription>
                  Each lane is scored from the current board structure so autonomy stays deterministic instead of improvised.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {autonomyAnalysis.laneAnalyses.map((lane) => (
                  <button
                    key={lane.laneId}
                    type="button"
                    onClick={() => onSelectLane(lane.laneId)}
                    className="w-full rounded-2xl border border-border/70 bg-background p-4 text-left transition hover:border-emerald-300/70 hover:bg-muted/30"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{lane.laneId}</div>
                        <div className="mt-1 font-medium text-foreground">{lane.title}</div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge className={cn('capitalize', statusTone(lane.status))}>{lane.status}</Badge>
                        <Badge className={cn('capitalize', readinessTone(lane.readiness))}>{lane.readiness}</Badge>
                      </div>
                    </div>
                    <div className="mt-3 text-sm text-muted-foreground">Autonomy score: {lane.score}</div>
                    {lane.unresolvedDependencies.length > 0 && (
                      <div className="mt-2 text-sm text-rose-700 dark:text-rose-300">
                        Unresolved dependencies: {lane.unresolvedDependencies.join(', ')}
                      </div>
                    )}
                    {lane.missingFields.length > 0 && (
                      <div className="mt-2 text-sm text-rose-700 dark:text-rose-300">
                        Missing execution fields: {lane.missingFields.join(', ')}
                      </div>
                    )}
                    {lane.structuralWarnings.length > 0 && (
                      <div className="mt-2 space-y-2 text-sm">
                        {lane.structuralWarnings.map((warning) => (
                          <div key={`${lane.laneId}-${warning.code}`} className="rounded-xl border border-border/60 bg-muted/20 px-3 py-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge className={cn('capitalize', warningTone(warning.severity))}>{warning.severity}</Badge>
                              <span className="text-foreground">{warning.message}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {lane.advisoryGaps.length > 0 && (
                      <div className="mt-2 text-sm text-muted-foreground">
                        Detail gaps: {lane.advisoryGaps.join(', ')}
                      </div>
                    )}
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Dispatch Packet</CardTitle>
                <CardDescription>
                  Agent-ready packet generated from the selected lane. This is the shortest path from board state to execution handoff.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedLaneAnalysis && (
                  <div className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Selected lane autonomy</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Badge className={cn('capitalize', statusTone(selectedLaneAnalysis.status))}>{selectedLaneAnalysis.status}</Badge>
                      <Badge className={cn('capitalize', readinessTone(selectedLaneAnalysis.readiness))}>
                        {selectedLaneAnalysis.readiness}
                      </Badge>
                    </div>
                    <div className="mt-3 text-sm text-muted-foreground">Autonomy score: {selectedLaneAnalysis.score}</div>
                    <div className="mt-3 space-y-2 text-sm text-muted-foreground">
                      {selectedLaneAnalysis.recommendations.map((recommendation) => (
                        <div key={recommendation}>{recommendation}</div>
                      ))}
                    </div>
                    <div className="mt-4 rounded-xl border border-border/60 bg-background/80 p-3 text-sm">
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
                        Validation basis
                      </div>
                      {selectedLane?.validation_basis ? (
                        <div className="mt-2 space-y-2 text-muted-foreground">
                          <div>
                            Owner: <span className="text-foreground">{selectedLane.validation_basis.owner}</span>
                          </div>
                          <div>
                            Last reviewed:{' '}
                            <span className="text-foreground">
                              {formatTimestamp(selectedLane.validation_basis.last_reviewed_at)}
                            </span>
                          </div>
                          <div>{selectedLane.validation_basis.summary}</div>
                          <div className="space-y-1">
                            {selectedLane.validation_basis.evidence.map((evidenceLine) => (
                              <div key={evidenceLine}>- {evidenceLine}</div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="mt-2 text-muted-foreground">
                          No validation basis declared for the selected lane.
                        </div>
                      )}
                    </div>
                    <div className="mt-4 rounded-xl border border-border/60 bg-background/80 p-3 text-sm">
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
                        Completion closure
                      </div>
                      {selectedLane?.closure ? (
                        <div className="mt-2 space-y-2 text-muted-foreground">
                          <div>
                            Queue job id:{' '}
                            <span className="font-mono text-foreground">{selectedLane.closure.queue_job_id}</span>
                          </div>
                          <div>
                            Queue hash:{' '}
                            <span className="font-mono text-foreground">{selectedLane.closure.queue_sha256}</span>
                          </div>
                          <div>
                            Source board token:{' '}
                            <span className="font-mono text-foreground">
                              {selectedLane.closure.source_board_concurrency_token}
                            </span>
                          </div>
                          <div>
                            Completed at:{' '}
                            <span className="text-foreground">
                              {formatTimestamp(selectedLane.closure.completed_at)}
                            </span>
                          </div>
                          <div>{selectedLane.closure.closure_summary}</div>
                          <div className="space-y-1">
                            {selectedLane.closure.evidence.map((evidenceLine) => (
                              <div key={evidenceLine}>- {evidenceLine}</div>
                            ))}
                          </div>
                          {selectedLane.closure.closeout_receipt && (
                            <div className="rounded-xl border border-border/60 bg-muted/20 p-3">
                              <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">
                                Stable runtime provenance
                              </div>
                              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                                <div>
                                  Mission id:{' '}
                                  <span className="font-mono text-foreground">
                                    {selectedLane.closure.closeout_receipt.mission_id ?? 'Not available'}
                                  </span>
                                </div>
                                <div>
                                  Producer:{' '}
                                  <span className="text-foreground">
                                    {selectedLane.closure.closeout_receipt.producer_key ?? 'Not available'}
                                  </span>
                                </div>
                                <div>
                                  Runtime profile:{' '}
                                  <span className="font-mono text-foreground">
                                    {selectedLane.closure.closeout_receipt.runtime_profile_id ?? 'Not available'}
                                  </span>
                                </div>
                                <div>
                                  Closeout status:{' '}
                                  <span className="text-foreground">
                                    {selectedLane.closure.closeout_receipt.closeout_status ?? 'Not available'}
                                  </span>
                                </div>
                                <div>
                                  Receipt recorded:{' '}
                                  <span className="text-foreground">
                                    {formatTimestamp(
                                      selectedLane.closure.closeout_receipt.receipt_recorded_at ?? null
                                    )}
                                  </span>
                                </div>
                                <div>
                                  Verification evidence:{' '}
                                  <span className="font-mono text-foreground break-all">
                                    {selectedLane.closure.closeout_receipt.verification_evidence_ref ?? 'Not available'}
                                  </span>
                                </div>
                              </div>
                              <div className="mt-2">
                                Refreshed artifacts:{' '}
                                <span className="text-foreground">
                                  {selectedLane.closure.closeout_receipt.artifact_paths.length > 0
                                    ? selectedLane.closure.closeout_receipt.artifact_paths.join(', ')
                                    : 'Not available'}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : selectedLane?.status === 'completed' ? (
                        <div className="mt-2 text-rose-700 dark:text-rose-300">
                          Selected lane is marked completed but has no persisted closure evidence.
                        </div>
                      ) : (
                        <div className="mt-2 text-muted-foreground">
                          No persisted closure for the selected lane yet.
                        </div>
                      )}
                    </div>
                    {selectedLaneAnalysis.structuralWarnings.length > 0 && (
                      <div className="mt-3 space-y-2 text-sm">
                        {selectedLaneAnalysis.structuralWarnings.map((warning) => (
                          <div key={`${selectedLaneAnalysis.laneId}-${warning.code}`} className="rounded-xl border border-border/60 bg-background/80 px-3 py-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge className={cn('capitalize', warningTone(warning.severity))}>{warning.severity}</Badge>
                              <span className="text-foreground">{warning.message}</span>
                            </div>
                            <div className="mt-1 text-muted-foreground">{warning.remediation}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    {selectedLaneAnalysis.status === 'planned' && selectedLaneAnalysis.readiness === 'ready' && (
                      <div className="mt-4">
                        <Button variant="outline" onClick={() => onPromoteLane(selectedLaneAnalysis.laneId)}>
                          Promote selected lane to active
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={() => recommendedLane && onSelectLane(recommendedLane.id)} disabled={!recommendedLane}>
                    Focus recommended lane
                  </Button>
                  <Button variant="outline" onClick={() => void onCopyDispatchPacket()} disabled={!dispatchPacket}>
                    Copy dispatch packet
                  </Button>
                  <Button variant="outline" onClick={() => void onCopyQueueCandidate()} disabled={!queueCandidate}>
                    Copy queue candidate
                  </Button>
                  <Button variant="outline" onClick={() => void onCopyQueueEntry()} disabled={!queueEntry}>
                    Copy queue entry
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => void onRefreshQueueStatus()}
                    disabled={queueStatusState === 'loading' || queueWriteState === 'writing'}
                  >
                    {queueStatusState === 'loading' ? 'Refreshing queue status...' : 'Refresh queue status'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => void onWriteQueueEntry()}
                    disabled={
                      !queueEntry ||
                      selectedLaneAnalysis?.readiness !== 'ready' ||
                      !hasReviewedDispatchReviewGates(selectedLane) ||
                      unresolvedQueueDependencyLaneIds.length > 0 ||
                      queueWriteState === 'writing'
                    }
                  >
                    {queueWriteState === 'writing' ? 'Writing queue entry...' : 'Write queue entry'}
                  </Button>
                </div>

                <div className="rounded-2xl border border-border/70 bg-muted/20 p-4 space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Manual Completion Write-Back</div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        Operator-explicit closure evidence write-back from a completed queue job into the canonical board.
                      </div>
                    </div>
                    <Badge
                      className={cn(
                        'capitalize',
                        completionWriteState === 'written'
                          ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                          : completionWriteState === 'conflict'
                            ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
                            : completionWriteState === 'error'
                              ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
                              : 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
                      )}
                    >
                      {completionWriteState}
                    </Badge>
                  </div>

                  <div className="space-y-2 text-sm text-muted-foreground">
                    <div>Selected lane queue job id: <span className="font-mono text-foreground">{selectedLaneQueueJobId ?? 'Unavailable until a lane and shared board token exist'}</span></div>
                    <div>Eligible lane status: <span className="text-foreground">{selectedLaneAnalysis?.status ?? 'No lane selected'}</span></div>
                  </div>

                  <div className="rounded-xl border border-border/60 bg-background/70 p-4">
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Autonomy Evidence Timeline</div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Visible chain from canonical board intent to runtime evidence and explicit closure write-back.
                    </div>

                    <div className="mt-4 space-y-3">
                      {autonomyEvidenceTimeline.map((stage, index) => (
                        <div key={stage.id} className="flex gap-3">
                          <div className="flex flex-col items-center">
                            <span className={cn('flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-semibold', timelineStageTone(stage.state))}>
                              {index + 1}
                            </span>
                            {index < autonomyEvidenceTimeline.length - 1 && (
                              <span className="mt-1 h-8 w-px bg-border/70" aria-hidden="true" />
                            )}
                          </div>
                          <div className="min-w-0 flex-1 rounded-xl border border-border/60 bg-muted/20 p-3 text-sm text-muted-foreground">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-medium text-foreground">{stage.label}</span>
                              <Badge className={cn('capitalize', timelineStageTone(stage.state))}>{stage.state}</Badge>
                            </div>
                            <div className="mt-2">{stage.detail}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <DecisionMemoryCard
                    state={decisionMemory.state}
                    record={decisionMemory.record}
                    error={decisionMemory.error}
                    lastCheckedAt={decisionMemory.lastCheckedAt}
                    scope={decisionMemory.scope}
                    resolution={decisionMemory.resolution}
                  />

                  <AutonomyCycleCard
                    state={runtimeAutonomyCycleState}
                    record={runtimeAutonomyCycleRecord}
                    error={runtimeAutonomyCycleError}
                    lastCheckedAt={runtimeAutonomyCycleLastCheckedAt}
                    missionStateState={missionStateState}
                    missionStateRecord={missionStateRecord}
                    selectedLaneId={selectedLane?.id ?? null}
                    onSelectLane={onSelectLane}
                    onDraftLaneCompletionForLane={onDraftLaneCompletionForLane}
                  />

                  <CompletionAssistCard
                    state={runtimeCompletionAssistState}
                    record={runtimeCompletionAssistRecord}
                    error={runtimeCompletionAssistError}
                    lastCheckedAt={runtimeCompletionAssistLastCheckedAt}
                    selectedLaneId={selectedLane?.id ?? null}
                    onSelectLane={onSelectLane}
                    onDraftLaneCompletionForLane={onDraftLaneCompletionForLane}
                  />

                  <div className="rounded-xl border border-border/60 bg-background/70 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Closeout Receipt Source</div>
                        <div className="mt-1 text-sm text-muted-foreground">
                          {closeoutReceiptDescription(closeoutReceiptState, selectedLaneQueueJobId)}
                        </div>
                      </div>
                      <Badge className={cn('capitalize', closeoutReceiptTone(closeoutReceiptState))}>
                        {closeoutReceiptState}
                      </Badge>
                    </div>

                    <div className="mt-4 space-y-2 text-sm text-muted-foreground">
                      <div>Receipt queue job id: <span className="font-mono text-foreground">{closeoutReceiptRecord?.queue_job_id ?? selectedLaneQueueJobId ?? 'Not available'}</span></div>
                      <div>Closeout status: <span className="text-foreground">{closeoutReceiptRecord?.closeout_status ?? 'Not available'}</span></div>
                      <div>Runtime profile: <span className="font-mono text-foreground">{closeoutReceiptRecord?.runtime_profile_id ?? 'Not available'}</span></div>
                      <div>Mission id: <span className="font-mono text-foreground">{closeoutReceiptRecord?.mission_id ?? 'Not available'}</span></div>
                      <div>Receipt recorded: <span className="text-foreground">{formatTimestamp(closeoutReceiptRecord?.receipt_recorded_at ?? null)}</span></div>
                      <div>Last checked: <span className="text-foreground">{formatTimestamp(closeoutReceiptLastCheckedAt)}</span></div>
                    </div>

                    {closeoutReceiptError && (
                      <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">{closeoutReceiptError}</p>
                    )}
                  </div>

                  <div className="rounded-xl border border-border/60 bg-background/70 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Durable Mission Snapshot</div>
                        <div className="mt-1 text-sm text-muted-foreground">
                          {selectedLaneMissionSummary
                            ? durableMissionClosurePending
                              ? 'Stable receipt has already anchored an active durable mission. Canonical board closure is still pending.'
                              : 'Durable mission snapshot is aligned to the selected execution chain.'
                            : closeoutReceiptState === 'available' && closeoutReceiptRecord?.exists
                              ? missionStateState === 'loading'
                                ? 'Stable receipt is present; waiting for the durable mission snapshot refresh.'
                                : missionStateState === 'error'
                                  ? 'Stable receipt is present, but durable mission-state could not be loaded.'
                                  : 'Stable receipt is present, but no durable mission snapshot is visible yet.'
                              : 'Durable mission snapshot appears after receipt observation or explicit completion write-back.'}
                        </div>
                      </div>
                      <Badge
                        className={cn(
                          'capitalize',
                          durableMissionTone(
                            missionStateState,
                            selectedLaneMissionSummary !== null,
                            durableMissionClosurePending,
                            closeoutReceiptState === 'available' && closeoutReceiptRecord?.exists === true
                          )
                        )}
                      >
                        {selectedLaneMissionSummary
                          ? durableMissionClosurePending
                            ? 'closure-pending'
                            : 'linked'
                          : closeoutReceiptState === 'available' && closeoutReceiptRecord?.exists
                            ? missionStateState === 'loading'
                              ? 'refreshing'
                              : missionStateState === 'error'
                                ? 'attention'
                                : 'awaiting-link'
                            : 'standby'}
                      </Badge>
                    </div>

                    <div className="mt-4 space-y-2 text-sm text-muted-foreground">
                      <div>Mission id: <span className="font-mono text-foreground">{selectedLaneMissionSummary?.mission_id ?? closeoutReceiptRecord?.mission_id ?? 'Not available'}</span></div>
                      <div>Mission objective: <span className="text-foreground">{selectedLaneMissionSummary?.objective ?? 'Not available'}</span></div>
                      <div>Mission status: <span className="text-foreground">{selectedLaneMissionSummary?.status ?? 'Not available'}</span></div>
                      <div>Queue job id: <span className="font-mono text-foreground">{selectedLaneMissionSummary?.queue_job_id ?? closeoutReceiptRecord?.queue_job_id ?? selectedLaneQueueJobId ?? 'Not available'}</span></div>
                      <div>Source lane: <span className="font-mono text-foreground">{selectedLaneMissionSummary?.source_lane_id ?? closeoutReceiptRecord?.source_lane_id ?? selectedLane?.id ?? 'Not available'}</span></div>
                      <div>Last updated: <span className="text-foreground">{formatTimestamp(selectedLaneMissionSummary?.updated_at ?? null)}</span></div>
                    </div>

                    {selectedLaneMissionSummary?.final_summary && (
                      <p className="mt-3 text-sm text-muted-foreground">{selectedLaneMissionSummary.final_summary}</p>
                    )}
                  </div>

                  <div className="rounded-xl border border-border/60 bg-background/70 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Runtime Watchdog</div>
                        <div className="mt-1 text-sm text-muted-foreground">
                          {runtimeWatchdogDescription(
                            runtimeWatchdogState,
                            runtimeWatchdogRecord,
                            selectedLaneQueueJobId,
                            selectedRuntimeWatchdogJob,
                            closeoutReceiptState,
                            runtimeEvidenceMismatch
                          )}
                        </div>
                      </div>
                      <Badge
                        className={cn(
                          'capitalize',
                          runtimeWatchdogTone(
                            runtimeWatchdogState,
                            runtimeEvidenceMismatch,
                            runtimeWatchdogRecord
                          )
                        )}
                      >
                        {runtimeEvidenceMismatch
                          ? 'mismatch'
                          : runtimeWatchdogState === 'ready'
                            ? !runtimeWatchdogRecord?.bootstrap_ready
                              ? 'bootstrap blocked'
                              : runtimeWatchdogRecord?.state_is_stale
                                ? 'stale snapshot'
                              : runtimeWatchdogRecord?.gateway_healthy
                                ? 'healthy'
                                : 'degraded'
                            : runtimeWatchdogState}
                      </Badge>
                    </div>

                    {runtimeCompletionAssistSummary && (
                      <div className="mt-3 rounded-lg border border-border/60 bg-background/60 px-3 py-3 text-sm text-muted-foreground">
                        {runtimeCompletionAssistSummary}
                      </div>
                    )}

                    <div className="mt-4 space-y-2 text-sm text-muted-foreground">
                      <div>Watchdog state path: <span className="font-mono text-foreground">{runtimeWatchdogRecord?.state_path ?? 'Not available'}</span></div>
                      <div>Watchdog snapshot: <span className="text-foreground">{runtimeWatchdogRecord?.state_is_stale ? 'Stale' : runtimeWatchdogRecord ? 'Current' : 'Not available'}</span></div>
                      <div>Runtime bootstrap: <span className="text-foreground">{runtimeWatchdogRecord?.bootstrap_ready ? 'Ready' : runtimeWatchdogRecord?.bootstrap_status === 'auth-store-missing' ? 'Blocked: auth missing' : 'Not available'}</span></div>
                      <div>Runtime auth store: <span className="font-mono text-foreground">{runtimeWatchdogRecord?.auth_store_path ?? 'Not available'}{runtimeWatchdogRecord && !runtimeWatchdogRecord.auth_store_exists ? ' (missing)' : ''}</span></div>
                      <div>Completion assist advisory: <span className="text-foreground">{runtimeCompletionAssistSummary ?? 'Not available'}</span></div>
                      <div>Advisory source: <span className="font-mono text-foreground">{runtimeCompletionAssistAdvisory?.observed_from_path ?? 'Not available'}</span></div>
                      <div>Gateway healthy: <span className="text-foreground">{runtimeWatchdogRecord?.gateway_healthy == null ? 'Not available' : runtimeWatchdogRecord?.state_is_stale ? `Stale snapshot (${runtimeWatchdogRecord.gateway_healthy ? 'last reported Yes' : 'last reported No'})` : runtimeWatchdogRecord.gateway_healthy ? 'Yes' : 'No'}</span></div>
                      <div>Tracked jobs: <span className="text-foreground">{runtimeWatchdogRecord?.job_count ?? 0}</span></div>
                      <div>Selected job runtime status: <span className="text-foreground">{selectedRuntimeWatchdogJob?.status == null ? 'Not available' : runtimeWatchdogRecord?.state_is_stale ? `Stale snapshot (${selectedRuntimeWatchdogJob.status})` : selectedRuntimeWatchdogJob.status}</span></div>
                      <div>Verification passed: <span className="text-foreground">{selectedRuntimeWatchdogJob?.verification_passed == null ? 'Not available' : runtimeWatchdogRecord?.state_is_stale ? `Stale snapshot (${selectedRuntimeWatchdogJob.verification_passed ? 'last reported Yes' : 'last reported No'})` : selectedRuntimeWatchdogJob.verification_passed ? 'Yes' : 'No'}</span></div>
                      <div>Mission evidence dir: <span className="font-mono text-foreground">{runtimeWatchdogRecord?.mission_evidence_dir_exists ? runtimeWatchdogRecord.mission_evidence_dir_path : 'Missing'}</span></div>
                      <div>Last checked: <span className="text-foreground">{formatTimestamp(runtimeWatchdogLastCheckedAt)}</span></div>
                    </div>

                    {runtimeEvidenceMismatch && (
                      <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">
                        Runtime reports a verified completion, but the stable closeout receipt is absent. Do not treat the lane as trustworthily closed out until watchdog mission evidence is present.
                      </p>
                    )}

                    {runtimeWatchdogState === 'ready' && runtimeWatchdogRecord && !runtimeWatchdogRecord.bootstrap_ready && (
                      <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">
                        Runtime bootstrap is blocked because the external auth store is missing. Seed runtime auth before expecting the reviewed dispatch pilot to project into execution.
                      </p>
                    )}

                    {runtimeWatchdogState === 'ready' && runtimeWatchdogRecord?.state_is_stale && (
                      <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">
                        Runtime watchdog state is stale. Refresh or rerun the watchdog before treating gateway health or runtime job state as current truth.
                      </p>
                    )}

                    {runtimeWatchdogError && (
                      <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">{runtimeWatchdogError}</p>
                    )}
                  </div>

                  <div className="grid gap-3 lg:grid-cols-2">
                    <div className="space-y-2">
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Closure Summary</div>
                      <Textarea
                        value={completionClosureSummary}
                        onChange={(event) => onCompletionClosureSummaryChange(event.target.value)}
                        placeholder="Summarize the reviewed closure evidence for this lane."
                        className="min-h-[8rem] text-sm leading-6"
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Evidence Lines</div>
                      <Textarea
                        value={completionEvidenceInput}
                        onChange={(event) => onCompletionEvidenceInputChange(event.target.value)}
                        placeholder="One evidence line per row."
                        className="min-h-[8rem] text-sm leading-6"
                      />
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      onClick={onDraftLaneCompletionFromCurrentState}
                      disabled={
                        !selectedLaneQueueJobId ||
                        !queueStatusRecord ||
                        selectedLaneAnalysis?.status !== 'active' ||
                        !hasReviewedCompletionVerificationEvidence(selectedLane) ||
                        completionWriteState === 'writing'
                      }
                    >
                      Draft closeout from current state
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => void onWriteLaneCompletion()}
                      disabled={
                        !selectedLaneQueueJobId ||
                        !completionClosureSummary.trim() ||
                        completionEvidenceInput
                          .split('\n')
                          .map((line) => line.trim())
                          .filter(Boolean).length === 0 ||
                        selectedLaneAnalysis?.status !== 'active' ||
                        !hasReviewedCompletionVerificationEvidence(selectedLane) ||
                        completionWriteState === 'writing'
                      }
                    >
                      {completionWriteState === 'writing'
                        ? 'Writing completion...'
                        : 'Write completion to board'}
                    </Button>
                  </div>

                  {lastCompletionWriteResult && (
                    <div className="rounded-xl border border-border/70 bg-background/70 p-4 text-sm text-muted-foreground space-y-2">
                      <p
                        className={cn(
                          lastCompletionWriteResult.status === 'written'
                            ? 'text-emerald-700 dark:text-emerald-300'
                            : lastCompletionWriteResult.status === 'conflict'
                              ? 'text-amber-700 dark:text-amber-300'
                              : 'text-rose-700 dark:text-rose-300'
                        )}
                      >
                        {lastCompletionWriteResult.message}
                      </p>
                      <div>Lane id: <span className="font-mono text-foreground">{lastCompletionWriteResult.laneId ?? 'Unavailable'}</span></div>
                      <div>Lane status: <span className="text-foreground">{lastCompletionWriteResult.currentLaneStatus ?? lastCompletionWriteResult.laneStatus ?? 'Unavailable'}</span></div>
                      <div>Queue job id: <span className="font-mono text-foreground">{lastCompletionWriteResult.queueJobId ?? 'Unavailable'}</span></div>
                      <div>Queue hash: <span className="font-mono text-foreground">{lastCompletionWriteResult.currentQueueSha256 ?? lastCompletionWriteResult.queueSha256 ?? 'Unavailable'}</span></div>
                      {lastCompletionWriteResult.approvalReceiptId !== null && (
                        <div>
                          Approval receipt:{' '}
                          <span className="font-mono text-foreground">
                            #{lastCompletionWriteResult.approvalReceiptId}
                          </span>
                        </div>
                      )}
                      {lastCompletionWriteResult.approvalReceiptRecordedAt && (
                        <div>
                          Approval recorded:{' '}
                          <span className="text-foreground">
                            {formatTimestamp(lastCompletionWriteResult.approvalReceiptRecordedAt)}
                          </span>
                        </div>
                      )}
                      {lastCompletionWriteResult.currentBoardConcurrencyToken && (
                        <div>Current board token: <span className="font-mono text-foreground">{lastCompletionWriteResult.currentBoardConcurrencyToken}</span></div>
                      )}
                      {lastCompletionWriteResult.refreshTargets.length > 0 && (
                        <div>
                          Recommended refresh:{' '}
                          <span className="text-foreground">
                            {lastCompletionWriteResult.refreshTargets.map(formatRefreshTarget).join(', ')}
                          </span>
                        </div>
                      )}
                      {lastCompletionWriteResult.retryPermittedAfterRefresh !== null && (
                        <div>
                          Retry after refresh:{' '}
                          <span className="text-foreground">
                            {lastCompletionWriteResult.retryPermittedAfterRefresh
                              ? 'Permitted after review'
                              : 'Manual review required'}
                          </span>
                        </div>
                      )}
                      {lastCompletionWriteResult.status === 'written' &&
                        lastCompletionWriteResult.nextRecommendedLaneId && (
                          <div className="rounded-xl border border-emerald-300/40 bg-emerald-50/60 px-3 py-3 text-emerald-900 dark:border-emerald-700/40 dark:bg-emerald-950/20 dark:text-emerald-200">
                            <div>
                              Next recommended lane:{' '}
                              <span className="font-medium text-foreground">
                                {lastCompletionWriteResult.nextRecommendedLaneTitle ??
                                  lastCompletionWriteResult.nextRecommendedLaneId}
                              </span>
                            </div>
                            <div className="mt-2">
                              <div className="flex flex-wrap gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    const nextLaneId =
                                      lastCompletionWriteResult.nextRecommendedLaneId
                                    if (nextLaneId) {
                                      onSelectLane(nextLaneId)
                                    }
                                  }}
                                >
                                  Focus next recommended lane
                                </Button>
                                {recommendedLane?.id ===
                                  lastCompletionWriteResult.nextRecommendedLaneId &&
                                  recommendedLane.status === 'planned' &&
                                  recommendedLaneAnalysis?.readiness === 'ready' && (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => onPromoteLane(recommendedLane.id)}
                                    >
                                      Promote next recommended lane
                                    </Button>
                                  )}
                              </div>
                              {nextRecommendedLaneQueueGuidance && (
                                <div
                                  className={cn(
                                    'mt-3 rounded-xl border px-3 py-3 text-sm',
                                    nextRecommendedLaneQueueGuidance.tone === 'ready'
                                      ? 'border-emerald-300/40 bg-emerald-100/60 text-emerald-900 dark:border-emerald-700/40 dark:bg-emerald-900/20 dark:text-emerald-200'
                                      : 'border-amber-300/40 bg-amber-50/60 text-amber-900 dark:border-amber-700/40 dark:bg-amber-950/20 dark:text-amber-200'
                                  )}
                                >
                                  {nextRecommendedLaneQueueGuidance.message}
                                  {nextRecommendedLaneQueueGuidance.refreshQueueStatusRecommended && (
                                    <div className="mt-3">
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => void onRefreshQueueStatus()}
                                        disabled={
                                          queueStatusState === 'loading' ||
                                          queueWriteState === 'writing' ||
                                          completionWriteState === 'writing'
                                        }
                                      >
                                        {queueStatusState === 'loading'
                                          ? 'Refreshing queue status...'
                                          : 'Refresh queue status for next lane'}
                                      </Button>
                                    </div>
                                  )}
                                  {nextRecommendedLaneQueueGuidance.refreshTargetsRecommended &&
                                    onRefreshRecommendedTargets && (
                                      <div className="mt-3">
                                        <Button
                                          size="sm"
                                          variant="outline"
                                          onClick={() =>
                                            void onRefreshRecommendedTargets(
                                              nextRecommendedLaneQueueGuidance.refreshTargetsRecommended ?? []
                                            )
                                          }
                                          disabled={
                                            persistenceStatus.tone === 'loading' ||
                                            queueStatusState === 'loading' ||
                                            closeoutReceiptState === 'loading' ||
                                            queueWriteState === 'writing' ||
                                            completionWriteState === 'writing'
                                          }
                                        >
                                          Refresh active board for next lane
                                        </Button>
                                      </div>
                                    )}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      {lastCompletionWriteResult.refreshTargets.length > 0 &&
                        onRefreshRecommendedTargets && (
                          <div className="pt-1">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                void onRefreshRecommendedTargets(
                                  lastCompletionWriteResult.refreshTargets
                                )
                              }
                              disabled={
                                queueStatusState === 'loading' ||
                                closeoutReceiptState === 'loading' ||
                                completionWriteState === 'writing'
                              }
                            >
                              Refresh recommended targets
                            </Button>
                          </div>
                        )}
                      {lastCompletionWriteResult.retryPermittedAfterRefresh &&
                        onRefreshAndRetryLaneCompletion && (
                          <div className="pt-1">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => void onRefreshAndRetryLaneCompletion()}
                              disabled={
                                queueStatusState === 'loading' ||
                                closeoutReceiptState === 'loading' ||
                                completionWriteState === 'writing'
                              }
                            >
                              Refresh and retry completion write
                            </Button>
                          </div>
                        )}
                      {lastCompletionWriteResult.remediationMessage && (
                        <div className="rounded-xl border border-amber-300/40 bg-amber-50/60 px-3 py-3 text-amber-900 dark:border-amber-700/40 dark:bg-amber-950/20 dark:text-amber-200">
                          {lastCompletionWriteResult.remediationMessage}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                  <div className="grid gap-3 lg:grid-cols-2">
                    <div className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Projected Queue Status</div>
                          <div className="mt-1 text-sm text-muted-foreground">
                            Queue snapshot visible inside the control-plane after manual refresh or write attempts.
                          </div>
                        </div>
                        <Badge className={cn('capitalize', queueStatusState === 'error' ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300' : queueStatusState === 'ready' ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300' : 'bg-slate-500/15 text-slate-700 dark:text-slate-300')}>
                          {queueStatusState}
                        </Badge>
                      </div>
                      <div className="mt-4 space-y-2 text-sm text-muted-foreground">
                        <div>Queue path: <span className="font-mono text-foreground">{queueStatusRecord?.queue_path ?? 'Not loaded yet'}</span></div>
                        <div>Queue hash: <span className="font-mono text-foreground">{queueStatusRecord?.queue_sha256 ?? 'Not loaded yet'}</span></div>
                        <div>Queue exists: <span className="text-foreground">{queueStatusRecord ? (queueStatusRecord.exists ? 'Yes' : 'No') : 'Unknown'}</span></div>
                        <div>Job count: <span className="text-foreground">{queueStatusRecord?.job_count ?? 'Not loaded yet'}</span></div>
                        <div>Queue updated: <span className="text-foreground">{formatTimestamp(queueStatusRecord?.updated_at ?? null)}</span></div>
                        <div>Last refreshed: <span className="text-foreground">{formatTimestamp(queueStatusLastRefreshedAt)}</span></div>
                      </div>
                      {queueStatusError && <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">{queueStatusError}</p>}
                    </div>

                    <div className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Last Write Result</div>
                          <div className="mt-1 text-sm text-muted-foreground">
                            Success and conflict evidence remain visible until the next write attempt replaces them.
                          </div>
                        </div>
                        <Badge
                          className={cn(
                            'capitalize',
                            lastQueueWriteResult?.status === 'written'
                              ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                              : lastQueueWriteResult?.status === 'conflict'
                                ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
                                : lastQueueWriteResult?.status === 'error'
                                  ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
                                  : 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
                          )}
                        >
                          {lastQueueWriteResult?.status ?? 'idle'}
                        </Badge>
                      </div>

                      {lastQueueWriteResult ? (
                        <div className="mt-4 space-y-2 text-sm text-muted-foreground">
                          <p className={cn(lastQueueWriteResult.status === 'written' ? 'text-emerald-700 dark:text-emerald-300' : lastQueueWriteResult.status === 'conflict' ? 'text-amber-700 dark:text-amber-300' : 'text-rose-700 dark:text-rose-300')}>
                            {lastQueueWriteResult.message}
                          </p>
                          <div>Written job id: <span className="font-mono text-foreground">{lastQueueWriteResult.writtenJobId ?? 'Not written'}</span></div>
                          <div>Previous queue hash: <span className="font-mono text-foreground">{lastQueueWriteResult.previousQueueSha256 ?? 'Not available'}</span></div>
                          <div>Current queue hash: <span className="font-mono text-foreground">{lastQueueWriteResult.currentQueueSha256 ?? 'Not available'}</span></div>
                          <div>Queue updated: <span className="text-foreground">{formatTimestamp(lastQueueWriteResult.queueUpdatedAt)}</span></div>
                          {lastQueueWriteResult.approvalReceiptId !== null && (
                            <div>
                              Approval receipt:{' '}
                              <span className="font-mono text-foreground">
                                #{lastQueueWriteResult.approvalReceiptId}
                              </span>
                            </div>
                          )}
                          {lastQueueWriteResult.approvalReceiptRecordedAt && (
                            <div>
                              Approval recorded:{' '}
                              <span className="text-foreground">
                                {formatTimestamp(lastQueueWriteResult.approvalReceiptRecordedAt)}
                              </span>
                            </div>
                          )}
                          {lastQueueWriteResult.conflictReason && (
                            <div>Conflict reason: <span className="font-mono text-foreground">{lastQueueWriteResult.conflictReason}</span></div>
                          )}
                          {lastQueueWriteResult.currentBoardConcurrencyToken && (
                            <div>Current board token: <span className="font-mono text-foreground">{lastQueueWriteResult.currentBoardConcurrencyToken}</span></div>
                          )}
                          {lastQueueWriteResult.conflictJobId && (
                            <div>Conflicting job id: <span className="font-mono text-foreground">{lastQueueWriteResult.conflictJobId}</span></div>
                          )}
                          {lastQueueWriteResult.refreshTargets.length > 0 && (
                            <div>
                              Recommended refresh:{' '}
                              <span className="text-foreground">
                                {lastQueueWriteResult.refreshTargets.map(formatRefreshTarget).join(', ')}
                              </span>
                            </div>
                          )}
                          {lastQueueWriteResult.retryPermittedAfterRefresh !== null && (
                            <div>
                              Retry after refresh:{' '}
                              <span className="text-foreground">
                                {lastQueueWriteResult.retryPermittedAfterRefresh
                                  ? 'Permitted after review'
                                  : 'Manual review required'}
                              </span>
                            </div>
                          )}
                          {lastQueueWriteResult.refreshTargets.length > 0 &&
                            onRefreshRecommendedTargets && (
                              <div className="pt-1">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() =>
                                    void onRefreshRecommendedTargets(
                                      lastQueueWriteResult.refreshTargets
                                    )
                                  }
                                  disabled={
                                    queueStatusState === 'loading' ||
                                    closeoutReceiptState === 'loading' ||
                                    queueWriteState === 'writing'
                                  }
                                >
                                  Refresh recommended targets
                                </Button>
                              </div>
                            )}
                          {lastQueueWriteResult.retryPermittedAfterRefresh &&
                            onRefreshAndRetryQueueWrite && (
                              <div className="pt-1">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => void onRefreshAndRetryQueueWrite()}
                                  disabled={
                                    queueStatusState === 'loading' ||
                                    closeoutReceiptState === 'loading' ||
                                    queueWriteState === 'writing'
                                  }
                                >
                                  Refresh and retry queue write
                                </Button>
                              </div>
                            )}
                          {lastQueueWriteResult.remediationMessage && (
                            <div className="rounded-xl border border-amber-300/40 bg-amber-50/60 px-3 py-3 text-amber-900 dark:border-amber-700/40 dark:bg-amber-950/20 dark:text-amber-200">
                              {lastQueueWriteResult.remediationMessage}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="mt-4 text-sm text-muted-foreground">
                          No queue write has been attempted in this session yet.
                        </div>
                      )}
                    </div>
                  </div>

                <Textarea
                  readOnly
                  value={dispatchPacket ? `${JSON.stringify(dispatchPacket, null, 2)}\n` : 'No dispatch packet available.'}
                  className="min-h-[18rem] font-mono text-xs leading-6"
                />

                <div className="space-y-2">
                  <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Queue Candidate Export</div>
                  <p className="text-sm text-muted-foreground">
                    Manual export only. The active board stays canonical, and the overnight queue stays derived from the current shared board token.
                  </p>
                </div>

                <Textarea
                  readOnly
                  value={
                    queueCandidate
                      ? `${JSON.stringify(queueCandidate, null, 2)}\n`
                      : 'Queue candidate export requires both a dispatch packet and a shared active-board concurrency token.'
                  }
                  className="min-h-[16rem] font-mono text-xs leading-6"
                />

                <div className="space-y-2">
                  <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Queue-Native Materialization</div>
                  <p className="text-sm text-muted-foreground">
                    Queue-native preview remains manual and derived. Queue-only fields are defaulted here without writing back into board planning state.
                  </p>
                  {unresolvedQueueDependencyLaneIds.length > 0 && (
                    <p className="text-sm text-amber-700 dark:text-amber-300">
                      Materialization blocked: unresolved dependency lane ids {unresolvedQueueDependencyLaneIds.join(', ')}.
                    </p>
                  )}
                </div>

                <Textarea
                  readOnly
                  value={
                    queueEntry
                      ? `${JSON.stringify(queueEntry, null, 2)}\n`
                      : 'Queue entry materialization requires a queue candidate plus fully resolved dependency lane-to-job mapping.'
                  }
                  className="min-h-[16rem] font-mono text-xs leading-6"
                />
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </TabsContent>
  )
}

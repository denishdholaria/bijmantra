import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react'

import {
  fetchDeveloperControlPlaneAutonomyCycle,
  fetchDeveloperControlPlaneIndigenousBrainBrief,
  fetchDeveloperControlPlaneActiveBoardVersions,
  fetchDeveloperControlPlaneRuntimeCompletionAssist,
  getDeveloperControlPlaneCompletionConflictDetail,
  fetchDeveloperControlPlaneCloseoutReceipt,
  fetchDeveloperControlPlaneLearnings,
  fetchDeveloperControlPlaneMissionDetail,
  fetchDeveloperControlPlaneMissionState,
  fetchDeveloperControlPlaneOvernightQueueStatus,
  prepareDeveloperControlPlaneLaneCompletionWrite,
  fetchDeveloperControlPlaneSilentMonitors,
  fetchDeveloperControlPlaneWatchdogStatus,
  fetchDeveloperControlPlaneActiveBoard,
  getDeveloperControlPlaneConflictRecord,
  getDeveloperControlPlaneOvernightQueueConflictDetail,
  getDeveloperControlPlanePersistenceErrorSummary,
  isDeveloperControlPlaneConflictError,
  getDeveloperControlPlanePersistenceErrorMessage,
  restoreDeveloperControlPlaneActiveBoardVersion,
  saveDeveloperControlPlaneActiveBoard,
  writeDeveloperControlPlaneLaneCompletion,
  writeDeveloperControlPlaneOvernightQueueEntry,
  type DeveloperControlPlaneBoardVersionsListResponse,
  type DeveloperControlPlaneAutonomyCycleResponse,
  type DeveloperControlPlaneCompletionConflictReason,
  type DeveloperControlPlaneCompletionWritePreparationResponse,
  type DeveloperControlPlaneCloseoutReceiptResponse,
  type DeveloperControlPlaneConflictRefreshTarget,
  type DeveloperControlPlaneIndigenousBrainBriefResponse,
  type DeveloperControlPlaneLearningEntryType,
  type DeveloperControlPlaneLearningLedgerResponse,
  type DeveloperControlPlaneMissionDetailResponse,
  type DeveloperControlPlaneMissionStateResponse,
  type DeveloperControlPlaneOvernightQueueConflictReason,
  type DeveloperControlPlaneOvernightQueueStatusResponse,
  type DeveloperControlPlaneRuntimeCompletionAssistResponse,
  type DeveloperControlPlaneSilentMonitorsResponse,
  type DeveloperControlPlaneWatchdogStatusResponse,
} from '../api/activeBoard'
import {
  type DeveloperBoardLane,
  type DeveloperBoardLaneReviewGate,
  type DeveloperBoardLaneReviewState,
  type DeveloperBoardLaneValidationBasis,
  canonicalizeDeveloperMasterBoardJson,
  createDeveloperLaneTemplate,
  createDeveloperSubplanTemplate,
  parseDeveloperMasterBoard,
  serializeDeveloperMasterBoard,
  type DeveloperBoardStatus,
  type DeveloperMasterBoard,
} from '../contracts/board'
import type { DeveloperLaneAutonomyAnalysis } from '../contracts/autonomy'
import {
  createDeveloperLaneQueueCandidate,
  createDeveloperLaneQueueJobId,
  materializeDeveloperLaneQueueEntry,
} from '../contracts/dispatch'
import {
  selectDevMasterBoardBackendConcurrencyToken,
  selectDevMasterBoardBackendHydrationState,
  selectDevMasterBoardConflictRecord,
  deriveDeveloperMasterBoardViewModel,
  selectDevMasterBoardFormatBoardJson,
  selectDevMasterBoardHasHydrated,
  selectDevMasterBoardHasUnsavedChanges,
  selectDevMasterBoardLastUpdatedAt,
  selectDevMasterBoardMarkBackendUnavailable,
  selectDevMasterBoardMarkNoRemoteRecord,
  selectDevMasterBoardMarkSaveConflict,
  selectDevMasterBoardMarkSaveError,
  selectDevMasterBoardMarkSaveStart,
  selectDevMasterBoardMarkSaveSuccess,
  selectDevMasterBoardPersistenceError,
  selectDevMasterBoardPersistenceErrorKind,
  selectDevMasterBoardRawBoardJson,
  selectDevMasterBoardReplaceBoardJson,
  selectDevMasterBoardResetBoard,
  selectDevMasterBoardSaveState,
  selectDevMasterBoardStorageAvailable,
  selectDevMasterBoardStartBackendHydration,
  selectDevMasterBoardHydrateFromBackendRecord,
  useDevMasterBoardStore,
} from '../state'
import {
  updateBoardTextField,
  type PlannerBoardTextField,
  type PlannerLaneField,
  type PlannerLaneReviewGateField,
  type PlannerLaneReviewStateField,
  type PlannerLaneValidationBasisField,
  type PlannerSubplanField,
} from './planner/shared'
import {
  findAutonomyCycleCompletionWritePreparationForLane,
  findCompletionAssistPreparationForLane,
} from './autonomy/completionWritePreparation'

type QueueStatusState = 'idle' | 'loading' | 'ready' | 'error'
type BoardVersionsState = 'idle' | 'loading' | 'ready' | 'error'
type BoardRestoreState = 'idle' | 'restoring' | 'restored' | 'conflict' | 'error'
type CloseoutReceiptState = 'idle' | 'loading' | 'available' | 'missing' | 'error'
type LearningLedgerState = 'idle' | 'loading' | 'ready' | 'error'
type WatchdogStatusState = 'idle' | 'loading' | 'ready' | 'error'
type AutonomyCycleState = 'idle' | 'loading' | 'ready' | 'missing' | 'error'
type RuntimeCompletionAssistState = 'idle' | 'loading' | 'ready' | 'missing' | 'error'
type SilentMonitorsState = 'idle' | 'loading' | 'ready' | 'error'
type MissionStateStatus = 'idle' | 'loading' | 'ready' | 'error'
type MissionDetailStatus = 'idle' | 'loading' | 'ready' | 'error'
type IndigenousBrainState = 'idle' | 'loading' | 'ready' | 'error'

type LearningLedgerQuery = {
  limit?: number
  entryType?: DeveloperControlPlaneLearningEntryType | null
  sourceClassification?: string | null
  sourceLaneId?: string | null
  queueJobId?: string | null
  linkedMissionId?: string | null
}

type BoardRestoreResult = {
  status: 'restored' | 'conflict' | 'error'
  message: string
  restored: boolean
  restoredFromRevisionId: number | null
  currentBoardConcurrencyToken: string | null
  previousBoardConcurrencyToken: string | null
  approvalReceiptId: number | null
  approvalReceiptRecordedAt: string | null
}

type QueueWriteResult = {
  status: 'written' | 'conflict' | 'error'
  message: string
  writtenJobId: string | null
  previousQueueSha256: string | null
  currentQueueSha256: string | null
  queueUpdatedAt: string | null
  approvalReceiptId: number | null
  approvalReceiptRecordedAt: string | null
  conflictReason: DeveloperControlPlaneOvernightQueueConflictReason | null
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
  approvalReceiptId: number | null
  approvalReceiptRecordedAt: string | null
  conflictReason: DeveloperControlPlaneCompletionConflictReason | null
  remediationMessage: string | null
  refreshTargets: DeveloperControlPlaneConflictRefreshTarget[]
  retryPermittedAfterRefresh: boolean | null
  currentBoardConcurrencyToken: string | null
  currentQueueSha256: string | null
  currentLaneStatus: string | null
  nextRecommendedLaneId?: string | null
  nextRecommendedLaneTitle?: string | null
}

type LiveWriteContext = {
  backendConcurrencyToken: string | null
  selectedLane: DeveloperBoardLane | null
  selectedLaneAnalysis: DeveloperLaneAutonomyAnalysis | null
  queueEntry: ReturnType<typeof materializeDeveloperLaneQueueEntry>['entry']
  selectedLaneQueueJobId: string | null
}

function getQueueConflictRemediationMessage(
  reason: DeveloperControlPlaneOvernightQueueConflictReason | null
) {
  if (reason === 'lane-review-missing') {
    return 'Update the canonical lane with explicit spec_review and risk_review evidence, save the shared board, then retry queue export from the current board token.'
  }

  if (reason === 'stale-board-token') {
    return 'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.'
  }

  if (reason === 'queue-sha-mismatch') {
    return 'Refresh queue status, compare the latest queue hash shown here, then retry only if the reviewed queue entry is still valid.'
  }

  if (reason === 'duplicate-job-id') {
    return 'Do not overwrite. Inspect whether the existing queued job already represents this lane and token pair, or regenerate from a newer board token if the board changed.'
  }

  if (reason === 'missing-active-board') {
    return 'Restore or resave the shared active board first. Queue writes stay blocked until shared board provenance exists.'
  }

  return 'Refresh queue status and retry only if the reviewed queue entry is still intended.'
}

function getQueueConflictRefreshTargets(
  reason: DeveloperControlPlaneOvernightQueueConflictReason | null
): DeveloperControlPlaneConflictRefreshTarget[] {
  if (reason === 'lane-review-missing') {
    return ['active-board']
  }

  if (reason === 'missing-active-board' || reason === 'stale-board-token') {
    return ['active-board']
  }

  if (reason === 'queue-sha-mismatch') {
    return ['overnight-queue']
  }

  if (reason === 'duplicate-job-id') {
    return ['overnight-queue', 'active-board']
  }

  return []
}

function getCompletionConflictRemediationMessage(
  reason: DeveloperControlPlaneCompletionConflictReason | null
) {
  if (reason === 'lane-verification-missing') {
    return 'Attach canonical verification_evidence to the lane, save the shared board, and retry completion write-back only after the reviewed verification gate is visible.'
  }

  if (reason === 'stale-board-token') {
    return 'Refresh the shared board state, confirm the lane is still the intended completion target, then retry with the current board token.'
  }

  if (reason === 'queue-sha-mismatch') {
    return 'Refresh queue status, confirm the current queue hash and the reviewed completion target, then retry only if the same job still applies.'
  }

  if (reason === 'queue-job-missing') {
    return 'The reviewed queue job is no longer present in the current queue snapshot. Refresh queue status and verify the job id before retrying.'
  }

  if (reason === 'queue-job-not-completed') {
    return 'Wait until the reviewed queue job reaches completed status before writing closure evidence back into the board.'
  }

  if (reason === 'closeout-receipt-required') {
    return 'Refresh the reviewed closeout receipt and retry only after the normalized receipt is visible in the control plane. Runtime-backed lanes should not be closed from freeform evidence alone.'
  }

  if (reason === 'closeout-receipt-mismatch') {
    return 'Refresh the reviewed closeout receipt, compare the latest normalized runtime evidence, and retry only if the receipt still matches the queue job being closed.'
  }

  if (reason === 'lane-job-mismatch') {
    return 'Refresh the shared board state and use the deterministic lane job id for the selected lane and board token. Do not apply completion evidence to a mismatched job.'
  }

  if (reason === 'lane-status-conflict') {
    return 'Only active lanes can move to completed in this slice. Review the current lane status and avoid forcing completion onto a non-active lane.'
  }

  if (reason === 'completion-overwrite-conflict') {
    return 'This lane already has different closure evidence. Review the current board record instead of overwriting closure data implicitly.'
  }

  if (reason === 'missing-active-board') {
    return 'Restore or resave the shared active board first. Completion write-back stays blocked until shared board provenance exists.'
  }

  return 'Refresh queue status and shared board state, then retry only if the reviewed completion remains intended.'
}

function getCompletionConflictRefreshTargets(
  reason: DeveloperControlPlaneCompletionConflictReason | null
): DeveloperControlPlaneConflictRefreshTarget[] {
  if (reason === 'lane-verification-missing') {
    return ['active-board']
  }

  if (
    reason === 'missing-active-board' ||
    reason === 'stale-board-token' ||
    reason === 'lane-status-conflict' ||
    reason === 'completion-overwrite-conflict'
  ) {
    return ['active-board']
  }

  if (reason === 'queue-sha-mismatch' || reason === 'queue-job-missing') {
    return ['overnight-queue']
  }

  if (
    reason === 'queue-job-not-completed' ||
    reason === 'closeout-receipt-required' ||
    reason === 'closeout-receipt-mismatch'
  ) {
    return ['closeout-receipt', 'overnight-queue']
  }

  if (reason === 'lane-job-mismatch') {
    return ['active-board', 'overnight-queue']
  }

  return []
}

function appendApprovalReceiptMessage(
  message: string,
  approvalReceipt: { receipt_id: number } | null | undefined
) {
  if (!approvalReceipt) {
    return message
  }

  return `${message} Approval receipt #${approvalReceipt.receipt_id} recorded.`
}

function normalizeRefreshTargets(
  targets: DeveloperControlPlaneConflictRefreshTarget[]
): DeveloperControlPlaneConflictRefreshTarget[] {
  const orderedTargets: DeveloperControlPlaneConflictRefreshTarget[] = [
    'active-board',
    'overnight-queue',
    'closeout-receipt',
  ]

  return orderedTargets.filter((target) => targets.includes(target))
}

function applyPreparedCompletionWriteState(
  prepared: {
    queue_status: DeveloperControlPlaneOvernightQueueStatusResponse
    closeout_receipt: DeveloperControlPlaneCloseoutReceiptResponse
  },
  setQueueStatusState: (state: QueueStatusState) => void,
  setQueueStatusRecord: (
    record: DeveloperControlPlaneOvernightQueueStatusResponse | null
  ) => void,
  setQueueStatusLastRefreshedAt: (value: string | null) => void,
  setCloseoutReceiptState: (state: CloseoutReceiptState) => void,
  setCloseoutReceiptRecord: (
    record: DeveloperControlPlaneCloseoutReceiptResponse | null
  ) => void,
  setCloseoutReceiptLastCheckedAt: (value: string | null) => void
) {
  const refreshedAt = new Date().toISOString()
  setQueueStatusState('ready')
  setQueueStatusRecord(prepared.queue_status)
  setQueueStatusLastRefreshedAt(refreshedAt)
  setCloseoutReceiptState(prepared.closeout_receipt.exists ? 'available' : 'missing')
  setCloseoutReceiptRecord(prepared.closeout_receipt)
  setCloseoutReceiptLastCheckedAt(refreshedAt)
}

function deriveNextRecommendedLaneHandoff(
  canonicalBoardJson: string,
  completedLaneId: string | null
) {
  const nextViewModel = deriveDeveloperMasterBoardViewModel(canonicalBoardJson, completedLaneId)

  if (
    nextViewModel.jsonError ||
    !nextViewModel.recommendedLane ||
    nextViewModel.recommendedLane.id === completedLaneId
  ) {
    return {
      nextRecommendedLaneId: null,
      nextRecommendedLaneTitle: null,
    }
  }

  return {
    nextRecommendedLaneId: nextViewModel.recommendedLane.id,
    nextRecommendedLaneTitle: nextViewModel.recommendedLane.title,
  }
}

function getPreferredMissionId(
  selectedLane: DeveloperBoardLane | null,
  closeoutReceiptRecord: DeveloperControlPlaneCloseoutReceiptResponse | null
) {
  if (closeoutReceiptRecord?.exists && closeoutReceiptRecord.mission_id) {
    return closeoutReceiptRecord.mission_id
  }

  return selectedLane?.closure?.closeout_receipt?.mission_id ?? null
}

function getPreferredMissionLookup(
  selectedLane: DeveloperBoardLane | null,
  selectedLaneQueueJobId: string | null,
  closeoutReceiptRecord: DeveloperControlPlaneCloseoutReceiptResponse | null
) {
  const queueJobId =
    closeoutReceiptRecord?.exists === true
      ? closeoutReceiptRecord.queue_job_id
      : selectedLane?.closure?.queue_job_id ?? selectedLaneQueueJobId

  const sourceLaneId =
    closeoutReceiptRecord?.exists === true
      ? closeoutReceiptRecord.source_lane_id ?? selectedLane?.id ?? null
      : selectedLane?.closure?.closeout_receipt?.source_lane_id ?? selectedLane?.id ?? null

  if (!queueJobId && !sourceLaneId) {
    return null
  }

  return {
    queueJobId: queueJobId ?? null,
    sourceLaneId: sourceLaneId ?? null,
  }
}

function mergeMissionStateRecords(
  missionState: DeveloperControlPlaneMissionStateResponse,
  supplementalMissionState: DeveloperControlPlaneMissionStateResponse | null
) {
  if (!supplementalMissionState || supplementalMissionState.missions.length === 0) {
    return missionState
  }

  const seenMissionIds = new Set<string>()
  const mergedMissions = [...supplementalMissionState.missions, ...missionState.missions].filter((mission) => {
    if (seenMissionIds.has(mission.mission_id)) {
      return false
    }

    seenMissionIds.add(mission.mission_id)
    return true
  })

  return {
    count: mergedMissions.length,
    missions: mergedMissions,
  } satisfies DeveloperControlPlaneMissionStateResponse
}

function findPreferredMissionSummary(
  missionStateRecord: DeveloperControlPlaneMissionStateResponse | null,
  preferredMissionId: string | null,
  preferredMissionLookup:
    | {
        queueJobId: string | null
        sourceLaneId: string | null
      }
    | null
) {
  if (!missionStateRecord) {
    return null
  }

  if (preferredMissionId) {
    const exactMatch = missionStateRecord.missions.find(
      (mission) => mission.mission_id === preferredMissionId
    )
    if (exactMatch) {
      return exactMatch
    }
  }

  if (!preferredMissionLookup) {
    return null
  }

  return (
    missionStateRecord.missions.find(
      (mission) =>
        (preferredMissionLookup.queueJobId !== null &&
          mission.queue_job_id === preferredMissionLookup.queueJobId) ||
        (preferredMissionLookup.sourceLaneId !== null &&
          mission.source_lane_id === preferredMissionLookup.sourceLaneId)
    ) ?? null
  )
}

export function useControlPlaneController() {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const remoteLoadStartedRef = useRef(false)
  const queueBootstrapStartedRef = useRef(false)
  const completionDraftTargetLaneRef = useRef<string | null>(null)
  const missionStateRecordRef = useRef<DeveloperControlPlaneMissionStateResponse | null>(null)
  const learningLedgerQueryRef = useRef<LearningLedgerQuery>({ limit: 6 })
  const missionStateLoadRef = useRef<{
    key: string
    promise: Promise<DeveloperControlPlaneMissionStateResponse | null>
  } | null>(null)
  const rawBoardJson = useDevMasterBoardStore(selectDevMasterBoardRawBoardJson)
  const lastUpdatedAt = useDevMasterBoardStore(selectDevMasterBoardLastUpdatedAt)
  const hasHydrated = useDevMasterBoardStore(selectDevMasterBoardHasHydrated)
  const storageAvailable = useDevMasterBoardStore(selectDevMasterBoardStorageAvailable)
  const backendHydrationState = useDevMasterBoardStore(selectDevMasterBoardBackendHydrationState)
  const saveState = useDevMasterBoardStore(selectDevMasterBoardSaveState)
  const backendConcurrencyToken = useDevMasterBoardStore(selectDevMasterBoardBackendConcurrencyToken)
  const hasUnsavedChanges = useDevMasterBoardStore(selectDevMasterBoardHasUnsavedChanges)
  const persistenceError = useDevMasterBoardStore(selectDevMasterBoardPersistenceError)
  const persistenceErrorKind = useDevMasterBoardStore(selectDevMasterBoardPersistenceErrorKind)
  const conflictRecord = useDevMasterBoardStore(selectDevMasterBoardConflictRecord)
  const replaceBoardJson = useDevMasterBoardStore(selectDevMasterBoardReplaceBoardJson)
  const formatBoardJson = useDevMasterBoardStore(selectDevMasterBoardFormatBoardJson)
  const resetBoard = useDevMasterBoardStore(selectDevMasterBoardResetBoard)
  const startBackendHydration = useDevMasterBoardStore(selectDevMasterBoardStartBackendHydration)
  const hydrateFromBackendRecord = useDevMasterBoardStore(selectDevMasterBoardHydrateFromBackendRecord)
  const markNoRemoteRecord = useDevMasterBoardStore(selectDevMasterBoardMarkNoRemoteRecord)
  const markBackendUnavailable = useDevMasterBoardStore(selectDevMasterBoardMarkBackendUnavailable)
  const markSaveStart = useDevMasterBoardStore(selectDevMasterBoardMarkSaveStart)
  const markSaveSuccess = useDevMasterBoardStore(selectDevMasterBoardMarkSaveSuccess)
  const markSaveConflict = useDevMasterBoardStore(selectDevMasterBoardMarkSaveConflict)
  const markSaveError = useDevMasterBoardStore(selectDevMasterBoardMarkSaveError)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedLaneId, setSelectedLaneId] = useState<string | null>(null)
  const [extraOwnersInput, setExtraOwnersInput] = useState('')
  const [queueWriteState, setQueueWriteState] = useState<
    'idle' | 'writing' | 'written' | 'conflict' | 'error'
  >('idle')
  const [completionWriteState, setCompletionWriteState] = useState<
    'idle' | 'writing' | 'written' | 'conflict' | 'error'
  >('idle')
  const [boardVersionsState, setBoardVersionsState] = useState<BoardVersionsState>('idle')
  const [boardVersionsRecord, setBoardVersionsRecord] =
    useState<DeveloperControlPlaneBoardVersionsListResponse | null>(null)
  const [boardVersionsError, setBoardVersionsError] = useState<string | null>(null)
  const [boardVersionsLastCheckedAt, setBoardVersionsLastCheckedAt] = useState<string | null>(null)
  const [boardRestoreState, setBoardRestoreState] = useState<BoardRestoreState>('idle')
  const [lastBoardRestoreResult, setLastBoardRestoreResult] =
    useState<BoardRestoreResult | null>(null)
  const [queueStatusState, setQueueStatusState] = useState<QueueStatusState>('idle')
  const [queueStatusRecord, setQueueStatusRecord] =
    useState<DeveloperControlPlaneOvernightQueueStatusResponse | null>(null)
  const [queueStatusError, setQueueStatusError] = useState<string | null>(null)
  const [queueStatusLastRefreshedAt, setQueueStatusLastRefreshedAt] = useState<string | null>(null)
  const [closeoutReceiptState, setCloseoutReceiptState] = useState<CloseoutReceiptState>('idle')
  const [closeoutReceiptRecord, setCloseoutReceiptRecord] =
    useState<DeveloperControlPlaneCloseoutReceiptResponse | null>(null)
  const [closeoutReceiptError, setCloseoutReceiptError] = useState<string | null>(null)
  const [closeoutReceiptLastCheckedAt, setCloseoutReceiptLastCheckedAt] = useState<string | null>(null)
  const [runtimeWatchdogState, setRuntimeWatchdogState] = useState<WatchdogStatusState>('idle')
  const [runtimeWatchdogRecord, setRuntimeWatchdogRecord] =
    useState<DeveloperControlPlaneWatchdogStatusResponse | null>(null)
  const [runtimeWatchdogError, setRuntimeWatchdogError] = useState<string | null>(null)
  const [runtimeWatchdogLastCheckedAt, setRuntimeWatchdogLastCheckedAt] = useState<string | null>(null)
  const [runtimeAutonomyCycleState, setRuntimeAutonomyCycleState] =
    useState<AutonomyCycleState>('idle')
  const [runtimeAutonomyCycleRecord, setRuntimeAutonomyCycleRecord] =
    useState<DeveloperControlPlaneAutonomyCycleResponse | null>(null)
  const [runtimeAutonomyCycleError, setRuntimeAutonomyCycleError] = useState<string | null>(null)
  const [runtimeAutonomyCycleLastCheckedAt, setRuntimeAutonomyCycleLastCheckedAt] =
    useState<string | null>(null)
  const [runtimeCompletionAssistState, setRuntimeCompletionAssistState] =
    useState<RuntimeCompletionAssistState>('idle')
  const [runtimeCompletionAssistRecord, setRuntimeCompletionAssistRecord] =
    useState<DeveloperControlPlaneRuntimeCompletionAssistResponse | null>(null)
  const [runtimeCompletionAssistError, setRuntimeCompletionAssistError] =
    useState<string | null>(null)
  const [runtimeCompletionAssistLastCheckedAt, setRuntimeCompletionAssistLastCheckedAt] =
    useState<string | null>(null)
  const [silentMonitorsState, setSilentMonitorsState] = useState<SilentMonitorsState>('idle')
  const [silentMonitorsRecord, setSilentMonitorsRecord] =
    useState<DeveloperControlPlaneSilentMonitorsResponse | null>(null)
  const [silentMonitorsError, setSilentMonitorsError] = useState<string | null>(null)
  const [silentMonitorsLastCheckedAt, setSilentMonitorsLastCheckedAt] = useState<string | null>(null)
  const [missionStateState, setMissionStateState] = useState<MissionStateStatus>('idle')
  const [missionStateRecord, setMissionStateRecord] =
    useState<DeveloperControlPlaneMissionStateResponse | null>(null)
  const [missionStateError, setMissionStateError] = useState<string | null>(null)
  const [missionStateLastCheckedAt, setMissionStateLastCheckedAt] = useState<string | null>(null)
  const [missionDetailState, setMissionDetailState] = useState<MissionDetailStatus>('idle')
  const [missionDetailRecord, setMissionDetailRecord] =
    useState<DeveloperControlPlaneMissionDetailResponse | null>(null)
  const [missionDetailError, setMissionDetailError] = useState<string | null>(null)
  const [missionDetailLastCheckedAt, setMissionDetailLastCheckedAt] = useState<string | null>(null)
  const [indigenousBrainState, setIndigenousBrainState] = useState<IndigenousBrainState>('idle')
  const [indigenousBrainBrief, setIndigenousBrainBrief] =
    useState<DeveloperControlPlaneIndigenousBrainBriefResponse | null>(null)
  const [indigenousBrainError, setIndigenousBrainError] = useState<string | null>(null)
  const [indigenousBrainLastCheckedAt, setIndigenousBrainLastCheckedAt] = useState<string | null>(null)
  const [learningLedgerState, setLearningLedgerState] = useState<LearningLedgerState>('idle')
  const [learningLedgerRecord, setLearningLedgerRecord] =
    useState<DeveloperControlPlaneLearningLedgerResponse | null>(null)
  const [learningLedgerError, setLearningLedgerError] = useState<string | null>(null)
  const [learningLedgerLastCheckedAt, setLearningLedgerLastCheckedAt] = useState<string | null>(null)
  const [learningLedgerQuery, setLearningLedgerQuery] = useState<LearningLedgerQuery>({
    limit: 6,
  })
  const [lastQueueWriteResult, setLastQueueWriteResult] = useState<QueueWriteResult | null>(null)
  const [completionClosureSummary, setCompletionClosureSummary] = useState('')
  const [completionEvidenceInput, setCompletionEvidenceInput] = useState('')
  const [lastCompletionWriteResult, setLastCompletionWriteResult] =
    useState<CompletionWriteResult | null>(null)

  const viewModel = useMemo(
    () =>
      deriveDeveloperMasterBoardViewModel(
        rawBoardJson,
        selectedLaneId,
        hasHydrated,
        storageAvailable,
        backendHydrationState,
        saveState,
        persistenceError,
        persistenceErrorKind,
        conflictRecord?.updated_at ?? null
      ),
    [
      rawBoardJson,
      selectedLaneId,
      hasHydrated,
      storageAvailable,
      backendHydrationState,
      saveState,
      persistenceError,
      persistenceErrorKind,
      conflictRecord?.updated_at,
    ]
  )

  const {
    parsedBoard,
    jsonError,
    lanes,
    activeLaneCount,
    blockedLaneCount,
    subplanCount,
    dependencyCount,
    selectedLane,
    availableAgents,
    autonomyAnalysis,
    selectedLaneAnalysis,
    recommendedLane,
    persistenceStatus,
    dispatchPacket,
  } = viewModel

  const queueCandidate = useMemo(
    () => createDeveloperLaneQueueCandidate(dispatchPacket, backendConcurrencyToken),
    [backendConcurrencyToken, dispatchPacket]
  )

  const laneIdToQueueJobId = useMemo(() => {
    if (!parsedBoard || !backendConcurrencyToken) {
      return {}
    }

    return Object.fromEntries(
      parsedBoard.lanes.map((lane) => [
        lane.id,
        createDeveloperLaneQueueJobId(lane.id, backendConcurrencyToken),
      ])
    )
  }, [backendConcurrencyToken, parsedBoard])

  const queueEntryMaterialization = useMemo(
    () => materializeDeveloperLaneQueueEntry(queueCandidate, laneIdToQueueJobId),
    [laneIdToQueueJobId, queueCandidate]
  )

  const selectedLaneQueueJobId = useMemo(() => {
    if (!selectedLane || !backendConcurrencyToken) {
      return null
    }

    return createDeveloperLaneQueueJobId(selectedLane.id, backendConcurrencyToken)
  }, [backendConcurrencyToken, selectedLane])

  const preferredMissionId = useMemo(
    () => getPreferredMissionId(selectedLane, closeoutReceiptRecord),
    [closeoutReceiptRecord, selectedLane]
  )
  const preferredMissionLookup = useMemo(
    () => getPreferredMissionLookup(selectedLane, selectedLaneQueueJobId, closeoutReceiptRecord),
    [closeoutReceiptRecord, selectedLane, selectedLaneQueueJobId]
  )

  useEffect(() => {
    missionStateRecordRef.current = missionStateRecord
  }, [missionStateRecord])

  useEffect(() => {
    if (!selectedLane && lanes.length === 0) {
      setSelectedLaneId(null)
      return
    }

    if (selectedLane) {
      return
    }

    setSelectedLaneId(lanes[0]?.id ?? null)
  }, [lanes, selectedLane])

  useEffect(() => {
    setExtraOwnersInput('')
    const shouldPreserveCompletionDraft = completionDraftTargetLaneRef.current === selectedLane?.id
    if (!shouldPreserveCompletionDraft) {
      setCompletionClosureSummary('')
      setCompletionEvidenceInput('')
    }
    setLastCompletionWriteResult(null)
    completionDraftTargetLaneRef.current = null
  }, [selectedLane?.id])

  useEffect(() => {
    setCloseoutReceiptState('idle')
    setCloseoutReceiptRecord(null)
    setCloseoutReceiptError(null)
    setCloseoutReceiptLastCheckedAt(null)
  }, [selectedLaneQueueJobId])

  const refreshActiveBoard = useCallback(async () => {
    startBackendHydration()

    try {
      const response = await fetchDeveloperControlPlaneActiveBoard()
      if (response.exists && response.record) {
        hydrateFromBackendRecord(response.record)
        return response.record
      }

      markNoRemoteRecord()
      return null
    } catch (error) {
      const persistenceErrorSummary = getDeveloperControlPlanePersistenceErrorSummary(error)
      markBackendUnavailable(
        persistenceErrorSummary.message,
        persistenceErrorSummary.kind
      )
      return null
    }
  }, [
    hydrateFromBackendRecord,
    markBackendUnavailable,
    markNoRemoteRecord,
    startBackendHydration,
  ])

  const loadBoardVersions = useCallback(async () => {
    setBoardVersionsState('loading')
    setBoardVersionsError(null)

    try {
      const response = await fetchDeveloperControlPlaneActiveBoardVersions()
      setBoardVersionsRecord(response)
      setBoardVersionsState('ready')
      setBoardVersionsLastCheckedAt(new Date().toISOString())
      return response
    } catch (error) {
      setBoardVersionsState('error')
      setBoardVersionsError(getDeveloperControlPlanePersistenceErrorMessage(error))
      return null
    }
  }, [])

  const loadLearnings = useCallback(async (query: LearningLedgerQuery = learningLedgerQueryRef.current) => {
    const normalizedQuery: LearningLedgerQuery = {
      limit: query.limit ?? 6,
      entryType: query.entryType ?? null,
      sourceClassification: query.sourceClassification ?? null,
      sourceLaneId: query.sourceLaneId ?? null,
      queueJobId: query.queueJobId ?? null,
      linkedMissionId: query.linkedMissionId ?? null,
    }

    learningLedgerQueryRef.current = normalizedQuery
    setLearningLedgerQuery(normalizedQuery)
    setLearningLedgerState('loading')
    setLearningLedgerError(null)

    try {
      const response = await fetchDeveloperControlPlaneLearnings(normalizedQuery)
      setLearningLedgerRecord(response)
      setLearningLedgerState('ready')
      setLearningLedgerLastCheckedAt(new Date().toISOString())
      return response
    } catch (error) {
      setLearningLedgerRecord(null)
      setLearningLedgerState('error')
      setLearningLedgerError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setLearningLedgerLastCheckedAt(new Date().toISOString())
      return null
    }
  }, [])

  useEffect(() => {
    if (!hasHydrated || remoteLoadStartedRef.current) {
      return
    }

    remoteLoadStartedRef.current = true

    void (async () => {
      await refreshActiveBoard()
    })()
  }, [hasHydrated, refreshActiveBoard])

  useEffect(() => {
    if (
      activeTab !== 'planner' ||
      persistenceStatus.tone !== 'synced' ||
      boardVersionsState !== 'idle'
    ) {
      return
    }

    void loadBoardVersions()
  }, [activeTab, boardVersionsState, loadBoardVersions, persistenceStatus.tone])

  useEffect(() => {
    if (
      activeTab !== 'overview' ||
      persistenceStatus.tone !== 'synced' ||
      learningLedgerState !== 'idle'
    ) {
      return
    }

    void loadLearnings({ limit: 6 })
  }, [activeTab, learningLedgerState, loadLearnings, persistenceStatus.tone])

  useEffect(() => {
    const shouldBootstrapSharedBoard =
      backendHydrationState === 'no-record' && backendConcurrencyToken === null

    if (!hasHydrated || !parsedBoard || (!hasUnsavedChanges && !shouldBootstrapSharedBoard)) {
      return
    }

    if (
      backendHydrationState === 'idle' ||
      backendHydrationState === 'loading' ||
      backendHydrationState === 'unavailable' ||
      saveState === 'saving' ||
      saveState === 'conflict' ||
      saveState === 'error'
    ) {
      return
    }

    const saveTimer = window.setTimeout(() => {
      void (async () => {
        markSaveStart()

        try {
          const record = await saveDeveloperControlPlaneActiveBoard({
            canonical_board_json: rawBoardJson,
            save_source: shouldBootstrapSharedBoard
              ? 'hidden-route-bootstrap'
              : 'hidden-route-ui',
            concurrency_token: backendConcurrencyToken,
          })
          markSaveSuccess(record)
        } catch (error) {
          const conflictRecordResponse = getDeveloperControlPlaneConflictRecord(error)
          const persistenceErrorSummary = getDeveloperControlPlanePersistenceErrorSummary(error)
          const message = persistenceErrorSummary.message

          if (conflictRecordResponse) {
            markSaveConflict(conflictRecordResponse, message)
            return
          }

          markSaveError(message, persistenceErrorSummary.kind)
        }
      })()
    }, 400)

    return () => {
      window.clearTimeout(saveTimer)
    }
  }, [
    backendConcurrencyToken,
    backendHydrationState,
    hasHydrated,
    hasUnsavedChanges,
    markSaveConflict,
    markSaveError,
    markSaveStart,
    markSaveSuccess,
    parsedBoard,
    rawBoardJson,
    saveState,
  ])

  const commitBoardUpdate = (updater: (board: DeveloperMasterBoard) => void) => {
    if (!parsedBoard) {
      return
    }

    const nextBoard = parseDeveloperMasterBoard(useDevMasterBoardStore.getState().rawBoardJson)
    updater(nextBoard)
    replaceBoardJson(serializeDeveloperMasterBoard(nextBoard))
  }

  const handleUpdateBoardTextField = (field: PlannerBoardTextField, value: string) => {
    updateBoardTextField(commitBoardUpdate, field, value)
  }

  const updateLaneField = (
    field: PlannerLaneField,
    value: string | DeveloperBoardStatus | string[]
  ) => {
    if (!selectedLane) {
      return
    }

    commitBoardUpdate((board) => {
      const lane = board.lanes.find((entry) => entry.id === selectedLane.id)
      if (!lane) {
        return
      }

      Object.assign(lane, { [field]: value })
    })
  }

  const updateValidationBasisField = (
    field: PlannerLaneValidationBasisField,
    value: string | string[]
  ) => {
    if (!selectedLane) {
      return
    }

    commitBoardUpdate((board) => {
      const lane = board.lanes.find((entry) => entry.id === selectedLane.id)
      if (!lane) {
        return
      }

      const nextValidationBasis: DeveloperBoardLaneValidationBasis = {
        owner: lane.validation_basis?.owner ?? '',
        summary: lane.validation_basis?.summary ?? '',
        evidence: [...(lane.validation_basis?.evidence ?? [])],
        last_reviewed_at: lane.validation_basis?.last_reviewed_at ?? '',
      }

      if (field === 'evidence') {
        if (!Array.isArray(value)) {
          return
        }

        nextValidationBasis.evidence = [...value]
      } else {
        if (Array.isArray(value)) {
          return
        }

        if (field === 'owner') {
          nextValidationBasis.owner = value
        } else if (field === 'summary') {
          nextValidationBasis.summary = value
        } else {
          nextValidationBasis.last_reviewed_at = value
        }
      }

      const hasAnyValidationBasisValue =
        nextValidationBasis.owner.trim().length > 0 ||
        nextValidationBasis.summary.trim().length > 0 ||
        nextValidationBasis.last_reviewed_at.trim().length > 0 ||
        nextValidationBasis.evidence.length > 0

      lane.validation_basis = hasAnyValidationBasisValue ? nextValidationBasis : undefined
    })
  }

  const updateReviewStateField = (
    reviewField: PlannerLaneReviewStateField,
    field: PlannerLaneReviewGateField,
    value: string | string[]
  ) => {
    if (!selectedLane) {
      return
    }

    commitBoardUpdate((board) => {
      const lane = board.lanes.find((entry) => entry.id === selectedLane.id)
      if (!lane) {
        return
      }

      const nextReviewState: DeveloperBoardLaneReviewState = {
        spec_review: lane.review_state?.spec_review
          ? {
              reviewed_by: lane.review_state.spec_review.reviewed_by,
              summary: lane.review_state.spec_review.summary,
              evidence: [...lane.review_state.spec_review.evidence],
              reviewed_at: lane.review_state.spec_review.reviewed_at,
            }
          : undefined,
        risk_review: lane.review_state?.risk_review
          ? {
              reviewed_by: lane.review_state.risk_review.reviewed_by,
              summary: lane.review_state.risk_review.summary,
              evidence: [...lane.review_state.risk_review.evidence],
              reviewed_at: lane.review_state.risk_review.reviewed_at,
            }
          : undefined,
        verification_evidence: lane.review_state?.verification_evidence
          ? {
              reviewed_by: lane.review_state.verification_evidence.reviewed_by,
              summary: lane.review_state.verification_evidence.summary,
              evidence: [...lane.review_state.verification_evidence.evidence],
              reviewed_at: lane.review_state.verification_evidence.reviewed_at,
            }
          : undefined,
      }

      const currentReviewGate: DeveloperBoardLaneReviewGate = nextReviewState[reviewField]
        ? {
            reviewed_by: nextReviewState[reviewField]!.reviewed_by,
            summary: nextReviewState[reviewField]!.summary,
            evidence: [...nextReviewState[reviewField]!.evidence],
            reviewed_at: nextReviewState[reviewField]!.reviewed_at,
          }
        : {
            reviewed_by: '',
            summary: '',
            evidence: [],
            reviewed_at: '',
          }

      if (field === 'evidence') {
        if (!Array.isArray(value)) {
          return
        }

        currentReviewGate.evidence = [...value]
      } else {
        if (Array.isArray(value)) {
          return
        }

        currentReviewGate[field] = value
      }

      const hasAnyReviewGateValue =
        currentReviewGate.reviewed_by.trim().length > 0 ||
        currentReviewGate.summary.trim().length > 0 ||
        currentReviewGate.reviewed_at.trim().length > 0 ||
        currentReviewGate.evidence.length > 0

      nextReviewState[reviewField] = hasAnyReviewGateValue ? currentReviewGate : undefined

      const hasAnyReviewStateValue = Boolean(
        nextReviewState.spec_review ||
          nextReviewState.risk_review ||
          nextReviewState.verification_evidence
      )

      lane.review_state = hasAnyReviewStateValue ? nextReviewState : undefined
    })
  }

  const handleCreateLane = () => {
    const nextIndex = lanes.length + 1
    const lane = createDeveloperLaneTemplate(nextIndex)

    commitBoardUpdate((board) => {
      board.lanes.unshift(lane)
    })

    setSelectedLaneId(lane.id)
    setActiveTab('planner')
  }

  const handleDeleteLane = () => {
    if (!selectedLane) {
      return
    }

    const currentIndex = lanes.findIndex((lane) => lane.id === selectedLane.id)
    const fallbackLane = lanes[currentIndex + 1] ?? lanes[currentIndex - 1] ?? null

    commitBoardUpdate((board) => {
      board.lanes = board.lanes.filter((lane) => lane.id !== selectedLane.id)
    })

    setSelectedLaneId(fallbackLane?.id ?? null)
  }

  const handleToggleOwner = (owner: string) => {
    if (!selectedLane) {
      return
    }

    const nextOwners = selectedLane.owners.includes(owner)
      ? selectedLane.owners.filter((entry) => entry !== owner)
      : [...selectedLane.owners, owner]

    updateLaneField('owners', nextOwners)
  }

  const handleAddExtraOwners = () => {
    if (!selectedLane) {
      return
    }

    const additions = extraOwnersInput
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean)

    if (additions.length === 0) {
      return
    }

    updateLaneField('owners', Array.from(new Set([...selectedLane.owners, ...additions])))
    setExtraOwnersInput('')
  }

  const handleAddSubplan = () => {
    if (!selectedLane) {
      return
    }

    commitBoardUpdate((board) => {
      const lane = board.lanes.find((entry) => entry.id === selectedLane.id)
      if (!lane) {
        return
      }

      lane.subplans.push(createDeveloperSubplanTemplate(lane.subplans.length + 1))
    })
  }

  const handleUpdateSubplan = (
    subplanId: string,
    field: PlannerSubplanField,
    value: string | DeveloperBoardStatus | string[]
  ) => {
    if (!selectedLane) {
      return
    }

    commitBoardUpdate((board) => {
      const lane = board.lanes.find((entry) => entry.id === selectedLane.id)
      const subplan = lane?.subplans.find((entry) => entry.id === subplanId)
      if (!subplan) {
        return
      }

      Object.assign(subplan, { [field]: value })
    })
  }

  const handleDeleteSubplan = (subplanId: string) => {
    if (!selectedLane) {
      return
    }

    commitBoardUpdate((board) => {
      const lane = board.lanes.find((entry) => entry.id === selectedLane.id)
      if (!lane) {
        return
      }

      lane.subplans = lane.subplans.filter((entry) => entry.id !== subplanId)
    })
  }

  const handlePromoteLane = (laneId: string) => {
    const lane = lanes.find((entry) => entry.id === laneId)
    const laneAnalysis = autonomyAnalysis?.laneAnalyses.find((entry) => entry.laneId === laneId)

    if (!lane || lane.status !== 'planned' || laneAnalysis?.readiness !== 'ready') {
      return
    }

    setSelectedLaneId(laneId)
    commitBoardUpdate((board) => {
      const targetLane = board.lanes.find((entry) => entry.id === laneId)
      if (!targetLane) {
        return
      }

      targetLane.status = 'active'
    })
  }

  const handleCopyDispatchPacket = async () => {
    if (!dispatchPacket || typeof navigator === 'undefined' || !navigator.clipboard) {
      return
    }

    await navigator.clipboard.writeText(`${JSON.stringify(dispatchPacket, null, 2)}\n`)
  }

  const handleCopyQueueCandidate = async () => {
    if (!queueCandidate || typeof navigator === 'undefined' || !navigator.clipboard) {
      return
    }

    await navigator.clipboard.writeText(`${JSON.stringify(queueCandidate, null, 2)}\n`)
  }

  const handleCopyQueueEntry = async () => {
    if (
      !queueEntryMaterialization.entry ||
      typeof navigator === 'undefined' ||
      !navigator.clipboard
    ) {
      return
    }

    await navigator.clipboard.writeText(
      `${JSON.stringify(queueEntryMaterialization.entry, null, 2)}\n`
    )
  }

  const loadCloseoutReceipt = async (queueJobId: string) => {
    setCloseoutReceiptState('loading')
    setCloseoutReceiptError(null)

    try {
      const receipt = await fetchDeveloperControlPlaneCloseoutReceipt(queueJobId)
      setCloseoutReceiptRecord(receipt)
      setCloseoutReceiptState(receipt.exists ? 'available' : 'missing')
      setCloseoutReceiptLastCheckedAt(new Date().toISOString())
      return receipt
    } catch (error) {
      setCloseoutReceiptRecord(null)
      setCloseoutReceiptState('error')
      setCloseoutReceiptError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setCloseoutReceiptLastCheckedAt(new Date().toISOString())
      return null
    }
  }

  const loadRuntimeWatchdogStatus = async () => {
    setRuntimeWatchdogState('loading')
    setRuntimeWatchdogError(null)

    try {
      const watchdogStatus = await fetchDeveloperControlPlaneWatchdogStatus()
      setRuntimeWatchdogRecord(watchdogStatus)
      setRuntimeWatchdogState('ready')
      setRuntimeWatchdogLastCheckedAt(new Date().toISOString())
      return watchdogStatus
    } catch (error) {
      setRuntimeWatchdogRecord(null)
      setRuntimeWatchdogState('error')
      setRuntimeWatchdogError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setRuntimeWatchdogLastCheckedAt(new Date().toISOString())
      return null
    }
  }

  const loadRuntimeAutonomyCycle = async () => {
    setRuntimeAutonomyCycleState('loading')
    setRuntimeAutonomyCycleError(null)

    try {
      const autonomyCycle = await fetchDeveloperControlPlaneAutonomyCycle()
      setRuntimeAutonomyCycleRecord(autonomyCycle)
      setRuntimeAutonomyCycleState(autonomyCycle.exists ? 'ready' : 'missing')
      setRuntimeAutonomyCycleLastCheckedAt(new Date().toISOString())
      return autonomyCycle
    } catch (error) {
      setRuntimeAutonomyCycleRecord(null)
      setRuntimeAutonomyCycleState('error')
      setRuntimeAutonomyCycleError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setRuntimeAutonomyCycleLastCheckedAt(new Date().toISOString())
      return null
    }
  }

  const loadRuntimeCompletionAssist = async () => {
    setRuntimeCompletionAssistState('loading')
    setRuntimeCompletionAssistError(null)

    try {
      const completionAssist = await fetchDeveloperControlPlaneRuntimeCompletionAssist()
      setRuntimeCompletionAssistRecord(completionAssist)
      setRuntimeCompletionAssistState(completionAssist.exists ? 'ready' : 'missing')
      setRuntimeCompletionAssistLastCheckedAt(new Date().toISOString())
      return completionAssist
    } catch (error) {
      setRuntimeCompletionAssistRecord(null)
      setRuntimeCompletionAssistState('error')
      setRuntimeCompletionAssistError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setRuntimeCompletionAssistLastCheckedAt(new Date().toISOString())
      return null
    }
  }

  const loadSilentMonitors = async () => {
    setSilentMonitorsState('loading')
    setSilentMonitorsError(null)

    try {
      const monitorSnapshot = await fetchDeveloperControlPlaneSilentMonitors()
      setSilentMonitorsRecord(monitorSnapshot)
      setSilentMonitorsState('ready')
      setSilentMonitorsLastCheckedAt(new Date().toISOString())
      return monitorSnapshot
    } catch (error) {
      setSilentMonitorsRecord(null)
      setSilentMonitorsState('error')
      setSilentMonitorsError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setSilentMonitorsLastCheckedAt(new Date().toISOString())
      return null
    }
  }

  const loadMissionState = async (
    preferredMissionId: string | null = null,
    preferredMissionLookupOverride: { queueJobId: string | null; sourceLaneId: string | null } | null = null
  ) => {
    const requestKey = JSON.stringify({
      preferredMissionId,
      queueJobId: preferredMissionLookupOverride?.queueJobId ?? null,
      sourceLaneId: preferredMissionLookupOverride?.sourceLaneId ?? null,
    })

    if (missionStateLoadRef.current?.key === requestKey) {
      return missionStateLoadRef.current.promise
    }

    setMissionStateState('loading')
    setMissionStateError(null)

    const inFlightRequest = {
      key: requestKey,
      promise: Promise.resolve(null) as Promise<DeveloperControlPlaneMissionStateResponse | null>,
    }

    inFlightRequest.promise = (async () => {
      try {
        const existingPreferredMission = findPreferredMissionSummary(
          missionStateRecordRef.current,
          preferredMissionId,
          preferredMissionLookupOverride
        )
        const [missionState, filteredMissionState] = await Promise.all([
          fetchDeveloperControlPlaneMissionState(),
          preferredMissionLookupOverride
            ? fetchDeveloperControlPlaneMissionState({
                limit: 1,
                queueJobId: preferredMissionLookupOverride.queueJobId,
                sourceLaneId: preferredMissionLookupOverride.sourceLaneId,
              })
            : Promise.resolve(null),
        ])
        const mergedMissionState = mergeMissionStateRecords(
          mergeMissionStateRecords(missionState, filteredMissionState),
          existingPreferredMission
            ? {
                count: 1,
                missions: [existingPreferredMission],
              }
            : null
        )
        missionStateRecordRef.current = mergedMissionState
        setMissionStateRecord(mergedMissionState)
        setMissionStateState('ready')
        setMissionStateLastCheckedAt(new Date().toISOString())
        const matchingMissionId =
          preferredMissionId &&
          mergedMissionState.missions.some((mission) => mission.mission_id === preferredMissionId)
            ? preferredMissionId
            : null
        const missionDetailTarget =
          matchingMissionId ??
          filteredMissionState?.missions[0]?.mission_id ??
          mergedMissionState.missions[0]?.mission_id ??
          null

        if (missionDetailTarget) {
          await loadMissionDetail(missionDetailTarget)
        } else {
          setMissionDetailState('idle')
          setMissionDetailRecord(null)
          setMissionDetailError(null)
          setMissionDetailLastCheckedAt(null)
        }
        return mergedMissionState
      } catch (error) {
        missionStateRecordRef.current = null
        setMissionStateRecord(null)
        setMissionStateState('error')
        setMissionStateError(getDeveloperControlPlanePersistenceErrorMessage(error))
        setMissionStateLastCheckedAt(new Date().toISOString())
        setMissionDetailState('idle')
        setMissionDetailRecord(null)
        setMissionDetailError(null)
        setMissionDetailLastCheckedAt(null)
        return null
      } finally {
        if (missionStateLoadRef.current === inFlightRequest) {
          missionStateLoadRef.current = null
        }
      }
    })()

    missionStateLoadRef.current = inFlightRequest

    return inFlightRequest.promise
  }

  const loadMissionDetail = async (missionId: string) => {
    setMissionDetailState('loading')
    setMissionDetailError(null)

    try {
      const missionDetail = await fetchDeveloperControlPlaneMissionDetail(missionId)
      setMissionDetailRecord(missionDetail)
      setMissionDetailState('ready')
      setMissionDetailLastCheckedAt(new Date().toISOString())
      return missionDetail
    } catch (error) {
      setMissionDetailRecord(null)
      setMissionDetailState('error')
      setMissionDetailError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setMissionDetailLastCheckedAt(new Date().toISOString())
      return null
    }
  }

  const refreshIndigenousBrain = useCallback(async (projectBrainQuery?: string | null) => {
    setIndigenousBrainState('loading')
    setIndigenousBrainError(null)

    try {
      const brief = await fetchDeveloperControlPlaneIndigenousBrainBrief(projectBrainQuery)
      setIndigenousBrainBrief(brief)
      setIndigenousBrainState('ready')
      setIndigenousBrainLastCheckedAt(new Date().toISOString())
      return brief
    } catch (error) {
      setIndigenousBrainBrief(null)
      setIndigenousBrainState('error')
      setIndigenousBrainError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setIndigenousBrainLastCheckedAt(new Date().toISOString())
      return null
    }
  }, [])

  useEffect(() => {
    if (!hasHydrated || activeTab !== 'indigenous' || indigenousBrainState !== 'idle') {
      return
    }

    void refreshIndigenousBrain()
  }, [activeTab, hasHydrated, indigenousBrainState, refreshIndigenousBrain])

  useEffect(() => {
    if (!hasHydrated || persistenceStatus.tone !== 'synced') {
      return
    }

    void loadMissionState(preferredMissionId, preferredMissionLookup)
  }, [
    hasHydrated,
    persistenceStatus.tone,
    backendConcurrencyToken,
    preferredMissionId,
    preferredMissionLookup,
  ])

  const refreshQueueStatus = async (
    queueJobIdOverride: string | null = null,
    sourceLaneIdOverride: string | null = null
  ) => {
    setQueueStatusState('loading')
    setQueueStatusError(null)

    try {
      const status = await fetchDeveloperControlPlaneOvernightQueueStatus()
      setQueueStatusRecord(status)
      setQueueStatusState('ready')
      setQueueStatusLastRefreshedAt(new Date().toISOString())

      const effectiveQueueJobId = queueJobIdOverride ?? selectedLaneQueueJobId
      const effectiveSelectedLane = sourceLaneIdOverride
        ? lanes.find((lane) => lane.id === sourceLaneIdOverride) ?? selectedLane
        : selectedLane
      const shouldLoadMissionContext = persistenceStatus.tone === 'synced'
      const runtimeWatchdogPromise = loadRuntimeWatchdogStatus()
      const runtimeAutonomyCyclePromise = loadRuntimeAutonomyCycle()
      const runtimeCompletionAssistPromise = loadRuntimeCompletionAssist()
      const silentMonitorsPromise = loadSilentMonitors()
      const preferredMissionLookupOverride =
        effectiveSelectedLane && effectiveQueueJobId
          ? {
              queueJobId: effectiveQueueJobId,
              sourceLaneId: effectiveSelectedLane.id,
            }
          : preferredMissionLookup
      const missionStatePromise = shouldLoadMissionContext
        ? loadMissionState(preferredMissionId, preferredMissionLookupOverride)
        : Promise.resolve(null)

      if (shouldLoadMissionContext && effectiveQueueJobId) {
        await Promise.all([
          loadCloseoutReceipt(effectiveQueueJobId),
          runtimeWatchdogPromise,
          runtimeAutonomyCyclePromise,
          runtimeCompletionAssistPromise,
          silentMonitorsPromise,
          missionStatePromise,
        ])
      } else {
        setCloseoutReceiptState('idle')
        setCloseoutReceiptRecord(null)
        setCloseoutReceiptError(null)
        setCloseoutReceiptLastCheckedAt(null)
        await Promise.all([
          runtimeWatchdogPromise,
          runtimeAutonomyCyclePromise,
          runtimeCompletionAssistPromise,
          silentMonitorsPromise,
          missionStatePromise,
        ])
      }

      return status
    } catch (error) {
      setQueueStatusState('error')
      setQueueStatusError(getDeveloperControlPlanePersistenceErrorMessage(error))
      setQueueStatusLastRefreshedAt(new Date().toISOString())
      setCloseoutReceiptState('idle')
      setCloseoutReceiptRecord(null)
      setCloseoutReceiptError(null)
      setCloseoutReceiptLastCheckedAt(null)
      return null
    }
  }

  const deriveQueueJobIdFromRecord = (
    canonicalBoardJson: string,
    concurrencyToken: string,
    laneId: string | null
  ) => {
    // Guided refresh can replace the shared board token before queue/receipt refreshes run,
    // so derive the deterministic queue job id from the refreshed board payload instead of
    // relying on the stale job id captured before the refresh sequence started.
    if (!laneId) {
      return null
    }

    const board = parseDeveloperMasterBoard(canonicalBoardJson)
    const laneExists = board.lanes.some((lane) => lane.id === laneId)
    if (!laneExists) {
      return null
    }

    return createDeveloperLaneQueueJobId(laneId, concurrencyToken)
  }

  const deriveLiveWriteContext = (
    rawBoardJsonOverride = useDevMasterBoardStore.getState().rawBoardJson,
    backendConcurrencyTokenOverride = useDevMasterBoardStore.getState().backendConcurrencyToken,
    selectedLaneIdOverride = selectedLaneId
  ): LiveWriteContext => {
    const liveViewModel = deriveDeveloperMasterBoardViewModel(
      rawBoardJsonOverride,
      selectedLaneIdOverride,
      hasHydrated,
      storageAvailable,
      useDevMasterBoardStore.getState().backendHydrationState,
      useDevMasterBoardStore.getState().saveState,
      useDevMasterBoardStore.getState().persistenceError,
      useDevMasterBoardStore.getState().persistenceErrorKind,
      useDevMasterBoardStore.getState().conflictRecord?.updated_at ?? null
    )

    const liveLaneIdToQueueJobId =
      liveViewModel.parsedBoard && backendConcurrencyTokenOverride
        ? Object.fromEntries(
            liveViewModel.parsedBoard.lanes.map((lane) => [
              lane.id,
              createDeveloperLaneQueueJobId(lane.id, backendConcurrencyTokenOverride),
            ])
          )
        : {}

    const liveQueueCandidate = createDeveloperLaneQueueCandidate(
      liveViewModel.dispatchPacket,
      backendConcurrencyTokenOverride
    )
    const liveQueueEntryMaterialization = materializeDeveloperLaneQueueEntry(
      liveQueueCandidate,
      liveLaneIdToQueueJobId
    )
    const liveSelectedLaneQueueJobId =
      liveViewModel.selectedLane && backendConcurrencyTokenOverride
        ? createDeveloperLaneQueueJobId(
            liveViewModel.selectedLane.id,
            backendConcurrencyTokenOverride
          )
        : null

    return {
      backendConcurrencyToken: backendConcurrencyTokenOverride,
      selectedLane: liveViewModel.selectedLane,
      selectedLaneAnalysis: liveViewModel.selectedLaneAnalysis,
      queueEntry: liveQueueEntryMaterialization.entry,
      selectedLaneQueueJobId: liveSelectedLaneQueueJobId,
    }
  }

  const handleRefreshRecommendedTargets = async (
    targets: DeveloperControlPlaneConflictRefreshTarget[]
  ) => {
    const normalizedTargets = normalizeRefreshTargets(targets)
    if (normalizedTargets.length === 0) {
      return { activeBoardRefreshFailed: false }
    }

    let effectiveQueueJobId = selectedLaneQueueJobId
    let activeBoardRefreshFailed = false

    if (normalizedTargets.includes('active-board')) {
      const refreshedRecord = await refreshActiveBoard()
      if (refreshedRecord) {
        effectiveQueueJobId = deriveQueueJobIdFromRecord(
          refreshedRecord.canonical_board_json,
          refreshedRecord.concurrency_token,
          selectedLaneId
        )
      } else {
        activeBoardRefreshFailed = true
      }
    }

    // If board refresh was the only requested target and it failed, stop here. When the
    // payload also recommends queue or receipt refreshes, still attempt them because those
    // surfaces can provide useful recovery evidence even while board hydration is unavailable.
    if (activeBoardRefreshFailed && normalizedTargets.length === 1) {
      return { activeBoardRefreshFailed }
    }

    let queueWasRefreshed = false

    if (normalizedTargets.includes('overnight-queue')) {
      await refreshQueueStatus(effectiveQueueJobId)
      queueWasRefreshed = true
    }

    if (
      normalizedTargets.includes('closeout-receipt') &&
      effectiveQueueJobId &&
      !queueWasRefreshed
    ) {
      await loadCloseoutReceipt(effectiveQueueJobId)
    }

    return { activeBoardRefreshFailed }
  }

  const handleRefreshAndRetryQueueWrite = async () => {
    if (
      lastQueueWriteResult?.status !== 'conflict' ||
      lastQueueWriteResult.retryPermittedAfterRefresh !== true
    ) {
      return
    }

    const refreshOutcome = await handleRefreshRecommendedTargets(lastQueueWriteResult.refreshTargets)

    if (
      lastQueueWriteResult.refreshTargets.includes('active-board') &&
      refreshOutcome.activeBoardRefreshFailed
    ) {
      return
    }

    const liveWriteContext = deriveLiveWriteContext()
    if (
      !liveWriteContext.queueEntry ||
      !liveWriteContext.backendConcurrencyToken ||
      liveWriteContext.selectedLaneAnalysis?.readiness !== 'ready'
    ) {
      return
    }

    await handleWriteQueueEntry()
  }

  const handleRefreshAndRetryLaneCompletion = async () => {
    if (
      lastCompletionWriteResult?.status !== 'conflict' ||
      lastCompletionWriteResult.retryPermittedAfterRefresh !== true
    ) {
      return
    }

    const refreshOutcome = await handleRefreshRecommendedTargets(
      lastCompletionWriteResult.refreshTargets
    )

    if (
      lastCompletionWriteResult.refreshTargets.includes('active-board') &&
      refreshOutcome.activeBoardRefreshFailed
    ) {
      return
    }

    const liveWriteContext = deriveLiveWriteContext()
    const closureSummary = completionClosureSummary.trim()
    const evidence = completionEvidenceInput
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)

    if (
      !liveWriteContext.selectedLane ||
      !liveWriteContext.backendConcurrencyToken ||
      !liveWriteContext.selectedLaneQueueJobId ||
      liveWriteContext.selectedLane.status !== 'active' ||
      !closureSummary ||
      evidence.length === 0
    ) {
      return
    }

    await handleWriteLaneCompletion()
  }

  useEffect(() => {
    if (!hasHydrated || queueBootstrapStartedRef.current || queueStatusState !== 'idle') {
      return
    }

    queueBootstrapStartedRef.current = true
    void refreshQueueStatus()
  }, [hasHydrated, queueStatusState, refreshQueueStatus])

  useEffect(() => {
    if (
      !hasHydrated ||
      persistenceStatus.tone !== 'synced' ||
      !selectedLaneQueueJobId ||
      closeoutReceiptState !== 'idle'
    ) {
      return
    }

    void loadCloseoutReceipt(selectedLaneQueueJobId)
  }, [
    closeoutReceiptState,
    hasHydrated,
    persistenceStatus.tone,
    selectedLaneQueueJobId,
  ])

  const handleRestoreBoardVersion = async (revisionId: number) => {
    setBoardRestoreState('restoring')
    setLastBoardRestoreResult(null)

    try {
      const previousBoardConcurrencyToken = backendConcurrencyToken
      const response = await restoreDeveloperControlPlaneActiveBoardVersion(
        revisionId,
        previousBoardConcurrencyToken
      )

      hydrateFromBackendRecord(response.record)
      await loadBoardVersions()

      setBoardRestoreState('restored')
      setLastBoardRestoreResult({
        status: 'restored',
        message: appendApprovalReceiptMessage(
          response.restored
            ? `Board restored from immutable revision ${response.restored_from_revision_id}.`
            : `Revision ${response.restored_from_revision_id} is already the active board head.`,
          response.approval_receipt
        ),
        restored: response.restored,
        restoredFromRevisionId: response.restored_from_revision_id,
        currentBoardConcurrencyToken: response.record.concurrency_token,
        previousBoardConcurrencyToken,
        approvalReceiptId: response.approval_receipt?.receipt_id ?? null,
        approvalReceiptRecordedAt: response.approval_receipt?.recorded_at ?? null,
      })
      void loadLearnings()
      return
    } catch (error) {
      const message = getDeveloperControlPlanePersistenceErrorMessage(error)

      if (isDeveloperControlPlaneConflictError(error)) {
        const conflictRecord = getDeveloperControlPlaneConflictRecord(error)

        setBoardRestoreState('conflict')
        setLastBoardRestoreResult({
          status: 'conflict',
          message,
          restored: false,
          restoredFromRevisionId: revisionId,
          currentBoardConcurrencyToken: conflictRecord?.concurrency_token ?? null,
          previousBoardConcurrencyToken: backendConcurrencyToken,
          approvalReceiptId: null,
          approvalReceiptRecordedAt: null,
        })
        return
      }

      setBoardRestoreState('error')
      setLastBoardRestoreResult({
        status: 'error',
        message,
        restored: false,
        restoredFromRevisionId: revisionId,
        currentBoardConcurrencyToken: null,
        previousBoardConcurrencyToken: backendConcurrencyToken,
        approvalReceiptId: null,
        approvalReceiptRecordedAt: null,
      })
    }
  }

  const handleWriteQueueEntry = async () => {
    const liveWriteContext = deriveLiveWriteContext()
    if (
      !liveWriteContext.queueEntry ||
      !liveWriteContext.backendConcurrencyToken ||
      liveWriteContext.selectedLaneAnalysis?.readiness !== 'ready'
    ) {
      return
    }

    setQueueWriteState('writing')
    setLastQueueWriteResult(null)
    let previousQueueStatus: DeveloperControlPlaneOvernightQueueStatusResponse | null = null

    try {
      const queueStatus = await refreshQueueStatus()
      previousQueueStatus = queueStatus
      if (!queueStatus) {
        setQueueWriteState('error')
        setLastQueueWriteResult({
          status: 'error',
          message: 'Queue status refresh failed before write attempt.',
          writtenJobId: null,
          previousQueueSha256: null,
          currentQueueSha256: null,
          queueUpdatedAt: null,
          approvalReceiptId: null,
          approvalReceiptRecordedAt: null,
          conflictReason: null,
          remediationMessage: getQueueConflictRemediationMessage(null),
          refreshTargets: [],
          retryPermittedAfterRefresh: null,
          currentBoardConcurrencyToken: null,
          conflictJobId: null,
        })
        return
      }

      const response = await writeDeveloperControlPlaneOvernightQueueEntry({
        source_board_concurrency_token: liveWriteContext.backendConcurrencyToken,
        expected_queue_sha256: queueStatus.queue_sha256,
        operator_intent: 'write-reviewed-queue-entry',
        queue_entry: liveWriteContext.queueEntry,
      })
      const refreshedQueueStatus = await refreshQueueStatus()

      setQueueWriteState('written')
      setLastQueueWriteResult({
        status: 'written',
        message: appendApprovalReceiptMessage(
          `Queue entry ${response.written_job_id} written with queue sha ${response.queue_sha256}.`,
          response.approval_receipt
        ),
        writtenJobId: response.written_job_id,
        previousQueueSha256: queueStatus.queue_sha256,
        currentQueueSha256: refreshedQueueStatus?.queue_sha256 ?? response.queue_sha256,
        queueUpdatedAt: refreshedQueueStatus?.updated_at ?? response.queue_updated_at,
        approvalReceiptId: response.approval_receipt?.receipt_id ?? null,
        approvalReceiptRecordedAt: response.approval_receipt?.recorded_at ?? null,
        conflictReason: null,
        remediationMessage: null,
        refreshTargets: [],
        retryPermittedAfterRefresh: null,
        currentBoardConcurrencyToken: null,
        conflictJobId: null,
      })
      void loadLearnings()
    } catch (error) {
      const message = getDeveloperControlPlanePersistenceErrorMessage(error)
      if (isDeveloperControlPlaneConflictError(error)) {
        const conflictDetail = getDeveloperControlPlaneOvernightQueueConflictDetail(error)
        const refreshedQueueStatus = await refreshQueueStatus()
        setQueueWriteState('conflict')
        setLastQueueWriteResult({
          status: 'conflict',
          message,
          writtenJobId: null,
          previousQueueSha256: previousQueueStatus?.queue_sha256 ?? null,
          currentQueueSha256:
            refreshedQueueStatus?.queue_sha256 ?? conflictDetail?.current_queue_sha256 ?? null,
          queueUpdatedAt: refreshedQueueStatus?.updated_at ?? null,
          approvalReceiptId: null,
          approvalReceiptRecordedAt: null,
          conflictReason: conflictDetail?.conflict_reason ?? null,
          remediationMessage:
            conflictDetail?.remediation_message ??
            getQueueConflictRemediationMessage(conflictDetail?.conflict_reason ?? null),
          refreshTargets:
            conflictDetail?.refresh_targets ??
            getQueueConflictRefreshTargets(conflictDetail?.conflict_reason ?? null),
          retryPermittedAfterRefresh: conflictDetail?.retry_permitted_after_refresh ?? null,
          currentBoardConcurrencyToken:
            conflictDetail?.current_board_concurrency_token ?? null,
          conflictJobId: conflictDetail?.job_id ?? null,
        })
        void loadLearnings()
        return
      }

      setQueueWriteState('error')
      setLastQueueWriteResult({
        status: 'error',
        message,
        writtenJobId: null,
        previousQueueSha256: previousQueueStatus?.queue_sha256 ?? null,
        currentQueueSha256: previousQueueStatus?.queue_sha256 ?? null,
        queueUpdatedAt: previousQueueStatus?.updated_at ?? null,
        approvalReceiptId: null,
        approvalReceiptRecordedAt: null,
        conflictReason: null,
        remediationMessage: getQueueConflictRemediationMessage(null),
        refreshTargets: [],
        retryPermittedAfterRefresh: null,
        currentBoardConcurrencyToken: null,
        conflictJobId: null,
      })
    }
  }

  const handleWriteLaneCompletion = async () => {
    const liveWriteContext = deriveLiveWriteContext()
    if (!liveWriteContext.selectedLane) {
      return
    }

    const closureSummary = completionClosureSummary.trim()
    const evidence = completionEvidenceInput
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)

    if (
      liveWriteContext.selectedLane.status !== 'active' ||
      !closureSummary ||
      evidence.length === 0
    ) {
      return
    }

    setCompletionWriteState('writing')
    setLastCompletionWriteResult(null)

    let preparedQueueStatus: DeveloperControlPlaneOvernightQueueStatusResponse | null = null
    let preparedCloseoutReceipt: DeveloperControlPlaneCloseoutReceiptResponse | null = null
    let preparedQueueJobId = liveWriteContext.selectedLaneQueueJobId

    try {
      const prepared = await prepareDeveloperControlPlaneLaneCompletionWrite({
        source_lane_id: liveWriteContext.selectedLane.id,
      })
      applyPreparedCompletionWriteState(
        prepared,
        setQueueStatusState,
        setQueueStatusRecord,
        setQueueStatusLastRefreshedAt,
        setCloseoutReceiptState,
        setCloseoutReceiptRecord,
        setCloseoutReceiptLastCheckedAt
      )
      preparedQueueStatus = prepared.queue_status
      preparedCloseoutReceipt = prepared.closeout_receipt
      preparedQueueJobId = prepared.queue_job_id

      const response = await writeDeveloperControlPlaneLaneCompletion({
        ...prepared.prepared_request,
        completion: {
          ...prepared.prepared_request.completion,
          closure_summary: closureSummary,
          evidence,
        },
      })
      const nextRecommendedLaneHandoff = deriveNextRecommendedLaneHandoff(
        response.record.canonical_board_json,
        response.lane_id
      )

      hydrateFromBackendRecord(response.record)
      await loadMissionState(
        preparedCloseoutReceipt?.mission_id ?? null,
        getPreferredMissionLookup(
          liveWriteContext.selectedLane,
          preparedQueueJobId,
          preparedCloseoutReceipt
        )
      )
      setCompletionWriteState('written')
      setLastCompletionWriteResult({
        status: 'written',
        message: appendApprovalReceiptMessage(
          response.no_op
            ? `Completion write-back for lane ${response.lane_id} was already applied.`
            : `Lane ${response.lane_id} marked completed from queue job ${response.queue_job_id}.`,
          response.approval_receipt
        ),
        noOp: response.no_op,
        laneId: response.lane_id,
        laneStatus: response.lane_status,
        queueJobId: response.queue_job_id,
        queueSha256: response.queue_sha256,
        approvalReceiptId: response.approval_receipt?.receipt_id ?? null,
        approvalReceiptRecordedAt: response.approval_receipt?.recorded_at ?? null,
        conflictReason: null,
        remediationMessage: null,
        refreshTargets: [],
        retryPermittedAfterRefresh: null,
        currentBoardConcurrencyToken: response.record.concurrency_token,
        currentQueueSha256: preparedQueueStatus?.queue_sha256 ?? null,
        currentLaneStatus: response.lane_status,
        nextRecommendedLaneId: nextRecommendedLaneHandoff.nextRecommendedLaneId,
        nextRecommendedLaneTitle: nextRecommendedLaneHandoff.nextRecommendedLaneTitle,
      })
      void loadLearnings()
      return
    } catch (error) {
      const message = getDeveloperControlPlanePersistenceErrorMessage(error)
      if (isDeveloperControlPlaneConflictError(error)) {
        const conflictDetail = getDeveloperControlPlaneCompletionConflictDetail(error)
        const refreshedQueueStatus = await refreshQueueStatus()
        setCompletionWriteState('conflict')
        setLastCompletionWriteResult({
          status: 'conflict',
          message,
          noOp: false,
          laneId: liveWriteContext.selectedLane.id,
          laneStatus: liveWriteContext.selectedLane.status,
          queueJobId: preparedQueueJobId,
          queueSha256: preparedQueueStatus?.queue_sha256 ?? null,
          approvalReceiptId: null,
          approvalReceiptRecordedAt: null,
          conflictReason: conflictDetail?.conflict_reason ?? null,
          remediationMessage:
            conflictDetail?.remediation_message ??
            getCompletionConflictRemediationMessage(conflictDetail?.conflict_reason ?? null),
          refreshTargets:
            conflictDetail?.refresh_targets ??
            getCompletionConflictRefreshTargets(conflictDetail?.conflict_reason ?? null),
          retryPermittedAfterRefresh: conflictDetail?.retry_permitted_after_refresh ?? null,
          currentBoardConcurrencyToken:
            conflictDetail?.current_board_concurrency_token ?? null,
          currentQueueSha256:
            refreshedQueueStatus?.queue_sha256 ?? conflictDetail?.current_queue_sha256 ?? null,
          currentLaneStatus: conflictDetail?.current_lane_status ?? null,
          nextRecommendedLaneId: null,
          nextRecommendedLaneTitle: null,
        })
        void loadLearnings()
        return
      }

      setCompletionWriteState('error')
      setLastCompletionWriteResult({
        status: 'error',
        message,
        noOp: false,
        laneId: liveWriteContext.selectedLane.id,
        laneStatus: liveWriteContext.selectedLane.status,
        queueJobId: preparedQueueJobId,
        queueSha256: preparedQueueStatus?.queue_sha256 ?? null,
        approvalReceiptId: null,
        approvalReceiptRecordedAt: null,
        conflictReason: null,
        remediationMessage: getCompletionConflictRemediationMessage(null),
        refreshTargets: [],
        retryPermittedAfterRefresh: null,
        currentBoardConcurrencyToken: null,
        currentQueueSha256: preparedQueueStatus?.queue_sha256 ?? null,
        currentLaneStatus: null,
        nextRecommendedLaneId: null,
        nextRecommendedLaneTitle: null,
      })
    }
  }

  const handleDraftLaneCompletionFromCurrentState = async () => {
    if (!selectedLane) {
      return
    }

    const autonomyCyclePreparation = findAutonomyCycleCompletionWritePreparationForLane(
      runtimeAutonomyCycleRecord,
      selectedLane.id
    )
    const canUseCompletionAssistFallback =
      autonomyCyclePreparation === null &&
      (runtimeAutonomyCycleState !== 'ready' ||
        (runtimeAutonomyCycleRecord?.next_action_count ?? 0) === 0)

    await handleDraftLaneCompletionForLane(
      selectedLane.id,
      autonomyCyclePreparation ??
        (canUseCompletionAssistFallback
          ? findCompletionAssistPreparationForLane(runtimeCompletionAssistRecord, selectedLane.id)
          : null)
    )
  }

  const handleDraftLaneCompletionForLane = async (
    laneId: string,
    prepared: DeveloperControlPlaneCompletionWritePreparationResponse | null = null
  ) => {
    if (!backendConcurrencyToken) {
      setSelectedLaneId(laneId)
      return
    }

    completionDraftTargetLaneRef.current = laneId
    setSelectedLaneId(laneId)

    const liveWriteContext = deriveLiveWriteContext(undefined, undefined, laneId)
    if (!liveWriteContext.selectedLane) {
      return
    }

    const resolvedPrepared =
      prepared && prepared.source_lane_id === liveWriteContext.selectedLane.id
        ? prepared
        : await prepareDeveloperControlPlaneLaneCompletionWrite({
            source_lane_id: liveWriteContext.selectedLane.id,
          })
    applyPreparedCompletionWriteState(
      resolvedPrepared,
      setQueueStatusState,
      setQueueStatusRecord,
      setQueueStatusLastRefreshedAt,
      setCloseoutReceiptState,
      setCloseoutReceiptRecord,
      setCloseoutReceiptLastCheckedAt
    )

    setCompletionClosureSummary(resolvedPrepared.prepared_request.completion.closure_summary)
    setCompletionEvidenceInput(resolvedPrepared.prepared_request.completion.evidence.join('\n'))
  }

  const handleExport = () => {
    const serializedBoard = parsedBoard ? serializeDeveloperMasterBoard(parsedBoard) : rawBoardJson
    const blob = new Blob([serializedBoard], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'bijmantra-app-development-master-board.json'
    anchor.click()
    window.URL.revokeObjectURL(url)
  }

  const triggerImport = () => {
    fileInputRef.current?.click()
  }

  const handleImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }

    const text = await file.text()
    replaceBoardJson(canonicalizeDeveloperMasterBoardJson(text))
    event.target.value = ''
  }

  return {
    fileInputRef,
    rawBoardJson,
    lastUpdatedAt,
    activeTab,
    selectedLaneId,
    extraOwnersInput,
    parsedBoard,
    jsonError,
    lanes,
    activeLaneCount,
    blockedLaneCount,
    subplanCount,
    dependencyCount,
    selectedLane,
    availableAgents,
    autonomyAnalysis,
    selectedLaneAnalysis,
    recommendedLane,
    persistenceStatus,
    dispatchPacket,
    queueCandidate,
    queueEntryMaterialization,
    selectedLaneQueueJobId,
    queueWriteState,
    completionWriteState,
    boardVersionsState,
    boardVersionsRecord,
    boardVersionsError,
    boardVersionsLastCheckedAt,
    boardRestoreState,
    lastBoardRestoreResult,
    queueStatusState,
    queueStatusRecord,
    queueStatusError,
    queueStatusLastRefreshedAt,
    closeoutReceiptState,
    closeoutReceiptRecord,
    closeoutReceiptError,
    closeoutReceiptLastCheckedAt,
    runtimeWatchdogState,
    runtimeWatchdogRecord,
    runtimeWatchdogError,
    runtimeWatchdogLastCheckedAt,
    runtimeAutonomyCycleState,
    runtimeAutonomyCycleRecord,
    runtimeAutonomyCycleError,
    runtimeAutonomyCycleLastCheckedAt,
    runtimeCompletionAssistState,
    runtimeCompletionAssistRecord,
    runtimeCompletionAssistError,
    runtimeCompletionAssistLastCheckedAt,
    silentMonitorsState,
    silentMonitorsRecord,
    silentMonitorsError,
    silentMonitorsLastCheckedAt,
    missionStateState,
    missionStateRecord,
    missionStateError,
    missionStateLastCheckedAt,
    missionDetailState,
    missionDetailRecord,
    missionDetailError,
    missionDetailLastCheckedAt,
    indigenousBrainState,
    indigenousBrainBrief,
    indigenousBrainError,
    indigenousBrainLastCheckedAt,
    learningLedgerState,
    learningLedgerRecord,
    learningLedgerError,
    learningLedgerLastCheckedAt,
    learningLedgerQuery,
    lastQueueWriteResult,
    completionClosureSummary,
    completionEvidenceInput,
    lastCompletionWriteResult,
    replaceBoardJson,
    formatBoardJson,
    resetBoard,
    setActiveTab,
    setSelectedLaneId,
    setExtraOwnersInput,
    handleUpdateBoardTextField,
    updateLaneField,
    updateValidationBasisField,
    updateReviewStateField,
    handleCreateLane,
    handleDeleteLane,
    handleToggleOwner,
    handleAddExtraOwners,
    handleAddSubplan,
    handleUpdateSubplan,
    handleDeleteSubplan,
    handlePromoteLane,
    handleCopyDispatchPacket,
    handleCopyQueueCandidate,
    handleCopyQueueEntry,
    handleRefreshRecommendedTargets,
    handleRefreshAndRetryQueueWrite,
    handleRefreshAndRetryLaneCompletion,
    loadBoardVersions,
    handleRestoreBoardVersion,
    refreshQueueStatus,
    loadLearnings,
    loadMissionDetail,
    refreshIndigenousBrain,
    handleWriteQueueEntry,
    setCompletionClosureSummary,
    setCompletionEvidenceInput,
    handleDraftLaneCompletionFromCurrentState,
    handleDraftLaneCompletionForLane,
    handleWriteLaneCompletion,
    handleExport,
    triggerImport,
    handleImport,
  }
}

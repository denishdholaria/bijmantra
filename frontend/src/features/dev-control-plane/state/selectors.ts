import {
  analyzeDeveloperMasterBoard,
  createDeveloperLaneDispatchPacket,
  selectAdvisoryGapDeveloperLaneAnalyses,
  selectBlockedDeveloperLaneAnalyses,
  selectReadyDeveloperLaneAnalyses,
} from '../autonomy'
import type { DeveloperControlPlanePersistenceErrorKind } from '../api/activeBoard'
import type {
  DeveloperBoardLane,
  DeveloperMasterBoard,
} from '../contracts/board'
import type {
  DeveloperBoardAutonomyAnalysis,
  DeveloperLaneAutonomyAnalysis,
} from '../contracts/autonomy'
import type { DeveloperLaneDispatchPacket } from '../contracts/dispatch'
import { parseDeveloperMasterBoard } from '../contracts/board'
import type {
  DevMasterBoardBackendHydrationState,
  DevMasterBoardSaveState,
  DevMasterBoardStore,
} from './store'

export const selectDevMasterBoardRawBoardJson = (state: DevMasterBoardStore) => state.rawBoardJson
export const selectDevMasterBoardLastUpdatedAt = (state: DevMasterBoardStore) => state.lastUpdatedAt
export const selectDevMasterBoardHasHydrated = (state: DevMasterBoardStore) => state.hasHydrated
export const selectDevMasterBoardStorageAvailable = (state: DevMasterBoardStore) =>
  state.storageAvailable
export const selectDevMasterBoardBackendHydrationState = (state: DevMasterBoardStore) =>
  state.backendHydrationState
export const selectDevMasterBoardSaveState = (state: DevMasterBoardStore) => state.saveState
export const selectDevMasterBoardBackendConcurrencyToken = (state: DevMasterBoardStore) =>
  state.backendConcurrencyToken
export const selectDevMasterBoardHasUnsavedChanges = (state: DevMasterBoardStore) =>
  state.hasUnsavedChanges
export const selectDevMasterBoardPersistenceError = (state: DevMasterBoardStore) =>
  state.persistenceError
export const selectDevMasterBoardPersistenceErrorKind = (state: DevMasterBoardStore) =>
  state.persistenceErrorKind
export const selectDevMasterBoardConflictRecord = (state: DevMasterBoardStore) =>
  state.conflictRecord
export const selectDevMasterBoardReplaceBoardJson = (state: DevMasterBoardStore) => state.replaceBoardJson
export const selectDevMasterBoardFormatBoardJson = (state: DevMasterBoardStore) => state.formatBoardJson
export const selectDevMasterBoardResetBoard = (state: DevMasterBoardStore) => state.resetBoard
export const selectDevMasterBoardStartBackendHydration = (state: DevMasterBoardStore) =>
  state.startBackendHydration
export const selectDevMasterBoardHydrateFromBackendRecord = (state: DevMasterBoardStore) =>
  state.hydrateFromBackendRecord
export const selectDevMasterBoardMarkNoRemoteRecord = (state: DevMasterBoardStore) =>
  state.markNoRemoteRecord
export const selectDevMasterBoardMarkBackendUnavailable = (state: DevMasterBoardStore) =>
  state.markBackendUnavailable
export const selectDevMasterBoardMarkSaveStart = (state: DevMasterBoardStore) =>
  state.markSaveStart
export const selectDevMasterBoardMarkSaveSuccess = (state: DevMasterBoardStore) =>
  state.markSaveSuccess
export const selectDevMasterBoardMarkSaveConflict = (state: DevMasterBoardStore) =>
  state.markSaveConflict
export const selectDevMasterBoardMarkSaveError = (state: DevMasterBoardStore) =>
  state.markSaveError

export type DeveloperControlPlanePersistenceStatus = {
  tone: 'loading' | 'fallback' | 'warning' | 'synced'
  label: string
  description: string
}

export type DeveloperMasterBoardViewModel = {
  parsedBoard: DeveloperMasterBoard | null
  jsonError: string | null
  lanes: DeveloperBoardLane[]
  activeLaneCount: number
  blockedLaneCount: number
  subplanCount: number
  dependencyCount: number
  selectedLane: DeveloperBoardLane | null
  availableAgents: string[]
  autonomyAnalysis: DeveloperBoardAutonomyAnalysis | null
  selectedLaneAnalysis: DeveloperLaneAutonomyAnalysis | null
  readyLanes: DeveloperBoardLane[]
  blockedLanes: DeveloperBoardLane[]
  advisoryGapAnalyses: DeveloperLaneAutonomyAnalysis[]
  persistenceStatus: DeveloperControlPlanePersistenceStatus
  recommendedLane: DeveloperBoardLane | null
  dispatchPacket: DeveloperLaneDispatchPacket | null
}

function selectLanesById(lanes: DeveloperBoardLane[], laneIds: string[]) {
  const laneIdSet = new Set(laneIds)
  return lanes.filter((lane) => laneIdSet.has(lane.id))
}

export function selectRecommendedDeveloperLane(
  board: DeveloperMasterBoard | null,
  autonomyAnalysis: DeveloperBoardAutonomyAnalysis | null
) {
  if (!board || !autonomyAnalysis?.nextRecommendedLaneId) {
    return null
  }

  return board.lanes.find((lane) => lane.id === autonomyAnalysis.nextRecommendedLaneId) ?? null
}

export function selectReadyDeveloperLanes(
  board: DeveloperMasterBoard | null,
  autonomyAnalysis: DeveloperBoardAutonomyAnalysis | null
) {
  if (!board || !autonomyAnalysis) {
    return []
  }

  return selectLanesById(
    board.lanes,
    selectReadyDeveloperLaneAnalyses(autonomyAnalysis.laneAnalyses).map((lane) => lane.laneId)
  )
}

export function selectBlockedDeveloperLanes(
  board: DeveloperMasterBoard | null,
  autonomyAnalysis: DeveloperBoardAutonomyAnalysis | null
) {
  if (!board || !autonomyAnalysis) {
    return []
  }

  return selectLanesById(
    board.lanes,
    selectBlockedDeveloperLaneAnalyses(autonomyAnalysis.laneAnalyses).map((lane) => lane.laneId)
  )
}

export function selectDeveloperAdvisoryGapAnalyses(
  autonomyAnalysis: DeveloperBoardAutonomyAnalysis | null
) {
  if (!autonomyAnalysis) {
    return []
  }

  return selectAdvisoryGapDeveloperLaneAnalyses(autonomyAnalysis.laneAnalyses)
}

export function selectDeveloperLaneAnalysis(
  autonomyAnalysis: DeveloperBoardAutonomyAnalysis | null,
  laneId: string | null | undefined
) {
  if (!autonomyAnalysis || !laneId) {
    return null
  }

  return autonomyAnalysis.laneAnalyses.find((lane) => lane.laneId === laneId) ?? null
}

export function deriveDeveloperControlPlanePersistenceStatus(
  hasHydrated: boolean,
  storageAvailable: boolean,
  backendHydrationState: DevMasterBoardBackendHydrationState,
  saveState: DevMasterBoardSaveState,
  persistenceError: string | null,
  persistenceErrorKind: DeveloperControlPlanePersistenceErrorKind,
  conflictRecordUpdatedAt: string | null
): DeveloperControlPlanePersistenceStatus {
  if (!hasHydrated) {
    return {
      tone: 'loading',
      label: 'Loading local fallback state',
      description: 'BijMantra is still hydrating the browser-local fallback board state for this hidden control-plane surface.',
    }
  }

  if (backendHydrationState === 'loading') {
    return {
      tone: 'loading',
      label: 'Checking shared board state',
      description: 'BijMantra is checking whether this hidden control-plane surface already has an active canonical board in shared backend persistence.',
    }
  }

  if (saveState === 'saving') {
    return {
      tone: 'loading',
      label: 'Saving shared canonical board',
      description: 'The hidden control-plane surface is writing the latest valid canonical JSON into backend persistence for this organization.',
    }
  }

  if (saveState === 'conflict') {
    return {
      tone: 'warning',
      label: 'Shared board conflict',
      description:
        conflictRecordUpdatedAt
          ? `Backend persistence rejected the save because a newer canonical board already exists from ${new Date(conflictRecordUpdatedAt).toLocaleString()}. Refetch the shared board before retrying so agent evidence is not overwritten silently.`
          : 'Backend persistence rejected the save because a newer canonical board already exists. Refetch the shared board before retrying so agent evidence is not overwritten silently.',
    }
  }

  if (persistenceErrorKind === 'schema-not-ready') {
    return {
      tone: 'warning',
      label: storageAvailable
        ? 'Shared persistence schema incomplete'
        : 'Shared schema incomplete; memory only',
      description:
        persistenceError ??
        (storageAvailable
          ? 'Shared backend persistence is blocked because the developer control-plane schema migration is incomplete. Browser-local fallback continuity is still active for this hidden surface.'
          : 'Shared backend persistence is blocked because the developer control-plane schema migration is incomplete, and persistent browser storage is unavailable, so this hidden surface is running in memory only.'),
    }
  }

  if (saveState === 'error' && backendHydrationState === 'unavailable') {
    return {
      tone: storageAvailable ? 'fallback' : 'warning',
      label: storageAvailable ? 'Backend unavailable; local fallback active' : 'Backend unavailable; memory only',
      description:
        persistenceError ??
        (storageAvailable
          ? 'Shared backend persistence could not be reached, so this hidden control-plane surface is still running from the browser-local fallback board.'
          : 'Shared backend persistence could not be reached and persistent browser storage is unavailable, so this hidden control-plane surface is currently running in memory only.'),
    }
  }

  if (saveState === 'error') {
    return {
      tone: 'warning',
      label: 'Shared save failed',
      description:
        persistenceError ??
        'The latest canonical JSON could not be saved to shared backend persistence. Local fallback state is still preserved for this browser session.',
    }
  }

  if (backendHydrationState === 'ready') {
    return {
      tone: 'synced',
      label: 'Shared backend persistence active',
      description: 'This hidden control-plane surface is now backed by the shared active-board API, with browser-local state retained only as fallback continuity.',
    }
  }

  if (backendHydrationState === 'no-record') {
    return {
      tone: storageAvailable ? 'fallback' : 'warning',
      label: storageAvailable ? 'No shared board yet' : 'No shared board; memory only',
      description:
        storageAvailable
          ? 'No active canonical board exists yet in backend persistence for this organization, so BijMantra is truthfully continuing from the browser-local fallback until the next successful save.'
          : 'No active canonical board exists yet in backend persistence and persistent browser storage is unavailable, so the control plane is currently operating in memory only until a save succeeds.',
    }
  }

  if (!storageAvailable) {
    return {
      tone: 'warning',
      label: 'Local fallback unavailable',
      description: 'Persistent browser storage is unavailable, so the control plane is running in memory only for this session until Phase 2 backend persistence exists.',
    }
  }

  return {
    tone: 'fallback',
    label: 'Local fallback only',
    description: 'The canonical board is currently persisted in this browser only and is not yet backed by shared backend persistence.',
  }
}

export function deriveDeveloperMasterBoardViewModel(
  rawBoardJson: string,
  selectedLaneId: string | null,
  hasHydrated = true,
  storageAvailable = true,
  backendHydrationState: DevMasterBoardBackendHydrationState = 'idle',
  saveState: DevMasterBoardSaveState = 'idle',
  persistenceError: string | null = null,
  persistenceErrorKind: DeveloperControlPlanePersistenceErrorKind = 'generic',
  conflictRecordUpdatedAt: string | null = null
): DeveloperMasterBoardViewModel {
  let parsedBoard: DeveloperMasterBoard | null = null
  let jsonError: string | null = null

  try {
    parsedBoard = parseDeveloperMasterBoard(rawBoardJson)
  } catch (error) {
    jsonError = error instanceof Error ? error.message : 'Unable to parse master board JSON'
  }

  const lanes = parsedBoard?.lanes ?? []
  const selectedLane = lanes.find((lane) => lane.id === selectedLaneId) ?? lanes[0] ?? null
  const autonomyAnalysis = parsedBoard ? analyzeDeveloperMasterBoard(parsedBoard) : null
  const selectedLaneAnalysis = selectDeveloperLaneAnalysis(autonomyAnalysis, selectedLane?.id)
  const readyLanes = selectReadyDeveloperLanes(parsedBoard, autonomyAnalysis)
  const blockedLanes = selectBlockedDeveloperLanes(parsedBoard, autonomyAnalysis)
  const advisoryGapAnalyses = selectDeveloperAdvisoryGapAnalyses(autonomyAnalysis)
  const recommendedLane = selectRecommendedDeveloperLane(parsedBoard, autonomyAnalysis)

  return {
    parsedBoard,
    jsonError,
    lanes,
    activeLaneCount: lanes.filter((lane) => lane.status === 'active').length,
    blockedLaneCount: blockedLanes.length,
    subplanCount: lanes.reduce((count, lane) => count + lane.subplans.length, 0),
    dependencyCount: lanes.reduce((count, lane) => count + lane.dependencies.length, 0),
    selectedLane,
    availableAgents: parsedBoard
      ? Array.from(
          new Set([
            ...parsedBoard.agent_roles.map((role) => role.agent),
            ...parsedBoard.lanes.flatMap((lane) => lane.owners),
          ])
        ).sort((left, right) => left.localeCompare(right))
      : [],
    autonomyAnalysis,
    selectedLaneAnalysis,
    readyLanes,
    blockedLanes,
    advisoryGapAnalyses,
    persistenceStatus: deriveDeveloperControlPlanePersistenceStatus(
      hasHydrated,
      storageAvailable,
      backendHydrationState,
      saveState,
      persistenceError,
      persistenceErrorKind,
      conflictRecordUpdatedAt
    ),
    recommendedLane,
    dispatchPacket: parsedBoard
      ? createDeveloperLaneDispatchPacket(parsedBoard, selectedLane?.id ?? undefined)
      : null,
  }
}
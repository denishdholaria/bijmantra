import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

import type {
  DeveloperControlPlaneActiveBoardRecord,
  DeveloperControlPlanePersistenceErrorKind,
} from '../api/activeBoard'
import {
  canonicalizeDeveloperMasterBoardJson,
  createDefaultDeveloperMasterBoardJson,
} from '../contracts/board'

export type DevMasterBoardBackendHydrationState =
  | 'idle'
  | 'loading'
  | 'ready'
  | 'no-record'
  | 'unavailable'

export type DevMasterBoardSaveState = 'idle' | 'saving' | 'saved' | 'conflict' | 'error'

export interface DevMasterBoardStore {
  rawBoardJson: string
  lastUpdatedAt: string
  hasHydrated: boolean
  storageAvailable: boolean
  backendHydrationState: DevMasterBoardBackendHydrationState
  saveState: DevMasterBoardSaveState
  backendConcurrencyToken: string | null
  backendLastSyncedAt: string | null
  lastPersistedBoardJson: string | null
  hasUnsavedChanges: boolean
  persistenceError: string | null
  persistenceErrorKind: DeveloperControlPlanePersistenceErrorKind
  conflictRecord: DeveloperControlPlaneActiveBoardRecord | null
  replaceBoardJson: (rawBoardJson: string) => void
  formatBoardJson: () => void
  resetBoard: () => void
  setHasHydrated: (hasHydrated: boolean) => void
  setStorageAvailable: (storageAvailable: boolean) => void
  startBackendHydration: () => void
  hydrateFromBackendRecord: (record: DeveloperControlPlaneActiveBoardRecord) => void
  markNoRemoteRecord: () => void
  markBackendUnavailable: (
    message: string,
    kind?: DeveloperControlPlanePersistenceErrorKind
  ) => void
  markSaveStart: () => void
  markSaveSuccess: (record: DeveloperControlPlaneActiveBoardRecord) => void
  markSaveConflict: (record: DeveloperControlPlaneActiveBoardRecord, message: string) => void
  markSaveError: (message: string, kind?: DeveloperControlPlanePersistenceErrorKind) => void
}

function nowIso() {
  return new Date().toISOString()
}

function dirtySinceLastPersisted(lastPersistedBoardJson: string | null, rawBoardJson: string) {
  return lastPersistedBoardJson !== rawBoardJson
}

export const useDevMasterBoardStore = create<DevMasterBoardStore>()(
  persist(
    (set) => ({
      rawBoardJson: createDefaultDeveloperMasterBoardJson(),
      lastUpdatedAt: nowIso(),
      hasHydrated: false,
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

      replaceBoardJson: (rawBoardJson) => {
        set((state) => ({
          rawBoardJson,
          lastUpdatedAt: nowIso(),
          hasUnsavedChanges: dirtySinceLastPersisted(state.lastPersistedBoardJson, rawBoardJson),
          saveState: state.saveState === 'conflict' ? 'conflict' : 'idle',
          persistenceError: state.saveState === 'conflict' ? state.persistenceError : null,
          persistenceErrorKind: state.saveState === 'conflict' ? state.persistenceErrorKind : 'generic',
          conflictRecord: state.saveState === 'conflict' ? state.conflictRecord : null,
        }))
      },

      formatBoardJson: () => {
        set((state) => {
          const formatted = canonicalizeDeveloperMasterBoardJson(state.rawBoardJson)
          return {
            rawBoardJson: formatted,
            lastUpdatedAt: nowIso(),
            hasUnsavedChanges: dirtySinceLastPersisted(state.lastPersistedBoardJson, formatted),
            saveState: state.saveState === 'conflict' ? 'conflict' : 'idle',
            persistenceError: state.saveState === 'conflict' ? state.persistenceError : null,
            persistenceErrorKind: state.saveState === 'conflict' ? state.persistenceErrorKind : 'generic',
            conflictRecord: state.saveState === 'conflict' ? state.conflictRecord : null,
          }
        })
      },

      resetBoard: () => {
        const rawBoardJson = createDefaultDeveloperMasterBoardJson()
        set({
          rawBoardJson,
          lastUpdatedAt: nowIso(),
          hasUnsavedChanges: true,
          saveState: 'idle',
          persistenceError: null,
          persistenceErrorKind: 'generic',
          conflictRecord: null,
        })
      },

      setHasHydrated: (hasHydrated) => {
        set({ hasHydrated })
      },

      setStorageAvailable: (storageAvailable) => {
        set({ storageAvailable })
      },

      startBackendHydration: () => {
        set({
          backendHydrationState: 'loading',
          persistenceError: null,
          persistenceErrorKind: 'generic',
        })
      },

      hydrateFromBackendRecord: (record) => {
        set({
          rawBoardJson: record.canonical_board_json,
          lastUpdatedAt: record.updated_at,
          backendHydrationState: 'ready',
          saveState: 'saved',
          backendConcurrencyToken: record.concurrency_token,
          backendLastSyncedAt: record.updated_at,
          lastPersistedBoardJson: record.canonical_board_json,
          hasUnsavedChanges: false,
          persistenceError: null,
          persistenceErrorKind: 'generic',
          conflictRecord: null,
        })
      },

      markNoRemoteRecord: () => {
        set({
          backendHydrationState: 'no-record',
          saveState: 'idle',
          backendConcurrencyToken: null,
          backendLastSyncedAt: null,
          lastPersistedBoardJson: null,
          persistenceError: null,
          persistenceErrorKind: 'generic',
          conflictRecord: null,
        })
      },

      markBackendUnavailable: (message, kind = 'generic') => {
        set({
          backendHydrationState: 'unavailable',
          saveState: 'error',
          persistenceError: message,
          persistenceErrorKind: kind,
          conflictRecord: null,
        })
      },

      markSaveStart: () => {
        set({
          saveState: 'saving',
          persistenceError: null,
          persistenceErrorKind: 'generic',
          conflictRecord: null,
        })
      },

      markSaveSuccess: (record) => {
        set({
          rawBoardJson: record.canonical_board_json,
          lastUpdatedAt: record.updated_at,
          backendHydrationState: 'ready',
          saveState: 'saved',
          backendConcurrencyToken: record.concurrency_token,
          backendLastSyncedAt: record.updated_at,
          lastPersistedBoardJson: record.canonical_board_json,
          hasUnsavedChanges: false,
          persistenceError: null,
          persistenceErrorKind: 'generic',
          conflictRecord: null,
        })
      },

      markSaveConflict: (record, message) => {
        set({
          backendHydrationState: 'ready',
          saveState: 'conflict',
          backendConcurrencyToken: record.concurrency_token,
          backendLastSyncedAt: record.updated_at,
          lastPersistedBoardJson: record.canonical_board_json,
          hasUnsavedChanges: true,
          persistenceError: message,
          persistenceErrorKind: 'generic',
          conflictRecord: record,
        })
      },

      markSaveError: (message, kind = 'generic') => {
        set({ saveState: 'error', persistenceError: message, persistenceErrorKind: kind })
      },
    }),
    {
      name: 'bijmantra-dev-master-board-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        rawBoardJson: state.rawBoardJson,
        lastUpdatedAt: state.lastUpdatedAt,
      }),
      onRehydrateStorage: () => (state, error) => {
        state?.setStorageAvailable(!error)
        state?.setHasHydrated(true)
      },
    }
  )
)
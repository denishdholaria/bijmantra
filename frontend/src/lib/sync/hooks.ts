import { useOfflineSync } from '@/lib/offline-sync';
import type { SyncStatus } from './types';

export function useSyncStatus() {
  const status = useOfflineSync();

  return {
    isOnline: status.isOnline,
    isSyncing: status.isSyncing,
    lastSyncTime: status.lastSyncTime,
    pendingUploads: status.pendingChanges,
    syncError: null,
  } satisfies SyncStatus;
}

export function usePendingUploadsCount() {
  return useOfflineSync().pendingChanges;
}

export function useSync() {
  const status = useOfflineSync();

  return {
    isOnline: status.isOnline,
    isSyncing: status.isSyncing,
    lastSyncTime: status.lastSyncTime,
    pendingUploads: status.pendingChanges,
    syncError: null,
    conflicts: status.conflicts,
    forceSync: status.forceSync,
  };
}

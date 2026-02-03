import { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { syncEngine } from './engine';
import { db } from './db';
import { SyncStatus } from './types';

export function useSyncStatus() {
  const [status, setStatus] = useState<SyncStatus>(syncEngine.getStatus());

  useEffect(() => {
    const unsubscribe = syncEngine.subscribe(setStatus);
    return () => {
      unsubscribe();
    };
  }, []);

  return status;
}

export function usePendingUploadsCount() {
  return useLiveQuery(() => db.pendingUploads.count()) || 0;
}

export function useSync() {
  const status = useSyncStatus();
  const pendingCount = usePendingUploadsCount();

  return {
    ...status,
    pendingUploads: pendingCount,
    forceSync: () => {
        syncEngine.pushChanges();
        syncEngine.pullChanges();
    }
  };
}

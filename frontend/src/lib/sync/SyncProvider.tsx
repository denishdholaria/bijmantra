import React, { useEffect } from 'react';
import { offlineSync } from '@/lib/offline-sync';

/**
 * SyncProvider — mounts the canonical Yjs CRDT offline sync engine.
 *
 * The old lib/sync/engine.ts (Dexie-based, no React integration) has been
 * removed. All offline sync now goes through lib/offline-sync.ts (Yjs CRDT).
 */
export const SyncProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    // Force an initial sync cycle when the app mounts
    offlineSync.forceSync().catch(() => {
      // Non-fatal — offlineSync handles its own error logging
    });
  }, []);

  return <>{children}</>;
};

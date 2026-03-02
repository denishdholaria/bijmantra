
import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { syncEngine, SyncResult } from './engine';
import { getPendingSyncCount } from './db';

interface SyncContextType {
  isOnline: boolean;
  isSyncing: boolean;
  pendingCount: number;
  lastSyncResult: SyncResult | null;
  sync: () => Promise<SyncResult>;
}

const SyncContext = createContext<SyncContextType | null>(null);

export function SyncProvider({ children }: { children: ReactNode }) {
  const [isOnline, setIsOnline] = useState(syncEngine.getOnlineStatus());
  const [isSyncing, setIsSyncing] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResult | null>(null);

  // Update online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Poll for pending sync count - CENTRALIZED POLLING
  useEffect(() => {
    const updatePendingCount = async () => {
      const count = await getPendingSyncCount();
      setPendingCount(count);
    };

    updatePendingCount();
    const interval = setInterval(updatePendingCount, 5000);

    return () => clearInterval(interval);
  }, []);

  // Sync function
  const sync = useCallback(async (): Promise<SyncResult> => {
    setIsSyncing(true);
    try {
      const result = await syncEngine.sync();
      setLastSyncResult(result);
      const count = await getPendingSyncCount();
      setPendingCount(count);
      return result;
    } finally {
      setIsSyncing(false);
    }
  }, []);

  const value = {
    isOnline,
    isSyncing,
    pendingCount,
    lastSyncResult,
    sync,
  };

  return <SyncContext.Provider value={value}>{children}</SyncContext.Provider>;
}

export function useSyncContext() {
  const context = useContext(SyncContext);
  if (!context) {
    throw new Error('useSync must be used within a SyncProvider');
  }
  return context;
}

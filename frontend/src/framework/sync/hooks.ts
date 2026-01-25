/**
 * Parashakti Framework - Sync Hooks
 * 
 * React hooks for offline sync functionality.
 */

import { useState, useEffect, useCallback } from 'react';
import { syncEngine, SyncResult } from './engine';
import { db, getPendingSyncCount } from './db';

/**
 * Hook for sync status and operations
 */
export function useSync() {
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

  // Update pending count
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

  return {
    isOnline,
    isSyncing,
    pendingCount,
    lastSyncResult,
    sync,
  };
}

/**
 * Hook for offline-first data operations
 */
export function useOfflineData<T extends { id: string }>(
  entityType: string
) {
  const [data, setData] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data from IndexedDB
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const table = (db as any)[entityType];
      if (table) {
        const items = await table.toArray();
        setData(items);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, [entityType]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Create item
  const create = useCallback(async (item: Omit<T, 'id'> & { id?: string }): Promise<T> => {
    const table = (db as any)[entityType];
    const id = item.id || crypto.randomUUID();
    const now = new Date().toISOString();
    
    const newItem = {
      ...item,
      id,
      _syncVersion: 1,
      _syncStatus: 'pending',
      _createdAt: now,
      _updatedAt: now,
    } as unknown as T;

    await table.add(newItem);
    await syncEngine.queueChange(entityType, id, 'create', newItem as any);
    await loadData();
    
    return newItem;
  }, [entityType, loadData]);

  // Update item
  const update = useCallback(async (id: string, changes: Partial<T>): Promise<void> => {
    const table = (db as any)[entityType];
    const existing = await table.get(id);
    
    if (!existing) {
      throw new Error('Item not found');
    }

    const updated = {
      ...existing,
      ...changes,
      _syncStatus: 'pending',
      _updatedAt: new Date().toISOString(),
    };

    await table.put(updated);
    await syncEngine.queueChange(entityType, id, 'update', updated);
    await loadData();
  }, [entityType, loadData]);

  // Delete item
  const remove = useCallback(async (id: string): Promise<void> => {
    const table = (db as any)[entityType];
    await table.delete(id);
    await syncEngine.queueChange(entityType, id, 'delete', {});
    await loadData();
  }, [entityType, loadData]);

  // Get single item
  const getById = useCallback(async (id: string): Promise<T | undefined> => {
    const table = (db as any)[entityType];
    return await table.get(id);
  }, [entityType]);

  return {
    data,
    isLoading,
    error,
    reload: loadData,
    create,
    update,
    remove,
    getById,
  };
}

/**
 * Hook for sync status indicator
 */
export function useSyncStatus() {
  const { isOnline, isSyncing, pendingCount } = useSync();

  const status = isSyncing
    ? 'syncing'
    : !isOnline
    ? 'offline'
    : pendingCount > 0
    ? 'pending'
    : 'synced';

  const statusText = {
    syncing: 'Syncing...',
    offline: 'Offline',
    pending: `${pendingCount} pending`,
    synced: 'Synced',
  }[status];

  const statusColor = {
    syncing: 'text-blue-500',
    offline: 'text-gray-500',
    pending: 'text-yellow-500',
    synced: 'text-green-500',
  }[status];

  return {
    status,
    statusText,
    statusColor,
    isOnline,
    isSyncing,
    pendingCount,
  };
}

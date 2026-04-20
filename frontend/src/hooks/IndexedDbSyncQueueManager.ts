import { useState, useEffect, useCallback } from 'react';
import Dexie, { Table } from 'dexie';
import { useLiveQuery } from 'dexie-react-hooks';

// ============================================
// TYPES & INTERFACES
// ============================================

export interface SyncQueueItem {
  id?: number;
  uuid: string;
  action: 'CREATE' | 'UPDATE' | 'DELETE';
  entity: 'OBSERVATION' | 'PLOT' | 'TRIAL' | 'GERMPLASM' | 'MEDIA';
  payload: unknown;
  timestamp: number;
  retryCount: number;
  lastError?: string;
  status: 'PENDING' | 'SYNCING' | 'FAILED' | 'COMPLETED';
}

export interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  pendingCount: number;
  lastSyncTime: number | null;
}

// ============================================
// DATABASE
// ============================================

class SyncQueueDB extends Dexie {
  queue!: Table<SyncQueueItem>;

  constructor() {
    super('IndexedDbSyncQueueDB');
    this.version(1).stores({
      queue: '++id, uuid, status, timestamp, entity'
    });
  }
}

export const db = new SyncQueueDB();

// ============================================
// HOOK
// ============================================

/**
 * IndexedDbSyncQueueManager Hook
 *
 * Manages an offline-first sync queue using IndexedDB.
 * Provides methods to add to queue, process queue, and monitor sync status.
 */
export function useIndexedDbSyncQueueManager() {
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<number | null>(null);

  const pendingCount = useLiveQuery(() => db.queue.where('status').anyOf('PENDING', 'FAILED').count()) ?? 0;

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

  const addToQueue = useCallback(async (
    entity: SyncQueueItem['entity'],
    action: SyncQueueItem['action'],
    payload: unknown,
    uuid: string = crypto.randomUUID()
  ) => {
    const item: SyncQueueItem = {
      uuid,
      entity,
      action,
      payload,
      timestamp: Date.now(),
      retryCount: 0,
      status: 'PENDING'
    };

    const id = await db.queue.add(item);
    return id;
  }, []);

  const removeFromQueue = useCallback(async (id: number) => {
    await db.queue.delete(id);
  }, []);

  const clearCompleted = useCallback(async () => {
    await db.queue.where('status').equals('COMPLETED').delete();
  }, []);

  /**
   * Calculates if an item should be retried based on exponential backoff
   */
  const shouldRetry = useCallback((item: SyncQueueItem) => {
    if (item.status === 'PENDING') return true;
    if (item.status !== 'FAILED') return false;

    // Exponential backoff: 2^retryCount * 1000ms
    const backoffMs = Math.pow(2, item.retryCount) * 1000;
    const nextRetryTime = item.timestamp + backoffMs;

    return Date.now() >= nextRetryTime;
  }, []);

  const processQueue = useCallback(async (processor: (item: SyncQueueItem) => Promise<void>) => {
    if (!isOnline || isSyncing) return;

    const allItems = await db.queue
      .where('status')
      .anyOf('PENDING', 'FAILED')
      .toArray();

    // Sort by timestamp manually since Dexie cannot orderBy on a filtered collection easily
    allItems.sort((a, b) => a.timestamp - b.timestamp);

    const itemsToProcess = allItems.filter(shouldRetry);

    if (itemsToProcess.length === 0) return;

    setIsSyncing(true);
    try {
      for (const item of itemsToProcess) {
        try {
          await db.queue.update(item.id!, { status: 'SYNCING' });
          await processor(item);
          await db.queue.update(item.id!, { status: 'COMPLETED' });
        } catch (error) {
          console.error(`Failed to process sync item ${item.id}:`, error);
          await db.queue.update(item.id!, {
            status: 'FAILED',
            retryCount: (item.retryCount || 0) + 1,
            lastError: error instanceof Error ? error.message : String(error),
            timestamp: Date.now() // Update timestamp for backoff calculation
          });

          if (error instanceof Error && (error.message.includes('401') || error.message.includes('UNAUTHORIZED'))) {
              break;
          }
        }
      }
      setLastSyncTime(Date.now());
    } finally {
      setIsSyncing(false);
    }
  }, [isOnline, isSyncing, shouldRetry]);

  return {
    isOnline,
    isSyncing,
    pendingCount,
    lastSyncTime,
    addToQueue,
    removeFromQueue,
    clearCompleted,
    processQueue,
    db // Expose db for advanced queries if needed
  };
}

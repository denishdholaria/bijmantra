import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useIndexedDbSyncQueueManager } from './IndexedDbSyncQueueManager';
import 'fake-indexeddb/auto';
import { db } from './IndexedDbSyncQueueManager'; // Note: I need to export db if I want to check it directly, or use the hook's returned db

describe('useIndexedDbSyncQueueManager', () => {
  beforeEach(async () => {
    await db.queue.clear();
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useIndexedDbSyncQueueManager());
    expect(result.current.isOnline).toBe(true);
    expect(result.current.isSyncing).toBe(false);
    expect(result.current.pendingCount).toBe(0);
  });

  it('should add items to the queue', async () => {
    const { result } = renderHook(() => useIndexedDbSyncQueueManager());

    await act(async () => {
      await result.current.addToQueue('OBSERVATION', 'CREATE', { test: 'data' });
    });

    await waitFor(() => expect(result.current.pendingCount).toBe(1));

    const items = await db.queue.toArray();
    expect(items[0]).toMatchObject({
      entity: 'OBSERVATION',
      action: 'CREATE',
      payload: { test: 'data' },
      status: 'PENDING'
    });
  });

  it('should process the queue', async () => {
    const { result } = renderHook(() => useIndexedDbSyncQueueManager());

    await act(async () => {
      await result.current.addToQueue('OBSERVATION', 'CREATE', { test: 'data' });
    });

    const processor = vi.fn().mockResolvedValue(undefined);

    await act(async () => {
      await result.current.processQueue(processor);
    });

    expect(processor).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(result.current.pendingCount).toBe(0));

    const items = await db.queue.toArray();
    expect(items[0].status).toBe('COMPLETED');
  });

  it('should handle failures and retries', async () => {
    const { result } = renderHook(() => useIndexedDbSyncQueueManager());

    await act(async () => {
      await result.current.addToQueue('OBSERVATION', 'CREATE', { test: 'data' });
    });

    const processor = vi.fn().mockRejectedValue(new Error('Sync failed'));

    await act(async () => {
      await result.current.processQueue(processor);
    });

    await waitFor(() => expect(result.current.pendingCount).toBe(1));
    const item = await db.queue.toCollection().first();
    expect(item?.status).toBe('FAILED');
    expect(item?.retryCount).toBe(1);

    // Try processing again immediately - should not retry due to backoff
    await act(async () => {
      await result.current.processQueue(processor);
    });
    expect(processor).toHaveBeenCalledTimes(1); // Still 1
  });

  it('should clear completed items', async () => {
     const { result } = renderHook(() => useIndexedDbSyncQueueManager());

    await act(async () => {
      await result.current.addToQueue('OBSERVATION', 'CREATE', { test: 'data' });
    });

    const processor = vi.fn().mockResolvedValue(undefined);

    await act(async () => {
      await result.current.processQueue(processor);
    });

    await waitFor(() => expect(result.current.pendingCount).toBe(0));

    await act(async () => {
        await result.current.clearCompleted();
    });

    const items = await db.queue.toArray();
    expect(items.length).toBe(0);
  });
});

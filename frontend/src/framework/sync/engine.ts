/**
 * Parashakti Framework - Sync Engine
 * 
 * Handles offline data synchronization with the server.
 */

import { db, PendingSyncOperation, SyncLogEntry, SyncStatus } from './db';

export interface SyncConfig {
  /** Entities to sync */
  entities: string[];
  /** Conflict resolution strategy */
  conflictStrategy: 'server-wins' | 'client-wins' | 'manual';
  /** Max retry attempts for failed operations */
  maxRetries: number;
  /** Batch size for sync operations */
  batchSize: number;
}

export interface SyncResult {
  success: boolean;
  pushed: number;
  pulled: number;
  conflicts: number;
  errors: string[];
  durationMs: number;
}

const DEFAULT_CONFIG: SyncConfig = {
  entities: ['programs', 'trials', 'studies', 'germplasm', 'observations', 'traits'],
  conflictStrategy: 'server-wins',
  maxRetries: 3,
  batchSize: 50,
};

/**
 * Sync Engine for offline-first data management
 */
export class SyncEngine {
  private config: SyncConfig;
  private isOnline: boolean;
  private isSyncing: boolean = false;
  private _listeners: Set<(status: SyncStatus) => void> = new Set();

  constructor(config: Partial<SyncConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;
    
    // Listen for online/offline events
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.handleOnline());
      window.addEventListener('offline', () => this.handleOffline());
    }
  }

  private handleOnline(): void {
    this.isOnline = true;
    // Auto-sync when coming back online
    this.sync().catch(console.error);
  }

  private handleOffline(): void {
    this.isOnline = false;
  }

  /**
   * Check if currently online
   */
  getOnlineStatus(): boolean {
    return this.isOnline;
  }

  /**
   * Check if sync is in progress
   */
  isSyncInProgress(): boolean {
    return this.isSyncing;
  }

  /**
   * Perform full sync
   */
  async sync(): Promise<SyncResult> {
    if (this.isSyncing) {
      return {
        success: false,
        pushed: 0,
        pulled: 0,
        conflicts: 0,
        errors: ['Sync already in progress'],
        durationMs: 0,
      };
    }

    if (!this.isOnline) {
      return {
        success: false,
        pushed: 0,
        pulled: 0,
        conflicts: 0,
        errors: ['Device is offline'],
        durationMs: 0,
      };
    }

    this.isSyncing = true;
    const startTime = Date.now();
    const errors: string[] = [];
    let pushed = 0;
    let pulled = 0;
    let conflicts = 0;

    try {
      // 1. Push pending changes to server
      const pushResult = await this.pushPendingChanges();
      pushed = pushResult.pushed;
      errors.push(...pushResult.errors);

      // 2. Pull updates from server
      const pullResult = await this.pullServerChanges();
      pulled = pullResult.pulled;
      conflicts = pullResult.conflicts;
      errors.push(...pullResult.errors);

      // 3. Log sync operation
      await this.logSync('push', pushed, errors.length);

      return {
        success: errors.length === 0,
        pushed,
        pulled,
        conflicts,
        errors,
        durationMs: Date.now() - startTime,
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      return {
        success: false,
        pushed,
        pulled,
        conflicts,
        errors: [...errors, errorMsg],
        durationMs: Date.now() - startTime,
      };
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * Push pending local changes to server
   */
  private async pushPendingChanges(): Promise<{ pushed: number; errors: string[] }> {
    const pending = await db.pendingSync.toArray();
    const errors: string[] = [];
    let pushed = 0;

    for (const op of pending) {
      try {
        await this.pushOperation(op);
        await db.pendingSync.delete(op.id!);
        pushed++;
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Push failed';
        errors.push(`${op.entityType}/${op.entityId}: ${errorMsg}`);
        
        // Update retry count
        await db.pendingSync.update(op.id!, {
          retryCount: op.retryCount + 1,
          lastError: errorMsg,
        });
      }
    }

    return { pushed, errors };
  }

  /**
   * Push a single operation to server
   */
  private async pushOperation(op: PendingSyncOperation): Promise<void> {
    const endpoint = `/api/v1/${op.entityType}`;
    const method = op.operation === 'create' ? 'POST' 
                 : op.operation === 'update' ? 'PUT' 
                 : 'DELETE';
    
    const url = op.operation === 'create' 
      ? endpoint 
      : `${endpoint}/${op.entityId}`;

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        // Auth token would be added here
      },
      body: op.operation !== 'delete' ? JSON.stringify(op.payload) : undefined,
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }
  }

  /**
   * Pull updates from server
   */
  private async pullServerChanges(): Promise<{ pulled: number; conflicts: number; errors: string[] }> {
    const errors: string[] = [];
    let pulled = 0;
    let conflicts = 0;

    for (const entityType of this.config.entities) {
      try {
        const result = await this.pullEntity(entityType);
        pulled += result.pulled;
        conflicts += result.conflicts;
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Pull failed';
        errors.push(`${entityType}: ${errorMsg}`);
      }
    }

    return { pulled, conflicts, errors };
  }

  /**
   * Pull a single entity type from server
   */
  private async pullEntity(entityType: string): Promise<{ pulled: number; conflicts: number }> {
    // Get last sync timestamp for this entity
    const lastSync = await this.getLastSyncTime(entityType);
    
    const response = await fetch(
      `/api/v1/sync/${entityType}?since=${lastSync || ''}`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const data = await response.json();
    const changes = data.changes || [];
    let pulled = 0;
    let conflicts = 0;

    for (const change of changes) {
      const result = await this.applyServerChange(entityType, change);
      if (result === 'applied') pulled++;
      if (result === 'conflict') conflicts++;
    }

    return { pulled, conflicts };
  }

  /**
   * Apply a server change to local database
   */
  private async applyServerChange(
    entityType: string,
    change: { id: string; action: string; data?: Record<string, unknown> }
  ): Promise<'applied' | 'conflict' | 'skipped'> {
    const table = (db as any)[entityType];
    if (!table) return 'skipped';

    const local = await table.get(change.id);

    // Check for conflicts
    if (local && local._syncStatus === 'pending') {
      if (this.config.conflictStrategy === 'server-wins') {
        // Server wins - overwrite local
        await table.put({
          ...change.data,
          id: change.id,
          _syncStatus: 'synced',
          _syncVersion: (local._syncVersion || 0) + 1,
        });
        return 'applied';
      } else if (this.config.conflictStrategy === 'client-wins') {
        // Client wins - keep local, mark for push
        return 'skipped';
      } else {
        // Manual resolution needed
        await table.update(change.id, { _syncStatus: 'conflict' });
        return 'conflict';
      }
    }

    // No conflict - apply change
    if (change.action === 'delete') {
      await table.delete(change.id);
    } else {
      await table.put({
        ...change.data,
        id: change.id,
        _syncStatus: 'synced',
        _syncVersion: (local?._syncVersion || 0) + 1,
      });
    }

    return 'applied';
  }

  /**
   * Get last sync timestamp for an entity type
   */
  private async getLastSyncTime(entityType: string): Promise<string | null> {
    const lastLog = await db.syncLog
      .where('entityType')
      .equals(entityType)
      .reverse()
      .first();
    
    return lastLog?.timestamp || null;
  }

  /**
   * Log a sync operation
   */
  private async logSync(
    direction: 'push' | 'pull',
    recordsProcessed: number,
    recordsFailed: number
  ): Promise<void> {
    const entry: SyncLogEntry = {
      timestamp: new Date().toISOString(),
      direction,
      entityType: 'all',
      recordsProcessed,
      recordsFailed,
      errors: [],
      durationMs: 0,
    };
    await db.syncLog.add(entry);
  }

  /**
   * Queue a local change for sync
   */
  async queueChange(
    entityType: string,
    entityId: string,
    operation: 'create' | 'update' | 'delete',
    payload: Record<string, unknown>
  ): Promise<void> {
    await db.pendingSync.add({
      entityType,
      entityId,
      operation,
      payload,
      createdAt: new Date().toISOString(),
      retryCount: 0,
    });

    // Update entity sync status
    const table = (db as any)[entityType];
    if (table && operation !== 'delete') {
      await table.update(entityId, { _syncStatus: 'pending' });
    }
  }

  /**
   * Get pending sync count
   */
  async getPendingCount(): Promise<number> {
    return await db.pendingSync.count();
  }
}

// Global sync engine instance
export const syncEngine = new SyncEngine();

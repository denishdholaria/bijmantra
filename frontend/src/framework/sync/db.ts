/**
 * Parashakti Framework - Offline Database
 * 
 * IndexedDB schema using Dexie.js for offline-first data storage.
 */

import Dexie, { Table } from 'dexie';

/**
 * Sync status for offline records
 */
export type SyncStatus = 'synced' | 'pending' | 'conflict' | 'error';

/**
 * Base interface for syncable entities
 */
export interface SyncableEntity {
  id: string;
  _syncVersion: number;
  _syncStatus: SyncStatus;
  _localChanges?: Record<string, unknown>;
  _serverVersion?: number;
  _lastSyncAt?: string;
  _createdAt: string;
  _updatedAt: string;
}

/**
 * Pending sync operation
 */
export interface PendingSyncOperation {
  id?: number;
  entityType: string;
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  payload: Record<string, unknown>;
  createdAt: string;
  retryCount: number;
  lastError?: string;
}

/**
 * Sync log entry
 */
export interface SyncLogEntry {
  id?: number;
  timestamp: string;
  direction: 'push' | 'pull';
  entityType: string;
  recordsProcessed: number;
  recordsFailed: number;
  errors: string[];
  durationMs: number;
}

// Entity interfaces
export interface OfflineProgram extends SyncableEntity {
  name: string;
  description?: string;
  organizationId: string;
}

export interface OfflineTrial extends SyncableEntity {
  name: string;
  programId: string;
  startDate?: string;
  endDate?: string;
  organizationId: string;
}

export interface OfflineStudy extends SyncableEntity {
  name: string;
  trialId: string;
  locationId?: string;
  organizationId: string;
}

export interface OfflineGermplasm extends SyncableEntity {
  name: string;
  accessionNumber?: string;
  species?: string;
  organizationId: string;
}

export interface OfflineObservation extends SyncableEntity {
  observationUnitId: string;
  traitId: string;
  value: string;
  observedAt: string;
  collectorId?: string;
  organizationId: string;
}

export interface OfflineTrait extends SyncableEntity {
  name: string;
  description?: string;
  dataType: string;
  organizationId: string;
}

export interface UserPreference {
  key: string;
  value: unknown;
}

/**
 * Bijmantra Offline Database
 */
export class BijmantraDB extends Dexie {
  // Core entities
  programs!: Table<OfflineProgram, string>;
  trials!: Table<OfflineTrial, string>;
  studies!: Table<OfflineStudy, string>;
  germplasm!: Table<OfflineGermplasm, string>;
  observations!: Table<OfflineObservation, string>;
  traits!: Table<OfflineTrait, string>;
  
  // Sync management
  pendingSync!: Table<PendingSyncOperation, number>;
  syncLog!: Table<SyncLogEntry, number>;
  
  // User preferences
  userPrefs!: Table<UserPreference, string>;

  constructor() {
    super('bijmantra');
    
    this.version(1).stores({
      // Core entities with sync tracking
      programs: 'id, organizationId, _syncStatus, _updatedAt',
      trials: 'id, programId, organizationId, _syncStatus, _updatedAt',
      studies: 'id, trialId, organizationId, _syncStatus, _updatedAt',
      germplasm: 'id, organizationId, accessionNumber, _syncStatus, _updatedAt',
      observations: 'id, observationUnitId, traitId, organizationId, _syncStatus, _updatedAt, observedAt',
      traits: 'id, organizationId, _syncStatus, _updatedAt',
      
      // Sync management
      pendingSync: '++id, entityType, entityId, operation, createdAt',
      syncLog: '++id, timestamp, direction, entityType',
      
      // User preferences
      userPrefs: 'key',
    });
  }
}

// Global database instance
export const db = new BijmantraDB();

/**
 * Clear all offline data (use with caution)
 */
export async function clearAllData(): Promise<void> {
  await db.programs.clear();
  await db.trials.clear();
  await db.studies.clear();
  await db.germplasm.clear();
  await db.observations.clear();
  await db.traits.clear();
  await db.pendingSync.clear();
  await db.syncLog.clear();
}

/**
 * Get count of pending sync operations
 */
export async function getPendingSyncCount(): Promise<number> {
  return await db.pendingSync.count();
}

/**
 * Get all entities with pending changes
 */
export async function getPendingEntities(): Promise<PendingSyncOperation[]> {
  return await db.pendingSync.toArray();
}

import Dexie, { Table } from 'dexie';

// ============================================
// INTERFACES
// ============================================

export interface OfflineTrial {
  id: string; // dbId
  name: string;
  programName: string;
  active: boolean;
  lastSync: number;
}

export interface OfflinePlot {
  id: string; // dbId
  trialId: string;
  accessionId: string;
  accessionName: string;
  replicate: number;
  block: number;
  plotNumber: number;
  // We can store layout info here
}

export interface OfflineTrait {
  id: string; // dbId / code
  trialId: string;
  name: string;
  dataType: string; // 'Numeric', 'Categorical'
  min?: number;
  max?: number;
  unit?: string;
}

export interface OfflineObservation {
  id?: number; // Auto-increment local ID
  statsId?: string; // Backend ID if already synced
  plotId: string;
  traitId: string;
  traitName: string;
  value: string | number;
  timestamp: number;
  synced: 0 | 1; // 0 = pending, 1 = synced
}

export interface SyncQueueItem {
  id?: number;
  action: 'CREATE' | 'UPDATE' | 'DELETE';
  entity: 'OBSERVATION' | 'PLOT' | 'TRIAL';
  data: any;
  timestamp: number;
  retryCount: number;
}

// ============================================
// DATABASE CLASS
// ============================================

export class FieldScoutDB extends Dexie {
  trials!: Table<OfflineTrial>;
  plots!: Table<OfflinePlot>;
  traits!: Table<OfflineTrait>;
  observations!: Table<OfflineObservation>;
  syncQueue!: Table<SyncQueueItem>;

  constructor() {
    super('BijmantraFieldScout');
    
    // Schema definition
    // ++id means auto-incrementing primary key
    // &id means unique index
    // [index1+index2] means compound index
    this.version(2).stores({
      trials: '&id, name, active',
      plots: '&id, trialId, [trialId+plotNumber]',
      traits: '&id, trialId',
      observations: '++id, &statsId, [plotId+traitId], synced',
      syncQueue: '++id, timestamp'
    });
  }
}

export const db = new FieldScoutDB();

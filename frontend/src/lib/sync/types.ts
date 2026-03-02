export interface Observation {
  id?: number; // Local auto-increment ID
  uuid: string; // Unique ID for sync (client-generated)
  observationDbId?: string; // Server ID
  observationUnitDbId: string;
  observationVariableDbId: string;
  value: string | number | any; // The observed value
  timestamp: number;
  synced: boolean;
  deleted?: boolean;
  notes?: string;
  media?: string[]; // Array of media URLs/Paths (Mergable-Log)
}

export interface Germplasm {
  id?: number;
  germplasmDbId: string;
  germplasmName: string;
  accessionNumber: string;
  pedigree?: string;
  // Additional fields for lookup
}

export interface PendingUpload {
  id?: number;
  uuid: string; // Reference to the object UUID
  type: 'observation' | 'media'; // Type of upload
  operation: 'CREATE' | 'UPDATE' | 'DELETE';
  payload: any;
  timestamp: number;
  retryCount: number;
  error?: string;
}

export interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime: number | null;
  pendingUploads: number;
  syncError: string | null;
}

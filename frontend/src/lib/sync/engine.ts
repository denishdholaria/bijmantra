import { db, BijmantraSyncDB } from './db';
import { crdtManager, CRDTManager } from './crdt';
import { PendingUpload, Observation, SyncStatus } from './types';

export class SyncEngine {
  private db: BijmantraSyncDB;
  private crdt: CRDTManager;
  private isOnline: boolean = typeof navigator !== 'undefined' ? navigator.onLine : true;
  private listeners: Set<(status: SyncStatus) => void> = new Set();
  private syncInProgress: boolean = false;
  private syncError: string | null = null;
  private lastSyncTime: number | null = null;

  constructor() {
    this.db = db;
    this.crdt = crdtManager;

    // Initialize listeners
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        this.isOnline = true;
        this.notifyListeners();
        this.pushChanges();
      });
      window.addEventListener('offline', () => {
        this.isOnline = false;
        this.notifyListeners();
      });
    }

    this.init();
  }

  async init() {
    await this.crdt.init();
    this.notifyListeners();
  }

  /**
   * Called by UI when user creates/updates observation
   */
  async saveObservation(obs: Observation, isNew: boolean) {
    // 1. Update Dexie (Local View)
    await this.db.observations.put({
      ...obs,
      synced: false,
      timestamp: Date.now()
    });

    // 2. Update CRDT (Conflict Resolution State)
    this.crdt.updateObservation(obs.uuid, obs);

    // 3. Queue Upload
    await this.db.pendingUploads.add({
      uuid: obs.uuid,
      type: 'observation',
      operation: isNew ? 'CREATE' : 'UPDATE',
      payload: obs,
      timestamp: Date.now(),
      retryCount: 0
    });

    this.notifyListeners();

    // Trigger sync if online
    if (this.isOnline) {
      this.pushChanges();
    }
  }

  /**
   * Delete Observation
   */
  async deleteObservation(uuid: string) {
    // 1. Update Dexie
    const obs = await this.db.observations.where('uuid').equals(uuid).first();
    if (obs) {
        await this.db.observations.update(obs.id!, { deleted: true, synced: false });
    }

    // 2. Update CRDT
    this.crdt.deleteObservation(uuid);

    // 3. Queue Upload
    await this.db.pendingUploads.add({
        uuid: uuid,
        type: 'observation',
        operation: 'DELETE',
        payload: { uuid }, // Payload only needs ID
        timestamp: Date.now(),
        retryCount: 0
    });

    this.notifyListeners();

    if (this.isOnline) {
        this.pushChanges();
    }
  }

  async saveMedia(obsUuid: string, file: File, photoPath: string) {
     // 1. Update Dexie
     const obs = await this.db.observations.where('uuid').equals(obsUuid).first();
     if (obs) {
         const media = obs.media || [];
         const newMedia = [...media, photoPath];
         await this.db.observations.update(obs.id!, { media: newMedia, synced: false });

         // 2. Update CRDT
         this.crdt.addMedia(obsUuid, photoPath);

         // 3. Queue Upload
         // Note: File handling needs robust FormData logic or Blob storage.
         // Here we just queue the metadata update or trigger file upload logic.
         // Assuming 'file' is handled by a separate media uploader service that returns 'photoPath',
         // then we just update the observation.
         await this.db.pendingUploads.add({
             uuid: obsUuid,
             type: 'media',
             operation: 'UPDATE',
             payload: { photoPath },
             timestamp: Date.now(),
             retryCount: 0
         });

         this.notifyListeners();
         if (this.isOnline) this.pushChanges();
     }
  }

  /**
   * Pushes pending changes to server
   */
  async pushChanges() {
    if (!this.isOnline || this.syncInProgress) return;

    this.syncInProgress = true;
    this.notifyListeners();

    try {
      const pending = await this.db.pendingUploads.orderBy('timestamp').toArray();

      for (const task of pending) {
        try {
          await this.processTask(task);
          // On success, remove from queue
          await this.db.pendingUploads.delete(task.id!);
        } catch (error) {
          console.error('Sync failed for task', task, error);
          await this.db.pendingUploads.update(task.id!, {
            retryCount: (task.retryCount || 0) + 1,
            error: (error as Error).message
          });
        }
      }

      this.lastSyncTime = Date.now();
    } catch (e) {
      this.syncError = (e as Error).message;
    } finally {
      this.syncInProgress = false;
      this.notifyListeners();
    }
  }

  private async processTask(task: PendingUpload) {
    const token = localStorage.getItem('auth_token');
    // If no token, we can't sync. Throwing error will retry.
    // If token expired (401), we should catch and handle.
    if (!token) throw new Error('No auth token');

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };

    const baseUrl = '/brapi/v2';

    if (task.type === 'observation') {
        let url = `${baseUrl}/observations`;
        let method = 'POST';
        let body;

        if (task.operation === 'DELETE') {
             // BrAPI delete logic vary. Assuming DELETE /observations/{id}
             // Need to resolve UUID to DbId if possible, or send UUID if server supports it.
             // If we only have UUID and server needs DbId, we might fail if we never synced the creation.
             // If we never synced creation, we shouldn't send DELETE, just delete local.
             // But for simplicity:
             url = `${url}/${task.payload.uuid}`; // Or look up DbId
             method = 'DELETE';
        } else if (task.operation === 'UPDATE') {
             // If we have DbId, use it.
             const dbId = task.payload.observationDbId;
             if (dbId) {
                 url = `${url}/${dbId}`;
                 method = 'PUT';
                 body = JSON.stringify(task.payload);
             } else {
                 // If no DbId, it might be a CREATE that was queued as UPDATE (rare) or just try POST
                 method = 'POST';
                 body = JSON.stringify([task.payload]);
             }
        } else {
             // CREATE
             body = JSON.stringify([task.payload]);
        }

        if (method !== 'DELETE' && !body) return; // Should not happen

        const res = await fetch(url, {
            method,
            headers,
            body
        });

        if (!res.ok) {
            if (res.status === 401) {
                // Token expired.
                // We should stop sync and prompt user or refresh token.
                throw new Error('Unauthorized');
            }
            throw new Error(`Server returned ${res.status}`);
        }

        // Update local sync status
        await this.db.observations.where('uuid').equals(task.uuid).modify({ synced: true });
    }
  }

  /**
   * Pulls changes from server (Differential Sync)
   */
  async pullChanges() {
    if (!this.isOnline) return;

    this.syncInProgress = true;
    this.notifyListeners();

    try {
       const token = localStorage.getItem('auth_token');
       if (!token) return;

       // 1. Fetch from Server
       // Fetch observations updated since last sync
       // Ideally we store lastSyncTime in DB meta for persistence
       const lastSync = this.lastSyncTime || 0;
       // BrAPI usually uses ISO8601 strings
       const lastSyncIso = new Date(lastSync).toISOString();

       const headers = {
           'Authorization': `Bearer ${token}`,
           'Content-Type': 'application/json'
       };

       // Note: Standard BrAPI might not support updatedSince on GET /observations directly
       // It might be GET /observations?observationTimeStampRangeStart=...
       // We assume a standard query param for delta here.
       const res = await fetch(`/brapi/v2/observations?observationTimeStampRangeStart=${encodeURIComponent(lastSyncIso)}`, { headers });

       if (res.ok) {
           const json = await res.json();
           const remoteObsList = json.result?.data || [];

           for (const remoteObs of remoteObsList) {
               // 2. Merge into CRDT
               // We need to map remote fields to our Observation type
               const uuid = remoteObs.externalReferences?.find((r: any) => r.referenceSource === 'UUID')?.referenceID || remoteObs.observationDbId;

               if (!uuid) continue;

               this.crdt.updateObservation(uuid, remoteObs);

               // 3. Update Dexie
               // Get the merged result from CRDT
               const merged = this.crdt.getObservation(uuid);
               if (merged) {
                   const existing = await this.db.observations.where('uuid').equals(uuid).first();
                   await this.db.observations.put({
                       ...merged,
                       id: existing?.id, // Keep local ID
                       synced: true
                   });
               }
           }
       }

       // Sync Germplasm Lookup
       await this.syncGermplasm();

       this.lastSyncTime = Date.now();
    } catch (e) {
        console.error('Pull failed', e);
        this.syncError = (e as Error).message;
    } finally {
        this.syncInProgress = false;
        this.notifyListeners();
    }
  }

  private async syncGermplasm() {
      try {
          const token = localStorage.getItem('auth_token');
          if (!token) return;

          // Simple fetch of first page of germplasm for lookup cache
          // In real world, this would be paginated loop or Delta sync
          const res = await fetch('/brapi/v2/germplasm?pageSize=1000', {
              headers: { 'Authorization': `Bearer ${token}` }
          });

          if (!res.ok) return;

          const json = await res.json();
          const germplasmList = json.result?.data || [];

          // Bulk put for performance
          await this.db.germplasm.bulkPut(germplasmList.map((g: any) => ({
              germplasmDbId: g.germplasmDbId,
              germplasmName: g.germplasmName,
              accessionNumber: g.accessionNumber
          })));
      } catch (e) {
          console.error('Germplasm sync failed', e);
      }
  }

  /**
   * Background Sync Loop
   */
  startBackgroundSync(intervalMs: number = 60000) {
      setInterval(() => {
          if (this.isOnline) {
              this.pushChanges();
              this.pullChanges();
          }
      }, intervalMs);
  }

  subscribe(listener: (status: SyncStatus) => void) {
    this.listeners.add(listener);
    listener(this.getStatus());
    return () => this.listeners.delete(listener);
  }

  private notifyListeners() {
    const status = this.getStatus();
    this.listeners.forEach(l => l(status));
  }

  getStatus(): SyncStatus {
    return {
      isOnline: this.isOnline,
      isSyncing: this.syncInProgress,
      lastSyncTime: this.lastSyncTime,
      pendingUploads: 0,
      syncError: this.syncError
    };
  }
}

export const syncEngine = new SyncEngine();

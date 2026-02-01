import * as Y from 'yjs';
import { IndexeddbPersistence } from 'y-indexeddb';
import { Observation } from './types';

export class CRDTManager {
  doc: Y.Doc;
  persistence: IndexeddbPersistence | null = null;
  observationsMap: Y.Map<Y.Map<any>>;

  constructor() {
    this.doc = new Y.Doc();
    this.observationsMap = this.doc.getMap('observations');

    // We initialize persistence asynchronously in init()
  }

  async init() {
    if (typeof window !== 'undefined') {
        this.persistence = new IndexeddbPersistence('bijmantra-crdt', this.doc);
        await new Promise<void>((resolve) => {
            this.persistence!.once('synced', () => {
                console.log('Yjs content loaded from IndexedDB');
                resolve();
            });
        });
    }
  }

  getObservation(uuid: string): Observation | null {
    if (!this.observationsMap.has(uuid)) return null;
    const yObs = this.observationsMap.get(uuid);
    if (!yObs) return null;

    return yObs.toJSON() as Observation;
  }

  getAllObservations(): Observation[] {
    const result: Observation[] = [];
    this.observationsMap.forEach((yObs) => {
      result.push(yObs.toJSON() as Observation);
    });
    return result;
  }

  /**
   * Updates an observation using LWW for fields.
   * Creates it if it doesn't exist.
   */
  updateObservation(uuid: string, data: Partial<Observation>) {
    this.doc.transact(() => {
      let yObs = this.observationsMap.get(uuid);

      if (!yObs) {
        yObs = new Y.Map();
        this.observationsMap.set(uuid, yObs);
      }

      // Update fields (LWW)
      Object.entries(data).forEach(([key, value]) => {
        // Protect 'media' field from LWW overwrite if it's meant to be append-only.
        // If the update comes from a pull (server state), we might want to merge,
        // but 'addMedia' is for local appends.
        // For now, we skip 'media' in generic updates to preserve the Y.Array structure
        // unless we explicitly want to overwrite it (which we shouldn't for Mergable-Log).
        if (key === 'media') {
            return;
        }
        yObs!.set(key, value);
      });

      yObs!.set('timestamp', Date.now());
    });
  }

  /**
   * Appends media to the observation's media list (Mergable-Log).
   */
  addMedia(uuid: string, mediaItem: string) {
    this.doc.transact(() => {
      let yObs = this.observationsMap.get(uuid);
      if (!yObs) {
        // Create if not exists (shouldn't happen usually)
        yObs = new Y.Map();
        this.observationsMap.set(uuid, yObs);
      }

      // We need to check if 'media' is already a Y.Array or just a JS Array property
      // In the updateObservation above, yObs.set('media', [...]) creates a JS Array content.
      // To support true merge, we should use Y.Array.

      // Let's ensure we use Y.Array for media
      if (!yObs.has('media')) {
          const yArray = new Y.Array();
          yObs.set('media', yArray);
          yArray.push([mediaItem]);
      } else {
          const existing = yObs.get('media');
          if (existing instanceof Y.Array) {
              existing.push([mediaItem]);
          } else if (Array.isArray(existing)) {
              // Convert JS array to Y.Array
              const yArray = new Y.Array();
              yArray.push(existing);
              yArray.push([mediaItem]);
              yObs.set('media', yArray);
          }
      }
    });
  }

  deleteObservation(uuid: string) {
    this.observationsMap.delete(uuid);
  }
}

export const crdtManager = new CRDTManager();

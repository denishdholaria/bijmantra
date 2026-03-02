import Dexie, { Table } from 'dexie';
import { Observation, Germplasm, PendingUpload } from './types';

export class BijmantraSyncDB extends Dexie {
  observations!: Table<Observation>;
  germplasm!: Table<Germplasm>;
  pendingUploads!: Table<PendingUpload>;
  meta!: Table<{ key: string; value: any }>;

  constructor() {
    super('BijmantraSyncDB');

    this.version(1).stores({
      observations: '++id, uuid, observationDbId, observationUnitDbId, synced, timestamp',
      germplasm: '++id, germplasmDbId, germplasmName, accessionNumber',
      pendingUploads: '++id, uuid, timestamp, type',
      meta: 'key'
    });
  }
}

export const db = new BijmantraSyncDB();

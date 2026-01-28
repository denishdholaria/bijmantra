/**
 * IndexedDB setup using Dexie.js for offline storage
 */

import Dexie, { Table } from 'dexie'

// Define database schema interfaces
export interface CachedObservation {
  id?: number
  observationDbId: string
  observationUnitDbId: string
  observationVariableDbId: string
  value: string
  timestamp: string
  synced: boolean
  createdAt: Date
}

export interface CachedTrait {
  id?: number
  traitDbId: string
  traitName: string
  traitClass: string
  data: any
  cachedAt: Date
}

// Dexie database class
export class BijmantraDB extends Dexie {
  observations!: Table<CachedObservation>
  traits!: Table<CachedTrait>

  constructor() {
    super('BijmantraDB')
    
    this.version(1).stores({
      observations: '++id, observationDbId, synced, createdAt',
      traits: '++id, traitDbId, cachedAt',
    })
  }
}

// Create database instance
export const db = new BijmantraDB()

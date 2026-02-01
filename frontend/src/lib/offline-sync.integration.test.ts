/**
 * Offline Sync Integration Tests
 * Tests for real-world offline/online scenarios
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { offlineSync, SyncableDocument } from './offline-sync'

describe('Offline Sync Integration', () => {
  beforeEach(async () => {
    await offlineSync.clearLocalData()
    // Reset online status
    Object.defineProperty(navigator, 'onLine', { value: true, writable: true })
  })

  afterEach(async () => {
    await offlineSync.clearLocalData()
    vi.restoreAllMocks()
  })

  describe('Scenario: Field Data Collection (Offline)', () => {
    it('should store observations while offline', async () => {
      // Simulate going offline
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      // Collect field observations
      const observations = [
        { id: 'obs-1', trait: 'plant_height', value: '125', unit: 'cm' },
        { id: 'obs-2', trait: 'leaf_count', value: '12', unit: 'count' },
        { id: 'obs-3', trait: 'chlorophyll', value: '45.2', unit: 'SPAD' },
      ]

      observations.forEach((obs) => {
        offlineSync.upsertDocument({
          id: obs.id,
          type: 'observation',
          data: obs,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        })
      })

      // Verify all observations are stored
      const stored = offlineSync.getAllDocuments('observation')
      expect(stored.length).toBe(3)

      // Verify they're marked as pending
      const pending = offlineSync.getPendingDocuments()
      expect(pending.length).toBe(3)
      expect(pending.every((d) => d.localOnly)).toBe(true)
    })

    it('should preserve data integrity across offline sessions', async () => {
      // Store data
      offlineSync.upsertDocument({
        id: 'germ-1',
        type: 'germplasm',
        data: {
          name: 'IR64',
          species: 'Oryza sativa',
          accessionNumber: 'IRRI-001',
        },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      // Retrieve and verify
      const retrieved = offlineSync.getDocument('germplasm', 'germ-1')
      expect(retrieved).toBeDefined()
      expect(retrieved?.data.name).toBe('IR64')
      expect(retrieved?.data.species).toBe('Oryza sativa')
    })
  })

  describe('Scenario: Sync Queue Management', () => {
    it('should track pending changes count', () => {
      const initialStatus = offlineSync.getStatus()
      expect(initialStatus.pendingChanges).toBe(0)

      // Add documents
      offlineSync.upsertDocument({
        id: 'trial-1',
        type: 'trial',
        data: { name: 'Yield Trial 2024' },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      const pending = offlineSync.getPendingDocuments()
      expect(pending.length).toBeGreaterThan(0)
    })

    it('should batch multiple changes for sync', () => {
      // Add multiple documents of different types
      offlineSync.upsertDocument({
        id: 'germ-1',
        type: 'germplasm',
        data: { name: 'Variety A' },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      offlineSync.upsertDocument({
        id: 'trial-1',
        type: 'trial',
        data: { name: 'Trial 1' },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      offlineSync.upsertDocument({
        id: 'obs-1',
        type: 'observation',
        data: { value: '100' },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      const pending = offlineSync.getPendingDocuments()
      expect(pending.length).toBe(3)

      // Verify different types
      const types = new Set(pending.map((d) => d.type))
      expect(types.size).toBe(3)
    })
  })

  describe('Scenario: Data Updates', () => {
    it('should handle document updates correctly', () => {
      // Create initial document
      offlineSync.upsertDocument({
        id: 'cross-1',
        type: 'cross',
        data: {
          femaleParent: 'IR64',
          maleParent: 'Nipponbare',
          status: 'planned',
        },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      // Update the document
      offlineSync.upsertDocument({
        id: 'cross-1',
        type: 'cross',
        data: {
          femaleParent: 'IR64',
          maleParent: 'Nipponbare',
          status: 'completed',
          seedsHarvested: 150,
        },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      const updated = offlineSync.getDocument('cross', 'cross-1')
      expect(updated?.data.status).toBe('completed')
      expect(updated?.data.seedsHarvested).toBe(150)
    })

    it('should preserve createdAt on updates', async () => {
      offlineSync.upsertDocument({
        id: 'seedlot-1',
        type: 'seedlot',
        data: { name: 'Lot A' },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      const firstDoc = offlineSync.getDocument('seedlot', 'seedlot-1')
      const originalCreatedAt = firstDoc?.createdAt

      // Wait a bit to ensure different timestamp
      await new Promise((resolve) => setTimeout(resolve, 10))

      // Update
      offlineSync.upsertDocument({
        id: 'seedlot-1',
        type: 'seedlot',
        data: { name: 'Lot A Updated' },
        createdAt: Date.now(), // This should be ignored
        updatedAt: Date.now(),
      })

      const updated = offlineSync.getDocument('seedlot', 'seedlot-1')
      expect(updated?.createdAt).toBe(originalCreatedAt)
      expect(updated?.updatedAt).toBeGreaterThanOrEqual(originalCreatedAt || 0)
    })
  })

  describe('Scenario: Document Deletion', () => {
    it('should delete documents correctly', () => {
      offlineSync.upsertDocument({
        id: 'obs-delete',
        type: 'observation',
        data: { value: 'to be deleted' },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      expect(offlineSync.getDocument('observation', 'obs-delete')).toBeDefined()

      offlineSync.deleteDocument('observation', 'obs-delete')

      expect(offlineSync.getDocument('observation', 'obs-delete')).toBeUndefined()
    })
  })

  describe('Scenario: Network Status', () => {
    it('should track online/offline status', () => {
      const status = offlineSync.getStatus()
      expect(typeof status.isOnline).toBe('boolean')
    })

    it('should mark documents as localOnly when offline', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      offlineSync.upsertDocument({
        id: 'offline-doc',
        type: 'germplasm',
        data: { name: 'Offline Entry' },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })

      const doc = offlineSync.getDocument('germplasm', 'offline-doc')
      expect(doc?.localOnly).toBe(true)
    })
  })

  describe('Scenario: Sync Status', () => {
    it('should provide complete sync status', () => {
      const status = offlineSync.getStatus()

      expect(status).toHaveProperty('isOnline')
      expect(status).toHaveProperty('isSyncing')
      expect(status).toHaveProperty('pendingChanges')
      expect(status).toHaveProperty('lastSyncTime')
      expect(status).toHaveProperty('conflicts')
      expect(Array.isArray(status.conflicts)).toBe(true)
    })
  })
})

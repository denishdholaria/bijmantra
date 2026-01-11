/**
 * Offline Sync Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { simulateOffline, simulateOnline } from '@/test/setup'

// Mock Yjs modules with class constructors for Vitest 4 compatibility
vi.mock('yjs', () => ({
  Doc: class MockDoc {
    getMap = vi.fn(() => ({
      get: vi.fn(),
      set: vi.fn(),
      delete: vi.fn(),
      forEach: vi.fn(),
    }))
    on = vi.fn()
    destroy = vi.fn()
  },
}))

vi.mock('y-indexeddb', () => ({
  IndexeddbPersistence: class MockPersistence {
    once = vi.fn((event: string, cb: () => void) => cb())
    clearData = vi.fn()
  },
}))

describe('Offline Sync', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    simulateOnline()
  })

  describe('network status', () => {
    it('should detect online status', () => {
      simulateOnline()
      expect(navigator.onLine).toBe(true)
    })

    it('should detect offline status', () => {
      simulateOffline()
      expect(navigator.onLine).toBe(false)
    })
  })

  describe('SyncableDocument types', () => {
    it('should support all document types', async () => {
      const { offlineSync } = await import('./offline-sync')
      
      const types = ['germplasm', 'observation', 'trial', 'cross', 'seedlot'] as const
      
      types.forEach((type) => {
        const collection = offlineSync.getCollection(type)
        expect(collection).toBeDefined()
      })
    })
  })

  describe('sync status', () => {
    it('should return current sync status', async () => {
      const { offlineSync } = await import('./offline-sync')
      
      const status = offlineSync.getStatus()
      
      expect(status).toHaveProperty('isOnline')
      expect(status).toHaveProperty('isSyncing')
      expect(status).toHaveProperty('pendingChanges')
      expect(status).toHaveProperty('lastSyncTime')
      expect(status).toHaveProperty('conflicts')
    })
  })
})

describe('useOfflineSync hook', () => {
  it('should export useOfflineSync hook', async () => {
    const { useOfflineSync } = await import('./offline-sync')
    expect(useOfflineSync).toBeDefined()
    expect(typeof useOfflineSync).toBe('function')
  })

  it('should export useSyncableCollection hook', async () => {
    const { useSyncableCollection } = await import('./offline-sync')
    expect(useSyncableCollection).toBeDefined()
    expect(typeof useSyncableCollection).toBe('function')
  })
})

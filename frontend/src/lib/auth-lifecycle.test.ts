import { describe, expect, it, beforeEach, vi } from 'vitest'
import {
  clearTenantClientState,
  TENANT_PERSISTENCE_KEYS,
} from './auth-lifecycle'
import { queryClient } from './query-client'
import { backgroundSyncService } from '@/services/BackgroundSyncService'

vi.mock('@/lib/offline-sync', () => ({
  offlineSync: {
    clearLocalData: vi.fn().mockResolvedValue(undefined),
  },
}))

vi.mock('@/framework/sync/db', () => ({
  clearAllData: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('@/services/BackgroundSyncService', () => ({
  backgroundSyncService: {
    clearLocalData: vi.fn().mockResolvedValue(undefined),
  },
}))

vi.mock('@/lib/socket', () => ({
  socketService: {
    disconnect: vi.fn(),
  },
}))

describe('auth lifecycle cleanup', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    queryClient.clear()
    localStorage.clear()
    vi.stubGlobal('caches', {
      delete: vi.fn().mockResolvedValue(true),
    })
  })

  it('clears tenant query data and persisted tenant stores', async () => {
    queryClient.setQueryData(['seed-bank', 'vaults'], [{ id: 'vault-a' }])
    TENANT_PERSISTENCE_KEYS.forEach((key) => localStorage.setItem(key, 'tenant-data'))

    await clearTenantClientState()

    expect(queryClient.getQueryData(['seed-bank', 'vaults'])).toBeUndefined()
    TENANT_PERSISTENCE_KEYS.forEach((key) => {
      expect(localStorage.getItem(key)).toBeNull()
    })
  })

  it('clears every offline data store, including PWA background drafts', async () => {
    await clearTenantClientState()

    expect(backgroundSyncService.clearLocalData).toHaveBeenCalled()
  })

  it('purges tenant-sensitive runtime caches', async () => {
    const cacheDelete = vi.fn().mockResolvedValue(true)
    vi.stubGlobal('caches', { delete: cacheDelete })

    await clearTenantClientState()

    expect(cacheDelete).toHaveBeenCalledWith('scientific-metadata-cache')
    expect(cacheDelete).toHaveBeenCalledWith('dataset-cache')
    expect(cacheDelete).toHaveBeenCalledWith('field-images-cache')
    expect(cacheDelete).toHaveBeenCalledWith('observation-write-through')
  })
})

import { queryClient } from '@/lib/query-client'
import { logger } from './logger'

export const TENANT_PERSISTENCE_KEYS = [
  'bijmantra-sync-storage',
  'bijmantra-workspace',
  'bijmantra-custom-workspaces',
  'bijmantra-notifications',
  'bijmantra-workbench-storage',
  'bijmantra-navigation-storage',
  'bijmantra-dock',
]

const TENANT_CACHE_NAMES = [
  'scientific-metadata-cache',
  'dataset-cache',
  'field-images-cache',
  'observation-write-through',
]

async function clearOfflineState(): Promise<void> {
  const [{ offlineSync }, { clearAllData }, { backgroundSyncService }] = await Promise.all([
    import('@/lib/offline-sync'),
    import('@/framework/sync/db'),
    import('@/services/BackgroundSyncService'),
  ])

  await Promise.all([
    offlineSync.clearLocalData(),
    clearAllData(),
    backgroundSyncService.clearLocalData(),
  ])
}

async function disconnectRealtime(): Promise<void> {
  const { socketService } = await import('@/lib/socket')
  socketService.disconnect()
}

async function clearTenantCaches(): Promise<void> {
  if (typeof globalThis.caches === 'undefined') {
    return
  }

  await Promise.all(TENANT_CACHE_NAMES.map((cacheName) => globalThis.caches.delete(cacheName)))
}

export async function clearTenantClientState(): Promise<void> {
  queryClient.clear()

  if (typeof localStorage !== 'undefined') {
    TENANT_PERSISTENCE_KEYS.forEach((key) => localStorage.removeItem(key))
  }

  const results = await Promise.allSettled([
    clearOfflineState(),
    disconnectRealtime(),
    clearTenantCaches(),
  ])

  results.forEach((result) => {
    if (result.status === 'rejected') {
      logger.warn('[AuthLifecycle] Tenant client state cleanup failed', {
        error: result.reason,
      })
    }
  })
}

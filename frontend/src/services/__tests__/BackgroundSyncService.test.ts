import { beforeEach, describe, expect, it, vi } from 'vitest'
import { BackgroundSyncService } from '../BackgroundSyncService'

async function resetDrafts(service: BackgroundSyncService) {
  const existing = await service.listDrafts()
  await Promise.all(existing.map((d) => service.deleteDraft(d.id)))
}

describe('BackgroundSyncService IndexedDB CRUD', () => {
  let service: BackgroundSyncService

  beforeEach(async () => {
    service = new BackgroundSyncService()
    await resetDrafts(service)
    vi.restoreAllMocks()
    Object.defineProperty(navigator, 'onLine', { value: true, writable: true })
  })

  it('creates and lists draft observations', async () => {
    await service.saveDraft({
      id: 'draft-1',
      trialDbId: 'trial-1',
      observationUnitDbId: 'plot-1',
      traitDbId: 'trait-1',
      value: '12.3',
    })

    const drafts = await service.listDrafts()
    expect(drafts).toHaveLength(1)
    expect(drafts[0].id).toBe('draft-1')
    expect(drafts[0].synced).toBe(false)
  })

  it('updates sync state and deletes drafts', async () => {
    await service.saveDraft({
      id: 'draft-2',
      trialDbId: 'trial-1',
      observationUnitDbId: 'plot-2',
      traitDbId: 'trait-2',
      value: 42,
    })

    await service.markSynced(['draft-2'])
    const unsynced = await service.listDrafts(true)
    expect(unsynced).toHaveLength(0)

    await service.deleteDraft('draft-2')
    const all = await service.listDrafts()
    expect(all).toHaveLength(0)
  })
})

describe('BackgroundSyncService sync logic', () => {
  let service: BackgroundSyncService

  beforeEach(async () => {
    service = new BackgroundSyncService()
    await resetDrafts(service)
    Object.defineProperty(navigator, 'onLine', { value: true, writable: true })

    await service.saveDraft({
      id: 'draft-sync-1',
      trialDbId: 'trial-99',
      observationUnitDbId: 'plot-99',
      traitDbId: 'trait-99',
      value: '88',
    })
  })

  it('skips sync when offline', async () => {
    Object.defineProperty(navigator, 'onLine', { value: false, writable: true })
    const result = await service.syncManager()
    expect(result.skippedReason).toBe('offline')
  })

  it('pushes local drafts when online', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200 } as Response)))
    const result = await service.syncManager()
    expect(result.pushed).toBe(1)

    const drafts = await service.listDrafts(true)
    expect(drafts).toHaveLength(0)
  })
})

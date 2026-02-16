export type DraftObservation = {
  id: string
  trialDbId: string
  observationUnitDbId: string
  traitDbId: string
  value: string | number
  updatedAt: number
  createdAt: number
  synced?: boolean
}

type BatteryLike = {
  charging: boolean
  level: number
}

const DB_NAME = 'bijmantra-pwa'
const STORE_NAME = 'draft_observations'

export class BackgroundSyncService {
  private dbPromise: Promise<IDBDatabase> | null = null

  private openDb(): Promise<IDBDatabase> {
    if (this.dbPromise) return this.dbPromise

    this.dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1)
      request.onupgradeneeded = () => {
        const db = request.result
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' })
          store.createIndex('updatedAt', 'updatedAt')
          store.createIndex('synced', 'synced')
        }
      }
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })

    return this.dbPromise
  }

  async saveDraft(draft: Omit<DraftObservation, 'updatedAt' | 'createdAt' | 'synced'>): Promise<DraftObservation> {
    const now = Date.now()
    const record: DraftObservation = {
      ...draft,
      createdAt: now,
      updatedAt: now,
      synced: false,
    }

    const db = await this.openDb()
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      tx.objectStore(STORE_NAME).put(record)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })

    return record
  }

  async listDrafts(onlyUnsynced = false): Promise<DraftObservation[]> {
    const db = await this.openDb()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const request = tx.objectStore(STORE_NAME).getAll()
      request.onsuccess = () => {
        const drafts = (request.result || []) as DraftObservation[]
        resolve(onlyUnsynced ? drafts.filter((d) => !d.synced) : drafts)
      }
      request.onerror = () => reject(request.error)
    })
  }

  async markSynced(ids: string[]): Promise<void> {
    const db = await this.openDb()
    await Promise.all(
      ids.map(
        (id) =>
          new Promise<void>((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite')
            const store = tx.objectStore(STORE_NAME)
            const getReq = store.get(id)
            getReq.onsuccess = () => {
              const current = getReq.result as DraftObservation | undefined
              if (!current) return resolve()
              store.put({ ...current, synced: true, updatedAt: Date.now() })
            }
            tx.oncomplete = () => resolve()
            tx.onerror = () => reject(tx.error)
          }),
      ),
    )
  }

  async deleteDraft(id: string): Promise<void> {
    const db = await this.openDb()
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      tx.objectStore(STORE_NAME).delete(id)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  }

  async syncManager(): Promise<{ pushed: number; skippedReason?: string }> {
    if (!navigator.onLine) {
      return { pushed: 0, skippedReason: 'offline' }
    }

    const connection = (navigator as Navigator & { connection?: { effectiveType?: string } }).connection
    if (connection?.effectiveType && ['slow-2g', '2g', '3g'].includes(connection.effectiveType)) {
      return { pushed: 0, skippedReason: `network-${connection.effectiveType}` }
    }

    const battery = await this.getBattery()
    if (battery && !battery.charging && battery.level < 0.2) {
      return { pushed: 0, skippedReason: 'low-battery' }
    }

    const drafts = await this.listDrafts(true)
    if (drafts.length === 0) return { pushed: 0 }

    const response = await fetch('/api/v2/pwa/drafts/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ drafts }),
    })

    if (!response.ok) throw new Error(`Sync failed: ${response.status}`)

    await this.markSynced(drafts.map((d) => d.id))
    return { pushed: drafts.length }
  }

  attachOnlineSync(): () => void {
    const handler = () => {
      this.syncManager().catch(() => undefined)
    }
    window.addEventListener('online', handler)
    return () => window.removeEventListener('online', handler)
  }

  private async getBattery(): Promise<BatteryLike | null> {
    const nav = navigator as Navigator & { getBattery?: () => Promise<BatteryLike> }
    if (!nav.getBattery) return null
    try {
      return await nav.getBattery()
    } catch {
      return null
    }
  }
}

export const backgroundSyncService = new BackgroundSyncService()

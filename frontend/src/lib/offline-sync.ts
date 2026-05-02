/**
 * Offline-First Data Sync with CRDTs
 * Conflict-free synchronization using Yjs
 * Enables seamless offline/online transitions for field data collection
 */

import * as Y from 'yjs'
import { logger } from './logger'

// Lazy import to avoid issues in environments without IndexedDB
let IndexeddbPersistence: typeof import('y-indexeddb').IndexeddbPersistence | null = null
const getIndexeddbPersistence = async () => {
  if (!IndexeddbPersistence) {
    try {
      const module = await import('y-indexeddb')
      IndexeddbPersistence = module.IndexeddbPersistence
    } catch (e) {
      logger.warn('[OfflineSync] IndexedDB persistence not available', { error: e })
    }
  }
  return IndexeddbPersistence
}

// Types
export interface SyncableDocument {
  id: string
  type: 'germplasm' | 'observation' | 'trial' | 'cross' | 'seedlot'
  data: Record<string, unknown>
  createdAt: number
  updatedAt: number
  syncedAt?: number
  localOnly?: boolean
}

export interface SyncStatus {
  isOnline: boolean
  isSyncing: boolean
  pendingChanges: number
  lastSyncTime: number | null
  conflicts: SyncConflict[]
}

export interface SyncConflict {
  id: string
  documentId: string
  documentType: string
  localValue: unknown
  remoteValue: unknown
  timestamp: number
  resolved: boolean
}

// Sync event types
type SyncEventType = 'sync:start' | 'sync:complete' | 'sync:error' | 'sync:conflict' | 'change:local' | 'change:remote'
type SyncEventCallback = (data: unknown) => void

class OfflineSyncService {
  private ydoc: Y.Doc
  private persistence: InstanceType<typeof import('y-indexeddb').IndexeddbPersistence> | null = null
  private isInitialized = false
  private listeners: Map<SyncEventType, Set<SyncEventCallback>> = new Map()
  private pendingDocIds: Set<string> = new Set()
  private syncStatus: SyncStatus = {
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    isSyncing: false,
    pendingChanges: 0,
    lastSyncTime: null,
    conflicts: [],
  }

  constructor() {
    this.ydoc = new Y.Doc()
    this.setupObservers()
    if (typeof window !== 'undefined') {
      this.setupNetworkListeners()
    }
  }

  private setupObservers(): void {
    const types: SyncableDocument['type'][] = ['germplasm', 'observation', 'trial', 'cross', 'seedlot']
    types.forEach((type) => {
      this.getCollection(type).observe((event) => {
        event.keysChanged.forEach((key) => {
          const doc = this.getDocument(type, key)
          const indexKey = `${type}:${key}`

          if (doc && (doc.localOnly || !doc.syncedAt || doc.updatedAt > doc.syncedAt)) {
            this.pendingDocIds.add(indexKey)
          } else {
            this.pendingDocIds.delete(indexKey)
          }
        })
      })
    })
  }

  private refreshPendingIndex(): void {
    this.pendingDocIds.clear()
    const types: SyncableDocument['type'][] = ['germplasm', 'observation', 'trial', 'cross', 'seedlot']

    types.forEach((type) => {
      const docs = this.getAllDocuments(type)
      docs.forEach((doc) => {
        if (doc.localOnly || !doc.syncedAt || doc.updatedAt > doc.syncedAt) {
          this.pendingDocIds.add(`${doc.type}:${doc.id}`)
        }
      })
    })
  }

  /**
   * Initialize the sync service
   */
  async initialize(userId: string): Promise<void> {
    if (this.isInitialized) return

    // Set up IndexedDB persistence (lazy loaded)
    const PersistenceClass = await getIndexeddbPersistence()
    if (PersistenceClass) {
      this.persistence = new PersistenceClass(`bijmantra-${userId}`, this.ydoc)
      
      await new Promise<void>((resolve) => {
        this.persistence!.once('synced', () => {
          logger.debug('[OfflineSync] IndexedDB synced')
          resolve()
        })
      })
    } else {
      logger.warn('[OfflineSync] Running without IndexedDB persistence')
    }

    // Listen for document changes
    this.ydoc.on('update', (update: Uint8Array, origin: unknown) => {
      if (origin !== 'remote') {
        this.syncStatus.pendingChanges++
        this.emit('change:local', { update })
        this.scheduleSyncToServer()
      }
    })

    this.isInitialized = true
    this.refreshPendingIndex()
    logger.debug('[OfflineSync] Initialized')
  }

  private setupNetworkListeners(): void {
    window.addEventListener('online', () => {
      this.syncStatus.isOnline = true
      logger.debug('[OfflineSync] Online - starting sync')
      this.syncToServer()
    })

    window.addEventListener('offline', () => {
      this.syncStatus.isOnline = false
      logger.debug('[OfflineSync] Offline - changes will be queued')
    })
  }

  /**
   * Get a shared map for a document type
   */
  getCollection(type: SyncableDocument['type']): Y.Map<unknown> {
    return this.ydoc.getMap(type)
  }

  /**
   * Add or update a document
   */
  upsertDocument(doc: SyncableDocument): void {
    const collection = this.getCollection(doc.type)
    const existing = collection.get(doc.id) as SyncableDocument | undefined

    // Check current online status (use navigator.onLine for real-time check)
    const isCurrentlyOnline = typeof navigator !== 'undefined' ? navigator.onLine : true

    const updatedDoc: SyncableDocument = {
      ...doc,
      updatedAt: Date.now(),
      createdAt: existing?.createdAt || Date.now(),
      localOnly: !isCurrentlyOnline,
    }

    collection.set(doc.id, updatedDoc)
  }

  /**
   * Get a document by ID
   */
  getDocument(type: SyncableDocument['type'], id: string): SyncableDocument | undefined {
    const collection = this.getCollection(type)
    return collection.get(id) as SyncableDocument | undefined
  }

  /**
   * Get all documents of a type
   */
  getAllDocuments(type: SyncableDocument['type']): SyncableDocument[] {
    const collection = this.getCollection(type)
    const docs: SyncableDocument[] = []
    collection.forEach((value) => {
      docs.push(value as SyncableDocument)
    })
    return docs
  }

  /**
   * Delete a document
   */
  deleteDocument(type: SyncableDocument['type'], id: string): void {
    const collection = this.getCollection(type)
    collection.delete(id)
  }

  /**
   * Get pending (unsynced) documents
   */
  getPendingDocuments(): SyncableDocument[] {
    const pending: SyncableDocument[] = []

    this.pendingDocIds.forEach((key) => {
      const separatorIndex = key.indexOf(':')
      if (separatorIndex === -1) return

      const type = key.substring(0, separatorIndex) as SyncableDocument['type']
      const id = key.substring(separatorIndex + 1)

      const doc = this.getDocument(type, id)
      if (doc && (doc.localOnly || !doc.syncedAt || doc.updatedAt > doc.syncedAt)) {
        pending.push(doc)
      } else {
        // Self-repair if index is stale
        this.pendingDocIds.delete(key)
      }
    })

    return pending
  }

  private syncTimeout: ReturnType<typeof setTimeout> | null = null

  private scheduleSyncToServer(): void {
    if (this.syncTimeout) {
      clearTimeout(this.syncTimeout)
    }

    // Debounce sync to batch changes
    this.syncTimeout = setTimeout(() => {
      this.syncToServer()
    }, 2000)
  }

  /**
   * Sync local changes to server
   */
  async syncToServer(): Promise<void> {
    if (!this.syncStatus.isOnline || this.syncStatus.isSyncing) {
      return
    }

    const pending = this.getPendingDocuments()
    if (pending.length === 0) {
      return
    }

    this.syncStatus.isSyncing = true
    this.emit('sync:start', { count: pending.length })

    try {
      // Group by type for batch operations
      const grouped = pending.reduce((acc, doc) => {
        if (!acc[doc.type]) acc[doc.type] = []
        acc[doc.type].push(doc)
        return acc
      }, {} as Record<string, SyncableDocument[]>)

      // Sync each type
      for (const [type, docs] of Object.entries(grouped)) {
        await this.syncDocumentType(type as SyncableDocument['type'], docs)
      }

      this.syncStatus.lastSyncTime = Date.now()
      this.syncStatus.pendingChanges = 0
      this.emit('sync:complete', { syncedCount: pending.length })
      
      logger.debug(`[OfflineSync] Synced ${pending.length} documents`)
    } catch (error) {
      logger.error('[OfflineSync] Sync failed', error instanceof Error ? error : new Error(String(error)))
      this.emit('sync:error', { error })
    } finally {
      this.syncStatus.isSyncing = false
    }
  }

  private async syncDocumentType(
    type: SyncableDocument['type'],
    docs: SyncableDocument[]
  ): Promise<void> {
    // Map document types to BrAPI endpoints
    const endpointMap: Record<SyncableDocument['type'], string> = {
      germplasm: '/brapi/v2/germplasm',
      observation: '/brapi/v2/observations',
      trial: '/brapi/v2/trials',
      cross: '/brapi/v2/crosses',
      seedlot: '/brapi/v2/seedlots',
    }

    const endpoint = endpointMap[type]
    const token = localStorage.getItem('auth_token')

    for (const doc of docs) {
      try {
        // Only sync if we have auth token
        if (token) {
          const isUpdate = !!doc.syncedAt
          const url = isUpdate ? `${endpoint}/${doc.id}` : endpoint

          const response = await fetch(url, {
            method: isUpdate ? 'PUT' : 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(doc.data),
          })

          if (!response.ok) {
            // If 401, token expired - don't throw, just skip sync
            if (response.status === 401) {
              logger.warn('[OfflineSync] Auth token expired, skipping sync')
              return
            }
            // For other errors, log but continue with local marking
            logger.warn(`[OfflineSync] Server sync failed for ${type}/${doc.id}: ${response.status}`)
          }
        }

        // Mark as synced locally (even if server sync failed, to prevent retry loops)
        const collection = this.getCollection(type)
        const updatedDoc: SyncableDocument = {
          ...doc,
          syncedAt: Date.now(),
          localOnly: false,
        }
        collection.set(doc.id, updatedDoc)
      } catch (error) {
        // Network error - mark as still pending
        logger.error(`[OfflineSync] Failed to sync ${type}/${doc.id}`, error instanceof Error ? error : new Error(String(error)))
        // Don't throw - continue with other documents
      }
    }
  }

  /**
   * Pull changes from server
   */
  async pullFromServer(): Promise<void> {
    if (!this.syncStatus.isOnline) return

    const token = localStorage.getItem('auth_token')
    if (!token) {
      logger.debug('[OfflineSync] No auth token, skipping pull')
      return
    }

    logger.debug('[OfflineSync] Pulling from server...')

    const types: SyncableDocument['type'][] = ['germplasm', 'observation', 'trial', 'cross', 'seedlot']
    const endpointMap: Record<SyncableDocument['type'], string> = {
      germplasm: '/brapi/v2/germplasm',
      observation: '/brapi/v2/observations',
      trial: '/brapi/v2/trials',
      cross: '/brapi/v2/crosses',
      seedlot: '/brapi/v2/seedlots',
    }

    for (const type of types) {
      try {
        const response = await fetch(endpointMap[type], {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        })

        if (!response.ok) {
          if (response.status === 401) {
            logger.warn('[OfflineSync] Auth token expired')
            return
          }
          continue
        }

        const data = await response.json()
        const items = data.result?.data || []

        // Merge with local data (server wins for conflicts)
        const collection = this.getCollection(type)
        for (const item of items) {
          const localDoc = collection.get(item.id || item.germplasmDbId || item.trialDbId) as SyncableDocument | undefined

          // Only update if server version is newer or local doesn't exist
          if (!localDoc || (localDoc.syncedAt && !localDoc.localOnly)) {
            const doc: SyncableDocument = {
              id: item.id || item.germplasmDbId || item.trialDbId || item.observationDbId,
              type,
              data: item,
              createdAt: localDoc?.createdAt || Date.now(),
              updatedAt: Date.now(),
              syncedAt: Date.now(),
              localOnly: false,
            }
            collection.set(doc.id, doc)
          }
        }

        this.emit('change:remote', { type, count: items.length })
      } catch (error) {
        logger.error(`[OfflineSync] Failed to pull ${type}`, error instanceof Error ? error : new Error(String(error)))
      }
    }

    logger.debug('[OfflineSync] Pull complete')
  }

  /**
   * Subscribe to sync events
   */
  on(event: SyncEventType, callback: SyncEventCallback): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)

    return () => {
      this.listeners.get(event)?.delete(callback)
    }
  }

  private emit(event: SyncEventType, data: unknown): void {
    this.listeners.get(event)?.forEach((callback) => {
      try {
        callback(data)
      } catch (e) {
        logger.error(`[OfflineSync] Error in ${event} listener`, e instanceof Error ? e : new Error(String(e)))
      }
    })
  }

  /**
   * Get current sync status
   */
  getStatus(): SyncStatus {
    return { ...this.syncStatus }
  }

  /**
   * Force sync now
   */
  async forceSync(): Promise<void> {
    await this.syncToServer()
    await this.pullFromServer()
  }

  /**
   * Clear all local data
   */
  async clearLocalData(): Promise<void> {
    if (this.persistence) {
      await this.persistence.clearData()
    }
    this.ydoc.destroy()
    this.ydoc = new Y.Doc()
    this.pendingDocIds.clear()
    this.setupObservers()
    logger.debug('[OfflineSync] Local data cleared')
  }
}

// Singleton instance
export const offlineSync = new OfflineSyncService()

// React hooks
import { useState, useEffect, useCallback } from 'react'

export function useOfflineSync() {
  const [status, setStatus] = useState<SyncStatus>(offlineSync.getStatus())

  useEffect(() => {
    const updateStatus = () => setStatus(offlineSync.getStatus())

    const unsubStart = offlineSync.on('sync:start', updateStatus)
    const unsubComplete = offlineSync.on('sync:complete', updateStatus)
    const unsubError = offlineSync.on('sync:error', updateStatus)
    const unsubLocal = offlineSync.on('change:local', updateStatus)

    // Also listen for online/offline
    window.addEventListener('online', updateStatus)
    window.addEventListener('offline', updateStatus)

    return () => {
      unsubStart()
      unsubComplete()
      unsubError()
      unsubLocal()
      window.removeEventListener('online', updateStatus)
      window.removeEventListener('offline', updateStatus)
    }
  }, [])

  const forceSync = useCallback(() => offlineSync.forceSync(), [])

  return {
    ...status,
    forceSync,
  }
}

export function useSyncableCollection<T extends Record<string, unknown>>(
  type: SyncableDocument['type']
) {
  const [documents, setDocuments] = useState<SyncableDocument[]>([])

  useEffect(() => {
    // Initial load
    setDocuments(offlineSync.getAllDocuments(type))

    // Listen for changes
    const unsubLocal = offlineSync.on('change:local', () => {
      setDocuments(offlineSync.getAllDocuments(type))
    })

    const unsubRemote = offlineSync.on('change:remote', () => {
      setDocuments(offlineSync.getAllDocuments(type))
    })

    return () => {
      unsubLocal()
      unsubRemote()
    }
  }, [type])

  const upsert = useCallback(
    (id: string, data: T) => {
      offlineSync.upsertDocument({
        id,
        type,
        data,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      })
    },
    [type]
  )

  const remove = useCallback(
    (id: string) => {
      offlineSync.deleteDocument(type, id)
    },
    [type]
  )

  return {
    documents,
    upsert,
    remove,
  }
}

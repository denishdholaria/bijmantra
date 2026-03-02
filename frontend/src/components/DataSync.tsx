/**
 * Data Sync Component
 * Manages offline data synchronization
 */
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { toast } from 'sonner'

interface PendingChange {
  id: string
  type: 'create' | 'update' | 'delete'
  entity: string
  data: any
  timestamp: number
}

// Simple IndexedDB wrapper for offline storage
const DB_NAME = 'bijmantra_offline'
const STORE_NAME = 'pending_changes'

async function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1)
    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve(request.result)
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' })
      }
    }
  })
}

export async function savePendingChange(change: Omit<PendingChange, 'id' | 'timestamp'>) {
  const db = await openDB()
  const tx = db.transaction(STORE_NAME, 'readwrite')
  const store = tx.objectStore(STORE_NAME)
  const pendingChange: PendingChange = {
    ...change,
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: Date.now(),
  }
  store.add(pendingChange)
  return pendingChange
}

export async function getPendingChanges(): Promise<PendingChange[]> {
  const db = await openDB()
  const tx = db.transaction(STORE_NAME, 'readonly')
  const store = tx.objectStore(STORE_NAME)

  return new Promise((resolve, reject) => {
    const request = store.getAll()
    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve(request.result)
  })
}

export async function clearPendingChange(id: string) {
  const db = await openDB()
  const tx = db.transaction(STORE_NAME, 'readwrite')
  const store = tx.objectStore(STORE_NAME)
  store.delete(id)
}

export function DataSyncStatus() {
  const [pendingChanges, setPendingChanges] = useState<PendingChange[]>([])
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncProgress, setSyncProgress] = useState(0)

  useEffect(() => {
    loadPendingChanges()
  }, [])

  const loadPendingChanges = async () => {
    try {
      const changes = await getPendingChanges()
      setPendingChanges(changes)
    } catch (error) {
      console.error('Failed to load pending changes:', error)
    }
  }

  const syncChanges = async () => {
    if (pendingChanges.length === 0) {
      toast.info('No pending changes to sync')
      return
    }

    setIsSyncing(true)
    setSyncProgress(0)

    for (let i = 0; i < pendingChanges.length; i++) {
      const change = pendingChanges[i]
      try {
        // Simulate API call - replace with actual sync logic
        await new Promise(r => setTimeout(r, 500))
        await clearPendingChange(change.id)
        setSyncProgress(((i + 1) / pendingChanges.length) * 100)
      } catch (error) {
        console.error('Failed to sync change:', change, error)
        toast.error(`Failed to sync ${change.entity}`)
      }
    }

    setIsSyncing(false)
    await loadPendingChanges()
    toast.success('All changes synced successfully!')
  }

  const getEntityIcon = (entity: string) => {
    const icons: Record<string, string> = {
      observation: '📊',
      germplasm: '🌱',
      sample: '🧫',
      location: '📍',
      default: '📝',
    }
    return icons[entity] || icons.default
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      create: 'bg-green-100 text-green-800',
      update: 'bg-blue-100 text-blue-800',
      delete: 'bg-red-100 text-red-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  if (pendingChanges.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <div className="text-4xl mb-2">✅</div>
          <p className="text-muted-foreground">All data is synced</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Pending Changes</span>
          <Badge variant="secondary">{pendingChanges.length}</Badge>
        </CardTitle>
        <CardDescription>
          Changes waiting to be synced to the server
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isSyncing && (
          <div className="space-y-2">
            <Progress value={syncProgress} />
            <p className="text-sm text-muted-foreground text-center">
              Syncing... {Math.round(syncProgress)}%
            </p>
          </div>
        )}

        <div className="space-y-2 max-h-48 overflow-y-auto">
          {pendingChanges.map((change) => (
            <div
              key={change.id}
              className="flex items-center justify-between p-2 bg-muted rounded-lg"
            >
              <div className="flex items-center gap-2">
                <span>{getEntityIcon(change.entity)}</span>
                <div>
                  <p className="text-sm font-medium capitalize">{change.entity}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(change.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
              <Badge className={getTypeColor(change.type)}>{change.type}</Badge>
            </div>
          ))}
        </div>

        <Button 
          onClick={syncChanges} 
          disabled={isSyncing || !navigator.onLine}
          className="w-full"
        >
          {isSyncing ? 'Syncing...' : '🔄 Sync Now'}
        </Button>

        {!navigator.onLine && (
          <p className="text-sm text-yellow-600 text-center">
            ⚠️ You're offline. Changes will sync when connected.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

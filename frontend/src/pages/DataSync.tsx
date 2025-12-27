import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Switch } from '@/components/ui/switch'
import { 
  Cloud, CloudOff, RefreshCw, Download, Upload, 
  CheckCircle, AlertCircle, Clock, Database, Wifi,
  WifiOff, HardDrive, Trash2, Settings
} from 'lucide-react'
import { dataSyncAPI } from '@/lib/api-client'

interface SyncItem {
  id: string
  entity_type: string
  entity_id: string
  name: string
  status: string
  size_bytes: number
  created_at: string
  last_modified: string
  error_message?: string
}

interface SyncStats {
  total_items: number
  synced_items: number
  pending_items: number
  conflicts: number
  errors: number
  last_full_sync?: string
  sync_in_progress: boolean
}

interface SyncHistoryEntry {
  id: string
  action: string
  description: string
  items_count: number
  status: string
  started_at: string
  completed_at?: string
  error_message?: string
}

interface OfflineDataCategory {
  type: string
  count: number
  size_bytes: number
  last_updated?: string
}

interface SyncSettings {
  auto_sync: boolean
  sync_on_wifi_only: boolean
  background_sync: boolean
  sync_images: boolean
  sync_interval_minutes: number
  max_offline_days: number
  conflict_resolution: string
}

export function DataSync() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [syncProgress, setSyncProgress] = useState(0)
  const queryClient = useQueryClient()

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Queries
  const { data: statsData } = useQuery({
    queryKey: ['sync-stats'],
    queryFn: () => dataSyncAPI.getStats(),
  })

  const { data: pendingData, isLoading: pendingLoading } = useQuery({
    queryKey: ['sync-pending'],
    queryFn: () => dataSyncAPI.getPending(),
  })

  const { data: historyData } = useQuery({
    queryKey: ['sync-history'],
    queryFn: () => dataSyncAPI.getHistory(),
  })

  const { data: offlineData } = useQuery({
    queryKey: ['offline-data'],
    queryFn: () => dataSyncAPI.getOfflineData(),
  })

  const { data: settingsData } = useQuery({
    queryKey: ['sync-settings'],
    queryFn: () => dataSyncAPI.getSettings(),
  })

  // Mutations
  const syncMutation = useMutation({
    mutationFn: () => dataSyncAPI.sync('full_sync'),
    onMutate: () => {
      setSyncProgress(0)
      const interval = setInterval(() => {
        setSyncProgress(p => {
          if (p >= 100) {
            clearInterval(interval)
            return 100
          }
          return p + 10
        })
      }, 200)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] })
      queryClient.invalidateQueries({ queryKey: ['sync-pending'] })
      queryClient.invalidateQueries({ queryKey: ['sync-history'] })
    },
  })

  const uploadMutation = useMutation({
    mutationFn: () => dataSyncAPI.upload(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] })
      queryClient.invalidateQueries({ queryKey: ['sync-pending'] })
      queryClient.invalidateQueries({ queryKey: ['sync-history'] })
    },
  })

  const deletePendingMutation = useMutation({
    mutationFn: (itemId: string) => dataSyncAPI.deletePending(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-pending'] })
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] })
    },
  })

  const clearOfflineDataMutation = useMutation({
    mutationFn: (category: string) => dataSyncAPI.clearOfflineData(category),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offline-data'] })
    },
  })

  const updateSettingsMutation = useMutation({
    mutationFn: (settings: Partial<SyncSettings>) => dataSyncAPI.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-settings'] })
    },
  })

  const syncStats = statsData || { total_items: 0, synced_items: 0, pending_items: 0, conflicts: 0, errors: 0, sync_in_progress: false }
  const pendingItems = pendingData?.items || []
  const syncHistory = historyData?.history || []
  const offlineCategories = offlineData?.categories || []
  const settings = settingsData || { auto_sync: true, sync_on_wifi_only: true, background_sync: true, sync_images: true, sync_interval_minutes: 15, max_offline_days: 30, conflict_resolution: 'server_wins' }

  const isSyncing = syncMutation.isPending || syncStats.sync_in_progress

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'synced': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />
      case 'conflict': return <AlertCircle className="h-4 w-4 text-orange-500" />
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Sync</h1>
          <p className="text-muted-foreground">Manage offline data and synchronization</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {isOnline ? <Wifi className="h-5 w-5 text-green-500" /> : <WifiOff className="h-5 w-5 text-red-500" />}
            <Badge variant={isOnline ? 'default' : 'destructive'}>{isOnline ? 'Online' : 'Offline'}</Badge>
          </div>
          <Button onClick={() => syncMutation.mutate()} disabled={!isOnline || isSyncing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Syncing...' : 'Sync Now'}
          </Button>
        </div>
      </div>

      {isSyncing && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm"><span>Synchronizing data...</span><span>{syncProgress}%</span></div>
              <Progress value={syncProgress} />
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Items</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{syncStats.total_items.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">In local database</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Synced</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{syncStats.synced_items.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{syncStats.total_items > 0 ? Math.round(syncStats.synced_items / syncStats.total_items * 100) : 0}% complete</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Upload className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{syncStats.pending_items}</div>
            <p className="text-xs text-muted-foreground">Waiting to sync</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conflicts</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{syncStats.conflicts}</div>
            <p className="text-xs text-muted-foreground">Need resolution</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div><CardTitle>Pending Changes</CardTitle><CardDescription>Items waiting to be synchronized</CardDescription></div>
              <Button 
                variant="outline" 
                size="sm" 
                disabled={!isOnline || uploadMutation.isPending}
                onClick={() => uploadMutation.mutate()}
              >
                <Upload className="mr-2 h-4 w-4" />Upload All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {pendingLoading ? (
              <div className="text-center py-4 text-muted-foreground">Loading...</div>
            ) : (
              <div className="space-y-3">
                {pendingItems.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(item.status)}
                      <div>
                        <p className="font-medium text-sm">{item.name}</p>
                        <p className="text-xs text-muted-foreground">{item.entity_type} • {formatBytes(item.size_bytes)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={item.status === 'conflict' ? 'destructive' : 'secondary'}>{item.status}</Badge>
                      {item.status === 'conflict' && <Button variant="outline" size="sm">Resolve</Button>}
                      <Button 
                        variant="ghost" 
                        size="icon"
                        onClick={() => deletePendingMutation.mutate(item.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                {pendingItems.length === 0 && (
                  <p className="text-center py-4 text-muted-foreground">No pending changes</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div><CardTitle>Offline Storage</CardTitle><CardDescription>Data available offline</CardDescription></div>
              <Button variant="outline" size="sm"><Settings className="mr-2 h-4 w-4" />Configure</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {offlineCategories.map((data) => (
                <div key={data.type} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <HardDrive className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium text-sm">{data.type}</p>
                      <p className="text-xs text-muted-foreground">{data.count.toLocaleString()} items</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">{formatBytes(data.size_bytes)}</span>
                    <Button 
                      variant="ghost" 
                      size="icon"
                      onClick={() => clearOfflineDataMutation.mutate(data.type)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              {offlineData && (
                <div className="pt-2 border-t">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Total Storage</span>
                    <span>{formatBytes(offlineData.total_size_bytes)}</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div><CardTitle>Sync Settings</CardTitle><CardDescription>Configure synchronization behavior</CardDescription></div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div><p className="font-medium">Auto-sync when online</p><p className="text-sm text-muted-foreground">Automatically sync changes when connected</p></div>
              <Switch 
                checked={settings.auto_sync} 
                onCheckedChange={(checked) => updateSettingsMutation.mutate({ auto_sync: checked })} 
              />
            </div>
            <div className="flex items-center justify-between">
              <div><p className="font-medium">Sync images over WiFi only</p><p className="text-sm text-muted-foreground">Save mobile data by syncing images on WiFi</p></div>
              <Switch 
                checked={settings.sync_on_wifi_only}
                onCheckedChange={(checked) => updateSettingsMutation.mutate({ sync_on_wifi_only: checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div><p className="font-medium">Background sync</p><p className="text-sm text-muted-foreground">Sync data even when app is in background</p></div>
              <Switch 
                checked={settings.background_sync}
                onCheckedChange={(checked) => updateSettingsMutation.mutate({ background_sync: checked })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Sync History</CardTitle><CardDescription>Recent synchronization activity</CardDescription></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {syncHistory.map((entry) => (
              <div key={entry.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {entry.status === 'success' ? <CheckCircle className="h-4 w-4 text-green-500" /> : <AlertCircle className="h-4 w-4 text-red-500" />}
                  <div>
                    <p className="font-medium text-sm">{entry.description}</p>
                    <p className="text-xs text-muted-foreground">{new Date(entry.started_at).toLocaleString()}</p>
                  </div>
                </div>
                <Badge variant={entry.status === 'success' ? 'default' : 'destructive'}>{entry.items_count} items</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

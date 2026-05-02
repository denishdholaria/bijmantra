import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { 
  RefreshCw, Upload,
  CheckCircle, AlertCircle, Clock, Database, Wifi,
  WifiOff, HardDrive, Trash2, Settings
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'

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
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['sync-stats'],
    queryFn: () => apiClient.dataSyncService.getStats(),
  })

  const { data: pendingData, isLoading: pendingLoading } = useQuery({
    queryKey: ['sync-pending'],
    queryFn: () => apiClient.dataSyncService.getPending(),
  })

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['sync-history'],
    queryFn: () => apiClient.dataSyncService.getHistory(),
  })

  const { data: offlineData, isLoading: offlineLoading } = useQuery({
    queryKey: ['offline-data'],
    queryFn: () => apiClient.dataSyncService.getOfflineData(),
  })

  const { data: settingsData, isLoading: settingsLoading } = useQuery({
    queryKey: ['sync-settings'],
    queryFn: () => apiClient.dataSyncService.getSettings(),
  })

  // Mutations
  const syncMutation = useMutation({
    mutationFn: () => apiClient.dataSyncService.sync('full_sync'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] })
      queryClient.invalidateQueries({ queryKey: ['sync-pending'] })
      queryClient.invalidateQueries({ queryKey: ['sync-history'] })
    },
  })

  const uploadMutation = useMutation({
    mutationFn: () => apiClient.dataSyncService.upload(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] })
      queryClient.invalidateQueries({ queryKey: ['sync-pending'] })
      queryClient.invalidateQueries({ queryKey: ['sync-history'] })
    },
  })

  const deletePendingMutation = useMutation({
    mutationFn: (itemId: string) => apiClient.dataSyncService.deletePending(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-pending'] })
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] })
    },
  })

  const clearOfflineDataMutation = useMutation({
    mutationFn: (category: string) => apiClient.dataSyncService.clearOfflineData(category),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offline-data'] })
    },
  })

  const updateSettingsMutation = useMutation({
    mutationFn: (settings: Partial<SyncSettings>) => apiClient.dataSyncService.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-settings'] })
    },
  })

  const syncStats = statsData
  const pendingItems = pendingData?.items || []
  const syncHistory = historyData?.history || []
  const offlineCategories = offlineData?.categories || []
  const settings = settingsData

  const isSyncing = syncMutation.isPending || syncStats?.sync_in_progress === true

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

  const formatCount = (value?: number | null) => (value == null ? '—' : value.toLocaleString())

  const syncStatusMessage = syncMutation.isPending
    ? 'Submitting sync request...'
    : 'A synchronization request is currently marked in progress.'

  const syncStatusDetail = syncMutation.isPending
    ? 'This page does not estimate progress until the backend reports it.'
    : 'Progress is unavailable until the backend exposes live sync status updates.'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Sync</h1>
          <p className="text-muted-foreground">Review sync records, pending changes, and offline cache summaries</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {isOnline ? <Wifi className="h-5 w-5 text-green-500" /> : <WifiOff className="h-5 w-5 text-red-500" />}
            <Badge variant={isOnline ? 'default' : 'destructive'}>{isOnline ? 'Browser Online' : 'Browser Offline'}</Badge>
          </div>
          <Button onClick={() => syncMutation.mutate()} disabled={!isOnline || isSyncing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Sync In Progress' : 'Start Sync'}
          </Button>
        </div>
      </div>

      {isSyncing && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-3 text-sm">
              <RefreshCw className="mt-0.5 h-4 w-4 animate-spin text-muted-foreground" />
              <div className="space-y-1">
                <p className="font-medium">{syncStatusMessage}</p>
                <p className="text-muted-foreground">{syncStatusDetail}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tracked Items</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statsLoading ? '...' : formatCount(syncStats?.total_items)}</div>
            <p className="text-xs text-muted-foreground">{statsLoading ? 'Loading sync statistics...' : syncStats ? 'Rows tracked in synchronization records' : 'Sync statistics unavailable'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Marked Synced</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statsLoading ? '...' : formatCount(syncStats?.synced_items)}</div>
            <p className="text-xs text-muted-foreground">
              {statsLoading
                ? 'Loading sync statistics...'
                : syncStats?.last_full_sync
                  ? `Last completed full sync ${new Date(syncStats.last_full_sync).toLocaleString()}`
                  : syncStats
                    ? 'No completed full sync reported'
                    : 'Sync statistics unavailable'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Records</CardTitle>
            <Upload className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statsLoading ? '...' : formatCount(syncStats?.pending_items)}</div>
            <p className="text-xs text-muted-foreground">{statsLoading ? 'Loading sync statistics...' : syncStats ? 'Not yet marked synced' : 'Sync statistics unavailable'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conflicts</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statsLoading ? '...' : formatCount(syncStats?.conflicts)}</div>
            <p className="text-xs text-muted-foreground">{statsLoading ? 'Loading sync statistics...' : syncStats ? 'Require review before retry' : 'Sync statistics unavailable'}</p>
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
            ) : !pendingData ? (
              <div className="text-center py-4 text-muted-foreground">Pending sync items unavailable.</div>
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
                        aria-label={`Delete pending item ${item.name}`}
                        onClick={() => deletePendingMutation.mutate(item.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                {pendingItems.length === 0 && (
                  <p className="text-center py-4 text-muted-foreground">No pending changes reported.</p>
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
            {offlineLoading ? (
              <div className="text-center py-4 text-muted-foreground">Loading...</div>
            ) : !offlineData ? (
              <div className="text-center py-4 text-muted-foreground">Offline storage summary unavailable.</div>
            ) : (
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
                        aria-label={`Clear offline ${data.type} data`}
                        onClick={() => clearOfflineDataMutation.mutate(data.type)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                {offlineCategories.length === 0 && (
                  <p className="text-center py-4 text-muted-foreground">No offline storage reported.</p>
                )}
                <div className="pt-2 border-t">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Total Storage</span>
                    <span>{formatBytes(offlineData.total_size_bytes)}</span>
                  </div>
                </div>
              </div>
            )}
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
          {settingsLoading ? (
            <div className="text-center py-4 text-muted-foreground">Loading...</div>
          ) : !settings ? (
            <div className="text-center py-4 text-muted-foreground">Sync settings unavailable.</div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div><p className="font-medium">Auto-sync when online</p><p className="text-sm text-muted-foreground">Automatically sync changes when connected</p></div>
                <Switch 
                  checked={settings.auto_sync}
                  disabled={updateSettingsMutation.isPending}
                  onCheckedChange={(checked) => updateSettingsMutation.mutate({ auto_sync: checked })} 
                />
              </div>
              <div className="flex items-center justify-between">
                <div><p className="font-medium">Sync images over WiFi only</p><p className="text-sm text-muted-foreground">Save mobile data by syncing images on WiFi</p></div>
                <Switch 
                  checked={settings.sync_on_wifi_only}
                  disabled={updateSettingsMutation.isPending}
                  onCheckedChange={(checked) => updateSettingsMutation.mutate({ sync_on_wifi_only: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div><p className="font-medium">Background sync</p><p className="text-sm text-muted-foreground">Sync data even when app is in background</p></div>
                <Switch 
                  checked={settings.background_sync}
                  disabled={updateSettingsMutation.isPending}
                  onCheckedChange={(checked) => updateSettingsMutation.mutate({ background_sync: checked })}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Sync History</CardTitle><CardDescription>Recent synchronization activity</CardDescription></CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="text-center py-4 text-muted-foreground">Loading...</div>
          ) : !historyData ? (
            <div className="text-center py-4 text-muted-foreground">Sync history unavailable.</div>
          ) : syncHistory.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">No synchronization history reported.</div>
          ) : (
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
          )}
        </CardContent>
      </Card>
    </div>
  )
}

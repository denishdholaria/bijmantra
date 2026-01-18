import { useState, useEffect } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  WifiOff,
  Wifi,
  Download,
  Upload,
  Database,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  HardDrive,
  Trash2,
  Settings,
  Loader2
} from 'lucide-react'
import { offlineSyncAPI } from '@/lib/api-client'
import { toast } from 'sonner'

export function OfflineMode() {
  const queryClient = useQueryClient()
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [syncProgress, setSyncProgress] = useState(0)
  const [isSyncing, setIsSyncing] = useState(false)

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

  // Fetch pending changes from API
  const { data: pendingChanges = [], isLoading: loadingPending } = useQuery({
    queryKey: ['offline-sync', 'pending-changes'],
    queryFn: () => offlineSyncAPI.getPendingChanges(),
  })

  // Fetch cached data from API
  const { data: cachedData = [], isLoading: loadingCache } = useQuery({
    queryKey: ['offline-sync', 'cached-data'],
    queryFn: () => offlineSyncAPI.getCachedData(),
  })

  // Fetch sync stats from API
  const { data: stats } = useQuery({
    queryKey: ['offline-sync', 'stats'],
    queryFn: () => offlineSyncAPI.getStats(),
  })

  // Fetch sync settings from API
  const { data: settings } = useQuery({
    queryKey: ['offline-sync', 'settings'],
    queryFn: () => offlineSyncAPI.getSettings(),
  })

  // Sync now mutation
  const syncNowMutation = useMutation({
    mutationFn: () => offlineSyncAPI.syncNow(),
    onMutate: () => {
      setIsSyncing(true)
      setSyncProgress(0)
    },
    onSuccess: (data) => {
      setSyncProgress(100)
      setTimeout(() => setIsSyncing(false), 500)
      queryClient.invalidateQueries({ queryKey: ['offline-sync'] })
      toast.success(`Synced ${data.synced} items${data.errors > 0 ? `, ${data.errors} errors` : ''}`)
    },
    onError: () => {
      setIsSyncing(false)
      toast.error('Sync failed')
    },
  })

  // Delete pending change mutation
  const deletePendingMutation = useMutation({
    mutationFn: (itemId: string) => offlineSyncAPI.deletePendingChange(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offline-sync', 'pending-changes'] })
      toast.success('Pending change deleted')
    },
  })

  // Update cache mutation
  const updateCacheMutation = useMutation({
    mutationFn: (category: string) => offlineSyncAPI.updateCache(category),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offline-sync', 'cached-data'] })
      toast.success('Cache updated')
    },
  })

  // Clear cache mutation
  const clearCacheMutation = useMutation({
    mutationFn: (category?: string) => offlineSyncAPI.clearCache(category),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offline-sync'] })
      toast.success('Cache cleared')
    },
  })

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: (data: any) => offlineSyncAPI.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offline-sync', 'settings'] })
      toast.success('Settings updated')
    },
  })

  const totalCacheSize = stats?.cached_data_mb || 0

  const handleSync = () => {
    if (!isOnline) {
      toast.error('Cannot sync while offline')
      return
    }
    syncNowMutation.mutate()
  }

  // Simulate progress for visual feedback
  useEffect(() => {
    if (isSyncing && syncProgress < 90) {
      const timer = setTimeout(() => {
        setSyncProgress(prev => Math.min(prev + 10, 90))
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [isSyncing, syncProgress])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            {isOnline ? <Wifi className="h-8 w-8 text-green-500" /> : <WifiOff className="h-8 w-8 text-red-500" />}
            Offline Mode
          </h1>
          <p className="text-muted-foreground mt-1">Manage offline data and synchronization</p>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant={isOnline ? 'default' : 'destructive'} className="text-sm py-1 px-3">
            {isOnline ? <><Wifi className="h-4 w-4 mr-1" />Online</> : <><WifiOff className="h-4 w-4 mr-1" />Offline</>}
          </Badge>
          <Button onClick={handleSync} disabled={!isOnline || isSyncing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Syncing...' : 'Sync Now'}
          </Button>
        </div>
      </div>

      {/* Sync Progress */}
      {isSyncing && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <RefreshCw className="h-5 w-5 animate-spin text-primary" />
              <div className="flex-1">
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Synchronizing data...</span>
                  <span className="text-sm text-muted-foreground">{syncProgress}%</span>
                </div>
                <Progress value={syncProgress} />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><HardDrive className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{totalCacheSize.toFixed(1)} MB</div>
                <div className="text-sm text-muted-foreground">Cached Data</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Upload className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats?.pending_uploads || pendingChanges.filter(c => c.status === 'pending').length}</div>
                <div className="text-sm text-muted-foreground">Pending Uploads</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><CheckCircle2 className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats?.last_sync || 'Never'}</div>
                <div className="text-sm text-muted-foreground">Last Sync</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg"><AlertCircle className="h-5 w-5 text-red-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats?.sync_errors || pendingChanges.filter(c => c.status === 'error').length}</div>
                <div className="text-sm text-muted-foreground">Sync Errors</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pending">Pending Changes</TabsTrigger>
          <TabsTrigger value="cache">Cached Data</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Upload className="h-5 w-5" />Pending Changes</CardTitle>
              <CardDescription>Changes waiting to be synchronized</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingPending ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : pendingChanges.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-500" />
                  <p>All changes are synchronized!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingChanges.map((item) => (
                    <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        {item.status === 'pending' ? <Clock className="h-5 w-5 text-yellow-500" /> : <AlertCircle className="h-5 w-5 text-red-500" />}
                        <div>
                          <div className="font-medium">{item.name}</div>
                          <div className="text-sm text-muted-foreground">{item.type} • {item.size}</div>
                          {item.error_message && (
                            <div className="text-xs text-red-500 mt-1">{item.error_message}</div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={item.status === 'pending' ? 'secondary' : 'destructive'}>{item.status}</Badge>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => deletePendingMutation.mutate(item.id)}
                          disabled={deletePendingMutation.isPending}
                          aria-label="Delete pending change"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cache" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Database className="h-5 w-5" />Cached Data</CardTitle>
              <CardDescription>Data available for offline use</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingCache ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <>
                  <div className="space-y-4">
                    {cachedData.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center gap-4">
                          <Switch checked={item.enabled} />
                          <div>
                            <div className="font-medium">{item.category}</div>
                            <div className="text-sm text-muted-foreground">{item.items.toLocaleString()} items • {item.size}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right text-sm text-muted-foreground">
                            <div>Updated: {item.last_updated}</div>
                          </div>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => updateCacheMutation.mutate(item.category)}
                            disabled={updateCacheMutation.isPending}
                          >
                            <Download className="h-4 w-4 mr-1" />Update
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between mt-4 pt-4 border-t">
                    <Button variant="outline"><Download className="h-4 w-4 mr-2" />Download All</Button>
                    <Button 
                      variant="destructive"
                      onClick={() => clearCacheMutation.mutate(undefined)}
                      disabled={clearCacheMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />Clear Cache
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Settings className="h-5 w-5" />Offline Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Auto-sync when online</div>
                  <div className="text-sm text-muted-foreground">Automatically sync changes when connection is restored</div>
                </div>
                <Switch 
                  checked={settings?.auto_sync ?? true}
                  onCheckedChange={(checked) => updateSettingsMutation.mutate({ auto_sync: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Background sync</div>
                  <div className="text-sm text-muted-foreground">Sync data in the background while using the app</div>
                </div>
                <Switch 
                  checked={settings?.background_sync ?? true}
                  onCheckedChange={(checked) => updateSettingsMutation.mutate({ background_sync: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">WiFi only</div>
                  <div className="text-sm text-muted-foreground">Only sync when connected to WiFi</div>
                </div>
                <Switch 
                  checked={settings?.wifi_only ?? false}
                  onCheckedChange={(checked) => updateSettingsMutation.mutate({ wifi_only: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Cache images</div>
                  <div className="text-sm text-muted-foreground">Download images for offline viewing (uses more storage)</div>
                </div>
                <Switch 
                  checked={settings?.cache_images ?? false}
                  onCheckedChange={(checked) => updateSettingsMutation.mutate({ cache_images: checked })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

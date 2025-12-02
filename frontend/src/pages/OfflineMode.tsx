import { useState, useEffect } from 'react'
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
  Cloud,
  CloudOff
} from 'lucide-react'

interface SyncItem {
  id: string
  type: string
  name: string
  status: 'synced' | 'pending' | 'error'
  lastSync: string
  size: string
}

interface CacheItem {
  category: string
  items: number
  size: string
  lastUpdated: string
  enabled: boolean
}

export function OfflineMode() {
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

  const pendingChanges: SyncItem[] = [
    { id: '1', type: 'Observation', name: 'Field observations - Block A', status: 'pending', lastSync: 'Never', size: '2.4 KB' },
    { id: '2', type: 'Germplasm', name: 'New accession BM-2025-001', status: 'pending', lastSync: 'Never', size: '1.1 KB' },
    { id: '3', type: 'Cross', name: 'Cross record CR-2025-045', status: 'error', lastSync: 'Failed', size: '0.8 KB' }
  ]

  const cachedData: CacheItem[] = [
    { category: 'Germplasm', items: 12847, size: '45.2 MB', lastUpdated: '2 hours ago', enabled: true },
    { category: 'Trials', items: 234, size: '12.8 MB', lastUpdated: '2 hours ago', enabled: true },
    { category: 'Observations', items: 284000, size: '156.4 MB', lastUpdated: '1 day ago', enabled: true },
    { category: 'Traits', items: 456, size: '2.1 MB', lastUpdated: '2 hours ago', enabled: true },
    { category: 'Locations', items: 89, size: '0.8 MB', lastUpdated: '1 week ago', enabled: true },
    { category: 'Images', items: 1234, size: '892.5 MB', lastUpdated: '3 days ago', enabled: false }
  ]

  const totalCacheSize = cachedData.reduce((sum, item) => {
    const size = parseFloat(item.size)
    return sum + (item.size.includes('GB') ? size * 1024 : size)
  }, 0)

  const handleSync = () => {
    setIsSyncing(true)
    setSyncProgress(0)
    const interval = setInterval(() => {
      setSyncProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsSyncing(false)
          return 100
        }
        return prev + 10
      })
    }, 500)
  }

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
                <div className="text-2xl font-bold">{pendingChanges.filter(c => c.status === 'pending').length}</div>
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
                <div className="text-2xl font-bold">2 hrs ago</div>
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
                <div className="text-2xl font-bold">{pendingChanges.filter(c => c.status === 'error').length}</div>
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
              {pendingChanges.length === 0 ? (
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
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={item.status === 'pending' ? 'secondary' : 'destructive'}>{item.status}</Badge>
                        <Button variant="ghost" size="icon"><Trash2 className="h-4 w-4" /></Button>
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
                        <div>Updated: {item.lastUpdated}</div>
                      </div>
                      <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-1" />Update</Button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex justify-between mt-4 pt-4 border-t">
                <Button variant="outline"><Download className="h-4 w-4 mr-2" />Download All</Button>
                <Button variant="destructive"><Trash2 className="h-4 w-4 mr-2" />Clear Cache</Button>
              </div>
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
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Background sync</div>
                  <div className="text-sm text-muted-foreground">Sync data in the background while using the app</div>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">WiFi only</div>
                  <div className="text-sm text-muted-foreground">Only sync when connected to WiFi</div>
                </div>
                <Switch />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Cache images</div>
                  <div className="text-sm text-muted-foreground">Download images for offline viewing (uses more storage)</div>
                </div>
                <Switch />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

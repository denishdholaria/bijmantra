import { useState, useEffect } from 'react'
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

interface SyncItem {
  id: string
  type: string
  name: string
  status: 'synced' | 'pending' | 'conflict' | 'error'
  lastSync?: string
  size: string
}

interface SyncStats {
  totalItems: number
  syncedItems: number
  pendingItems: number
  conflicts: number
  lastFullSync: string
}

export function DataSync() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [autoSync, setAutoSync] = useState(true)
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncProgress, setSyncProgress] = useState(0)

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

  const syncStats: SyncStats = {
    totalItems: 1247,
    syncedItems: 1235,
    pendingItems: 10,
    conflicts: 2,
    lastFullSync: '10 minutes ago'
  }

  const pendingItems: SyncItem[] = [
    { id: '1', type: 'observation', name: 'Plot observations - Block A', status: 'pending', size: '24 KB' },
    { id: '2', type: 'germplasm', name: 'New accession GRM-2025-001', status: 'pending', size: '8 KB' },
    { id: '3', type: 'image', name: 'Field photos (12 images)', status: 'pending', size: '45 MB' },
    { id: '4', type: 'cross', name: 'Cross record CRS-2025-042', status: 'conflict', size: '4 KB' },
    { id: '5', type: 'trial', name: 'Trial metadata update', status: 'conflict', size: '12 KB' },
  ]

  const syncHistory = [
    { id: '1', action: 'Full sync completed', timestamp: '10 minutes ago', items: 1247, status: 'success' },
    { id: '2', action: 'Uploaded 15 observations', timestamp: '25 minutes ago', items: 15, status: 'success' },
    { id: '3', action: 'Downloaded germplasm updates', timestamp: '1 hour ago', items: 42, status: 'success' },
    { id: '4', action: 'Sync failed - network error', timestamp: '2 hours ago', items: 0, status: 'error' },
    { id: '5', action: 'Uploaded field images', timestamp: '3 hours ago', items: 28, status: 'success' },
  ]

  const offlineData = [
    { type: 'Trials', count: 24, size: '2.4 MB' },
    { type: 'Studies', count: 156, size: '8.2 MB' },
    { type: 'Germplasm', count: 3420, size: '45.6 MB' },
    { type: 'Observations', count: 28450, size: '124.8 MB' },
    { type: 'Images', count: 1240, size: '2.1 GB' },
  ]

  const handleSync = async () => {
    setIsSyncing(true)
    setSyncProgress(0)
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(r => setTimeout(r, 200))
      setSyncProgress(i)
    }
    setIsSyncing(false)
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
          <Button onClick={handleSync} disabled={!isOnline || isSyncing}>
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
            <div className="text-2xl font-bold">{syncStats.totalItems.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">In local database</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Synced</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{syncStats.syncedItems.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{Math.round(syncStats.syncedItems / syncStats.totalItems * 100)}% complete</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Upload className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{syncStats.pendingItems}</div>
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
              <Button variant="outline" size="sm" disabled={!isOnline}><Upload className="mr-2 h-4 w-4" />Upload All</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pendingItems.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(item.status)}
                    <div>
                      <p className="font-medium text-sm">{item.name}</p>
                      <p className="text-xs text-muted-foreground">{item.type} • {item.size}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={item.status === 'conflict' ? 'destructive' : 'secondary'}>{item.status}</Badge>
                    {item.status === 'conflict' && <Button variant="outline" size="sm">Resolve</Button>}
                  </div>
                </div>
              ))}
            </div>
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
              {offlineData.map((data) => (
                <div key={data.type} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <HardDrive className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium text-sm">{data.type}</p>
                      <p className="text-xs text-muted-foreground">{data.count.toLocaleString()} items</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">{data.size}</span>
                    <Button variant="ghost" size="icon"><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </div>
              ))}
              <div className="pt-2 border-t">
                <div className="flex justify-between text-sm"><span className="font-medium">Total Storage</span><span>2.3 GB</span></div>
              </div>
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
              <Switch checked={autoSync} onCheckedChange={setAutoSync} />
            </div>
            <div className="flex items-center justify-between">
              <div><p className="font-medium">Sync images over WiFi only</p><p className="text-sm text-muted-foreground">Save mobile data by syncing images on WiFi</p></div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div><p className="font-medium">Background sync</p><p className="text-sm text-muted-foreground">Sync data even when app is in background</p></div>
              <Switch defaultChecked />
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
                    <p className="font-medium text-sm">{entry.action}</p>
                    <p className="text-xs text-muted-foreground">{entry.timestamp}</p>
                  </div>
                </div>
                <Badge variant={entry.status === 'success' ? 'default' : 'destructive'}>{entry.items} items</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

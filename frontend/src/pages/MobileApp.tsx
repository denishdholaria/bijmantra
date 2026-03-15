import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { 
  Smartphone, Download, Wifi, WifiOff, HardDrive,
  Bell, Camera, MapPin, RefreshCw, CheckCircle
} from 'lucide-react'

export function MobileApp() {
  const [offlineMode, setOfflineMode] = useState(true)
  const [notifications, setNotifications] = useState(true)
  const [locationAccess, setLocationAccess] = useState(true)
  const [cameraAccess, setCameraAccess] = useState(true)

  const syncStatus = { lastSync: '5 minutes ago', pendingChanges: 3, cachedData: '45 MB' }

  const features = [
    { name: 'Offline Data Collection', description: 'Collect observations without internet', enabled: true, icon: WifiOff },
    { name: 'GPS Tagging', description: 'Auto-tag observations with location', enabled: locationAccess, icon: MapPin },
    { name: 'Camera Integration', description: 'Capture plant images directly', enabled: cameraAccess, icon: Camera },
    { name: 'Push Notifications', description: 'Get alerts for important events', enabled: notifications, icon: Bell },
    { name: 'Background Sync', description: 'Sync data when online', enabled: true, icon: RefreshCw },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mobile App</h1>
          <p className="text-muted-foreground">Configure mobile PWA settings</p>
        </div>
        <Button><Download className="mr-2 h-4 w-4" />Install App</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Smartphone className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">PWA</p><p className="text-xs text-muted-foreground">Installed</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3">{offlineMode ? <WifiOff className="h-8 w-8 text-green-500" /> : <Wifi className="h-8 w-8 text-blue-500" />}<div><p className="text-2xl font-bold">{offlineMode ? 'Offline' : 'Online'}</p><p className="text-xs text-muted-foreground">Mode</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><HardDrive className="h-8 w-8 text-purple-500" /><div><p className="text-2xl font-bold">{syncStatus.cachedData}</p><p className="text-xs text-muted-foreground">Cached</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><RefreshCw className="h-8 w-8 text-orange-500" /><div><p className="text-2xl font-bold">{syncStatus.pendingChanges}</p><p className="text-xs text-muted-foreground">Pending Sync</p></div></div></CardContent></Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>App Settings</CardTitle><CardDescription>Configure mobile app behavior</CardDescription></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between"><div><p className="font-medium">Offline Mode</p><p className="text-sm text-muted-foreground">Work without internet connection</p></div><Switch checked={offlineMode} onCheckedChange={setOfflineMode} /></div>
            <div className="flex items-center justify-between"><div><p className="font-medium">Push Notifications</p><p className="text-sm text-muted-foreground">Receive alerts and reminders</p></div><Switch checked={notifications} onCheckedChange={setNotifications} /></div>
            <div className="flex items-center justify-between"><div><p className="font-medium">Location Access</p><p className="text-sm text-muted-foreground">GPS for field observations</p></div><Switch checked={locationAccess} onCheckedChange={setLocationAccess} /></div>
            <div className="flex items-center justify-between"><div><p className="font-medium">Camera Access</p><p className="text-sm text-muted-foreground">Capture plant images</p></div><Switch checked={cameraAccess} onCheckedChange={setCameraAccess} /></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Features</CardTitle><CardDescription>Mobile-optimized capabilities</CardDescription></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {features.map((feature) => (
                <div key={feature.name} className="flex items-center gap-3 p-3 border rounded-lg">
                  <feature.icon className={`h-5 w-5 ${feature.enabled ? 'text-green-500' : 'text-gray-400'}`} />
                  <div className="flex-1">
                    <p className="font-medium text-sm">{feature.name}</p>
                    <p className="text-xs text-muted-foreground">{feature.description}</p>
                  </div>
                  {feature.enabled ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Badge variant="secondary">Disabled</Badge>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Sync Status</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-accent rounded-lg">
            <div><p className="font-medium">Last synchronized</p><p className="text-sm text-muted-foreground">{syncStatus.lastSync}</p></div>
            <div className="text-center"><p className="text-2xl font-bold">{syncStatus.pendingChanges}</p><p className="text-xs text-muted-foreground">Pending changes</p></div>
            <Button><RefreshCw className="mr-2 h-4 w-4" />Sync Now</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

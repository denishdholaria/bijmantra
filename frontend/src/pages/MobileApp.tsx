import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import {
  Bell,
  Camera,
  CheckCircle,
  Download,
  HardDrive,
  MapPin,
  RefreshCw,
  Smartphone,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

type CapabilityState = 'granted' | 'prompt' | 'denied' | 'unsupported'
type CapabilityBadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline'
type OfflineSyncStats = Awaited<ReturnType<typeof apiClient.offlineSyncService.getStats>>
type OfflineSyncSettings = Awaited<ReturnType<typeof apiClient.offlineSyncService.getSettings>>
type OfflineSyncCachedDataItem = Awaited<ReturnType<typeof apiClient.offlineSyncService.getCachedData>>[number]
type OfflineSyncSyncNowResult = Awaited<ReturnType<typeof apiClient.offlineSyncService.syncNow>>
type OfflineSyncSettingsUpdate = Parameters<typeof apiClient.offlineSyncService.updateSettings>[0]

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const isStandalone = () => {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as Navigator & { standalone?: boolean }).standalone === true
}

const isIOS = () => {
  if (typeof navigator === 'undefined') return false
  return /iPad|iPhone|iPod/.test(navigator.userAgent)
}

const getCapabilityBadge = (
  state: CapabilityState
): { label: string; variant: CapabilityBadgeVariant } => {
  switch (state) {
    case 'granted':
      return { label: 'Granted', variant: 'default' }
    case 'prompt':
      return { label: 'Prompt', variant: 'secondary' }
    case 'denied':
      return { label: 'Denied', variant: 'destructive' }
    default:
      return { label: 'Unsupported', variant: 'outline' }
  }
}

export function MobileApp() {
  const queryClient = useQueryClient()
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [isInstalled, setIsInstalled] = useState(isStandalone())
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [notificationPermission, setNotificationPermission] = useState<CapabilityState>('unsupported')
  const [locationPermission, setLocationPermission] = useState<CapabilityState>('unsupported')
  const [cameraPermission, setCameraPermission] = useState<CapabilityState>('unsupported')

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    const handleBeforeInstallPrompt = (event: Event) => {
      event.preventDefault()
      setInstallPrompt(event as BeforeInstallPromptEvent)
    }
    const handleInstalled = () => {
      setIsInstalled(true)
      setInstallPrompt(null)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleInstalled)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleInstalled)
    }
  }, [])

  useEffect(() => {
    const readPermissionState = async () => {
      if (typeof window === 'undefined') return

      if ('Notification' in window) {
        setNotificationPermission(
          Notification.permission === 'default' ? 'prompt' : Notification.permission
        )
      }

      if (navigator.permissions?.query) {
        try {
          const locationStatus = await navigator.permissions.query({ name: 'geolocation' as PermissionName })
          setLocationPermission(locationStatus.state as CapabilityState)
        } catch {
          setLocationPermission('unsupported')
        }

        try {
          const cameraStatus = await navigator.permissions.query({ name: 'camera' as PermissionName })
          setCameraPermission(cameraStatus.state as CapabilityState)
        } catch {
          setCameraPermission(typeof navigator !== 'undefined' && 'mediaDevices' in navigator ? 'prompt' : 'unsupported')
        }
      }
    }

    void readPermissionState()
  }, [])

  const { data: stats, isLoading: statsLoading } = useQuery<OfflineSyncStats>({
    queryKey: ['offline-sync', 'stats'],
    queryFn: () => apiClient.offlineSyncService.getStats(),
  })

  const { data: settings, isLoading: settingsLoading } = useQuery<OfflineSyncSettings>({
    queryKey: ['offline-sync', 'settings'],
    queryFn: () => apiClient.offlineSyncService.getSettings(),
  })

  const { data: cachedData = [], isLoading: cachedDataLoading } = useQuery<OfflineSyncCachedDataItem[]>({
    queryKey: ['offline-sync', 'cached-data'],
    queryFn: () => apiClient.offlineSyncService.getCachedData(),
  })

  const syncNowMutation = useMutation({
    mutationFn: () => apiClient.offlineSyncService.syncNow(),
    onSuccess: (data: OfflineSyncSyncNowResult) => {
      queryClient.invalidateQueries({ queryKey: ['offline-sync'] })
      toast.success(data.message)
    },
    onError: () => {
      toast.error('Failed to start synchronization')
    },
  })

  const updateSettingsMutation = useMutation({
    mutationFn: (nextSettings: OfflineSyncSettingsUpdate) =>
      apiClient.offlineSyncService.updateSettings(nextSettings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offline-sync', 'settings'] })
      toast.success('Mobile sync settings updated')
    },
    onError: () => {
      toast.error('Failed to update mobile sync settings')
    },
  })

  const handleInstall = async () => {
    if (isInstalled) return

    if (installPrompt) {
      await installPrompt.prompt()
      const { outcome } = await installPrompt.userChoice
      if (outcome === 'accepted') {
        setIsInstalled(true)
      }
      setInstallPrompt(null)
      return
    }

    if (isIOS()) {
      toast.info('Use Safari Share > Add to Home Screen to install BijMantra.')
      return
    }

    toast.info('Install is only available when the browser exposes a PWA install prompt.')
  }

  const capabilityRows = [
    {
      name: 'Notifications',
      description: 'Browser permission for in-app and push alerts',
      icon: Bell,
      state: notificationPermission,
    },
    {
      name: 'Location',
      description: 'Browser permission for field geolocation tagging',
      icon: MapPin,
      state: locationPermission,
    },
    {
      name: 'Camera',
      description: 'Browser permission for image capture workflows',
      icon: Camera,
      state: cameraPermission,
    },
  ]

  const installStatusLabel = isInstalled ? 'Installed' : installPrompt || isIOS() ? 'Available' : 'Browser'
  const installStatusDetail = isInstalled
    ? 'This browser is already running the installed PWA.'
    : installPrompt
      ? 'Install prompt available in this browser session.'
      : isIOS()
        ? 'Install is available through Safari Add to Home Screen.'
        : 'Install prompt not currently available.'

  const cachedDataLabel = statsLoading ? '...' : `${(stats?.cached_data_mb ?? 0).toFixed(1)} MB`
  const pendingUploadsLabel = statsLoading ? '...' : `${stats?.pending_uploads ?? 0}`
  const lastSyncLabel = stats?.last_sync || 'Not reported'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mobile App</h1>
          <p className="text-muted-foreground">Review PWA install state, offline sync settings, and browser capabilities</p>
        </div>
        <Button onClick={() => void handleInstall()} disabled={isInstalled && !installPrompt}>
          <Download className="mr-2 h-4 w-4" />
          {isInstalled ? 'Installed' : 'Install App'}
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Smartphone className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{installStatusLabel}</p>
                <p className="text-xs text-muted-foreground">PWA status</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              {isOnline ? <Wifi className="h-8 w-8 text-green-500" /> : <WifiOff className="h-8 w-8 text-red-500" />}
              <div>
                <p className="text-2xl font-bold">{isOnline ? 'Online' : 'Offline'}</p>
                <p className="text-xs text-muted-foreground">Browser network state</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <HardDrive className="h-8 w-8 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{cachedDataLabel}</p>
                <p className="text-xs text-muted-foreground">Cached by offline sync</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <RefreshCw className="h-8 w-8 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">{pendingUploadsLabel}</p>
                <p className="text-xs text-muted-foreground">Pending uploads</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Offline Sync Settings</CardTitle>
            <CardDescription>These controls are backed by the existing offline-sync service.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border bg-accent/40 p-3 text-sm text-muted-foreground">
              {installStatusDetail}
            </div>
            {settingsLoading ? (
              <div className="text-sm text-muted-foreground">Loading mobile sync settings...</div>
            ) : settings ? (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Auto Sync</p>
                    <p className="text-sm text-muted-foreground">Automatically upload queued changes when connectivity is available.</p>
                  </div>
                  <Switch
                    checked={settings.auto_sync}
                    disabled={updateSettingsMutation.isPending}
                    onCheckedChange={(checked: boolean) => updateSettingsMutation.mutate({ auto_sync: checked })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Background Sync</p>
                    <p className="text-sm text-muted-foreground">Allow offline-sync jobs to continue in the background.</p>
                  </div>
                  <Switch
                    checked={settings.background_sync}
                    disabled={updateSettingsMutation.isPending}
                    onCheckedChange={(checked: boolean) => updateSettingsMutation.mutate({ background_sync: checked })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Wi-Fi Only</p>
                    <p className="text-sm text-muted-foreground">Restrict automatic sync to Wi-Fi connections.</p>
                  </div>
                  <Switch
                    checked={settings.wifi_only}
                    disabled={updateSettingsMutation.isPending}
                    onCheckedChange={(checked: boolean) => updateSettingsMutation.mutate({ wifi_only: checked })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Cache Images</p>
                    <p className="text-sm text-muted-foreground">Keep image data available for low-connectivity field work.</p>
                  </div>
                  <Switch
                    checked={settings.cache_images}
                    disabled={updateSettingsMutation.isPending}
                    onCheckedChange={(checked: boolean) => updateSettingsMutation.mutate({ cache_images: checked })}
                  />
                </div>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">Mobile sync settings are unavailable.</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Browser Capabilities</CardTitle>
            <CardDescription>Permission state is derived from the current browser, not stored in this page.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {capabilityRows.map((capability) => {
                const badge = getCapabilityBadge(capability.state)
                return (
                  <div key={capability.name} className="flex items-center gap-3 rounded-lg border p-3">
                    <capability.icon className="h-5 w-5 text-muted-foreground" />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{capability.name}</p>
                      <p className="text-xs text-muted-foreground">{capability.description}</p>
                    </div>
                    {capability.state === 'granted' ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <Badge variant={badge.variant}>{badge.label}</Badge>
                    )}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sync Status</CardTitle>
          <CardDescription>Stats come from the offline-sync service and cached categories it reports.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-4 rounded-lg bg-accent p-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="font-medium">Last synchronized</p>
              <p className="text-sm text-muted-foreground">{lastSyncLabel}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">{pendingUploadsLabel}</p>
              <p className="text-xs text-muted-foreground">Pending uploads</p>
            </div>
            <Button onClick={() => syncNowMutation.mutate()} disabled={!isOnline || syncNowMutation.isPending}>
              <RefreshCw className={`mr-2 h-4 w-4 ${syncNowMutation.isPending ? 'animate-spin' : ''}`} />
              {syncNowMutation.isPending ? 'Syncing...' : 'Sync Now'}
            </Button>
          </div>

          {cachedDataLoading ? (
            <div className="text-sm text-muted-foreground">Loading cached categories...</div>
          ) : cachedData.length > 0 ? (
            <div className="grid gap-3 md:grid-cols-2">
              {cachedData.map((item: OfflineSyncCachedDataItem) => (
                <div key={item.category} className="rounded-lg border p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-sm">{item.category}</p>
                      <p className="text-xs text-muted-foreground">{item.items.toLocaleString()} items cached</p>
                    </div>
                    <Badge variant={item.enabled ? 'secondary' : 'outline'}>{item.size}</Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">Last updated: {item.last_updated}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No cached categories are currently reported.</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

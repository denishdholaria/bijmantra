/**
 * System Settings Page
 * Admin configuration for the system
 */
import { useState, useEffect } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'
import { SyncStatusPanel } from '@/components/sync'
import { systemSettingsAPI } from '@/lib/api-client'
import { Loader2 } from 'lucide-react'

export function SystemSettings() {
  const queryClient = useQueryClient()
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Fetch all settings
  const { data: allSettings, isLoading } = useQuery({
    queryKey: ['system-settings', 'all'],
    queryFn: () => systemSettingsAPI.getAllSettings(),
  })

  // Local state for form
  const [settings, setSettings] = useState({
    siteName: '',
    siteDescription: '',
    defaultLanguage: 'en',
    timezone: 'UTC',
    dateFormat: 'YYYY-MM-DD',
    enableRegistration: false,
    requireEmailVerification: true,
    sessionTimeout: 60,
    maxUploadSize: 50,
    enableOfflineMode: true,
    enableNotifications: true,
    enableAuditLog: true,
    brapiVersion: '2.1',
    apiRateLimit: 1000,
  })

  // Update local state when API data loads
  useEffect(() => {
    if (allSettings?.general && allSettings?.security && allSettings?.api && allSettings?.features) {
      setSettings({
        siteName: allSettings.general.site_name ?? '',
        siteDescription: allSettings.general.site_description ?? '',
        defaultLanguage: allSettings.general.default_language ?? 'en',
        timezone: allSettings.general.timezone ?? 'UTC',
        dateFormat: allSettings.general.date_format ?? 'YYYY-MM-DD',
        enableRegistration: allSettings.security.enable_registration ?? false,
        requireEmailVerification: allSettings.security.require_email_verification ?? true,
        sessionTimeout: allSettings.security.session_timeout ?? 60,
        maxUploadSize: allSettings.api.max_upload_size ?? 50,
        enableOfflineMode: allSettings.features.enable_offline_mode ?? true,
        enableNotifications: allSettings.features.enable_notifications ?? true,
        enableAuditLog: allSettings.features.enable_audit_log ?? true,
        brapiVersion: allSettings.api.brapi_version ?? '2.1',
        apiRateLimit: allSettings.api.api_rate_limit ?? 1000,
      })
    }
  }, [allSettings])

  // Mutations for updating settings
  const updateGeneralMutation = useMutation({
    mutationFn: (data: any) => systemSettingsAPI.updateGeneralSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] })
      toast.success('General settings updated')
    },
  })

  const updateSecurityMutation = useMutation({
    mutationFn: (data: any) => systemSettingsAPI.updateSecuritySettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] })
      toast.success('Security settings updated')
    },
  })

  const updateAPIMutation = useMutation({
    mutationFn: (data: any) => systemSettingsAPI.updateAPISettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] })
      toast.success('API settings updated')
    },
  })

  const updateFeaturesMutation = useMutation({
    mutationFn: (data: any) => systemSettingsAPI.updateFeatureToggles(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] })
      toast.success('Feature toggles updated')
    },
  })

  const handleSave = () => {
    // Save all settings
    updateGeneralMutation.mutate({
      site_name: settings.siteName,
      site_description: settings.siteDescription,
      default_language: settings.defaultLanguage,
      timezone: settings.timezone,
      date_format: settings.dateFormat,
    })
    updateSecurityMutation.mutate({
      enable_registration: settings.enableRegistration,
      require_email_verification: settings.requireEmailVerification,
      session_timeout: settings.sessionTimeout,
    })
    updateAPIMutation.mutate({
      brapi_version: settings.brapiVersion,
      api_rate_limit: settings.apiRateLimit,
      max_upload_size: settings.maxUploadSize,
    })
    updateFeaturesMutation.mutate({
      enable_offline_mode: settings.enableOfflineMode,
      enable_notifications: settings.enableNotifications,
      enable_audit_log: settings.enableAuditLog,
    })
  }

  const handleChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">System Settings</h1>
          <p className="text-muted-foreground mt-1">Configure system-wide settings</p>
        </div>
        <Button onClick={handleSave}>💾 Save Changes</Button>
      </div>

      <Tabs defaultValue="general">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
          <TabsTrigger value="sync">Sync</TabsTrigger>
          <TabsTrigger value="status">Status</TabsTrigger>
          <TabsTrigger value="dev">Dev</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Site Information</CardTitle>
              <CardDescription>Basic site configuration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Site Name</Label>
                  <Input 
                    value={settings.siteName} 
                    onChange={(e) => handleChange('siteName', e.target.value)} 
                  />
                </div>
                <div className="space-y-2">
                  <Label>Default Language</Label>
                  <Select value={settings.defaultLanguage} onValueChange={(v) => handleChange('defaultLanguage', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="pt">Portuguese</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Site Description</Label>
                <Textarea 
                  value={settings.siteDescription}
                  onChange={(e) => handleChange('siteDescription', e.target.value)}
                  rows={2}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Timezone</Label>
                  <Select value={settings.timezone} onValueChange={(v) => handleChange('timezone', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="America/New_York">Eastern Time</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                      <SelectItem value="Europe/London">London</SelectItem>
                      <SelectItem value="Asia/Manila">Manila</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Date Format</Label>
                  <Select value={settings.dateFormat} onValueChange={(v) => handleChange('dateFormat', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                      <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                      <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Authentication</CardTitle>
              <CardDescription>User authentication settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Allow Registration</Label>
                  <p className="text-sm text-muted-foreground">Allow new users to register</p>
                </div>
                <Switch 
                  checked={settings.enableRegistration}
                  onCheckedChange={(v) => handleChange('enableRegistration', v)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Require Email Verification</Label>
                  <p className="text-sm text-muted-foreground">Users must verify email before access</p>
                </div>
                <Switch 
                  checked={settings.requireEmailVerification}
                  onCheckedChange={(v) => handleChange('requireEmailVerification', v)}
                />
              </div>
              <div className="space-y-2">
                <Label>Session Timeout (minutes)</Label>
                <Input 
                  type="number"
                  value={settings.sessionTimeout}
                  onChange={(e) => handleChange('sessionTimeout', parseInt(e.target.value))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>BrAPI Configuration</CardTitle>
              <CardDescription>API settings and limits</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>BrAPI Version</Label>
                  <Select value={settings.brapiVersion} onValueChange={(v) => handleChange('brapiVersion', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2.1">v2.1</SelectItem>
                      <SelectItem value="2.0">v2.0</SelectItem>
                      <SelectItem value="1.3">v1.3</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Rate Limit (requests/hour)</Label>
                  <Input 
                    type="number"
                    value={settings.apiRateLimit}
                    onChange={(e) => handleChange('apiRateLimit', parseInt(e.target.value))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Max Upload Size (MB)</Label>
                <Input 
                  type="number"
                  value={settings.maxUploadSize}
                  onChange={(e) => handleChange('maxUploadSize', parseInt(e.target.value))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="features" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Feature Toggles</CardTitle>
              <CardDescription>Enable or disable system features</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Offline Mode</Label>
                  <p className="text-sm text-muted-foreground">Enable PWA offline capabilities</p>
                </div>
                <Switch 
                  checked={settings.enableOfflineMode}
                  onCheckedChange={(v) => handleChange('enableOfflineMode', v)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Notifications</Label>
                  <p className="text-sm text-muted-foreground">Enable system notifications</p>
                </div>
                <Switch 
                  checked={settings.enableNotifications}
                  onCheckedChange={(v) => handleChange('enableNotifications', v)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Audit Log</Label>
                  <p className="text-sm text-muted-foreground">Track all system activities</p>
                </div>
                <Switch 
                  checked={settings.enableAuditLog}
                  onCheckedChange={(v) => handleChange('enableAuditLog', v)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sync" className="space-y-6 mt-6">
          <SyncStatusPanel />
        </TabsContent>

        <TabsContent value="status" className="space-y-6 mt-6">
          <SystemStatusPanel />
        </TabsContent>

        <TabsContent value="dev" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Development Tools</CardTitle>
              <CardDescription>Track development progress and project status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div>
                  <h3 className="font-medium">🧠 Security Command Center</h3>
                  <p className="text-sm text-muted-foreground">ASHTA-STAMBHA unified security dashboard (CHAITANYA + PRAHARI + RAKSHAKA)</p>
                </div>
                <Button variant="outline" onClick={() => window.location.href = '/security'}>
                  Open →
                </Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div>
                  <h3 className="font-medium">🛡️ RAKSHAKA System Health</h3>
                  <p className="text-sm text-muted-foreground">Self-healing system monitoring and anomaly detection</p>
                </div>
                <Button variant="outline" onClick={() => window.location.href = '/system-health'}>
                  Open →
                </Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div>
                  <h3 className="font-medium">📊 Dev Progress</h3>
                  <p className="text-sm text-muted-foreground">View development progress, features, and roadmap</p>
                </div>
                <Button variant="outline" onClick={() => window.location.href = '/dev-progress'}>
                  Open →
                </Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div>
                  <h3 className="font-medium">📖 API Documentation</h3>
                  <p className="text-sm text-muted-foreground">Interactive API docs (Swagger UI)</p>
                </div>
                <Button variant="outline" onClick={() => window.open(`${API_BASE}/docs`, '_blank')}>
                  Open ↗
                </Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div>
                  <h3 className="font-medium">🔬 Server Info</h3>
                  <p className="text-sm text-muted-foreground">Backend server details and health</p>
                </div>
                <Button variant="outline" onClick={() => window.location.href = '/server-info'}>
                  Open →
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

// System Status Panel Component
function SystemStatusPanel() {
  const { data: status, isLoading, refetch } = useQuery({
    queryKey: ['system-settings', 'status'],
    queryFn: () => systemSettingsAPI.getSystemStatus(),
    refetchInterval: 10000, // Refresh every 10s
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📋 Task Queue
            <Button variant="ghost" size="sm" onClick={() => refetch()}>🔄</Button>
          </CardTitle>
          <CardDescription>Background task processing status</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : status?.task_queue ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{status.task_queue.pending || 0}</p>
                <p className="text-sm text-blue-600 dark:text-blue-400">Pending</p>
              </div>
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg">
                <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">{status.task_queue.running || 0}</p>
                <p className="text-sm text-yellow-600 dark:text-yellow-400">Running</p>
              </div>
              <div className="p-3 bg-green-50 dark:bg-green-900/30 rounded-lg">
                <p className="text-2xl font-bold text-green-700 dark:text-green-300">{status.task_queue.completed || 0}</p>
                <p className="text-sm text-green-600 dark:text-green-400">Completed</p>
              </div>
              <div className="p-3 bg-red-50 dark:bg-red-900/30 rounded-lg">
                <p className="text-2xl font-bold text-red-700 dark:text-red-300">{status.task_queue.failed || 0}</p>
                <p className="text-sm text-red-600 dark:text-red-400">Failed</p>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">Unable to connect to backend</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>📡 Event Bus</CardTitle>
          <CardDescription>Inter-module communication subscriptions</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : status?.event_bus?.subscriptions && Object.keys(status.event_bus.subscriptions).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(status.event_bus.subscriptions).map(([event, modules]: [string, any]) => (
                <div key={event} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-slate-800 rounded">
                  <code className="text-sm">{event}</code>
                  <span className="text-xs text-muted-foreground">{modules.join(', ')}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No active subscriptions</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>🔗 Service Health</CardTitle>
          <CardDescription>Backend service connectivity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {status?.service_health && Object.entries(status.service_health).map(([service, health]) => (
              <div key={service} className="flex items-center justify-between p-2 border rounded">
                <span className="capitalize">{service.replace('_', ' ')}</span>
                <span className={`px-2 py-1 rounded text-xs ${
                  health === 'connected' || health === 'running' 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {health === 'connected' || health === 'running' ? '● ' : '○ '}
                  {health}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

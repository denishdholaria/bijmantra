/**
 * System Settings Page
 * Admin configuration for the system
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'

export function SystemSettings() {
  const [settings, setSettings] = useState({
    siteName: 'Bijmantra',
    siteDescription: 'Plant Breeding Management System',
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

  const handleSave = () => {
    toast.success('Settings saved successfully')
  }

  const handleChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
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
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
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
      </Tabs>
    </div>
  )
}

/**
 * Settings Page
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { useDemoMode } from '@/hooks/useDemoMode'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { toast } from 'sonner'
import { FlaskConical } from 'lucide-react'

export function Settings() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('api_url') || '')
  const { 
    isDemoMode, 
    showDemoBanner, 
    toggleDemoBanner,
  } = useDemoMode()

  const handleSaveApiUrl = () => {
    if (apiUrl) {
      localStorage.setItem('api_url', apiUrl)
      toast.success('API URL saved. Refresh to apply changes.')
    } else {
      localStorage.removeItem('api_url')
      toast.success('API URL reset to default.')
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your account and application preferences</p>
      </div>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="ai" onClick={() => navigate('/ai-settings')} className="text-amber-600">🤖 AI Agent</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="about">About</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>User Profile</CardTitle>
              <CardDescription>Your account information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                  {user?.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <div>
                  <h3 className="font-semibold">{user?.full_name || 'User'}</h3>
                  <p className="text-sm text-muted-foreground">{user?.email}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4">
                <div>
                  <Label className="text-muted-foreground">Role</Label>
                  <p className="font-medium">Breeder</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Organization</Label>
                  <p className="font-medium">Bijmantra</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>BrAPI Configuration</CardTitle>
              <CardDescription>Configure the BrAPI server connection</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="apiUrl">API Base URL</Label>
                <Input
                  id="apiUrl"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="Leave empty for default (same origin)"
                />
                <p className="text-xs text-muted-foreground">
                  Current: {window.location.origin}
                </p>
              </div>
              <Button onClick={handleSaveApiUrl}>Save API Settings</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>BrAPI Version</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Badge className="bg-green-500">v2.1</Badge>
                <span className="text-sm text-muted-foreground">
                  Fully compliant with BrAPI v2.1 specification
                </span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
              <CardDescription>Customize the application appearance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Button variant="outline" className="flex-1">☀️ Light</Button>
                <Button variant="outline" className="flex-1" disabled>🌙 Dark (Coming Soon)</Button>
                <Button variant="outline" className="flex-1" disabled>💻 System</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FlaskConical className="h-5 w-5 text-amber-500" />
                Data Mode
              </CardTitle>
              <CardDescription>
                Your data mode is determined by your account type. 
                Demo users see sample data, production users see real data.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Status Display (Read-Only) */}
              <div className={`flex items-center justify-between p-4 rounded-lg ${
                isDemoMode 
                  ? 'bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800' 
                  : 'bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800'
              }`}>
                <div className="space-y-0.5">
                  <Label className="text-base font-medium">
                    {isDemoMode ? '🧪 Demo Mode' : '🏭 Production Mode'}
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    {isDemoMode 
                      ? 'You are viewing demo data for exploration and learning' 
                      : 'You are viewing real production data'}
                  </p>
                </div>
                <Badge variant={isDemoMode ? 'secondary' : 'default'}>
                  {isDemoMode ? 'Demo' : 'Production'}
                </Badge>
              </div>

              {/* Organization Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">Organization</Label>
                  <p className="font-medium">{user?.organization_name || 'Unknown'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Account Type</Label>
                  <p className="font-medium">{isDemoMode ? 'Demo Account' : 'Production Account'}</p>
                </div>
              </div>

              {/* Banner Toggle (only for demo users) */}
              {isDemoMode && (
                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="space-y-0.5">
                    <Label>Show Demo Banner</Label>
                    <p className="text-sm text-muted-foreground">
                      Display a banner indicating demo mode is active
                    </p>
                  </div>
                  <Switch
                    checked={showDemoBanner}
                    onCheckedChange={toggleDemoBanner}
                  />
                </div>
              )}

              {/* Info Box */}
              <div className={`p-3 rounded-lg ${
                isDemoMode 
                  ? 'bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800' 
                  : 'bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800'
              }`}>
                <p className={`text-sm ${
                  isDemoMode 
                    ? 'text-amber-800 dark:text-amber-200' 
                    : 'text-blue-800 dark:text-blue-200'
                }`}>
                  {isDemoMode ? (
                    <>
                      <strong>Demo Account:</strong> You're logged in with a demo account. 
                      All data shown is sample data for exploration. To work with real data, 
                      log in with a production account.
                    </>
                  ) : (
                    <>
                      <strong>Production Account:</strong> You're viewing real data. 
                      If you see empty pages, it means no data has been entered yet. 
                      To explore with sample data, log in with demo@bijmantra.org.
                    </>
                  )}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="about" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>About Bijmantra</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                  <span className="text-3xl">🌱</span>
                </div>
                <div>
                  <h3 className="text-xl font-bold">Bijmantra</h3>
                  <p className="text-muted-foreground">Plant Breeding Management System</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4">
                <div>
                  <Label className="text-muted-foreground">Version</Label>
                  <p className="font-medium">0.1.0-alpha</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">BrAPI Version</Label>
                  <p className="font-medium">v2.1</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">License</Label>
                  <p className="font-medium">MIT</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Build</Label>
                  <p className="font-medium font-mono text-xs">{new Date().toISOString().split('T')[0]}</p>
                </div>
              </div>
              <div className="pt-4 border-t">
                <h4 className="font-semibold mb-2">Features</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">Programs</Badge>
                  <Badge variant="secondary">Germplasm</Badge>
                  <Badge variant="secondary">Traits</Badge>
                  <Badge variant="secondary">Observations</Badge>
                  <Badge variant="secondary">Trials</Badge>
                  <Badge variant="secondary">Studies</Badge>
                  <Badge variant="secondary">Locations</Badge>
                  <Badge variant="outline">PWA Ready</Badge>
                  <Badge variant="outline">Offline Support</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

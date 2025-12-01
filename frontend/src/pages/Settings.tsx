/**
 * Settings Page
 */

import { useState } from 'react'
import { useAuthStore } from '@/store/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

export function Settings() {
  const { user } = useAuthStore()
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('api_url') || '')

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
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="profile">Profile</TabsTrigger>
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

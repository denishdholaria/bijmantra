/**
 * User Profile Page
 * Account management and preferences
 * Enhanced with i18n, density, and field mode settings
 */

import { useState, useEffect, useCallback } from 'react'
import { useAuthStore } from '@/store/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'
import { useI18n } from '@/hooks/useI18n'
import { useDensity } from '@/hooks/useDensity'
import { useFieldMode } from '@/hooks/useFieldMode'
import { useColorScheme } from '@/hooks/useColorScheme'
import { useTheme } from '@/hooks/useTheme'
import { LanguageSelector } from '@/components/LanguageSelector'
import { Sun, Moon, Smartphone, Monitor, Palette, Languages, Maximize2, Eye, Volume2 } from 'lucide-react'

export function Profile() {
  const { user } = useAuthStore()
  const { t, language, setLanguage, isRTL } = useI18n()
  const { density, setDensity } = useDensity()
  const fieldMode = useFieldMode()
  const colorScheme = useColorScheme()
  const { isDark } = useTheme()
  
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // Preferences
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [pushNotifications, setPushNotifications] = useState(true)
  const [soundEnabled, setSoundEnabled] = useState(true)

  // Handle dark mode toggle
  const handleDarkModeChange = useCallback((checked: boolean) => {
    const newTheme = checked ? 'dark' : 'light'
    document.documentElement.classList.remove('light', 'dark')
    document.documentElement.classList.add(newTheme)
    localStorage.setItem('bijmantra-theme', newTheme)
    window.dispatchEvent(new CustomEvent('theme-change', { detail: newTheme }))
  }, [])

  const handleUpdateProfile = () => {
    toast.success('Profile updated (demo)')
  }

  const handleChangePassword = () => {
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }
    toast.success('Password changed (demo)')
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">Profile</h1>
        <p className="text-muted-foreground mt-1">Manage your account and preferences</p>
      </div>

      {/* Profile Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center text-4xl">
              {user?.full_name?.[0] || user?.email?.[0] || '👤'}
            </div>
            <div>
              <h2 className="text-xl font-bold">{user?.full_name || 'User'}</h2>
              <p className="text-muted-foreground">{user?.email}</p>
              <Badge variant="outline" className="mt-2">Active</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="account" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
        </TabsList>

        <TabsContent value="account" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
              <CardDescription>Update your personal details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full Name</Label>
                  <Input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                </div>
              </div>
              <Button onClick={handleUpdateProfile}>Save Changes</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Organization</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-muted rounded-lg">
                <p className="font-medium">Default Organization</p>
                <p className="text-sm text-muted-foreground">Organization ID: {user?.organization_id || 1}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>Update your password regularly for security</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Current Password</Label>
                <Input id="currentPassword" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="newPassword">New Password</Label>
                <Input id="newPassword" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <Input id="confirmPassword" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
              </div>
              <Button onClick={handleChangePassword}>Change Password</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sessions</CardTitle>
              <CardDescription>Manage your active sessions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-muted rounded-lg flex items-center justify-between">
                <div>
                  <p className="font-medium">Current Session</p>
                  <p className="text-sm text-muted-foreground">This device • Active now</p>
                </div>
                <Badge variant="default">Current</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="space-y-6 mt-6">
          {/* Language & Localization */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Languages className="h-5 w-5" />
                Language & Localization
              </CardTitle>
              <CardDescription>Choose your preferred language and regional settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Language</p>
                  <p className="text-sm text-muted-foreground">
                    Select your preferred language {isRTL && '(RTL enabled)'}
                  </p>
                </div>
                <LanguageSelector variant="default" />
              </div>
            </CardContent>
          </Card>

          {/* Display Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                Display Settings
              </CardTitle>
              <CardDescription>Customize how the interface looks</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Dark Mode</p>
                  <p className="text-sm text-muted-foreground">Use dark theme</p>
                </div>
                <Switch checked={isDark} onCheckedChange={handleDarkModeChange} />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Display Density</p>
                  <p className="text-sm text-muted-foreground">Adjust spacing between elements</p>
                </div>
                <Select value={density} onValueChange={(v: 'compact' | 'comfortable' | 'spacious') => setDensity(v)}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="compact">Compact</SelectItem>
                    <SelectItem value="comfortable">Comfortable</SelectItem>
                    <SelectItem value="spacious">Spacious</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Color Scheme</p>
                  <p className="text-sm text-muted-foreground">Chart and data visualization colors</p>
                </div>
                <Select value={colorScheme.mode} onValueChange={(v: 'standard' | 'colorblind') => colorScheme.setMode(v)}>
                  <SelectTrigger className="w-[160px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="colorblind">Colorblind Safe</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Field Mode Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5" />
                Field Mode
              </CardTitle>
              <CardDescription>Optimize the interface for outdoor field work</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Enable Field Mode</p>
                  <p className="text-sm text-muted-foreground">High contrast, large touch targets</p>
                </div>
                <Switch checked={fieldMode.isFieldMode} onCheckedChange={fieldMode.toggleFieldMode} />
              </div>

              {fieldMode.isFieldMode && (
                <>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Eye className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="font-medium">High Contrast</p>
                        <p className="text-sm text-muted-foreground">WCAG AAA 7:1 contrast ratio</p>
                      </div>
                    </div>
                    <Switch 
                      checked={fieldMode.highContrast} 
                      onCheckedChange={(v) => fieldMode.updateSettings({ highContrast: v })} 
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Maximize2 className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Large Text</p>
                        <p className="text-sm text-muted-foreground">Increase font size for readability</p>
                      </div>
                    </div>
                    <Switch 
                      checked={fieldMode.largeText} 
                      onCheckedChange={(v) => fieldMode.updateSettings({ largeText: v })} 
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Volume2 className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Haptic Feedback</p>
                        <p className="text-sm text-muted-foreground">Vibration on button press</p>
                      </div>
                    </div>
                    <Switch 
                      checked={fieldMode.hapticFeedback} 
                      onCheckedChange={(v) => fieldMode.updateSettings({ hapticFeedback: v })} 
                    />
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card>
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
              <CardDescription>Manage how you receive updates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-muted-foreground">Receive updates via email</p>
                </div>
                <Switch checked={emailNotifications} onCheckedChange={setEmailNotifications} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Push Notifications</p>
                  <p className="text-sm text-muted-foreground">Browser push notifications</p>
                </div>
                <Switch checked={pushNotifications} onCheckedChange={setPushNotifications} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Sound Effects</p>
                  <p className="text-sm text-muted-foreground">Play sounds for notifications</p>
                </div>
                <Switch checked={soundEnabled} onCheckedChange={setSoundEnabled} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

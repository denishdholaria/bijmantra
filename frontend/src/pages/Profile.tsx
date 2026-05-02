/**
 * User Profile Page
 * Account management and preferences
 */

import { useCallback, useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
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
import { apiClient } from '@/lib/api-client'
import { Eye, Languages, Maximize2, Monitor, Smartphone, Volume2 } from 'lucide-react'

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}

const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return 'Not reported'
  }

  const timestamp = new Date(value)
  if (Number.isNaN(timestamp.getTime())) {
    return value
  }

  return timestamp.toLocaleString()
}

export function Profile() {
  const queryClient = useQueryClient()
  const user = useAuthStore((state) => state.user)
  const { isRTL } = useI18n()
  const { density, setDensity } = useDensity()
  const fieldMode = useFieldMode()
  const colorScheme = useColorScheme()
  const { isDark } = useTheme()

  const [fullName, setFullName] = useState(user?.full_name || '')
  const [phone, setPhone] = useState('')
  const [location, setLocation] = useState('')
  const [bio, setBio] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [pushNotifications, setPushNotifications] = useState(true)
  const [soundEnabled, setSoundEnabled] = useState(true)

  const profileQuery = useQuery({
    queryKey: ['profile'],
    queryFn: () => apiClient.profileService.getProfile(),
  })

  const preferencesQuery = useQuery({
    queryKey: ['profile', 'preferences'],
    queryFn: () => apiClient.profileService.getPreferences(),
  })

  const sessionsQuery = useQuery({
    queryKey: ['profile', 'sessions'],
    queryFn: () => apiClient.profileService.getSessions(),
  })

  const profile = profileQuery.data?.data
  const preferences = preferencesQuery.data?.data
  const sessions = sessionsQuery.data?.data ?? []

  useEffect(() => {
    if (!profile) {
      return
    }

    setFullName(profile.full_name || '')
    setPhone(profile.phone || '')
    setLocation(profile.location || '')
    setBio(profile.bio || '')
  }, [profile])

  useEffect(() => {
    if (!preferences) {
      return
    }

    setEmailNotifications(preferences.email_notifications)
    setPushNotifications(preferences.push_notifications)
    setSoundEnabled(preferences.sound_enabled)
  }, [preferences])

  const handleDarkModeChange = useCallback((checked: boolean) => {
    const newTheme = checked ? 'dark' : 'light'
    document.documentElement.classList.remove('light', 'dark')
    document.documentElement.classList.add(newTheme)
    localStorage.setItem('bijmantra-theme', newTheme)
    window.dispatchEvent(new CustomEvent('theme-change', { detail: newTheme }))
  }, [])

  const updateProfileMutation = useMutation({
    mutationFn: () =>
      apiClient.profileService.updateProfile({
        full_name: fullName.trim() || undefined,
        phone: phone.trim() || null,
        location: location.trim() || null,
        bio: bio.trim() || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      useAuthStore.setState((state) => ({
        user: state.user ? { ...state.user, full_name: fullName.trim() || state.user.full_name } : state.user,
      }))
      toast.success('Profile updated')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Failed to update profile'))
    },
  })

  const updatePreferencesMutation = useMutation({
    mutationFn: (nextPreferences: Record<string, boolean>) => apiClient.profileService.updatePreferences(nextPreferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile', 'preferences'] })
      toast.success('Notification preferences updated')
    },
    onError: (error) => {
      queryClient.invalidateQueries({ queryKey: ['profile', 'preferences'] })
      toast.error(getErrorMessage(error, 'Failed to update notification preferences'))
    },
  })

  const changePasswordMutation = useMutation({
    mutationFn: () =>
      apiClient.profileService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      }),
    onSuccess: () => {
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      toast.success('Password changed successfully')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Failed to change password'))
    },
  })

  const revokeSessionMutation = useMutation({
    mutationFn: (sessionId: string) => apiClient.profileService.revokeSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile', 'sessions'] })
      toast.success('Session revoked')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Failed to revoke session'))
    },
  })

  const handleSaveProfile = () => {
    updateProfileMutation.mutate()
  }

  const handleChangePassword = () => {
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    changePasswordMutation.mutate()
  }

  const handleNotificationPreferenceChange = (
    field: 'email_notifications' | 'push_notifications' | 'sound_enabled',
    checked: boolean,
  ) => {
    if (field === 'email_notifications') {
      setEmailNotifications(checked)
    }
    if (field === 'push_notifications') {
      setPushNotifications(checked)
    }
    if (field === 'sound_enabled') {
      setSoundEnabled(checked)
    }

    updatePreferencesMutation.mutate({ [field]: checked })
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">Profile</h1>
        <p className="text-muted-foreground mt-1">Manage your account and preferences</p>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center text-4xl">
              {(profile?.full_name || user?.full_name || profile?.email || user?.email || 'U')[0]}
            </div>
            <div>
              <h2 className="text-xl font-bold">{profile?.full_name || user?.full_name || 'User'}</h2>
              <p className="text-muted-foreground">{profile?.email || user?.email}</p>
              <Badge variant="outline" className="mt-2">
                {profile?.status === 'active' || !profile ? 'Active' : profile.status}
              </Badge>
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
              <CardDescription>Update the personal fields backed by your profile record.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {profileQuery.isLoading && !profile ? (
                <div className="text-sm text-muted-foreground">Loading profile details...</div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="fullName">Full Name</Label>
                      <Input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input id="email" type="email" value={profile?.email || user?.email || ''} readOnly disabled />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone</Label>
                      <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="location">Location</Label>
                      <Input id="location" value={location} onChange={(e) => setLocation(e.target.value)} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bio">Bio</Label>
                    <Input id="bio" value={bio} onChange={(e) => setBio(e.target.value)} />
                  </div>
                  <Button onClick={handleSaveProfile} disabled={updateProfileMutation.isPending}>
                    {updateProfileMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Organization</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-muted rounded-lg space-y-1">
                <p className="font-medium">{profile?.organization_name || user?.organization_name || 'Current Organization'}</p>
                <p className="text-sm text-muted-foreground">Organization ID: {profile?.organization_id || user?.organization_id || 'Not reported'}</p>
                <p className="text-sm text-muted-foreground">Email identity is managed by the authenticated account and is not editable from this page.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>Rotate the password for the authenticated account.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border bg-accent/40 p-3 text-sm text-muted-foreground">
                Password changes now call the live profile API and enforce the backend password policy.
              </div>
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
              <Button onClick={handleChangePassword} disabled={changePasswordMutation.isPending}>
                {changePasswordMutation.isPending ? 'Changing...' : 'Change Password'}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sessions</CardTitle>
              <CardDescription>Manage active sessions currently reported by the backend.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {sessionsQuery.isLoading ? (
                <div className="text-sm text-muted-foreground">Loading active sessions...</div>
              ) : sessions.length > 0 ? (
                sessions.map((session: { id: number; device?: string | null; ip_address?: string | null; location?: string | null; last_active?: string | null; is_current: boolean }) => (
                  <div key={session.id} className="p-4 bg-muted rounded-lg flex items-center justify-between gap-4">
                    <div>
                      <p className="font-medium">{session.device || 'Unknown device'}</p>
                      <p className="text-sm text-muted-foreground">
                        {[session.location || 'Unknown location', session.ip_address || 'IP unavailable', `Last active ${formatTimestamp(session.last_active)}`].join(' • ')}
                      </p>
                    </div>
                    {session.is_current ? (
                      <Badge variant="default">Current</Badge>
                    ) : (
                      <Button
                        variant="outline"
                        onClick={() => revokeSessionMutation.mutate(String(session.id))}
                        disabled={revokeSessionMutation.isPending}
                      >
                        Revoke
                      </Button>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-sm text-muted-foreground">No persisted sessions are currently reported.</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="space-y-6 mt-6">
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
                  <p className="text-sm text-muted-foreground">Select your preferred language {isRTL && '(RTL enabled)'}</p>
                </div>
                <LanguageSelector variant="default" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                Display Settings
              </CardTitle>
              <CardDescription>Customize how the interface looks on this device.</CardDescription>
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

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5" />
                Field Mode
              </CardTitle>
              <CardDescription>Optimize the interface for outdoor field work on this device.</CardDescription>
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
                    <Switch checked={fieldMode.highContrast} onCheckedChange={(v) => fieldMode.updateSettings({ highContrast: v })} />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Maximize2 className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Large Text</p>
                        <p className="text-sm text-muted-foreground">Increase font size for readability</p>
                      </div>
                    </div>
                    <Switch checked={fieldMode.largeText} onCheckedChange={(v) => fieldMode.updateSettings({ largeText: v })} />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Volume2 className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Haptic Feedback</p>
                        <p className="text-sm text-muted-foreground">Vibration on button press</p>
                      </div>
                    </div>
                    <Switch checked={fieldMode.hapticFeedback} onCheckedChange={(v) => fieldMode.updateSettings({ hapticFeedback: v })} />
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
              <CardDescription>Manage backend-backed notification preferences for this account.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {preferencesQuery.isLoading && !preferences ? (
                <div className="text-sm text-muted-foreground">Loading notification preferences...</div>
              ) : (
                <>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Email Notifications</p>
                      <p className="text-sm text-muted-foreground">Receive updates via email</p>
                    </div>
                    <Switch
                      checked={emailNotifications}
                      disabled={updatePreferencesMutation.isPending}
                      onCheckedChange={(checked) => handleNotificationPreferenceChange('email_notifications', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Push Notifications</p>
                      <p className="text-sm text-muted-foreground">Browser push notifications</p>
                    </div>
                    <Switch
                      checked={pushNotifications}
                      disabled={updatePreferencesMutation.isPending}
                      onCheckedChange={(checked) => handleNotificationPreferenceChange('push_notifications', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Sound Effects</p>
                      <p className="text-sm text-muted-foreground">Play sounds for notifications</p>
                    </div>
                    <Switch
                      checked={soundEnabled}
                      disabled={updatePreferencesMutation.isPending}
                      onCheckedChange={(checked) => handleNotificationPreferenceChange('sound_enabled', checked)}
                    />
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

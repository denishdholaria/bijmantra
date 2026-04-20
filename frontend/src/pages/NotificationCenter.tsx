import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import type {
  NotificationPreferenceRecord,
  NotificationRecord,
  QuietHoursRecord,
} from '@/lib/api/system/notifications'
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  Settings,
  AlertTriangle,
  Info,
  CheckCircle2,
  XCircle,
  FlaskConical,
  Leaf,
  Cloud,
  Mail,
  Smartphone,
  Monitor
} from 'lucide-react'

export function NotificationCenter() {
  const [filter, setFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const queryClient = useQueryClient()

  // Fetch notifications
  const { data: notificationsData, isLoading } = useQuery({
    queryKey: ['notifications', filter],
    queryFn: () => apiClient.notificationService.getNotifications({
      filter: filter as 'all' | 'unread' | 'success' | 'warning' | 'error' | 'info',
    }),
  })

  const notifications = notificationsData || []

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['notification-stats'],
    queryFn: () => apiClient.notificationService.getStats(),
  })

  const stats = statsData

  const { data: preferences = [], isLoading: preferencesLoading } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: () => apiClient.notificationService.getPreferences(),
  })

  const { data: quietHours } = useQuery({
    queryKey: ['notification-quiet-hours'],
    queryFn: () => apiClient.notificationService.getQuietHours(),
  })

  // Mark read mutation
  const markReadMutation = useMutation({
    mutationFn: (notificationId: number) => apiClient.notificationService.markAsRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] })
      toast.success('Marked as read')
    },
  })

  // Mark all read mutation
  const markAllReadMutation = useMutation({
    mutationFn: () => apiClient.notificationService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] })
      toast.success('All notifications marked as read')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (notificationId: number) => apiClient.notificationService.deleteNotification(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] })
      toast.success('Notification deleted')
    },
  })

  const updatePreferenceMutation = useMutation({
    mutationFn: (preference: NotificationPreferenceRecord) => apiClient.notificationService.updatePreference(preference),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] })
      toast.success('Preferences updated')
    },
  })

  const updateQuietHoursMutation = useMutation({
    mutationFn: (settings: QuietHoursRecord) => apiClient.notificationService.updateQuietHours(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-quiet-hours'] })
      toast.success('Quiet hours updated')
    },
  })

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'error': return <XCircle className="h-5 w-5 text-red-500" />
      default: return <Info className="h-5 w-5 text-blue-500" />
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'trials': return <FlaskConical className="h-4 w-4" />
      case 'inventory': return <Leaf className="h-4 w-4" />
      case 'weather': return <Cloud className="h-4 w-4" />
      default: return <Bell className="h-4 w-4" />
    }
  }

  const unreadCount = stats?.unread || 0
  const filteredNotifications = notifications.filter((n) => {
    const matchesSearch = n.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         n.message.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesSearch
  })

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins} minutes ago`
    if (diffHours < 24) return `${diffHours} hours ago`
    return `${diffDays} days ago`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bell className="h-8 w-8 text-primary" />
            Notification Center
            {unreadCount > 0 && <Badge variant="destructive">{unreadCount} new</Badge>}
          </h1>
          <p className="text-muted-foreground mt-1">Stay updated on your breeding program activities</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending || unreadCount === 0}
          >
            <CheckCheck className="h-4 w-4 mr-2" />Mark All Read
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      {stats ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg"><Bell className="h-5 w-5 text-blue-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.total}</div>
                  <div className="text-sm text-muted-foreground">Total</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-100 rounded-lg"><AlertTriangle className="h-5 w-5 text-red-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.unread}</div>
                  <div className="text-sm text-muted-foreground">Unread</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg"><AlertTriangle className="h-5 w-5 text-yellow-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.warnings || 0}</div>
                  <div className="text-sm text-muted-foreground">Warnings</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg"><CheckCircle2 className="h-5 w-5 text-green-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.success || 0}</div>
                  <div className="text-sm text-muted-foreground">Success</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      )}

      <Tabs defaultValue="notifications" className="space-y-4">
        <TabsList>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
        </TabsList>

        <TabsContent value="notifications" className="space-y-4">
          <div className="flex items-center gap-4">
            <Input 
              placeholder="Search notifications..." 
              value={searchQuery} 
              onChange={(e) => setSearchQuery(e.target.value)} 
              className="max-w-sm" 
            />
            <div className="flex gap-1">
              {['all', 'unread', 'success', 'warning', 'error', 'info'].map((f) => (
                <Button 
                  key={f} 
                  variant={filter === f ? 'default' : 'outline'} 
                  size="sm" 
                  onClick={() => setFilter(f)} 
                  className="capitalize"
                >
                  {f}
                </Button>
              ))}
            </div>
          </div>

          <Card>
            <ScrollArea className="h-[500px]">
              {isLoading ? (
                <div className="p-4 space-y-4">
                  {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-20" />)}
                </div>
              ) : (
                <div className="divide-y">
                  {filteredNotifications.length === 0 ? (
                    <div className="p-8 text-center text-muted-foreground">
                      No notifications found
                    </div>
                  ) : (
                    filteredNotifications.map((notification: NotificationRecord) => (
                      <div 
                        key={notification.id} 
                        className={`p-4 hover:bg-muted/50 transition-colors ${!notification.read ? 'bg-primary/5' : ''}`}
                      >
                        <div className="flex items-start gap-4">
                          <div className="mt-1">{getTypeIcon(notification.type)}</div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className={`font-medium ${!notification.read ? 'text-foreground' : 'text-muted-foreground'}`}>
                                {notification.title}
                              </h4>
                              {!notification.read && <div className="w-2 h-2 bg-primary rounded-full" />}
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">{notification.message}</p>
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                {getCategoryIcon(notification.category)}
                                {notification.category}
                              </span>
                              <span>{formatTimestamp(notification.timestamp)}</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            {notification.action_url && (
                              <Button variant="outline" size="sm">View</Button>
                            )}
                            {!notification.read && (
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => markReadMutation.mutate(notification.id)}
                                disabled={markReadMutation.isPending}
                                aria-label="Mark as read"
                              >
                                <Check className="h-4 w-4" />
                              </Button>
                            )}
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => deleteMutation.mutate(notification.id)}
                              disabled={deleteMutation.isPending}
                              aria-label="Delete notification"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </ScrollArea>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Choose how you want to receive notifications</CardDescription>
            </CardHeader>
            <CardContent>
              {preferencesLoading ? (
                <div className="space-y-4">
                  {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-12" />)}
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-4 gap-4 pb-2 border-b font-medium text-sm">
                    <div>Category</div>
                    <div className="flex items-center gap-2"><Mail className="h-4 w-4" />Email</div>
                    <div className="flex items-center gap-2"><Smartphone className="h-4 w-4" />Push</div>
                    <div className="flex items-center gap-2"><Monitor className="h-4 w-4" />In-App</div>
                  </div>
                  {preferences.map((pref, index) => (
                    <div key={pref.category} className="grid grid-cols-4 gap-4 items-center">
                      <div className="font-medium">{pref.category}</div>
                      <div>
                        <Switch 
                          checked={pref.email} 
                          onCheckedChange={(checked) => updatePreferenceMutation.mutate({ ...pref, email: checked })}
                          disabled={updatePreferenceMutation.isPending}
                        />
                      </div>
                      <div>
                        <Switch 
                          checked={pref.push} 
                          onCheckedChange={(checked) => updatePreferenceMutation.mutate({ ...pref, push: checked })}
                          disabled={updatePreferenceMutation.isPending}
                        />
                      </div>
                      <div>
                        <Switch 
                          checked={pref.in_app} 
                          onCheckedChange={(checked) => updatePreferenceMutation.mutate({ ...pref, in_app: checked })}
                          disabled={updatePreferenceMutation.isPending}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quiet Hours</CardTitle>
              <CardDescription>Pause notifications during specific times</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Enable Quiet Hours</div>
                  <div className="text-sm text-muted-foreground">
                    No push notifications from {quietHours?.start_time || '22:00'} to {quietHours?.end_time || '07:00'}
                  </div>
                </div>
                <Switch 
                  checked={quietHours?.enabled ?? false}
                  onCheckedChange={(checked) => quietHours ? updateQuietHoursMutation.mutate({ ...quietHours, enabled: checked }) : undefined}
                  disabled={!quietHours || updateQuietHoursMutation.isPending}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

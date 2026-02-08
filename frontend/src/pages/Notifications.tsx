/**
 * Notifications Page
 * System notifications and alerts - Connected to /api/v2/notifications
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { Bell, Check, CheckCheck, Settings, Trash2, Loader2 } from 'lucide-react'

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
  link?: string
  category: 'system' | 'data' | 'task' | 'alert'
}

// API functions
async function fetchNotifications(filter: string): Promise<{ data: Notification[]; total: number; unread_count: number }> {
  const params = new URLSearchParams()
  if (filter === 'unread') {
    params.append('read', 'false')
  } else if (filter !== 'all') {
    params.append('category', filter)
  }
  
  const response = await fetch(`/api/v2/notifications?${params}`)
  if (!response.ok) throw new Error('Failed to fetch notifications')
  return response.json()
}

async function markNotificationRead(id: string): Promise<void> {
  const response = await fetch(`/api/v2/notifications/${id}/read`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) throw new Error('Failed to mark as read')
}

async function markAllNotificationsRead(): Promise<void> {
  const response = await fetch('/api/v2/notifications/mark-all-read', {
    method: 'POST',
  })
  if (!response.ok) throw new Error('Failed to mark all as read')
}

async function deleteNotification(id: string): Promise<void> {
  const response = await fetch(`/api/v2/notifications/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error('Failed to delete notification')
}

export function Notifications() {
  const [filter, setFilter] = useState<string>('all')
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['notifications', filter],
    queryFn: () => fetchNotifications(filter),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const notifications = data?.data || []
  const unreadCount = data?.unread_count || 0

  const markAsReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Marked as read')
    },
    onError: () => {
      toast.error('Failed to mark as read')
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('All notifications marked as read')
    },
    onError: () => {
      toast.error('Failed to mark all as read')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteNotification,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Notification deleted')
    },
    onError: () => {
      toast.error('Failed to delete notification')
    },
  })

  const getTypeIcon = (type: Notification['type']) => {
    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' }
    return icons[type]
  }

  const getTypeColor = (type: Notification['type']) => {
    const colors = {
      info: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300',
      success: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-300',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-300',
      error: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-300',
    }
    return colors[type]
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    
    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'Just now'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Bell className="h-7 w-7" />
            Notifications
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white">{unreadCount}</Badge>
            )}
          </h1>
          <p className="text-muted-foreground mt-1">System alerts and updates</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => markAllReadMutation.mutate()}
            disabled={unreadCount === 0 || markAllReadMutation.isPending}
          >
            {markAllReadMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <CheckCheck className="h-4 w-4 mr-2" />
            )}
            Mark All Read
          </Button>
          <Button variant="outline" onClick={() => toast.info('Notification settings coming soon')}>
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      <Tabs value={filter} onValueChange={setFilter}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="unread">
            Unread {unreadCount > 0 && `(${unreadCount})`}
          </TabsTrigger>
          <TabsTrigger value="alert">Alerts</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
          <TabsTrigger value="task">Tasks</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value={filter} className="mt-6">
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 w-full" />)}
            </div>
          ) : error ? (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="text-4xl mb-4">⚠️</div>
                <p className="text-muted-foreground">Failed to load notifications</p>
                <Button 
                  variant="outline" 
                  className="mt-4"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ['notifications'] })}
                >
                  Retry
                </Button>
              </CardContent>
            </Card>
          ) : notifications.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="text-4xl mb-4">🔔</div>
                <p className="text-muted-foreground">
                  {filter === 'unread' ? 'No unread notifications' : 'No notifications'}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {notifications.map((notification) => (
                <Card 
                  key={notification.id} 
                  className={`transition-all ${!notification.read ? 'border-l-4 border-l-primary bg-primary/5' : ''}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-full ${getTypeColor(notification.type)}`}>
                        <span className="text-lg">{getTypeIcon(notification.type)}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h3 className="font-semibold">{notification.title}</h3>
                            <p className="text-sm text-muted-foreground mt-1">{notification.message}</p>
                          </div>
                          <div className="text-right shrink-0">
                            <p className="text-xs text-muted-foreground">{formatTime(notification.timestamp)}</p>
                            <Badge variant="outline" className="mt-1 text-xs">{notification.category}</Badge>
                          </div>
                        </div>
                        <div className="flex gap-2 mt-3">
                          {notification.link && (
                            <Button size="sm" variant="outline" asChild>
                              <a href={notification.link}>View Details</a>
                            </Button>
                          )}
                          {!notification.read && (
                            <Button 
                              size="sm" 
                              variant="ghost"
                              onClick={() => markAsReadMutation.mutate(notification.id)}
                              disabled={markAsReadMutation.isPending}
                            >
                              <Check className="h-4 w-4 mr-1" />
                              Mark Read
                            </Button>
                          )}
                          <Button 
                            size="sm" 
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            onClick={() => deleteMutation.mutate(notification.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

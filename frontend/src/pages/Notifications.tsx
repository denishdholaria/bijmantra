/**
 * Notifications Page
 * System notifications and alerts
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

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

const mockNotifications: Notification[] = [
  { id: 'n001', type: 'success', title: 'Import Complete', message: 'Successfully imported 150 germplasm entries', timestamp: '2024-02-20T10:30:00', read: false, category: 'data', link: '/germplasm' },
  { id: 'n002', type: 'warning', title: 'Low Seed Stock', message: 'Seed lot SL-2024-001 is below minimum threshold', timestamp: '2024-02-20T09:15:00', read: false, category: 'alert', link: '/seedlots' },
  { id: 'n003', type: 'info', title: 'Trial Started', message: 'Rice Yield Trial 2024 has been activated', timestamp: '2024-02-19T14:00:00', read: true, category: 'task', link: '/trials' },
  { id: 'n004', type: 'error', title: 'Sync Failed', message: 'Failed to sync observations from field device', timestamp: '2024-02-19T11:30:00', read: true, category: 'system' },
  { id: 'n005', type: 'success', title: 'Genotyping Complete', message: 'Order ORD-2024-001 results are ready', timestamp: '2024-02-18T16:45:00', read: true, category: 'data', link: '/vendororders' },
  { id: 'n006', type: 'info', title: 'New User Added', message: 'John Smith has joined the Rice Breeding Program', timestamp: '2024-02-18T10:00:00', read: true, category: 'system' },
  { id: 'n007', type: 'warning', title: 'Data Quality Issue', message: '5 observations have outlier values in Study S-2024-003', timestamp: '2024-02-17T15:20:00', read: true, category: 'alert', link: '/observations' },
]

export function Notifications() {
  const [filter, setFilter] = useState<string>('all')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', filter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 300))
      let filtered = mockNotifications
      if (filter === 'unread') filtered = filtered.filter(n => !n.read)
      else if (filter !== 'all') filtered = filtered.filter(n => n.category === filter)
      return filtered
    },
  })

  const notifications = data || []
  const unreadCount = mockNotifications.filter(n => !n.read).length

  const markAsRead = useMutation({
    mutationFn: async (id: string) => {
      await new Promise(r => setTimeout(r, 200))
      return id
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Marked as read')
    },
  })

  const markAllAsRead = () => {
    toast.success('All notifications marked as read')
  }

  const getTypeIcon = (type: Notification['type']) => {
    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' }
    return icons[type]
  }

  const getTypeColor = (type: Notification['type']) => {
    const colors = {
      info: 'bg-blue-100 text-blue-800 border-blue-200',
      success: 'bg-green-100 text-green-800 border-green-200',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      error: 'bg-red-100 text-red-800 border-red-200',
    }
    return colors[type]
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(hours / 24)
    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    return 'Just now'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            Notifications
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white">{unreadCount}</Badge>
            )}
          </h1>
          <p className="text-muted-foreground mt-1">System alerts and updates</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={markAllAsRead} disabled={unreadCount === 0}>
            ✓ Mark All Read
          </Button>
          <Button variant="outline" onClick={() => toast.success('Settings opened (demo)')}>
            ⚙️ Settings
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
          ) : notifications.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="text-4xl mb-4">🔔</div>
                <p className="text-muted-foreground">No notifications</p>
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
                          <div className="text-right">
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
                              onClick={() => markAsRead.mutate(notification.id)}
                            >
                              Mark as Read
                            </Button>
                          )}
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

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Bell,
  BellOff,
  Check,
  CheckCheck,
  Trash2,
  Settings,
  Filter,
  AlertTriangle,
  Info,
  CheckCircle2,
  XCircle,
  Calendar,
  Leaf,
  FlaskConical,
  Cloud,
  Mail,
  Smartphone,
  Monitor
} from 'lucide-react'

interface Notification {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title: string
  message: string
  category: string
  timestamp: string
  read: boolean
  actionUrl?: string
}

interface NotificationPreference {
  category: string
  email: boolean
  push: boolean
  inApp: boolean
}

export function NotificationCenter() {
  const [filter, setFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const notifications: Notification[] = [
    { id: '1', type: 'success', title: 'Trial Completed', message: 'Trial YT-2025-001 has been marked as complete. View results now.', category: 'trials', timestamp: '10 minutes ago', read: false, actionUrl: '/trials/YT-2025-001' },
    { id: '2', type: 'warning', title: 'Low Seed Inventory', message: 'Seed lot SL-2024-089 is below minimum threshold (500 seeds remaining).', category: 'inventory', timestamp: '1 hour ago', read: false, actionUrl: '/seedlots/SL-2024-089' },
    { id: '3', type: 'info', title: 'Weather Alert', message: 'Heavy rain expected tomorrow. Consider rescheduling field activities.', category: 'weather', timestamp: '2 hours ago', read: false },
    { id: '4', type: 'success', title: 'Data Sync Complete', message: 'Successfully synced 1,247 observations from mobile devices.', category: 'sync', timestamp: '3 hours ago', read: true },
    { id: '5', type: 'error', title: 'Import Failed', message: 'Failed to import germplasm data. Check file format and try again.', category: 'import', timestamp: '5 hours ago', read: true, actionUrl: '/import-export' },
    { id: '6', type: 'info', title: 'New Team Member', message: 'Dr. Sarah Johnson has joined the Rice Breeding program.', category: 'team', timestamp: '1 day ago', read: true },
    { id: '7', type: 'success', title: 'Variety Released', message: 'BM-Gold-2025 has been officially released. Congratulations!', category: 'releases', timestamp: '2 days ago', read: true },
    { id: '8', type: 'warning', title: 'Disease Detected', message: 'Possible rice blast detected in Field A, Block 3. Immediate inspection recommended.', category: 'alerts', timestamp: '3 days ago', read: true, actionUrl: '/crop-health' }
  ]

  const preferences: NotificationPreference[] = [
    { category: 'Trial Updates', email: true, push: true, inApp: true },
    { category: 'Inventory Alerts', email: true, push: true, inApp: true },
    { category: 'Weather Alerts', email: false, push: true, inApp: true },
    { category: 'Data Sync', email: false, push: false, inApp: true },
    { category: 'Team Updates', email: true, push: false, inApp: true },
    { category: 'System Alerts', email: true, push: true, inApp: true }
  ]

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

  const unreadCount = notifications.filter(n => !n.read).length
  const filteredNotifications = notifications.filter(n => {
    const matchesFilter = filter === 'all' || (filter === 'unread' && !n.read) || n.type === filter
    const matchesSearch = n.title.toLowerCase().includes(searchQuery.toLowerCase()) || n.message.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesSearch
  })

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
          <Button variant="outline"><CheckCheck className="h-4 w-4 mr-2" />Mark All Read</Button>
          <Button variant="outline"><Settings className="h-4 w-4 mr-2" />Settings</Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Bell className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{notifications.length}</div>
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
                <div className="text-2xl font-bold">{unreadCount}</div>
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
                <div className="text-2xl font-bold">{notifications.filter(n => n.type === 'warning').length}</div>
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
                <div className="text-2xl font-bold">{notifications.filter(n => n.type === 'success').length}</div>
                <div className="text-sm text-muted-foreground">Success</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="notifications" className="space-y-4">
        <TabsList>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
        </TabsList>

        <TabsContent value="notifications" className="space-y-4">
          <div className="flex items-center gap-4">
            <Input placeholder="Search notifications..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="max-w-sm" />
            <div className="flex gap-1">
              {['all', 'unread', 'success', 'warning', 'error', 'info'].map((f) => (
                <Button key={f} variant={filter === f ? 'default' : 'outline'} size="sm" onClick={() => setFilter(f)} className="capitalize">{f}</Button>
              ))}
            </div>
          </div>

          <Card>
            <ScrollArea className="h-[500px]">
              <div className="divide-y">
                {filteredNotifications.map((notification) => (
                  <div key={notification.id} className={`p-4 hover:bg-muted/50 transition-colors ${!notification.read ? 'bg-primary/5' : ''}`}>
                    <div className="flex items-start gap-4">
                      <div className="mt-1">{getTypeIcon(notification.type)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className={`font-medium ${!notification.read ? 'text-foreground' : 'text-muted-foreground'}`}>{notification.title}</h4>
                          {!notification.read && <div className="w-2 h-2 bg-primary rounded-full" />}
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">{notification.message}</p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">{getCategoryIcon(notification.category)}{notification.category}</span>
                          <span>{notification.timestamp}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {notification.actionUrl && <Button variant="outline" size="sm">View</Button>}
                        <Button variant="ghost" size="icon"><Check className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
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
              <div className="space-y-6">
                <div className="grid grid-cols-4 gap-4 pb-2 border-b font-medium text-sm">
                  <div>Category</div>
                  <div className="flex items-center gap-2"><Mail className="h-4 w-4" />Email</div>
                  <div className="flex items-center gap-2"><Smartphone className="h-4 w-4" />Push</div>
                  <div className="flex items-center gap-2"><Monitor className="h-4 w-4" />In-App</div>
                </div>
                {preferences.map((pref, index) => (
                  <div key={index} className="grid grid-cols-4 gap-4 items-center">
                    <div className="font-medium">{pref.category}</div>
                    <div><Switch checked={pref.email} /></div>
                    <div><Switch checked={pref.push} /></div>
                    <div><Switch checked={pref.inApp} /></div>
                  </div>
                ))}
              </div>
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
                  <div className="text-sm text-muted-foreground">No push notifications from 10:00 PM to 7:00 AM</div>
                </div>
                <Switch />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

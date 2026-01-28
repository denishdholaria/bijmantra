/**
 * Activity Timeline Page
 * Track all changes and activities - Connected to /api/v2/activity
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Clock,
  Search,
  Filter,
  Calendar,
  User,
  Leaf,
  FlaskConical,
  Database,
  Upload,
  Download,
  Edit,
  Trash2,
  Plus,
  Eye,
  Loader2,
  RefreshCw
} from 'lucide-react'

interface ActivityItem {
  id: string
  type: 'create' | 'update' | 'delete' | 'import' | 'export' | 'view'
  entity: string
  entity_id: string
  entity_name: string
  user: string
  user_id: string
  timestamp: string
  details?: string
}

// API functions
async function fetchActivities(params: { type?: string; entity?: string; search?: string }): Promise<{ data: ActivityItem[]; total: number }> {
  const searchParams = new URLSearchParams()
  if (params.type && params.type !== 'all') searchParams.append('type', params.type)
  if (params.entity && params.entity !== 'all') searchParams.append('entity', params.entity)
  if (params.search) searchParams.append('search', params.search)
  searchParams.append('limit', '50')
  
  const response = await fetch(`/api/v2/activity?${searchParams}`)
  if (!response.ok) throw new Error('Failed to fetch activities')
  return response.json()
}

async function fetchActivityStats(): Promise<{ data: { total: number; creates: number; updates: number; imports: number; exports: number } }> {
  const response = await fetch('/api/v2/activity/stats?days=7')
  if (!response.ok) throw new Error('Failed to fetch stats')
  return response.json()
}

export function ActivityTimeline() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [filterEntity, setFilterEntity] = useState('all')

  const { data: activitiesData, isLoading, error, refetch } = useQuery({
    queryKey: ['activities', filterType, filterEntity, searchQuery],
    queryFn: () => fetchActivities({ type: filterType, entity: filterEntity, search: searchQuery }),
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['activity-stats'],
    queryFn: fetchActivityStats,
    refetchInterval: 60000,
  })

  const activities = activitiesData?.data || []
  const stats = statsData?.data || { total: 0, creates: 0, updates: 0, imports: 0, exports: 0 }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'create': return <Plus className="h-4 w-4 text-green-500" />
      case 'update': return <Edit className="h-4 w-4 text-blue-500" />
      case 'delete': return <Trash2 className="h-4 w-4 text-red-500" />
      case 'import': return <Upload className="h-4 w-4 text-purple-500" />
      case 'export': return <Download className="h-4 w-4 text-orange-500" />
      case 'view': return <Eye className="h-4 w-4 text-gray-500" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  const getEntityIcon = (entity: string) => {
    switch (entity.toLowerCase()) {
      case 'germplasm': return <Leaf className="h-4 w-4" />
      case 'trial': case 'study': return <FlaskConical className="h-4 w-4" />
      default: return <Database className="h-4 w-4" />
    }
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Clock className="h-8 w-8 text-primary" />
            Activity Timeline
          </h1>
          <p className="text-muted-foreground mt-1">Track all changes and activities in your breeding program</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Log
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Calendar className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                {statsLoading ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <div className="text-2xl font-bold">{stats.total}</div>
                )}
                <div className="text-sm text-muted-foreground">This Week</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Plus className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                {statsLoading ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <div className="text-2xl font-bold">{stats.creates}</div>
                )}
                <div className="text-sm text-muted-foreground">New Records</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Edit className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                {statsLoading ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <div className="text-2xl font-bold">{stats.updates}</div>
                )}
                <div className="text-sm text-muted-foreground">Updates</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <Upload className="h-5 w-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                {statsLoading ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <div className="text-2xl font-bold">{stats.imports}</div>
                )}
                <div className="text-sm text-muted-foreground">Imports</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search activities..." 
                value={searchQuery} 
                onChange={(e) => setSearchQuery(e.target.value)} 
                className="pl-10" 
              />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[150px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Action" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                <SelectItem value="create">Created</SelectItem>
                <SelectItem value="update">Updated</SelectItem>
                <SelectItem value="delete">Deleted</SelectItem>
                <SelectItem value="import">Imported</SelectItem>
                <SelectItem value="export">Exported</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterEntity} onValueChange={setFilterEntity}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Entity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Entities</SelectItem>
                <SelectItem value="germplasm">Germplasm</SelectItem>
                <SelectItem value="trial">Trials</SelectItem>
                <SelectItem value="study">Studies</SelectItem>
                <SelectItem value="observation">Observations</SelectItem>
                <SelectItem value="cross">Crosses</SelectItem>
                <SelectItem value="sample">Samples</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            {isLoading ? 'Loading...' : `Showing ${activities.length} activities`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="flex gap-4 pl-12">
                  <Skeleton className="h-20 flex-1" />
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Failed to load activities</p>
              <Button variant="outline" className="mt-4" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          ) : activities.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No activities found</p>
            </div>
          ) : (
            <ScrollArea className="h-[500px]">
              <div className="relative">
                <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />
                <div className="space-y-6">
                  {activities.map((activity) => (
                    <div key={activity.id} className="relative flex gap-4 pl-12">
                      <div className="absolute left-4 w-5 h-5 rounded-full bg-background border-2 border-primary flex items-center justify-center">
                        {getTypeIcon(activity.type)}
                      </div>
                      <div className="flex-1 p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline" className="capitalize">{activity.type}</Badge>
                              <span className="flex items-center gap-1 text-sm text-muted-foreground">
                                {getEntityIcon(activity.entity)}
                                {activity.entity}
                              </span>
                            </div>
                            <h4 className="font-medium">{activity.entity_name}</h4>
                            {activity.details && (
                              <p className="text-sm text-muted-foreground mt-1">{activity.details}</p>
                            )}
                          </div>
                          <div className="text-right text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {activity.user}
                            </div>
                            <div className="flex items-center gap-1 mt-1">
                              <Clock className="h-3 w-3" />
                              {formatTime(activity.timestamp)}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

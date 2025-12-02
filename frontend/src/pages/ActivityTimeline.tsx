import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
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
  CheckCircle2,
  AlertCircle
} from 'lucide-react'

interface ActivityItem {
  id: string
  type: 'create' | 'update' | 'delete' | 'import' | 'export' | 'view'
  entity: string
  entityId: string
  entityName: string
  user: string
  timestamp: string
  details?: string
}

export function ActivityTimeline() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [filterEntity, setFilterEntity] = useState('all')

  const activities: ActivityItem[] = [
    { id: '1', type: 'create', entity: 'Germplasm', entityId: 'GERM-2025-001', entityName: 'BM-Gold-2025', user: 'Dr. Sarah Johnson', timestamp: '10 minutes ago', details: 'New elite line registered' },
    { id: '2', type: 'update', entity: 'Trial', entityId: 'TRIAL-2025-047', entityName: 'Yield Trial Spring 2025', user: 'John Smith', timestamp: '25 minutes ago', details: 'Status changed to Active' },
    { id: '3', type: 'import', entity: 'Observations', entityId: 'BATCH-001', entityName: '1,247 observations', user: 'Maria Garcia', timestamp: '1 hour ago', details: 'Field data from mobile devices' },
    { id: '4', type: 'create', entity: 'Cross', entityId: 'CROSS-2025-089', entityName: 'IR64 × FR13A', user: 'Dr. Raj Patel', timestamp: '2 hours ago', details: 'Submergence tolerance cross' },
    { id: '5', type: 'export', entity: 'Report', entityId: 'RPT-2025-012', entityName: 'Monthly Progress Report', user: 'Admin', timestamp: '3 hours ago', details: 'PDF export completed' },
    { id: '6', type: 'update', entity: 'Germplasm', entityId: 'GERM-2024-456', entityName: 'Swarna-Sub1', user: 'Dr. Sarah Johnson', timestamp: '4 hours ago', details: 'Pedigree information updated' },
    { id: '7', type: 'delete', entity: 'Observation', entityId: 'OBS-2025-789', entityName: 'Duplicate entry', user: 'John Smith', timestamp: '5 hours ago', details: 'Removed duplicate record' },
    { id: '8', type: 'view', entity: 'Trial', entityId: 'TRIAL-2024-089', entityName: 'Disease Screening 2024', user: 'Guest User', timestamp: '6 hours ago' },
    { id: '9', type: 'create', entity: 'Location', entityId: 'LOC-2025-003', entityName: 'North Field Block C', user: 'Admin', timestamp: '1 day ago', details: 'New trial location added' },
    { id: '10', type: 'import', entity: 'Germplasm', entityId: 'BATCH-002', entityName: '234 accessions', user: 'Dr. Raj Patel', timestamp: '1 day ago', details: 'Genebank import' }
  ]

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
      case 'trial': return <FlaskConical className="h-4 w-4" />
      case 'observations': case 'observation': return <Database className="h-4 w-4" />
      default: return <Database className="h-4 w-4" />
    }
  }

  const filteredActivities = activities.filter(a => {
    const matchesSearch = a.entityName.toLowerCase().includes(searchQuery.toLowerCase()) || a.user.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || a.type === filterType
    const matchesEntity = filterEntity === 'all' || a.entity.toLowerCase() === filterEntity.toLowerCase()
    return matchesSearch && matchesType && matchesEntity
  })

  const activityStats = {
    today: activities.filter(a => a.timestamp.includes('hour') || a.timestamp.includes('minute')).length,
    creates: activities.filter(a => a.type === 'create').length,
    updates: activities.filter(a => a.type === 'update').length,
    imports: activities.filter(a => a.type === 'import').length
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
        <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Log</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Calendar className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{activityStats.today}</div>
                <div className="text-sm text-muted-foreground">Today's Activities</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><Plus className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{activityStats.creates}</div>
                <div className="text-sm text-muted-foreground">New Records</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Edit className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">{activityStats.updates}</div>
                <div className="text-sm text-muted-foreground">Updates</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg"><Upload className="h-5 w-5 text-orange-600" /></div>
              <div>
                <div className="text-2xl font-bold">{activityStats.imports}</div>
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
              <Input placeholder="Search activities..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[150px]"><Filter className="h-4 w-4 mr-2" /><SelectValue placeholder="Action" /></SelectTrigger>
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
              <SelectTrigger className="w-[150px]"><SelectValue placeholder="Entity" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Entities</SelectItem>
                <SelectItem value="germplasm">Germplasm</SelectItem>
                <SelectItem value="trial">Trials</SelectItem>
                <SelectItem value="observations">Observations</SelectItem>
                <SelectItem value="cross">Crosses</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Showing {filteredActivities.length} activities</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="relative">
              <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />
              <div className="space-y-6">
                {filteredActivities.map((activity) => (
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
                          <h4 className="font-medium">{activity.entityName}</h4>
                          {activity.details && <p className="text-sm text-muted-foreground mt-1">{activity.details}</p>}
                        </div>
                        <div className="text-right text-sm text-muted-foreground">
                          <div className="flex items-center gap-1"><User className="h-3 w-3" />{activity.user}</div>
                          <div className="flex items-center gap-1 mt-1"><Clock className="h-3 w-3" />{activity.timestamp}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

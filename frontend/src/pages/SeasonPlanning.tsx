import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Calendar,
  Sun,
  Cloud,
  Droplets,
  Leaf,
  Target,
  Plus,
  Settings,
  Download,
  ChevronRight
} from 'lucide-react'

interface SeasonActivity {
  id: string
  name: string
  startWeek: number
  duration: number
  type: 'planting' | 'management' | 'harvest' | 'evaluation'
  status: 'planned' | 'active' | 'completed'
}

export function SeasonPlanning() {
  const [selectedSeason, setSelectedSeason] = useState('2025-wet')

  const activities: SeasonActivity[] = [
    { id: '1', name: 'Land Preparation', startWeek: 1, duration: 2, type: 'management', status: 'completed' },
    { id: '2', name: 'Nursery Sowing', startWeek: 2, duration: 3, type: 'planting', status: 'completed' },
    { id: '3', name: 'Transplanting', startWeek: 5, duration: 2, type: 'planting', status: 'active' },
    { id: '4', name: 'Fertilizer Application', startWeek: 7, duration: 1, type: 'management', status: 'planned' },
    { id: '5', name: 'Disease Scoring', startWeek: 10, duration: 2, type: 'evaluation', status: 'planned' },
    { id: '6', name: 'Flowering Observation', startWeek: 12, duration: 2, type: 'evaluation', status: 'planned' },
    { id: '7', name: 'Harvest', startWeek: 18, duration: 3, type: 'harvest', status: 'planned' },
    { id: '8', name: 'Data Analysis', startWeek: 21, duration: 2, type: 'evaluation', status: 'planned' }
  ]

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'planting': return 'bg-green-500'
      case 'management': return 'bg-blue-500'
      case 'harvest': return 'bg-yellow-500'
      case 'evaluation': return 'bg-purple-500'
      default: return 'bg-gray-500'
    }
  }

  const weeks = Array.from({ length: 24 }, (_, i) => i + 1)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Calendar className="h-8 w-8 text-primary" />
            Season Planning
          </h1>
          <p className="text-muted-foreground mt-1">Plan and track seasonal breeding activities</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedSeason} onValueChange={setSelectedSeason}>
            <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="2025-wet">2025 Wet Season</SelectItem>
              <SelectItem value="2025-dry">2025 Dry Season</SelectItem>
              <SelectItem value="2024-wet">2024 Wet Season</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
          <Button><Plus className="h-4 w-4 mr-2" />Add Activity</Button>
        </div>
      </div>

      {/* Season Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><Leaf className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">256</div>
                <div className="text-sm text-muted-foreground">Entries Planned</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Target className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">4</div>
                <div className="text-sm text-muted-foreground">Trials</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Calendar className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">Week 5</div>
                <div className="text-sm text-muted-foreground">Current Week</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Sun className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">24</div>
                <div className="text-sm text-muted-foreground">Season Length (wks)</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gantt Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Season Timeline</CardTitle>
          <CardDescription>Activity schedule for the season</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <div className="min-w-[1200px]">
              {/* Week headers */}
              <div className="flex border-b pb-2 mb-4">
                <div className="w-48 flex-shrink-0 font-medium">Activity</div>
                <div className="flex-1 flex">
                  {weeks.map(week => (
                    <div key={week} className={`flex-1 text-center text-xs ${week === 5 ? 'font-bold text-primary' : 'text-muted-foreground'}`}>
                      W{week}
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Activities */}
              {activities.map(activity => (
                <div key={activity.id} className="flex items-center mb-2">
                  <div className="w-48 flex-shrink-0 flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${getTypeColor(activity.type)}`} />
                    <span className="text-sm truncate">{activity.name}</span>
                  </div>
                  <div className="flex-1 flex h-8 relative">
                    <div
                      className={`absolute h-6 rounded ${getTypeColor(activity.type)} ${activity.status === 'completed' ? 'opacity-50' : activity.status === 'active' ? 'ring-2 ring-primary' : ''}`}
                      style={{
                        left: `${((activity.startWeek - 1) / 24) * 100}%`,
                        width: `${(activity.duration / 24) * 100}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Legend */}
          <div className="flex items-center gap-6 mt-6 pt-4 border-t">
            <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-green-500" /><span className="text-sm">Planting</span></div>
            <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-blue-500" /><span className="text-sm">Management</span></div>
            <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-yellow-500" /><span className="text-sm">Harvest</span></div>
            <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-purple-500" /><span className="text-sm">Evaluation</span></div>
          </div>
        </CardContent>
      </Card>

      {/* Activity List */}
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Activities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {activities.filter(a => a.status !== 'completed').map(activity => (
              <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${getTypeColor(activity.type)}`} />
                  <div>
                    <div className="font-medium">{activity.name}</div>
                    <div className="text-sm text-muted-foreground">Week {activity.startWeek} - {activity.startWeek + activity.duration - 1}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={activity.status === 'active' ? 'default' : 'secondary'} className="capitalize">{activity.status}</Badge>
                  <Button variant="ghost" size="icon"><ChevronRight className="h-4 w-4" /></Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

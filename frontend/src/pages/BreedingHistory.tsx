import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import {
  History,
  Search,
  Calendar,
  Leaf,
  GitBranch,
  Award,
  TrendingUp,
  Filter,
  Download,
  AlertCircle
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface HistoryEvent {
  id: string
  year: number
  type: 'cross' | 'selection' | 'release' | 'milestone'
  title: string
  description: string
  germplasm?: string
}

export function BreedingHistory() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedYear, setSelectedYear] = useState<number | null>(null)

  // Fetch breeding events from database
  const { data: eventsData, isLoading, error } = useQuery({
    queryKey: ['breeding-history-events'],
    queryFn: () => apiClient.get<{ data: any[] }>('/api/v2/events/history'),
  })

  // Map API events to the HistoryEvent shape
  const events: HistoryEvent[] = (eventsData?.data || []).map((e: any) => ({
    id: String(e.id || e.event_id || ''),
    year: e.year || new Date(e.event_date || e.created_at || '').getFullYear() || 2025,
    type: (e.event_type || e.type || 'milestone') as HistoryEvent['type'],
    title: e.title || e.name || e.event_name || '',
    description: e.description || e.summary || '',
    germplasm: e.germplasm_name || e.germplasm || undefined,
  }))

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'cross': return <GitBranch className="h-5 w-5 text-blue-500" />
      case 'selection': return <TrendingUp className="h-5 w-5 text-green-500" />
      case 'release': return <Award className="h-5 w-5 text-yellow-500" />
      case 'milestone': return <Calendar className="h-5 w-5 text-purple-500" />
      default: return <History className="h-5 w-5" />
    }
  }

  const years = [...new Set(events.map(e => e.year))].sort((a, b) => b - a)
  const filteredEvents = events.filter(e => {
    const matchesSearch = e.title.toLowerCase().includes(searchQuery.toLowerCase()) || e.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesYear = !selectedYear || e.year === selectedYear
    return matchesSearch && matchesYear
  })

  const stats = {
    totalYears: years.length,
    releases: events.filter(e => e.type === 'release').length,
    crosses: events.filter(e => e.type === 'cross').length,
    milestones: events.filter(e => e.type === 'milestone').length
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <History className="h-8 w-8 text-primary" />
            Breeding History
          </h1>
          <p className="text-muted-foreground mt-1">Chronicle of breeding program achievements</p>
        </div>
        <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Timeline</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Calendar className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.totalYears}</div>
                <div className="text-sm text-muted-foreground">Years Active</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Award className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.releases}</div>
                <div className="text-sm text-muted-foreground">Varieties Released</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><GitBranch className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.crosses}</div>
                <div className="text-sm text-muted-foreground">Crossing Cycles</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><TrendingUp className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.milestones}</div>
                <div className="text-sm text-muted-foreground">Milestones</div>
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
              <Input placeholder="Search history..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
            </div>
            <div className="flex gap-2">
              <Button variant={!selectedYear ? 'default' : 'outline'} size="sm" onClick={() => setSelectedYear(null)}>All</Button>
              {years.map(year => (
                <Button key={year} variant={selectedYear === year ? 'default' : 'outline'} size="sm" onClick={() => setSelectedYear(year)}>{year}</Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Program Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array(4).fill(0).map((_, i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No breeding events found</h3>
              <p className="text-muted-foreground">
                {events.length === 0
                  ? 'Record breeding events (crosses, selections, releases) to build your program timeline.'
                  : 'No events match your current search/filter criteria.'}
              </p>
            </div>
          ) : (
          <ScrollArea className="h-[500px]">
            <div className="relative">
              <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />
              <div className="space-y-6">
                {filteredEvents.map((event) => (
                  <div key={event.id} className="relative flex gap-4 pl-12">
                    <div className="absolute left-4 w-5 h-5 rounded-full bg-background border-2 border-primary flex items-center justify-center">
                      {getTypeIcon(event.type)}
                    </div>
                    <div className="flex-1 p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{event.year}</Badge>
                            <Badge variant="secondary" className="capitalize">{event.type}</Badge>
                          </div>
                          <h4 className="font-semibold mt-2">{event.title}</h4>
                        </div>
                        {event.germplasm && (
                          <Badge variant="outline" className="flex items-center gap-1">
                            <Leaf className="h-3 w-3" />{event.germplasm}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{event.description}</p>
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

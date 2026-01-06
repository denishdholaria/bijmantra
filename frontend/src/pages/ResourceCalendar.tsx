import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { 
  Calendar, ChevronLeft, ChevronRight, Plus, 
  Users, Truck, Beaker, MapPin, Clock, Filter, RefreshCw
} from 'lucide-react'

interface CalendarEvent {
  id: string
  title: string
  type: 'field' | 'lab' | 'equipment' | 'meeting'
  date: string
  time: string
  duration: string
  location: string
  assignee: string
  status: 'scheduled' | 'in-progress' | 'completed' | 'cancelled'
  description?: string
}

export function ResourceCalendar() {
  const queryClient = useQueryClient()
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [viewType, setViewType] = useState('month')
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newEvent, setNewEvent] = useState({
    title: '',
    type: 'meeting',
    date: new Date().toISOString().split('T')[0],
    time: '09:00',
    duration: '1h',
    location: '',
    assignee: '',
  })

  // Fetch calendar events
  const { data: events = [], isLoading, refetch } = useQuery({
    queryKey: ['calendar-events'],
    queryFn: () => apiClient.getCalendarEvents(),
  })

  // Fetch calendar summary
  const { data: summary } = useQuery({
    queryKey: ['calendar-summary'],
    queryFn: () => apiClient.getCalendarSummary(),
  })

  // Create event mutation
  const createMutation = useMutation({
    mutationFn: (event: typeof newEvent) => apiClient.createCalendarEvent(event),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-summary'] })
      setIsCreateOpen(false)
      setNewEvent({
        title: '',
        type: 'meeting',
        date: new Date().toISOString().split('T')[0],
        time: '09:00',
        duration: '1h',
        location: '',
        assignee: '',
      })
      toast.success('Event created successfully')
    },
    onError: () => {
      toast.error('Failed to create event')
    },
  })

  const resources = [
    { type: 'field', name: 'Field Operations', count: summary?.by_type?.field || 0, icon: MapPin, color: 'bg-green-100 text-green-800' },
    { type: 'lab', name: 'Lab Activities', count: summary?.by_type?.lab || 0, icon: Beaker, color: 'bg-blue-100 text-blue-800' },
    { type: 'equipment', name: 'Equipment', count: summary?.by_type?.equipment || 0, icon: Truck, color: 'bg-orange-100 text-orange-800' },
    { type: 'meeting', name: 'Meetings', count: summary?.by_type?.meeting || 0, icon: Users, color: 'bg-purple-100 text-purple-800' },
  ]

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1).getDay()
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    return { firstDay, daysInMonth }
  }

  const { firstDay, daysInMonth } = getDaysInMonth(currentMonth)
  const monthName = currentMonth.toLocaleString('default', { month: 'long', year: 'numeric' })

  const getEventsForDay = (day: number) => {
    const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    return events.filter((e: CalendarEvent) => e.date === dateStr)
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = { 
      field: 'bg-green-500', 
      lab: 'bg-blue-500', 
      equipment: 'bg-orange-500', 
      meeting: 'bg-purple-500' 
    }
    return colors[type] || 'bg-gray-500'
  }

  const getTypeIcon = (type: string) => {
    const icons: Record<string, any> = {
      field: MapPin,
      lab: Beaker,
      equipment: Truck,
      meeting: Users,
    }
    return icons[type] || Calendar
  }

  const handlePrevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))
  }

  const handleNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))
  }

  const handleCreateEvent = () => {
    if (!newEvent.title.trim()) {
      toast.error('Please enter an event title')
      return
    }
    createMutation.mutate(newEvent)
  }

  // Get upcoming events (next 7 days)
  const today = new Date().toISOString().split('T')[0]
  const upcomingEvents = events
    .filter((e: CalendarEvent) => e.date >= today && e.status === 'scheduled')
    .slice(0, 5)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Resource Calendar</h1>
          <p className="text-muted-foreground">Schedule and manage field operations, lab work, and equipment</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />Refresh
          </Button>
          <Button variant="outline"><Filter className="mr-2 h-4 w-4" />Filter</Button>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="mr-2 h-4 w-4" />New Event</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Event</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Title</Label>
                  <Input 
                    value={newEvent.title} 
                    onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                    placeholder="Event title"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Type</Label>
                    <Select value={newEvent.type} onValueChange={(v) => setNewEvent({ ...newEvent, type: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="field">Field</SelectItem>
                        <SelectItem value="lab">Lab</SelectItem>
                        <SelectItem value="equipment">Equipment</SelectItem>
                        <SelectItem value="meeting">Meeting</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Date</Label>
                    <Input 
                      type="date" 
                      value={newEvent.date} 
                      onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Time</Label>
                    <Input 
                      type="time" 
                      value={newEvent.time} 
                      onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Duration</Label>
                    <Select value={newEvent.duration} onValueChange={(v) => setNewEvent({ ...newEvent, duration: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="30m">30 minutes</SelectItem>
                        <SelectItem value="1h">1 hour</SelectItem>
                        <SelectItem value="2h">2 hours</SelectItem>
                        <SelectItem value="4h">4 hours</SelectItem>
                        <SelectItem value="8h">Full day</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Location</Label>
                  <Input 
                    value={newEvent.location} 
                    onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                    placeholder="Location"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Assignee</Label>
                  <Input 
                    value={newEvent.assignee} 
                    onChange={(e) => setNewEvent({ ...newEvent, assignee: e.target.value })}
                    placeholder="Assigned to"
                  />
                </div>
                <Button onClick={handleCreateEvent} className="w-full" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Event'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Resource Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        {resources.map((res) => (
          <Card key={res.type}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${res.color}`}>
                  <res.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium">{res.name}</p>
                  <p className="text-sm text-muted-foreground">{res.count} scheduled</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Calendar Grid */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button variant="outline" size="icon" onClick={handlePrevMonth}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <CardTitle>{monthName}</CardTitle>
                <Button variant="outline" size="icon" onClick={handleNextMonth}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <Select value={viewType} onValueChange={setViewType}>
                <SelectTrigger className="w-[120px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="month">Month</SelectItem>
                  <SelectItem value="week">Week</SelectItem>
                  <SelectItem value="day">Day</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[400px] w-full" />
            ) : (
              <div className="grid grid-cols-7 gap-1">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="p-2 text-center text-sm font-medium text-muted-foreground">{day}</div>
                ))}
                {Array.from({ length: firstDay }).map((_, i) => (
                  <div key={`empty-${i}`} className="p-2" />
                ))}
                {Array.from({ length: daysInMonth }).map((_, i) => {
                  const day = i + 1
                  const dayEvents = getEventsForDay(day)
                  const isToday = new Date().getDate() === day && new Date().getMonth() === currentMonth.getMonth()
                  return (
                    <div 
                      key={day} 
                      className={`p-2 min-h-[80px] border rounded-lg cursor-pointer hover:bg-accent ${isToday ? 'bg-primary/10 border-primary' : ''}`} 
                      onClick={() => setSelectedDate(`${currentMonth.getFullYear()}-${currentMonth.getMonth() + 1}-${day}`)}
                    >
                      <p className={`text-sm font-medium ${isToday ? 'text-primary' : ''}`}>{day}</p>
                      <div className="mt-1 space-y-1">
                        {dayEvents.slice(0, 2).map((event: CalendarEvent) => (
                          <div 
                            key={event.id} 
                            className={`h-1.5 rounded-full ${getTypeColor(event.type)}`} 
                            title={event.title} 
                          />
                        ))}
                        {dayEvents.length > 2 && (
                          <p className="text-xs text-muted-foreground">+{dayEvents.length - 2} more</p>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upcoming Events */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Events</CardTitle>
            <CardDescription>Next 7 days • {summary?.next_7_days || 0} events</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </div>
            ) : upcomingEvents.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No upcoming events</p>
            ) : (
              <div className="space-y-4">
                {upcomingEvents.map((event: CalendarEvent) => {
                  const TypeIcon = getTypeIcon(event.type)
                  return (
                    <div key={event.id} className="flex items-start gap-3 p-3 border rounded-lg">
                      <div className={`w-1 h-full rounded-full ${getTypeColor(event.type)}`} />
                      <div className="flex-1">
                        <p className="font-medium text-sm">{event.title}</p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{event.date} at {event.time}</span>
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <MapPin className="h-3 w-3" />
                          <span>{event.location}</span>
                        </div>
                        <div className="flex items-center justify-between mt-2">
                          <Badge variant="outline" className="text-xs">{event.assignee}</Badge>
                          <Badge variant="secondary" className="text-xs">{event.duration}</Badge>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

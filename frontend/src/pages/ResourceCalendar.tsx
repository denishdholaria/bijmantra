import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Calendar, ChevronLeft, ChevronRight, Plus, 
  Users, Truck, Beaker, MapPin, Clock, Filter
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
  status: 'scheduled' | 'in-progress' | 'completed'
}

export function ResourceCalendar() {
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [viewType, setViewType] = useState('month')
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  const events: CalendarEvent[] = [
    { id: '1', title: 'Field Planting - Block A', type: 'field', date: '2025-12-02', time: '06:00', duration: '4h', location: 'Field Station 1', assignee: 'Maria Garcia', status: 'scheduled' },
    { id: '2', title: 'DNA Extraction', type: 'lab', date: '2025-12-02', time: '09:00', duration: '3h', location: 'Molecular Lab', assignee: 'Dr. Sarah Chen', status: 'scheduled' },
    { id: '3', title: 'Tractor Maintenance', type: 'equipment', date: '2025-12-03', time: '08:00', duration: '2h', location: 'Equipment Shed', assignee: 'John Smith', status: 'scheduled' },
    { id: '4', title: 'Breeding Team Meeting', type: 'meeting', date: '2025-12-03', time: '14:00', duration: '1h', location: 'Conference Room', assignee: 'All Team', status: 'scheduled' },
    { id: '5', title: 'Phenotyping - Height', type: 'field', date: '2025-12-04', time: '07:00', duration: '6h', location: 'Trial Block B', assignee: 'Raj Patel', status: 'scheduled' },
    { id: '6', title: 'PCR Analysis', type: 'lab', date: '2025-12-05', time: '10:00', duration: '4h', location: 'Molecular Lab', assignee: 'Aisha Okonkwo', status: 'scheduled' },
  ]

  const resources = [
    { type: 'field', name: 'Field Operations', count: 12, icon: MapPin, color: 'bg-green-100 text-green-800' },
    { type: 'lab', name: 'Lab Activities', count: 8, icon: Beaker, color: 'bg-blue-100 text-blue-800' },
    { type: 'equipment', name: 'Equipment', count: 5, icon: Truck, color: 'bg-orange-100 text-orange-800' },
    { type: 'meeting', name: 'Meetings', count: 4, icon: Users, color: 'bg-purple-100 text-purple-800' },
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
    return events.filter(e => e.date === dateStr)
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = { field: 'bg-green-500', lab: 'bg-blue-500', equipment: 'bg-orange-500', meeting: 'bg-purple-500' }
    return colors[type] || 'bg-gray-500'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Resource Calendar</h1>
          <p className="text-muted-foreground">Schedule and manage field operations, lab work, and equipment</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Filter className="mr-2 h-4 w-4" />Filter</Button>
          <Button><Plus className="mr-2 h-4 w-4" />New Event</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {resources.map((res) => (
          <Card key={res.type}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${res.color}`}><res.icon className="h-5 w-5" /></div>
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
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button variant="outline" size="icon" onClick={() => setCurrentMonth(new Date(currentMonth.setMonth(currentMonth.getMonth() - 1)))}><ChevronLeft className="h-4 w-4" /></Button>
                <CardTitle>{monthName}</CardTitle>
                <Button variant="outline" size="icon" onClick={() => setCurrentMonth(new Date(currentMonth.setMonth(currentMonth.getMonth() + 1)))}><ChevronRight className="h-4 w-4" /></Button>
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
            <div className="grid grid-cols-7 gap-1">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <div key={day} className="p-2 text-center text-sm font-medium text-muted-foreground">{day}</div>
              ))}
              {Array.from({ length: firstDay }).map((_, i) => (<div key={`empty-${i}`} className="p-2" />))}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                const day = i + 1
                const dayEvents = getEventsForDay(day)
                const isToday = new Date().getDate() === day && new Date().getMonth() === currentMonth.getMonth()
                return (
                  <div key={day} className={`p-2 min-h-[80px] border rounded-lg cursor-pointer hover:bg-accent ${isToday ? 'bg-primary/10 border-primary' : ''}`} onClick={() => setSelectedDate(`${currentMonth.getFullYear()}-${currentMonth.getMonth() + 1}-${day}`)}>
                    <p className={`text-sm font-medium ${isToday ? 'text-primary' : ''}`}>{day}</p>
                    <div className="mt-1 space-y-1">
                      {dayEvents.slice(0, 2).map(event => (
                        <div key={event.id} className={`h-1.5 rounded-full ${getTypeColor(event.type)}`} title={event.title} />
                      ))}
                      {dayEvents.length > 2 && <p className="text-xs text-muted-foreground">+{dayEvents.length - 2} more</p>}
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Upcoming Events</CardTitle><CardDescription>Next 7 days</CardDescription></CardHeader>
          <CardContent>
            <div className="space-y-4">
              {events.slice(0, 5).map((event) => (
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
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

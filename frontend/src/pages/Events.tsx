/**
 * Events Page - Field Events Management
 * BrAPI v2.1 Phenotyping Module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'

export function Events() {
  const [searchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [selectedStudy, setSelectedStudy] = useState(searchParams.get('studyDbId') || 'all')
  const [showCreate, setShowCreate] = useState(false)
  const [newEventType, setNewEventType] = useState('')
  const [newEventDate, setNewEventDate] = useState('')
  const [newEventDesc, setNewEventDesc] = useState('')
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data: studiesData } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.getStudies(0, 100),
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['events', selectedStudy, page],
    queryFn: () => apiClient.getEvents(selectedStudy === 'all' ? undefined : selectedStudy, page, pageSize),
  })

  const createMutation = useMutation({
    mutationFn: () => apiClient.createEvent({
      eventType: newEventType,
      date: newEventDate,
      eventDescription: newEventDesc || undefined,
      studyDbId: selectedStudy || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
      toast.success('Event created!')
      setShowCreate(false)
      setNewEventType('')
      setNewEventDate('')
      setNewEventDesc('')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed'),
  })

  const studies = studiesData?.result?.data || []
  const events = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  const eventTypeColors: Record<string, string> = {
    Planting: 'bg-green-100 text-green-800',
    Fertilization: 'bg-blue-100 text-blue-800',
    Irrigation: 'bg-cyan-100 text-cyan-800',
    Harvest: 'bg-orange-100 text-orange-800',
    Treatment: 'bg-purple-100 text-purple-800',
    Observation: 'bg-pink-100 text-pink-800',
  }

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Events</h1>
          <p className="text-muted-foreground mt-1">Field activities and treatments</p>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger asChild>
            <Button>📆 New Event</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Record New Event</DialogTitle>
              <DialogDescription>Log a field activity or treatment</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Event Type *</Label>
                <Select value={newEventType} onValueChange={setNewEventType}>
                  <SelectTrigger><SelectValue placeholder="Select type..." /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Planting">Planting</SelectItem>
                    <SelectItem value="Fertilization">Fertilization</SelectItem>
                    <SelectItem value="Irrigation">Irrigation</SelectItem>
                    <SelectItem value="Pesticide">Pesticide Application</SelectItem>
                    <SelectItem value="Harvest">Harvest</SelectItem>
                    <SelectItem value="Treatment">Treatment</SelectItem>
                    <SelectItem value="Observation">Observation</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="eventDate">Date *</Label>
                <Input id="eventDate" type="date" value={newEventDate} onChange={(e) => setNewEventDate(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="eventDesc">Description</Label>
                <Textarea id="eventDesc" value={newEventDesc} onChange={(e) => setNewEventDesc(e.target.value)} rows={2} placeholder="Details about the event..." />
              </div>
              <Button onClick={() => createMutation.mutate()} disabled={!newEventType || !newEventDate || createMutation.isPending} className="w-full">
                {createMutation.isPending ? 'Creating...' : '📆 Record Event'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Select value={selectedStudy} onValueChange={setSelectedStudy}>
                <SelectTrigger><SelectValue placeholder="Filter by study..." /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Studies</SelectItem>
                  {studies.map((s: any) => (
                    <SelectItem key={s.studyDbId} value={s.studyDbId}>{s.studyName}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Input placeholder="Search events..." className="flex-1" />
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{totalCount}</div>
            <div className="text-sm text-muted-foreground">Total Events</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">-</div>
            <div className="text-sm text-muted-foreground">This Month</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">-</div>
            <div className="text-sm text-muted-foreground">Treatments</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-orange-600">-</div>
            <div className="text-sm text-muted-foreground">Harvests</div>
          </CardContent>
        </Card>
      </div>

      {/* Events List */}
      <Card>
        <CardHeader>
          <CardTitle>Event Log</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Events</h3>
              <p className="text-muted-foreground">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
          ) : events.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📆</div>
              <h3 className="text-xl font-bold mb-2">No Events Yet</h3>
              <p className="text-muted-foreground mb-6">Record field activities and treatments</p>
              <Button onClick={() => setShowCreate(true)}>📆 Record First Event</Button>
            </div>
          ) : (
            <div className="divide-y">
              {events.map((event: any) => (
                <div key={event.eventDbId} className="p-4 hover:bg-muted/30 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl">📆</div>
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge className={eventTypeColors[event.eventType] || 'bg-gray-100 text-gray-800'}>
                          {event.eventType}
                        </Badge>
                        <span className="text-sm text-muted-foreground">{event.date?.split('T')[0] || '-'}</span>
                      </div>
                      {event.eventDescription && (
                        <p className="text-sm text-muted-foreground mt-1">{event.eventDescription}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {event.studyDbId || 'No study'}
                  </div>
                </div>
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="px-6 py-4 border-t flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Page {page + 1} of {totalPages}</div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>Previous</Button>
                <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}>Next</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

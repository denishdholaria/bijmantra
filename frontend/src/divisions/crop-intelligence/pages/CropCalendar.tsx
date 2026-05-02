/**
 * Crop Calendar Page
 * Manage crop phenology events and schedules
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, Calendar as CalendarIcon, RefreshCw, Trash2, Sprout } from 'lucide-react'

// Adjust interface based on BrAPI response structure if needed
// Assuming simplified response for now or extracting data from Result
interface CropCalendarEvent {
  id: number
  crop_name: string
  event_type: string
  event_date: string
  description: string
  created_at: string
}

export function CropCalendar() {
  const [showCreate, setShowCreate] = useState(false)
  const [newEvent, setNewEvent] = useState({
    crop_name: '',
    event_type: 'planting',
    event_date: new Date().toISOString().split('T')[0],
    description: '',
  })
  const queryClient = useQueryClient()

  // Note: Backend returns BrAPI formatted response
  const { data: responseData, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'crop-calendars'],
    queryFn: () => apiClient.get('/api/v2/future/crop-calendars'),
  })

  // Extract events from BrAPI response (result.data)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const events = (responseData as any)?.result?.data || []

  const createMutation = useMutation({
    mutationFn: (data: typeof newEvent) => apiClient.post('/api/v2/future/crop-calendars', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'crop-calendars'] })
      toast.success('Event scheduled')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create event'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/crop-calendars/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'crop-calendars'] })
      toast.success('Event deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <CalendarIcon className="h-8 w-8 text-blue-600" />
            Crop Calendar
          </h1>
          <p className="text-muted-foreground mt-1">
            Schedule and track key crop phenology events
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />Schedule Event
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New Calendar Event</DialogTitle>
                <DialogDescription>Record planting, harvesting, or other crop events</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                    <Label>Crop Name</Label>
                    <Input
                      value={newEvent.crop_name}
                      onChange={(e) => setNewEvent((p) => ({ ...p, crop_name: e.target.value }))}
                      placeholder="e.g. Wheat, Corn"
                    />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Event Type</Label>
                    <Select value={newEvent.event_type} onValueChange={(v) => setNewEvent(p => ({...p, event_type: v}))}>
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="planting">Planting</SelectItem>
                            <SelectItem value="emergence">Emergence</SelectItem>
                            <SelectItem value="flowering">Flowering</SelectItem>
                            <SelectItem value="harvest">Harvest</SelectItem>
                            <SelectItem value="tillage">Tillage</SelectItem>
                        </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Date</Label>
                    <Input
                      type="date"
                      value={newEvent.event_date}
                      onChange={(e) => setNewEvent((p) => ({ ...p, event_date: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                    <Label>Description</Label>
                    <Input
                      value={newEvent.description}
                      onChange={(e) => setNewEvent((p) => ({ ...p, description: e.target.value }))}
                      placeholder="Optional notes"
                    />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newEvent)}
                  className="bg-blue-600 hover:bg-blue-700"
                  disabled={!newEvent.crop_name || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Saving...' : 'Save Event'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load calendar events.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      )}

      {/* Data Table */}
      {!isLoading && !error && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Crop</TableHead>
                  <TableHead>Event Type</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(events) && events.length > 0 ? (
                  events.map((event: CropCalendarEvent) => (
                    <TableRow key={event.id}>
                      <TableCell className="font-medium flex items-center gap-2">
                        <Sprout className="h-4 w-4 text-green-500" />
                        {event.crop_name}
                      </TableCell>
                      <TableCell className="capitalize">{event.event_type}</TableCell>
                      <TableCell>{formatDate(event.event_date)}</TableCell>
                      <TableCell className="text-muted-foreground">{event.description || '—'}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete event"
                          onClick={() => deleteMutation.mutate(event.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-12">
                      <CalendarIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No events scheduled</p>
                      <Button className="mt-4" onClick={() => setShowCreate(true)}>
                        <Plus className="h-4 w-4 mr-2" />Add First Event
                      </Button>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

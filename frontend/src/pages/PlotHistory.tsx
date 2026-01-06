/**
 * Plot History Page
 * View historical data for each plot - Connected to backend API
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { History, Search, Calendar, Leaf, Droplets, TrendingUp, Plus, Loader2, AlertCircle, MapPin, Activity } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'

interface PlotEvent {
  id: string
  plot_id: string
  date: string
  type: string
  description: string
  value?: string
  notes?: string
  recorded_by?: string
}

interface Plot {
  id: string
  name: string
  field_id: string
  field_name: string
  current_crop: string
  planting_date: string
  expected_harvest: string
  status: string
  event_count: number
  events?: PlotEvent[]
}

interface EventType {
  id: string
  name: string
  description: string
  color: string
}

export function PlotHistory() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedField, setSelectedField] = useState<string>('all')
  const [selectedPlotId, setSelectedPlotId] = useState<string | null>(null)
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['plot-history-stats', selectedField],
    queryFn: () => apiClient.getPlotHistoryStats(selectedField !== 'all' ? selectedField : undefined),
  })

  // Fetch event types
  const { data: eventTypesData } = useQuery({
    queryKey: ['plot-history-event-types'],
    queryFn: () => apiClient.getPlotHistoryEventTypes(),
  })

  // Fetch fields
  const { data: fieldsData } = useQuery({
    queryKey: ['plot-history-fields'],
    queryFn: () => apiClient.getPlotHistoryFields(),
  })

  // Fetch plots
  const { data: plotsData, isLoading: plotsLoading } = useQuery({
    queryKey: ['plot-history-plots', selectedField, searchQuery],
    queryFn: () => apiClient.getPlotHistoryPlots({
      field_id: selectedField !== 'all' ? selectedField : undefined,
      search: searchQuery || undefined,
      limit: 100,
    }),
  })

  // Fetch selected plot details
  const { data: selectedPlot, isLoading: plotLoading } = useQuery({
    queryKey: ['plot-history-plot', selectedPlotId],
    queryFn: () => selectedPlotId ? apiClient.getPlotHistoryPlot(selectedPlotId) : null,
    enabled: !!selectedPlotId,
  })

  // Create event mutation
  const createEventMutation = useMutation({
    mutationFn: ({ plotId, data }: { plotId: string; data: Parameters<typeof apiClient.createPlotHistoryEvent>[1] }) =>
      apiClient.createPlotHistoryEvent(plotId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plot-history-plot', selectedPlotId] })
      queryClient.invalidateQueries({ queryKey: ['plot-history-plots'] })
      queryClient.invalidateQueries({ queryKey: ['plot-history-stats'] })
      setIsCreateOpen(false)
      toast.success('Event recorded')
    },
    onError: () => toast.error('Failed to record event'),
  })

  const eventTypes = eventTypesData?.types || []
  const fields = fieldsData?.fields || []
  const plots = plotsData?.plots || []

  const getEventIcon = (type: string) => {
    const icons: Record<string, any> = {
      planting: Leaf,
      observation: TrendingUp,
      treatment: Droplets,
      harvest: Calendar,
      maintenance: Activity,
      sampling: MapPin,
    }
    const Icon = icons[type] || History
    return <Icon className="h-4 w-4" />
  }

  const getEventColor = (type: string) => {
    const colors: Record<string, string> = {
      planting: 'bg-green-100 text-green-800',
      observation: 'bg-blue-100 text-blue-800',
      treatment: 'bg-orange-100 text-orange-800',
      harvest: 'bg-purple-100 text-purple-800',
      maintenance: 'bg-gray-100 text-gray-800',
      sampling: 'bg-cyan-100 text-cyan-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const handleCreateSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!selectedPlotId) return
    const formData = new FormData(e.currentTarget)
    createEventMutation.mutate({
      plotId: selectedPlotId,
      data: {
        type: formData.get('type') as string,
        description: formData.get('description') as string,
        date: formData.get('date') as string || undefined,
        value: formData.get('value') as string || undefined,
        notes: formData.get('notes') as string || undefined,
      },
    })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Plot History</h1>
          <p className="text-muted-foreground mt-1">View historical data for each plot</p>
        </div>
        <Select value={selectedField} onValueChange={setSelectedField}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Fields" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Fields</SelectItem>
            {fields.map((field: { id: string; name: string }) => (
              <SelectItem key={field.id} value={field.id}>{field.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.total_plots || plots.length}</p>
                <p className="text-xs text-muted-foreground">Total Plots</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <History className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.total_events || 0}</p>
                <p className="text-xs text-muted-foreground">Total Events</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.recent_events || 0}</p>
                <p className="text-xs text-muted-foreground">Last 7 Days</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Leaf className="h-5 w-5 text-emerald-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.active_plots || 0}</p>
                <p className="text-xs text-muted-foreground">Active Plots</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Plot List */}
        <Card>
          <CardHeader>
            <CardTitle>Plots</CardTitle>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search plots..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {plotsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : plots.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No plots found</div>
            ) : (
              <div className="divide-y max-h-[400px] overflow-auto">
                {plots.map((plot: Plot) => (
                  <div
                    key={plot.id}
                    className={`p-3 cursor-pointer hover:bg-accent transition-colors ${selectedPlotId === plot.id ? 'bg-accent' : ''}`}
                    onClick={() => setSelectedPlotId(plot.id)}
                  >
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{plot.name}</p>
                      <Badge variant="secondary" className="text-xs">{plot.event_count} events</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{plot.field_name} • {plot.current_crop}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Plot Details & Events */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>
                  {selectedPlot ? `Plot ${selectedPlot.name} History` : 'Select a Plot'}
                </CardTitle>
                {selectedPlot && (
                  <CardDescription>
                    {selectedPlot.current_crop} • Planted {selectedPlot.planting_date}
                  </CardDescription>
                )}
              </div>
              {selectedPlot && (
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm"><Plus className="h-4 w-4 mr-1" />Add Event</Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Record Event for {selectedPlot.name}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleCreateSubmit} className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="type">Event Type *</Label>
                          <Select name="type" defaultValue="observation">
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              {eventTypes.map((type: EventType) => (
                                <SelectItem key={type.id} value={type.id}>{type.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="date">Date</Label>
                          <Input id="date" name="date" type="date" defaultValue={new Date().toISOString().split('T')[0]} />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="description">Description *</Label>
                        <Input id="description" name="description" required placeholder="What happened?" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="value">Value (optional)</Label>
                        <Input id="value" name="value" placeholder="e.g., 45 cm, 12 tillers" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="notes">Notes</Label>
                        <Textarea id="notes" name="notes" placeholder="Additional notes..." />
                      </div>
                      <Button type="submit" className="w-full" disabled={createEventMutation.isPending}>
                        {createEventMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                        Record Event
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {plotLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : selectedPlot ? (
              <div className="space-y-4">
                {selectedPlot.events && selectedPlot.events.length > 0 ? (
                  selectedPlot.events.map((event: PlotEvent) => (
                    <div key={event.id} className="flex items-start gap-4 p-4 border rounded-lg">
                      <div className={`p-2 rounded-lg ${getEventColor(event.type)}`}>
                        {getEventIcon(event.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="font-medium">{event.description}</p>
                          <Badge variant="outline">{event.date}</Badge>
                        </div>
                        {event.value && (
                          <p className="text-sm text-muted-foreground mt-1">
                            Value: <span className="font-medium">{event.value}</span>
                          </p>
                        )}
                        {event.notes && (
                          <p className="text-sm text-muted-foreground mt-1">{event.notes}</p>
                        )}
                        {event.recorded_by && (
                          <p className="text-xs text-muted-foreground mt-2">Recorded by: {event.recorded_by}</p>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <History className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No events recorded for this plot</p>
                    <Button variant="outline" className="mt-4" onClick={() => setIsCreateOpen(true)}>
                      <Plus className="h-4 w-4 mr-2" />Record First Event
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">Select a plot to view its history</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

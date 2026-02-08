/**
 * Field Map Page
 * Interactive field and plot visualization with backend API integration
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Map, Layers, Maximize2, Download, Plus, Search, MapPin, Grid3X3 } from 'lucide-react'
import { apiClient, type Field, type Plot } from '@/lib/api-client'
import { toast } from 'sonner'
import { GoogleMapWrapper } from '@/components/maps/GoogleMapWrapper'

export function FieldMap() {
  const queryClient = useQueryClient()
  const [selectedField, setSelectedField] = useState<string | null>(null)
  const [mapLayer, setMapLayer] = useState('satellite')
  const [stationFilter, setStationFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newField, setNewField] = useState({ name: '', location: '', area: 0, plots: 0, soilType: '', irrigationType: '' })

  // Fetch fields
  const { data: fieldsData, isLoading: fieldsLoading } = useQuery({
    queryKey: ['fields', stationFilter, statusFilter, searchQuery],
    queryFn: () => apiClient.fieldMapService.getFields({
      station: stationFilter !== 'all' ? stationFilter : undefined,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      search: searchQuery || undefined,
    }),
  })

  // Fetch summary
  const { data: summary } = useQuery({
    queryKey: ['fieldMapSummary'],
    queryFn: () => apiClient.fieldMapService.getSummary(),
  })

  // Fetch stations
  const { data: stations } = useQuery({
    queryKey: ['fieldMapStations'],
    queryFn: () => apiClient.fieldMapService.getStations(),
  })

  // Fetch plots for selected field
  const { data: plots, isLoading: plotsLoading } = useQuery({
    queryKey: ['fieldPlots', selectedField],
    queryFn: () => selectedField ? apiClient.fieldMapService.getPlots(selectedField) : Promise.resolve([]),
    enabled: !!selectedField,
  })

  // Create field mutation
  const createFieldMutation = useMutation({
    mutationFn: (data: typeof newField) => apiClient.fieldMapService.createField({
      name: data.name,
      location: data.location,
      area: data.area,
      plots: data.plots,
      soilType: data.soilType,
      irrigationType: data.irrigationType,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fields'] })
      queryClient.invalidateQueries({ queryKey: ['fieldMapSummary'] })
      setShowCreateDialog(false)
      setNewField({ name: '', location: '', area: 0, plots: 0, soilType: '', irrigationType: '' })
      toast.success('Field created successfully')
    },
    onError: () => toast.error('Failed to create field'),
  })

  const fields: Field[] = fieldsData || []

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      fallow: 'bg-yellow-100 text-yellow-800',
      harvested: 'bg-blue-100 text-blue-800',
      preparation: 'bg-purple-100 text-purple-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const selectedFieldData = fields.find(f => f.id === selectedField)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Field Map</h1>
          <p className="text-muted-foreground mt-1">Interactive field and plot visualization</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Select value={mapLayer} onValueChange={setMapLayer}>
            <SelectTrigger className="w-[130px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="satellite">Satellite</SelectItem>
              <SelectItem value="terrain">Terrain</SelectItem>
              <SelectItem value="hybrid">Hybrid</SelectItem>
            </SelectContent>
          </Select>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button><Plus className="mr-2 h-4 w-4" />Add Field</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Create New Field</DialogTitle></DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Field Name</Label>
                    <Input value={newField.name} onChange={e => setNewField({ ...newField, name: e.target.value })} placeholder="Block E" />
                  </div>
                  <div>
                    <Label>Location</Label>
                    <Input value={newField.location} onChange={e => setNewField({ ...newField, location: e.target.value })} placeholder="Research Station 1" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Area (ha)</Label>
                    <Input type="number" value={newField.area || ''} onChange={e => setNewField({ ...newField, area: parseFloat(e.target.value) || 0 })} />
                  </div>
                  <div>
                    <Label>Number of Plots</Label>
                    <Input type="number" value={newField.plots || ''} onChange={e => setNewField({ ...newField, plots: parseInt(e.target.value) || 0 })} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Soil Type</Label>
                    <Input value={newField.soilType} onChange={e => setNewField({ ...newField, soilType: e.target.value })} placeholder="Clay loam" />
                  </div>
                  <div>
                    <Label>Irrigation Type</Label>
                    <Input value={newField.irrigationType} onChange={e => setNewField({ ...newField, irrigationType: e.target.value })} placeholder="Drip" />
                  </div>
                </div>
                <Button className="w-full" onClick={() => createFieldMutation.mutate(newField)} disabled={!newField.name || !newField.location || createFieldMutation.isPending}>
                  {createFieldMutation.isPending ? 'Creating...' : 'Create Field'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{summary?.totalFields || fields.length}</p>
            <p className="text-xs text-muted-foreground">Total Fields</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{summary?.totalArea?.toFixed(1) || fields.reduce((s: number, f: Field) => s + f.area, 0).toFixed(1)} ha</p>
            <p className="text-xs text-muted-foreground">Total Area</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{summary?.totalPlots?.toLocaleString() || fields.reduce((s: number, f: Field) => s + f.plots, 0).toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">Total Plots</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-green-600">{summary?.activeFields || fields.filter((f: Field) => f.status === 'active').length}</p>
            <p className="text-xs text-muted-foreground">Active Fields</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input className="pl-10" placeholder="Search fields..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        </div>
        <Select value={stationFilter} onValueChange={setStationFilter}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Station" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Stations</SelectItem>
            {(stations || []).map((s: string) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="fallow">Fallow</SelectItem>
            <SelectItem value="harvested">Harvested</SelectItem>
            <SelectItem value="preparation">Preparation</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Map View */}
        <Card className="lg:col-span-3">
          <CardContent className="p-0 relative h-[500px]">
             {/* Google Map Background */}
            <div className="absolute inset-0 z-0">
               <GoogleMapWrapper height="100%" />
            </div>

            {/* Overlay Content */}
            <div className="relative z-10 w-full h-full pointer-events-none p-6 flex flex-col items-center justify-center">
              {selectedFieldData ? (
                <div className="bg-background/95 backdrop-blur-sm p-6 rounded-xl shadow-lg border max-w-md w-full pointer-events-auto">
                  <div className="text-center">
                    <MapPin className="h-12 w-12 mx-auto mb-4 text-primary" />
                    <h3 className="text-xl font-bold">{selectedFieldData.name}</h3>
                    <p className="text-muted-foreground">{selectedFieldData.location}</p>
                    <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                      <div className="p-2 bg-accent/50 rounded">
                        <p className="font-medium">{selectedFieldData.area} ha</p>
                        <p className="text-xs text-muted-foreground">Area</p>
                      </div>
                      <div className="p-2 bg-accent/50 rounded">
                        <p className="font-medium">{selectedFieldData.plots}</p>
                        <p className="text-xs text-muted-foreground">Plots</p>
                      </div>
                      <div className="p-2 bg-accent/50 rounded">
                        <p className="font-medium">{selectedFieldData.soilType || 'N/A'}</p>
                        <p className="text-xs text-muted-foreground">Soil Type</p>
                      </div>
                      <div className="p-2 bg-accent/50 rounded">
                        <p className="font-medium">{selectedFieldData.irrigationType || 'N/A'}</p>
                        <p className="text-xs text-muted-foreground">Irrigation</p>
                      </div>
                    </div>
                    {plotsLoading ? (
                      <Skeleton className="h-32 w-full mt-4" />
                    ) : plots && plots.length > 0 ? (
                      <div className="mt-4 text-left">
                        <p className="text-sm font-medium mb-2">Plot Grid ({plots.length} plots)</p>
                        <div className="flex flex-wrap gap-1 justify-center max-h-32 overflow-auto p-1">
                          {plots.slice(0, 50).map((plot: any) => (
                            <div
                              key={plot.id}
                              className={`w-4 h-4 rounded-sm ${
                                plot.status === 'growing' ? 'bg-green-500' :
                                plot.status === 'harvested' ? 'bg-blue-500' :
                                plot.status === 'planted' ? 'bg-yellow-500' :
                                'bg-gray-300'
                              }`}
                              title={`Plot ${plot.plotNumber}: ${plot.status}`}
                            />
                          ))}
                          {plots.length > 50 && <span className="text-xs text-muted-foreground">+{plots.length - 50} more</span>}
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              ) : (
                <div className="text-center bg-background/80 backdrop-blur-sm p-6 rounded-xl shadow-sm border pointer-events-auto">
                  <Map className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                  <p className="font-medium">Select a field to view details</p>
                  <p className="text-sm text-muted-foreground">Map visualization initialized</p>
                </div>
              )}
            </div>

            <div className="absolute top-4 right-4 flex flex-col gap-2 z-20 pointer-events-auto">
                <Button variant="secondary" size="icon" aria-label="Fullscreen"><Maximize2 className="h-4 w-4" /></Button>
                <Button variant="secondary" size="icon" aria-label="Toggle layers"><Layers className="h-4 w-4" /></Button>
                <Button variant="secondary" size="icon" aria-label="Show grid"><Grid3X3 className="h-4 w-4" /></Button>
            </div>
          </CardContent>
        </Card>

        {/* Field List */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-lg">Fields</CardTitle></CardHeader>
            <CardContent className="p-0">
              {fieldsLoading ? (
                <div className="p-4 space-y-2">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : (
                <div className="divide-y max-h-[400px] overflow-auto">
                  {fields.map((field: Field) => (
                    <div
                      key={field.id}
                      className={`p-3 cursor-pointer hover:bg-accent transition-colors ${selectedField === field.id ? 'bg-accent' : ''}`}
                      onClick={() => setSelectedField(field.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{field.name}</p>
                          <p className="text-xs text-muted-foreground">{field.area} ha • {field.plots} plots</p>
                        </div>
                        <Badge className={getStatusColor(field.status)}>{field.status}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

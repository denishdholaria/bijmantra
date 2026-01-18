/**
 * Field Map Page
 *
 * Interactive GIS map for field visualization and management.
 * Connected to /api/v2/field-map endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import { RefreshCw, Plus, MapPin, Layers, BarChart3, Droplets, Leaf, AlertTriangle } from 'lucide-react';

interface Field {
  id: string;
  name: string;
  location: string;
  station?: string;
  area: number;
  plots: number;
  status: string;
  coordinates?: { lat: number; lng: number };
  soil_type?: string;
  irrigation_type?: string;
  current_crop?: string;
  health_score?: number;
}

interface FieldSummary {
  total_fields: number;
  total_area: number;
  total_plots: number;
  by_status: Record<string, number>;
  by_station: Record<string, number>;
}

export function FieldMap() {
  const [selectedField, setSelectedField] = useState<Field | null>(null);
  const [stationFilter, setStationFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newField, setNewField] = useState({
    name: '',
    location: '',
    station: '',
    area: 0,
    plots: 0,
    soil_type: '',
    irrigation_type: '',
  });
  const queryClient = useQueryClient();

  // Fetch fields
  const { data: fieldsData, isLoading, error, refetch } = useQuery({
    queryKey: ['field-map-fields', stationFilter, statusFilter, search],
    queryFn: () => apiClient.getFields({
      station: stationFilter !== 'all' ? stationFilter : undefined,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      search: search || undefined,
    }),
  });

  // Fetch summary
  const { data: summaryData } = useQuery({
    queryKey: ['field-map-summary'],
    queryFn: () => apiClient.getFieldMapSummary(),
  });

  // Fetch stations
  const { data: stationsData } = useQuery({
    queryKey: ['field-map-stations'],
    queryFn: () => apiClient.getFieldMapStations(),
  });

  // Fetch statuses
  const { data: statusesData } = useQuery({
    queryKey: ['field-map-statuses'],
    queryFn: () => apiClient.getFieldMapStatuses(),
  });

  // Create field mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newField) => apiClient.createField({
      name: data.name,
      location: data.location,
      station: data.station || undefined,
      area: data.area,
      plots: data.plots,
      soilType: data.soil_type || undefined,
      irrigationType: data.irrigation_type || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['field-map-fields'] });
      queryClient.invalidateQueries({ queryKey: ['field-map-summary'] });
      toast.success('Field created successfully');
      setShowCreate(false);
      setNewField({ name: '', location: '', station: '', area: 0, plots: 0, soil_type: '', irrigation_type: '' });
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create field'),
  });

  const fields: Field[] = fieldsData?.fields || [];
  const summary: FieldSummary = summaryData || { total_fields: 0, total_area: 0, total_plots: 0, by_status: {}, by_station: {} };
  const stations: string[] = stationsData?.stations || [];
  const fieldStatuses: string[] = statusesData?.fieldStatuses || ['active', 'fallow', 'preparation', 'harvested'];

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'active': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      'planted': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      'growing': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      'harvest-ready': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      'harvested': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      'fallow': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
      'preparation': 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    };
    return colors[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400';
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, string> = {
      'active': '🌱',
      'planted': '🌾',
      'growing': '🌿',
      'harvest-ready': '🌻',
      'harvested': '✅',
      'fallow': '🏜️',
      'preparation': '🚜',
    };
    return icons[status] || '📍';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">Field Map</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Interactive field visualization and management</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />Add Field</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Field</DialogTitle>
                <DialogDescription>Register a new field for management</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Field Name *</Label>
                    <Input
                      value={newField.name}
                      onChange={(e) => setNewField({ ...newField, name: e.target.value })}
                      placeholder="e.g., North Block A"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Location *</Label>
                    <Input
                      value={newField.location}
                      onChange={(e) => setNewField({ ...newField, location: e.target.value })}
                      placeholder="e.g., Research Station"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Station</Label>
                    <Input
                      value={newField.station}
                      onChange={(e) => setNewField({ ...newField, station: e.target.value })}
                      placeholder="e.g., Main Campus"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Area (ha) *</Label>
                    <Input
                      type="number"
                      value={newField.area || ''}
                      onChange={(e) => setNewField({ ...newField, area: parseFloat(e.target.value) || 0 })}
                      placeholder="12.5"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Number of Plots</Label>
                    <Input
                      type="number"
                      value={newField.plots || ''}
                      onChange={(e) => setNewField({ ...newField, plots: parseInt(e.target.value) || 0 })}
                      placeholder="100"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Soil Type</Label>
                    <Select value={newField.soil_type} onValueChange={(v) => setNewField({ ...newField, soil_type: v })}>
                      <SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="clay">Clay</SelectItem>
                        <SelectItem value="loam">Loam</SelectItem>
                        <SelectItem value="sandy">Sandy</SelectItem>
                        <SelectItem value="silt">Silt</SelectItem>
                        <SelectItem value="clay-loam">Clay Loam</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Irrigation Type</Label>
                  <Select value={newField.irrigation_type} onValueChange={(v) => setNewField({ ...newField, irrigation_type: v })}>
                    <SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="drip">Drip</SelectItem>
                      <SelectItem value="sprinkler">Sprinkler</SelectItem>
                      <SelectItem value="flood">Flood</SelectItem>
                      <SelectItem value="rainfed">Rainfed</SelectItem>
                      <SelectItem value="center-pivot">Center Pivot</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newField)}
                  disabled={!newField.name || !newField.location || !newField.area || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Field'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <Layers className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{summary.total_fields}</div>
                <div className="text-sm text-muted-foreground">Total Fields</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <MapPin className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{summary.total_area.toFixed(1)}</div>
                <div className="text-sm text-muted-foreground">Total Hectares</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <BarChart3 className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{summary.total_plots}</div>
                <div className="text-sm text-muted-foreground">Total Plots</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                <Leaf className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{summary.by_status?.active || 0}</div>
                <div className="text-sm text-muted-foreground">Active Fields</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search fields..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={stationFilter} onValueChange={setStationFilter}>
              <SelectTrigger className="w-[180px]"><SelectValue placeholder="Station" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Stations</SelectItem>
                {stations.map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {fieldStatuses.map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Map Area */}
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-2"><MapPin className="h-5 w-5" />Field Overview</CardTitle></CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-96 w-full" />
            ) : error ? (
              <div className="h-96 flex items-center justify-center bg-red-50 rounded-lg">
                <div className="text-center">
                  <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-2" />
                  <p className="text-red-600">Failed to load fields</p>
                  <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>Retry</Button>
                </div>
              </div>
            ) : (
              <div className="h-96 bg-gradient-to-br from-green-100 to-green-200 rounded-lg relative overflow-hidden">
                {/* Simple visual representation of fields */}
                <div className="absolute inset-4 grid grid-cols-3 gap-2">
                  {fields.slice(0, 9).map((field, i) => (
                    <div
                      key={field.id}
                      className={`rounded-lg cursor-pointer transition-all hover:scale-105 flex items-center justify-center text-white font-medium text-sm shadow-md ${
                        selectedField?.id === field.id ? 'ring-4 ring-blue-500' : ''
                      } ${
                        field.status === 'active' || field.status === 'growing' ? 'bg-green-500' :
                        field.status === 'harvest-ready' ? 'bg-yellow-500' :
                        field.status === 'fallow' ? 'bg-gray-400' :
                        field.status === 'preparation' ? 'bg-purple-500' :
                        'bg-blue-500'
                      }`}
                      style={{ opacity: 0.85 }}
                      onClick={() => setSelectedField(field)}
                    >
                      <div className="text-center p-2">
                        <div className="text-lg">{getStatusIcon(field.status)}</div>
                        <div className="truncate max-w-full">{field.name}</div>
                        <div className="text-xs opacity-80">{field.area} ha</div>
                      </div>
                    </div>
                  ))}
                </div>
                {fields.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center text-gray-600">
                      <MapPin className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>No fields registered yet</p>
                      <Button variant="outline" size="sm" className="mt-2" onClick={() => setShowCreate(true)}>
                        Add First Field
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
            <p className="text-xs text-muted-foreground mt-2 text-center">
              Click on a field to view details • Full GIS integration coming soon
            </p>
          </CardContent>
        </Card>

        {/* Field List */}
        <Card>
          <CardHeader><CardTitle>Fields ({fields.length})</CardTitle></CardHeader>
          <CardContent className="p-0 max-h-[450px] overflow-y-auto">
            {isLoading ? (
              <div className="p-4 space-y-3">
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
              </div>
            ) : fields.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <Layers className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No fields found</p>
              </div>
            ) : (
              <div className="divide-y">
                {fields.map((field) => (
                  <div
                    key={field.id}
                    className={`p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors ${
                      selectedField?.id === field.id ? 'bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500' : ''
                    }`}
                    onClick={() => setSelectedField(field)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{field.name}</span>
                      <Badge className={getStatusColor(field.status)}>{field.status}</Badge>
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-2">
                      <span>{field.current_crop || field.location}</span>
                      <span>•</span>
                      <span>{field.area} ha</span>
                      {field.plots > 0 && (
                        <>
                          <span>•</span>
                          <span>{field.plots} plots</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Selected Field Details */}
      {selectedField && (
        <Card className="border-green-200 dark:border-green-800 bg-green-50/30 dark:bg-green-900/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">{getStatusIcon(selectedField.status)}</span>
              {selectedField.name}
              <Badge className={getStatusColor(selectedField.status)}>{selectedField.status}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-5 gap-4">
              <div className="text-center p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">{selectedField.area}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Hectares</div>
              </div>
              <div className="text-center p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{selectedField.plots || '-'}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Plots</div>
              </div>
              <div className="text-center p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
                <div className="text-lg font-bold text-purple-600 dark:text-purple-400">{selectedField.current_crop || selectedField.location}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Location/Crop</div>
              </div>
              <div className="text-center p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
                <div className="flex items-center justify-center gap-1">
                  <Droplets className="h-5 w-5 text-cyan-500" />
                  <span className="text-lg font-bold">{selectedField.irrigation_type || 'N/A'}</span>
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Irrigation</div>
              </div>
              <div className="text-center p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
                <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">{selectedField.health_score || 85}%</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Health Score</div>
              </div>
            </div>
            {selectedField.soil_type && (
              <div className="mt-4 p-3 bg-white dark:bg-slate-800 rounded-lg">
                <span className="text-sm text-gray-500 dark:text-gray-400">Soil Type:</span>
                <span className="ml-2 font-medium">{selectedField.soil_type}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default FieldMap;

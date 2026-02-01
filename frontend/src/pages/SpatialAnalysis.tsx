/**
 * Spatial Analysis Page
 * 
 * GIS and spatial analysis for field trials.
 * Connects to /api/v2/spatial endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Map,
  Grid3X3,
  Ruler,
  Calculator,
  Plus,
  MapPin,
  Layers,
  TrendingUp,
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface Field {
  field_id: string;
  name: string;
  location: string;
  latitude: number;
  longitude: number;
  area_ha: number;
  rows: number;
  columns: number;
  plot_size_m2: number;
  soil_type?: string;
  irrigation?: string;
}

interface Plot {
  plot_id: string;
  row: number;
  column: number;
  x_m: number;
  y_m: number;
  center_lat: number;
  center_lon: number;
}

export function SpatialAnalysis() {
  const [activeTab, setActiveTab] = useState('fields');
  const [showNewFieldDialog, setShowNewFieldDialog] = useState(false);
  const [selectedField, setSelectedField] = useState<string | null>(null);
  
  // New field form state
  const [fieldName, setFieldName] = useState('');
  const [fieldLocation, setFieldLocation] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [areaHa, setAreaHa] = useState('');
  const [rows, setRows] = useState('');
  const [columns, setColumns] = useState('');
  const [plotSize, setPlotSize] = useState('');
  
  // Distance calculator state
  const [lat1, setLat1] = useState('');
  const [lon1, setLon1] = useState('');
  const [lat2, setLat2] = useState('');
  const [lon2, setLon2] = useState('');
  const [distanceResult, setDistanceResult] = useState<{ distance_m: number; distance_km: number } | null>(null);
  
  const queryClient = useQueryClient();

  // Fetch fields
  const { data: fieldsResponse, isLoading: fieldsLoading } = useQuery({
    queryKey: ['spatial-fields'],
    queryFn: () => apiClient.spatialService.getFields(),
  });

  const fields = fieldsResponse?.data || [];

  // Fetch plots for selected field
  const { data: plotsResponse, isLoading: plotsLoading } = useQuery({
    queryKey: ['field-plots', selectedField],
    queryFn: () => apiClient.spatialService.getPlots(selectedField!),
    enabled: !!selectedField,
  });

  const plots = plotsResponse?.data || [];

  // Create field mutation
  const createFieldMutation = useMutation({
    mutationFn: () => apiClient.spatialService.createField({
      name: fieldName,
      location: fieldLocation,
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      area_ha: parseFloat(areaHa),
      rows: parseInt(rows),
      columns: parseInt(columns),
      plot_size_m2: parseFloat(plotSize),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['spatial-fields'] });
      setShowNewFieldDialog(false);
      resetFieldForm();
    },
  });

  // Calculate distance mutation
  const calculateDistanceMutation = useMutation({
    mutationFn: () => apiClient.spatialService.calculateDistance(
      parseFloat(lat1),
      parseFloat(lon1),
      parseFloat(lat2),
      parseFloat(lon2)
    ),
    onSuccess: (data) => {
      setDistanceResult(data.data);
    },
  });

  // Generate plots mutation
  const generatePlotsMutation = useMutation({
    mutationFn: (fieldId: string) => apiClient.spatialService.generatePlots(fieldId, {
      plot_width_m: 2.5,
      plot_length_m: 4.0,
      alley_width_m: 0.5,
      border_m: 2.0,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['field-plots', selectedField] });
    },
  });

  const resetFieldForm = () => {
    setFieldName('');
    setFieldLocation('');
    setLatitude('');
    setLongitude('');
    setAreaHa('');
    setRows('');
    setColumns('');
    setPlotSize('');
  };

  const totalPlots = fields.reduce((sum, f) => sum + f.rows * f.columns, 0);
  const totalArea = fields.reduce((sum, f) => sum + f.area_ha, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Map className="h-6 w-6" />
            Spatial Analysis
          </h1>
          <p className="text-muted-foreground">
            GIS and spatial analysis for field trials
          </p>
        </div>
        <Dialog open={showNewFieldDialog} onOpenChange={setShowNewFieldDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Field
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Create Field</DialogTitle>
              <DialogDescription>Define a new field for spatial analysis</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Field Name</Label>
                  <Input value={fieldName} onChange={(e) => setFieldName(e.target.value)} placeholder="Research Station A" />
                </div>
                <div className="space-y-2">
                  <Label>Location</Label>
                  <Input value={fieldLocation} onChange={(e) => setFieldLocation(e.target.value)} placeholder="Hyderabad" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Latitude</Label>
                  <Input type="number" step="0.0001" value={latitude} onChange={(e) => setLatitude(e.target.value)} placeholder="17.385" />
                </div>
                <div className="space-y-2">
                  <Label>Longitude</Label>
                  <Input type="number" step="0.0001" value={longitude} onChange={(e) => setLongitude(e.target.value)} placeholder="78.4867" />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Area (ha)</Label>
                  <Input type="number" step="0.1" value={areaHa} onChange={(e) => setAreaHa(e.target.value)} placeholder="5.0" />
                </div>
                <div className="space-y-2">
                  <Label>Rows</Label>
                  <Input type="number" value={rows} onChange={(e) => setRows(e.target.value)} placeholder="20" />
                </div>
                <div className="space-y-2">
                  <Label>Columns</Label>
                  <Input type="number" value={columns} onChange={(e) => setColumns(e.target.value)} placeholder="25" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Plot Size (m²)</Label>
                <Input type="number" step="0.1" value={plotSize} onChange={(e) => setPlotSize(e.target.value)} placeholder="10" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewFieldDialog(false)}>Cancel</Button>
              <Button onClick={() => createFieldMutation.mutate()} disabled={!fieldName || !latitude || !longitude || createFieldMutation.isPending}>
                {createFieldMutation.isPending ? 'Creating...' : 'Create Field'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>


      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Map className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{fields.length}</p>
                <p className="text-xs text-muted-foreground">Fields</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Grid3X3 className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalPlots.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">Total Plots</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Layers className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalArea.toFixed(1)}</p>
                <p className="text-xs text-muted-foreground">Total Area (ha)</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">4</p>
                <p className="text-xs text-muted-foreground">Analysis Tools</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="fields">
            <Map className="h-4 w-4 mr-2" />
            Fields ({fields.length})
          </TabsTrigger>
          <TabsTrigger value="plots">
            <Grid3X3 className="h-4 w-4 mr-2" />
            Plot Grid
          </TabsTrigger>
          <TabsTrigger value="tools">
            <Calculator className="h-4 w-4 mr-2" />
            Analysis Tools
          </TabsTrigger>
        </TabsList>

        {/* Fields Tab */}
        <TabsContent value="fields">
          <Card>
            <CardHeader>
              <CardTitle>Field Registry</CardTitle>
              <CardDescription>Manage fields for spatial analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Coordinates</TableHead>
                    <TableHead>Area</TableHead>
                    <TableHead>Grid</TableHead>
                    <TableHead>Soil</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fields.map(field => (
                    <TableRow key={field.field_id}>
                      <TableCell className="font-medium">{field.name}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {field.location}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {field.latitude.toFixed(4)}, {field.longitude.toFixed(4)}
                      </TableCell>
                      <TableCell>{field.area_ha} ha</TableCell>
                      <TableCell>
                        <Badge variant="outline">{field.rows} × {field.columns}</Badge>
                      </TableCell>
                      <TableCell>{field.soil_type || '-'}</TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedField(field.field_id);
                            setActiveTab('plots');
                          }}
                        >
                          View Plots
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Plots Tab */}
        <TabsContent value="plots">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Plot Grid</CardTitle>
                  <CardDescription>View and manage plot coordinates</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Select value={selectedField || ''} onValueChange={setSelectedField}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select field" />
                    </SelectTrigger>
                    <SelectContent>
                      {fields.map(field => (
                        <SelectItem key={field.field_id} value={field.field_id}>
                          {field.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {selectedField && (
                    <Button
                      variant="outline"
                      onClick={() => generatePlotsMutation.mutate(selectedField)}
                      disabled={generatePlotsMutation.isPending}
                    >
                      {generatePlotsMutation.isPending ? 'Generating...' : 'Generate Plots'}
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {selectedField && plots.length > 0 ? (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    {plots.length} plots generated
                  </div>
                  <div className="max-h-[400px] overflow-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Plot ID</TableHead>
                          <TableHead>Row</TableHead>
                          <TableHead>Column</TableHead>
                          <TableHead>X (m)</TableHead>
                          <TableHead>Y (m)</TableHead>
                          <TableHead>Center Lat</TableHead>
                          <TableHead>Center Lon</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {plots.slice(0, 50).map(plot => (
                          <TableRow key={plot.plot_id}>
                            <TableCell className="font-mono text-xs">{plot.plot_id}</TableCell>
                            <TableCell>{plot.row}</TableCell>
                            <TableCell>{plot.column}</TableCell>
                            <TableCell>{plot.x_m.toFixed(2)}</TableCell>
                            <TableCell>{plot.y_m.toFixed(2)}</TableCell>
                            <TableCell className="font-mono text-xs">{plot.center_lat.toFixed(6)}</TableCell>
                            <TableCell className="font-mono text-xs">{plot.center_lon.toFixed(6)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    {plots.length > 50 && (
                      <p className="text-center text-sm text-muted-foreground py-2">
                        Showing 50 of {plots.length} plots
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  {selectedField ? 'No plots generated. Click "Generate Plots" to create plot coordinates.' : 'Select a field to view plots'}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tools Tab */}
        <TabsContent value="tools">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Ruler className="h-5 w-5" />
                  Distance Calculator
                </CardTitle>
                <CardDescription>Calculate distance between GPS coordinates (Haversine)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Point 1 Latitude</Label>
                    <Input type="number" step="0.0001" value={lat1} onChange={(e) => setLat1(e.target.value)} placeholder="17.385" />
                  </div>
                  <div className="space-y-2">
                    <Label>Point 1 Longitude</Label>
                    <Input type="number" step="0.0001" value={lon1} onChange={(e) => setLon1(e.target.value)} placeholder="78.4867" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Point 2 Latitude</Label>
                    <Input type="number" step="0.0001" value={lat2} onChange={(e) => setLat2(e.target.value)} placeholder="17.390" />
                  </div>
                  <div className="space-y-2">
                    <Label>Point 2 Longitude</Label>
                    <Input type="number" step="0.0001" value={lon2} onChange={(e) => setLon2(e.target.value)} placeholder="78.490" />
                  </div>
                </div>
                <Button
                  onClick={() => calculateDistanceMutation.mutate()}
                  disabled={!lat1 || !lon1 || !lat2 || !lon2 || calculateDistanceMutation.isPending}
                  className="w-full"
                >
                  {calculateDistanceMutation.isPending ? 'Calculating...' : 'Calculate Distance'}
                </Button>
                {distanceResult && (
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="p-4 border rounded-lg text-center">
                      <p className="text-2xl font-bold">{distanceResult.distance_m.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">meters</p>
                    </div>
                    <div className="p-4 border rounded-lg text-center">
                      <p className="text-2xl font-bold">{distanceResult.distance_km}</p>
                      <p className="text-xs text-muted-foreground">kilometers</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Analysis Methods</CardTitle>
                <CardDescription>Available spatial analysis tools</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 border rounded-lg">
                    <div className="font-medium">Moran's I Autocorrelation</div>
                    <p className="text-sm text-muted-foreground">Measure spatial clustering of values</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="font-medium">Moving Average Adjustment</div>
                    <p className="text-sm text-muted-foreground">Spatial smoothing for field variation</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="font-medium">Nearest Neighbor Analysis</div>
                    <p className="text-sm text-muted-foreground">Point pattern analysis</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="font-medium">Row-Column Trend</div>
                    <p className="text-sm text-muted-foreground">Detect systematic field gradients</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default SpatialAnalysis;

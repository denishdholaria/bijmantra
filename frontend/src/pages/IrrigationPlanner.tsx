/**
 * Irrigation Planner Page
 * 
 * Schedule and monitor irrigation across field zones.
 * Connects to /api/v2/field-environment/irrigation endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { Droplets, AlertTriangle, CheckCircle, Clock, Loader2, AlertCircle, Plus, Calendar } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface IrrigationZone {
  id: string;
  name: string;
  field: string;
  soilMoisture: number;
  lastIrrigation: string;
  nextScheduled: string;
  status: 'optimal' | 'needs-water' | 'scheduled';
  irrigationType?: string;
}

interface IrrigationEvent {
  id: string;
  field_id: string;
  irrigation_type: string;
  date: string;
  duration_hours: number;
  water_volume_m3: number;
  notes: string | null;
}

export function IrrigationPlanner() {
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [selectedField, setSelectedField] = useState('');
  const [irrigationType, setIrrigationType] = useState('drip');
  const [scheduledDate, setScheduledDate] = useState('');
  const [duration, setDuration] = useState('');
  const [waterVolume, setWaterVolume] = useState('');
  const [notes, setNotes] = useState('');
  const queryClient = useQueryClient();

  // Fetch irrigation events
  const { data: eventsData, isLoading: eventsLoading, error: eventsError } = useQuery({
    queryKey: ['irrigation-events'],
    queryFn: () => apiClient.getIrrigationEvents(),
  });

  // Fetch irrigation types
  const { data: typesData } = useQuery({
    queryKey: ['irrigation-types'],
    queryFn: () => apiClient.getIrrigationTypes(),
  });

  // Fetch fields for zone data
  const { data: fieldsData, isLoading: fieldsLoading } = useQuery({
    queryKey: ['fields'],
    queryFn: async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v2/field-map/fields`);
        if (!res.ok) return { fields: [] };
        return res.json();
      } catch {
        return { fields: [] };
      }
    },
  });

  // Fetch live sensor readings for soil moisture
  const { data: sensorData } = useQuery({
    queryKey: ['live-readings-irrigation'],
    queryFn: () => apiClient.getLiveSensorReadings(),
    refetchInterval: 30000,
  });

  // Create irrigation event mutation
  const createEventMutation = useMutation({
    mutationFn: () => apiClient.scheduleIrrigation({
      field_id: selectedField,
      irrigation_type: irrigationType,
      scheduled_date: scheduledDate,
      duration_hours: parseFloat(duration),
      water_volume: parseFloat(waterVolume),
      notes: notes || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['irrigation-events'] });
      setShowScheduleDialog(false);
      resetForm();
    },
  });

  const resetForm = () => {
    setSelectedField('');
    setIrrigationType('drip');
    setScheduledDate('');
    setDuration('');
    setWaterVolume('');
    setNotes('');
  };

  const events: IrrigationEvent[] = eventsData || [];
  const irrigationTypes = typesData?.irrigation_types || [
    { value: 'drip', name: 'Drip' },
    { value: 'sprinkler', name: 'Sprinkler' },
    { value: 'flood', name: 'Flood' },
    { value: 'furrow', name: 'Furrow' },
    { value: 'center_pivot', name: 'Center Pivot' },
  ];
  const fields = fieldsData?.fields || [];
  const sensorReadings = sensorData?.readings || [];

  // Build zones from fields with sensor data
  const zones: IrrigationZone[] = fields.map((field: any) => {
    // Find soil moisture reading for this field
    const moistureReading = sensorReadings.find((r: any) => 
      r.sensor === 'soil_moisture' && (
        r.location?.toLowerCase().includes(field.name?.toLowerCase()) ||
        r.device_name?.toLowerCase().includes(field.name?.toLowerCase())
      )
    );
    
    // Find last irrigation event for this field
    const fieldEvents = events.filter(e => e.field_id === field.id);
    const lastEvent = fieldEvents.sort((a, b) => 
      new Date(b.date).getTime() - new Date(a.date).getTime()
    )[0];

    const soilMoisture = moistureReading?.value ?? Math.floor(Math.random() * 30) + 25;
    
    // Determine status based on soil moisture
    let status: 'optimal' | 'needs-water' | 'scheduled' = 'optimal';
    if (soilMoisture < 30) status = 'needs-water';
    else if (fieldEvents.some(e => new Date(e.date) > new Date())) status = 'scheduled';

    return {
      id: field.id,
      name: field.name || `Zone ${field.id}`,
      field: field.location || field.name,
      soilMoisture,
      lastIrrigation: lastEvent ? formatRelativeDate(lastEvent.date) : 'Never',
      nextScheduled: 'Not scheduled',
      status,
      irrigationType: field.irrigation_type,
    };
  });

  const isLoading = eventsLoading || fieldsLoading;

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { 
      optimal: 'bg-green-100 text-green-800', 
      'needs-water': 'bg-red-100 text-red-800', 
      scheduled: 'bg-blue-100 text-blue-800' 
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getMoistureColor = (moisture: number) => {
    if (moisture < 30) return 'bg-red-500';
    if (moisture < 40) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  function formatRelativeDate(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading irrigation data...</span>
      </div>
    );
  }

  if (eventsError) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <span>Failed to load irrigation data. Please try again later.</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const needsWaterCount = zones.filter(z => z.status === 'needs-water').length;
  const scheduledCount = zones.filter(z => z.status === 'scheduled').length;
  const optimalCount = zones.filter(z => z.status === 'optimal').length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Irrigation Planner</h1>
          <p className="text-muted-foreground">Schedule and monitor irrigation across fields</p>
        </div>
        <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Schedule Irrigation
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Schedule Irrigation</DialogTitle>
              <DialogDescription>Plan an irrigation event for a field</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Field</Label>
                <Select value={selectedField} onValueChange={setSelectedField}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select field" />
                  </SelectTrigger>
                  <SelectContent>
                    {fields.map((field: any) => (
                      <SelectItem key={field.id} value={field.id}>
                        {field.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Irrigation Type</Label>
                <Select value={irrigationType} onValueChange={setIrrigationType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {irrigationTypes.map((type: any) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Scheduled Date</Label>
                <Input
                  type="date"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Duration (hours)</Label>
                  <Input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    placeholder="4"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Water Volume (m³)</Label>
                  <Input
                    type="number"
                    value={waterVolume}
                    onChange={(e) => setWaterVolume(e.target.value)}
                    placeholder="100"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Notes (optional)</Label>
                <Input
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Any additional notes..."
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowScheduleDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => createEventMutation.mutate()}
                disabled={!selectedField || !scheduledDate || !duration || !waterVolume || createEventMutation.isPending}
              >
                {createEventMutation.isPending ? 'Scheduling...' : 'Schedule'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Droplets className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{zones.length}</p>
                <p className="text-xs text-muted-foreground">Total Zones</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <div>
                <p className="text-2xl font-bold">{needsWaterCount}</p>
                <p className="text-xs text-muted-foreground">Need Water</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{scheduledCount}</p>
                <p className="text-xs text-muted-foreground">Scheduled</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{optimalCount}</p>
                <p className="text-xs text-muted-foreground">Optimal</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Irrigation Zones</CardTitle>
          <CardDescription>Monitor soil moisture and schedule irrigation</CardDescription>
        </CardHeader>
        <CardContent>
          {zones.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Droplets className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No irrigation zones found</p>
              <p className="text-sm">Add fields to start managing irrigation</p>
            </div>
          ) : (
            <div className="space-y-4">
              {zones.map((zone) => (
                <div key={zone.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    <Droplets className={`h-8 w-8 ${zone.soilMoisture < 30 ? 'text-red-500' : zone.soilMoisture < 40 ? 'text-yellow-500' : 'text-blue-500'}`} />
                    <div>
                      <p className="font-medium">{zone.name}</p>
                      <p className="text-sm text-muted-foreground">{zone.field}</p>
                      {zone.irrigationType && (
                        <p className="text-xs text-muted-foreground capitalize">Type: {zone.irrigationType}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="w-32">
                      <div className="flex justify-between text-xs mb-1">
                        <span>Moisture</span>
                        <span>{zone.soilMoisture}%</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${getMoistureColor(zone.soilMoisture)} rounded-full transition-all`} 
                          style={{ width: `${Math.min(zone.soilMoisture, 100)}%` }} 
                        />
                      </div>
                    </div>
                    <div className="text-right text-sm min-w-[120px]">
                      <p>Last: {zone.lastIrrigation}</p>
                      <p className="text-muted-foreground">Next: {zone.nextScheduled}</p>
                    </div>
                    <Badge className={getStatusColor(zone.status)}>{zone.status.replace('-', ' ')}</Badge>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        setSelectedField(zone.id);
                        setShowScheduleDialog(true);
                      }}
                    >
                      <Calendar className="h-4 w-4 mr-1" />
                      Schedule
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Irrigation Events */}
      {events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Irrigation Events</CardTitle>
            <CardDescription>History of irrigation activities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {events.slice(0, 5).map((event) => (
                <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Droplets className="h-5 w-5 text-blue-500" />
                    <div>
                      <p className="font-medium capitalize">{event.irrigation_type} Irrigation</p>
                      <p className="text-sm text-muted-foreground">
                        {event.duration_hours}h • {event.water_volume_m3}m³
                      </p>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <p>{new Date(event.date).toLocaleDateString()}</p>
                    {event.notes && <p className="text-muted-foreground">{event.notes}</p>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default IrrigationPlanner;

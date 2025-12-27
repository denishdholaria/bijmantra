/**
 * Crop Calendar Page
 * 
 * Planting schedules, growth stages, and activity planning.
 * Connects to /api/v2/crop-calendar endpoints.
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
  Calendar,
  Sprout,
  Leaf,
  Sun,
  Clock,
  CheckCircle2,
  Plus,
  MapPin,
  CalendarDays,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface CropProfile {
  crop_id: string;
  name: string;
  species: string;
  days_to_maturity: number;
  base_temperature: number;
  optimal_temp_min: number;
  optimal_temp_max: number;
  growth_stages: Record<string, number>;
}

interface PlantingEvent {
  event_id: string;
  crop_id: string;
  crop_name: string;
  trial_id: string;
  sowing_date: string;
  expected_harvest: string;
  location: string;
  area_hectares: number;
  notes: string;
  status: string;
}

interface Activity {
  activity_id: string;
  event_id: string;
  activity_type: string;
  scheduled_date: string;
  description: string;
  completed: boolean;
  completed_date?: string;
}

const stageColors: Record<string, string> = {
  germination: 'bg-yellow-100 text-yellow-800',
  seedling: 'bg-lime-100 text-lime-800',
  vegetative: 'bg-green-100 text-green-800',
  tillering: 'bg-green-100 text-green-800',
  flowering: 'bg-pink-100 text-pink-800',
  grain_filling: 'bg-amber-100 text-amber-800',
  maturity: 'bg-orange-100 text-orange-800',
};

const activityIcons: Record<string, React.ReactNode> = {
  observation: <Leaf className="h-4 w-4" />,
  fertilization: <Sprout className="h-4 w-4" />,
  pest_control: <Sun className="h-4 w-4" />,
  harvest: <Calendar className="h-4 w-4" />,
};

export function CropCalendar() {
  const [activeTab, setActiveTab] = useState('events');
  const [showNewEventDialog, setShowNewEventDialog] = useState(false);
  const [selectedCrop, setSelectedCrop] = useState('');
  const [sowingDate, setSowingDate] = useState('');
  const [location, setLocation] = useState('');
  const [area, setArea] = useState('');
  const [trialId, setTrialId] = useState('');
  const queryClient = useQueryClient();

  // Fetch crops from API
  const { data: cropsData, isLoading: cropsLoading, error: cropsError } = useQuery({
    queryKey: ['crop-profiles'],
    queryFn: () => apiClient.getCropProfiles(),
  });
  const crops: CropProfile[] = cropsData?.crops || [];

  // Fetch events from API
  const { data: eventsData, isLoading: eventsLoading, error: eventsError } = useQuery({
    queryKey: ['planting-events'],
    queryFn: () => apiClient.getPlantingEvents(),
  });
  const events: PlantingEvent[] = eventsData?.events || [];

  // Fetch activities from API
  const { data: activitiesData, isLoading: activitiesLoading, error: activitiesError } = useQuery({
    queryKey: ['upcoming-activities'],
    queryFn: () => apiClient.getUpcomingActivities(30),
  });
  const activities: Activity[] = activitiesData?.activities || [];

  // Create event mutation
  const createEventMutation = useMutation({
    mutationFn: () => apiClient.createPlantingEvent({
      crop_id: selectedCrop,
      trial_id: trialId || undefined,
      sowing_date: sowingDate,
      location,
      area_hectares: parseFloat(area),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planting-events'] });
      queryClient.invalidateQueries({ queryKey: ['upcoming-activities'] });
      setShowNewEventDialog(false);
      setSelectedCrop('');
      setSowingDate('');
      setLocation('');
      setArea('');
      setTrialId('');
    },
  });

  // Complete activity mutation
  const completeActivityMutation = useMutation({
    mutationFn: (activityId: string) => apiClient.completeActivity(activityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['upcoming-activities'] });
    },
  });

  const pendingActivities = activities.filter(a => !a.completed);
  const completedActivities = activities.filter(a => a.completed);
  const isLoading = cropsLoading || eventsLoading || activitiesLoading;
  const hasError = cropsError || eventsError || activitiesError;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading crop calendar...</span>
      </div>
    );
  }

  if (hasError) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <span>Failed to load crop calendar data. Please try again later.</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Calendar className="h-6 w-6" />
            Crop Calendar
          </h1>
          <p className="text-muted-foreground">
            Planting schedules, growth stages, and activity planning
          </p>
        </div>
        <Dialog open={showNewEventDialog} onOpenChange={setShowNewEventDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Planting
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Planting Event</DialogTitle>
              <DialogDescription>Schedule a new planting event</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Crop</Label>
                <Select value={selectedCrop} onValueChange={setSelectedCrop}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select crop" />
                  </SelectTrigger>
                  <SelectContent>
                    {crops.map(crop => (
                      <SelectItem key={crop.crop_id} value={crop.crop_id}>
                        {crop.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Trial ID (optional)</Label>
                <Input
                  value={trialId}
                  onChange={(e) => setTrialId(e.target.value)}
                  placeholder="TRIAL-2025-001"
                />
              </div>
              <div className="space-y-2">
                <Label>Sowing Date</Label>
                <Input
                  type="date"
                  value={sowingDate}
                  onChange={(e) => setSowingDate(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Location</Label>
                  <Input
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="Field A"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Area (ha)</Label>
                  <Input
                    type="number"
                    value={area}
                    onChange={(e) => setArea(e.target.value)}
                    placeholder="2.5"
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewEventDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => createEventMutation.mutate()}
                disabled={!selectedCrop || !sowingDate || !location || createEventMutation.isPending}
              >
                {createEventMutation.isPending ? 'Creating...' : 'Create Event'}
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
                <Sprout className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{crops.length}</p>
                <p className="text-xs text-muted-foreground">Crop Profiles</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <CalendarDays className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{events.length}</p>
                <p className="text-xs text-muted-foreground">Planting Events</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{pendingActivities.length}</p>
                <p className="text-xs text-muted-foreground">Pending Activities</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{completedActivities.length}</p>
                <p className="text-xs text-muted-foreground">Completed</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="events">
            <CalendarDays className="h-4 w-4 mr-2" />
            Planting Events ({events.length})
          </TabsTrigger>
          <TabsTrigger value="activities">
            <Clock className="h-4 w-4 mr-2" />
            Activities ({pendingActivities.length})
          </TabsTrigger>
          <TabsTrigger value="crops">
            <Sprout className="h-4 w-4 mr-2" />
            Crop Profiles ({crops.length})
          </TabsTrigger>
        </TabsList>

        {/* Events Tab */}
        <TabsContent value="events">
          <Card>
            <CardHeader>
              <CardTitle>Planting Events</CardTitle>
              <CardDescription>Active and planned planting schedules</CardDescription>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CalendarDays className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No planting events yet</p>
                  <p className="text-sm">Create your first planting event to get started</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Crop</TableHead>
                      <TableHead>Trial</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead>Sowing</TableHead>
                      <TableHead>Expected Harvest</TableHead>
                      <TableHead>Area</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {events.map(event => (
                      <TableRow key={event.event_id}>
                        <TableCell className="font-medium">{event.crop_name}</TableCell>
                        <TableCell>{event.trial_id || '-'}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {event.location}
                          </div>
                        </TableCell>
                        <TableCell>{event.sowing_date}</TableCell>
                        <TableCell>{event.expected_harvest}</TableCell>
                        <TableCell>{event.area_hectares} ha</TableCell>
                        <TableCell>
                          <Badge variant={event.status === 'active' ? 'default' : 'secondary'}>
                            {event.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Activities Tab */}
        <TabsContent value="activities">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Pending Activities</CardTitle>
                <CardDescription>Upcoming scheduled tasks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {pendingActivities.map(activity => (
                    <div key={activity.activity_id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {activityIcons[activity.activity_type] || <Leaf className="h-4 w-4" />}
                          <span className="font-medium capitalize">{activity.activity_type.replace('_', ' ')}</span>
                        </div>
                        <Badge variant="outline">{activity.scheduled_date}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">{activity.description}</p>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => completeActivityMutation.mutate(activity.activity_id)}
                        disabled={completeActivityMutation.isPending}
                      >
                        <CheckCircle2 className="h-4 w-4 mr-1" />
                        Mark Complete
                      </Button>
                    </div>
                  ))}
                  {pendingActivities.length === 0 && (
                    <p className="text-center text-muted-foreground py-4">No pending activities</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Completed Activities</CardTitle>
                <CardDescription>Recently completed tasks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {completedActivities.map(activity => (
                    <div key={activity.activity_id} className="p-3 border rounded-lg bg-muted/50">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                          <span className="font-medium capitalize">{activity.activity_type.replace('_', ' ')}</span>
                        </div>
                        <Badge variant="secondary">{activity.completed_date}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{activity.description}</p>
                    </div>
                  ))}
                  {completedActivities.length === 0 && (
                    <p className="text-center text-muted-foreground py-4">No completed activities</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Crops Tab */}
        <TabsContent value="crops">
          {crops.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                <Sprout className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No crop profiles available</p>
                <p className="text-sm">Crop profiles will be added by administrators</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {crops.map(crop => (
                <Card key={crop.crop_id}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">{crop.name}</CardTitle>
                    <CardDescription className="italic">{crop.species}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Days to Maturity</span>
                        <span className="font-medium">{crop.days_to_maturity} days</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Base Temperature</span>
                        <span className="font-medium">{crop.base_temperature}°C</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Optimal Range</span>
                        <span className="font-medium">{crop.optimal_temp_min}-{crop.optimal_temp_max}°C</span>
                      </div>
                      <div className="pt-2 border-t">
                        <p className="text-xs text-muted-foreground mb-2">Growth Stages</p>
                        <div className="flex flex-wrap gap-1">
                          {Object.keys(crop.growth_stages).slice(0, 4).map(stage => (
                            <Badge
                              key={stage}
                              variant="outline"
                              className={`text-xs ${stageColors[stage] || ''}`}
                            >
                              {stage.replace('_', ' ')}
                            </Badge>
                          ))}
                          {Object.keys(crop.growth_stages).length > 4 && (
                            <Badge variant="outline" className="text-xs">
                              +{Object.keys(crop.growth_stages).length - 4}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default CropCalendar;

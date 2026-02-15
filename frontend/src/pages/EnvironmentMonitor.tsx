/**
 * Environment Monitor Page
 * 
 * Real-time environmental data from field sensors.
 * Connects to /api/v2/sensors endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Thermometer, Droplets, Wind, Sun, CloudRain,
  AlertTriangle, TrendingUp, TrendingDown, Minus,
  MapPin, RefreshCw, Settings, Bell, Loader2, AlertCircle
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

export function EnvironmentMonitor() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const queryClient = useQueryClient();

  // Fetch devices from API
  const { data: devicesData, isLoading: devicesLoading, error: devicesError, refetch: refetchDevices } = useQuery({
    queryKey: ['sensor-devices'],
    queryFn: () => apiClient.sensorService.getSensorDevices(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch live readings
  const { data: liveData, isLoading: liveLoading, refetch: refetchLive } = useQuery({
    queryKey: ['live-readings'],
    queryFn: () => apiClient.sensorService.getLiveSensorReadings(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Fetch alert events
  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['sensor-alerts'],
    queryFn: () => apiClient.sensorService.getSensorAlertEvents({ acknowledged: false, limit: 10 }),
  });

  // Fetch network stats
  const { data: statsData } = useQuery({
    queryKey: ['sensor-stats'],
    queryFn: () => apiClient.sensorService.getSensorNetworkStats(),
    refetchInterval: 30000,
  });

  // Acknowledge alert mutation
  const acknowledgeMutation = useMutation({
    mutationFn: (eventId: string) => apiClient.sensorService.acknowledgeSensorAlert(eventId, 'current_user'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sensor-alerts'] });
    },
  });

  const devices = devicesData?.devices || [];
  const liveReadings = liveData?.readings || [];
  const alerts = alertsData?.events || [];
  const stats = statsData;

  const isLoading = devicesLoading || liveLoading || alertsLoading;
  const isRefreshing = queryClient.isFetching({ queryKey: ['sensor-devices'] }) > 0;

  // Build sensor data from devices and live readings
  const sensors = devices.map(device => {
    const deviceReadings = liveReadings.filter(r => r.device_id === device.device_id);
    const tempReading = deviceReadings.find(r => r.sensor === 'temperature');
    const humidityReading = deviceReadings.find(r => r.sensor === 'humidity');
    const moistureReading = deviceReadings.find(r => r.sensor === 'soil_moisture');
    const lightReading = deviceReadings.find(r => r.sensor === 'light');
    const windReading = deviceReadings.find(r => r.sensor === 'wind_speed');

    return {
      id: device.device_id,
      name: device.name,
      location: device.location,
      temperature: tempReading?.value ?? 0,
      humidity: humidityReading?.value ?? 0,
      soilMoisture: moistureReading?.value ?? 0,
      lightIntensity: lightReading?.value ?? 0,
      windSpeed: windReading?.value ?? 0,
      lastUpdate: device.last_seen || 'Unknown',
      status: device.status as 'online' | 'offline' | 'warning',
      battery: device.battery,
      signal: device.signal,
    };
  });

  // Calculate averages
  const onlineSensors = sensors.filter(s => s.status === 'online');
  const avgTemp = onlineSensors.length > 0 
    ? (onlineSensors.reduce((sum, s) => sum + s.temperature, 0) / onlineSensors.length).toFixed(1)
    : '0';
  const avgHumidity = onlineSensors.length > 0
    ? Math.round(onlineSensors.reduce((sum, s) => sum + s.humidity, 0) / onlineSensors.length)
    : 0;
  const avgMoisture = onlineSensors.length > 0
    ? Math.round(onlineSensors.reduce((sum, s) => sum + s.soilMoisture, 0) / onlineSensors.length)
    : 0;

  const handleRefresh = async () => {
    await Promise.all([refetchDevices(), refetchLive()]);
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = { 
      low: 'bg-yellow-100 text-yellow-800', 
      medium: 'bg-orange-100 text-orange-800', 
      high: 'bg-red-100 text-red-800',
      warning: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return colors[severity] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { online: 'bg-green-500', offline: 'bg-red-500', warning: 'bg-yellow-500' };
    return colors[status] || 'bg-gray-500';
  };

  // Filter sensors by location
  const filteredSensors = selectedLocation === 'all' 
    ? sensors 
    : sensors.filter(s => s.location === selectedLocation);

  const uniqueLocations = [...new Set(sensors.map(s => s.location))];

  if (isLoading && sensors.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading sensor data...</span>
      </div>
    );
  }

  if (devicesError) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <span>Failed to load sensor data. Please try again later.</span>
            </div>
            <Button variant="outline" className="mt-4" onClick={() => refetchDevices()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Environment Monitor</h1>
          <p className="text-muted-foreground">Real-time environmental data from field sensors</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline">
            <Bell className="mr-2 h-4 w-4" />
            Alerts ({alerts.length})
          </Button>
          <Button>
            <Settings className="mr-2 h-4 w-4" />
            Configure
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Temperature</CardTitle>
            <Thermometer className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgTemp}°C</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-red-500" />
              Average across {onlineSensors.length} sensors
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Humidity</CardTitle>
            <Droplets className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgHumidity}%</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Minus className="h-3 w-3" />
              Relative humidity
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Soil Moisture</CardTitle>
            <CloudRain className="h-4 w-4 text-cyan-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgMoisture}%</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <TrendingDown className="h-3 w-3 text-yellow-500" />
              Volumetric water content
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Light</CardTitle>
            <Sun className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_readings_today || 0}</div>
            <p className="text-xs text-muted-foreground">Readings today</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sensors</CardTitle>
            <Wind className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.online_devices || onlineSensors.length}/{stats?.total_devices || sensors.length}</div>
            <p className="text-xs text-muted-foreground">Online</p>
          </CardContent>
        </Card>
      </div>

      {alerts.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <CardTitle className="text-lg">Active Alerts</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge className={getSeverityColor(alert.severity)}>{alert.severity}</Badge>
                    <div>
                      <p className="font-medium text-sm">{alert.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {alert.sensor} • {new Date(alert.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => acknowledgeMutation.mutate(alert.id)}
                    disabled={acknowledgeMutation.isPending}
                  >
                    Dismiss
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sensors">Sensors ({sensors.length})</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="flex gap-4">
            <Select value={selectedLocation} onValueChange={setSelectedLocation}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Location" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Locations</SelectItem>
                {uniqueLocations.map(loc => (
                  <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {filteredSensors.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                <Wind className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No sensors found</p>
                <p className="text-sm">Register sensors to start monitoring</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredSensors.map((sensor) => (
                <Card key={sensor.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`h-2 w-2 rounded-full ${getStatusColor(sensor.status)}`} />
                        <CardTitle className="text-lg">{sensor.name}</CardTitle>
                      </div>
                      <Badge variant="outline">{sensor.status}</Badge>
                    </div>
                    <CardDescription className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />{sensor.location}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center gap-2">
                        <Thermometer className="h-4 w-4 text-orange-500" />
                        <span className="text-sm">{sensor.temperature.toFixed(1)}°C</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Droplets className="h-4 w-4 text-blue-500" />
                        <span className="text-sm">{sensor.humidity}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CloudRain className="h-4 w-4 text-cyan-500" />
                        <span className="text-sm">{sensor.soilMoisture}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Wind className="h-4 w-4 text-gray-500" />
                        <span className="text-sm">{sensor.windSpeed} km/h</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-3 pt-3 border-t text-xs text-muted-foreground">
                      <span>Battery: {sensor.battery}%</span>
                      <span>Signal: {sensor.signal}%</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Updated {sensor.lastUpdate}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="sensors">
          <Card>
            <CardHeader>
              <CardTitle>Sensor Devices</CardTitle>
              <CardDescription>All registered sensor devices in the network</CardDescription>
            </CardHeader>
            <CardContent>
              {sensors.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No sensors registered</p>
              ) : (
                <div className="space-y-4">
                  {sensors.map(sensor => (
                    <div key={sensor.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className={`h-3 w-3 rounded-full ${getStatusColor(sensor.status)}`} />
                        <div>
                          <p className="font-medium">{sensor.name}</p>
                          <p className="text-sm text-muted-foreground">{sensor.location}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <span>Battery: {sensor.battery}%</span>
                        <span>Signal: {sensor.signal}%</span>
                        <Badge variant={sensor.status === 'online' ? 'default' : 'secondary'}>
                          {sensor.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Historical Data</CardTitle>
              <CardDescription>View historical sensor readings and trends</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <p className="text-muted-foreground text-center py-8">
                Historical data visualization coming soon. Use the Telemetry page for detailed time-series data.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default EnvironmentMonitor;

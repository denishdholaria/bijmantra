/**
 * Live Sensor Data
 *
 * Real-time visualization of sensor readings.
 * Connected to /api/v2/sensors/readings endpoints.
 */

import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useActiveWorkspace } from '@/store/workspaceStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Activity,
  AlertCircle,
  Cloud,
  Droplets,
  Gauge,
  Leaf,
  RefreshCw,
  Sun,
  Thermometer,
  Wind,
} from 'lucide-react';
import { LiveSensorChart } from '@/components/charts/LiveSensorChart';

interface SensorReading {
  id: string;
  device_id: string;
  device_name: string;
  sensor: string;
  value: number;
  unit: string;
  timestamp: string;
}

interface Device {
  id: string;
  name: string;
}

const sensorIcons: Record<string, React.ReactNode> = {
  temperature: <Thermometer className="h-5 w-5" />,
  humidity: <Droplets className="h-5 w-5" />,
  pressure: <Gauge className="h-5 w-5" />,
  wind_speed: <Wind className="h-5 w-5" />,
  soil_moisture: <Droplets className="h-5 w-5" />,
  soil_temp: <Thermometer className="h-5 w-5" />,
  ec: <Activity className="h-5 w-5" />,
  ph: <Activity className="h-5 w-5" />,
  leaf_wetness: <Leaf className="h-5 w-5" />,
  par: <Sun className="h-5 w-5" />,
  water_level: <Droplets className="h-5 w-5" />,
  flow_rate: <Activity className="h-5 w-5" />,
};

const sensorLabels: Record<string, string> = {
  temperature: 'Temperature',
  humidity: 'Humidity',
  pressure: 'Pressure',
  wind_speed: 'Wind Speed',
  soil_moisture: 'Soil Moisture',
  soil_temp: 'Soil Temperature',
  ec: 'Electrical Conductivity',
  ph: 'pH Level',
  leaf_wetness: 'Leaf Wetness',
  par: 'PAR (Light)',
  water_level: 'Water Level',
  flow_rate: 'Flow Rate',
};

export function LiveData() {
  const activeWorkspace = useActiveWorkspace();
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('all');
  const [isLive, setIsLive] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLiveReadings = async () => {
    setError(null);
    try {
      const res = await fetch('/api/v2/sensors/readings/live');
      if (res.ok) {
        const data = await res.json();
        setReadings(data.readings || []);
      } else {
        setReadings([]);
      }
    } catch {
      console.error('Failed to fetch live readings');
      setError('Failed to load live sensor data. Please check your connection.');
      setReadings([]);
    }
    setLastUpdate(new Date());
    setLoading(false);
  };

  const fetchDevices = async () => {
    try {
      const res = await fetch('/api/v2/sensors/devices');
      if (res.ok) {
        const data = await res.json();
        setDevices(data.devices?.map((d: any) => ({ id: d.id, name: d.name })) || []);
      }
    } catch {
      // Use devices from readings
    }
  };

  useEffect(() => {
    if (activeWorkspace) {
      fetchLiveReadings();
      fetchDevices();
    }
  }, [activeWorkspace]);

  // Live updates
  useEffect(() => {
    if (!isLive || !activeWorkspace) return;

    const interval = setInterval(() => {
      fetchLiveReadings();
    }, 3000);

    return () => clearInterval(interval);
  }, [isLive, activeWorkspace]);

  if (!activeWorkspace) return <Navigate to="/gateway" />;

  const uniqueDevices = devices.length > 0
    ? devices
    : [...new Map(readings.map(r => [r.device_id, { id: r.device_id, name: r.device_name }])).values()];

  const filteredReadings = selectedDevice === 'all'
    ? readings
    : readings.filter(r => r.device_id === selectedDevice);

  // Group readings by device
  const groupedByDevice = filteredReadings.reduce((acc, reading) => {
    if (!acc[reading.device_id]) {
      acc[reading.device_id] = {
        deviceName: reading.device_name,
        readings: [],
      };
    }
    acc[reading.device_id].readings.push(reading);
    return acc;
  }, {} as Record<string, { deviceName: string; readings: SensorReading[] }>);

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-32" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={fetchLiveReadings} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Activity className="h-8 w-8" />
            Live Sensor Data
          </h1>
          <p className="text-muted-foreground mt-1">
            Real-time readings from all connected sensors
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">
            Last update: {lastUpdate.toLocaleTimeString()}
          </div>
          <Button
            variant={isLive ? 'default' : 'outline'}
            size="sm"
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? (
              <>
                <span className="relative flex h-2 w-2 mr-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                Live
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Paused
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Device Filter */}
      <div className="flex gap-4">
        <Select value={selectedDevice} onValueChange={setSelectedDevice}>
          <SelectTrigger className="w-[250px]">
            <SelectValue placeholder="Select device" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Devices</SelectItem>
            {uniqueDevices.map(device => (
              <SelectItem key={device.id} value={device.id}>
                {device.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Current Conditions Summary */}
      <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <Cloud className="h-5 w-5" />
            Current Conditions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {readings.filter(r => ['temperature', 'humidity', 'wind_speed', 'soil_moisture'].includes(r.sensor)).slice(0, 4).map(reading => (
              <div key={reading.id} className="text-center">
                <div className="text-3xl font-bold">
                  {reading.value.toFixed(1)}
                  <span className="text-lg font-normal text-muted-foreground">{reading.unit}</span>
                </div>
                <div className="text-sm text-muted-foreground">{sensorLabels[reading.sensor]}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Live Streaming Chart */}
      <LiveSensorChart
        title="Real-Time Sensor Trends"
        description="Live streaming data from environmental sensors"
        sensors={[
          { id: 'temp', name: 'Temperature', type: 'temperature', unit: '°C', color: '#ef4444', warningThreshold: 30, criticalThreshold: 35 },
          { id: 'humidity', name: 'Humidity', type: 'humidity', unit: '%', color: '#3b82f6', warningThreshold: 80 },
          { id: 'soil', name: 'Soil Moisture', type: 'soil_moisture', unit: '%', color: '#22c55e', warningThreshold: 30 },
          { id: 'light', name: 'Light (PAR)', type: 'light', unit: 'µmol', color: '#f59e0b' },
        ]}
        pollingInterval={3000}
        maxDataPoints={60}
        height={300}
      />

      {/* Readings by Device */}
      <div className="space-y-4">
        {Object.entries(groupedByDevice).map(([deviceId, { deviceName, readings: deviceReadings }]) => (
          <Card key={deviceId}>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">{deviceName}</CardTitle>
              <CardDescription className="font-mono">{deviceId}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {deviceReadings.map(reading => (
                  <div
                    key={reading.id}
                    className="p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                      {sensorIcons[reading.sensor] || <Activity className="h-5 w-5" />}
                      <span className="text-sm">{sensorLabels[reading.sensor] || reading.sensor}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-bold">
                        {reading.value.toFixed(reading.sensor === 'ph' ? 1 : reading.sensor === 'ec' ? 2 : 1)}
                      </span>
                      <span className="text-muted-foreground">{reading.unit}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
        {Object.keys(groupedByDevice).length === 0 && (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No sensor readings available
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default LiveData;

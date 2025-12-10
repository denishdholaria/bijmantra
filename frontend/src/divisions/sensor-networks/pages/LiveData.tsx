/**
 * Live Sensor Data
 * 
 * Real-time visualization of sensor readings.
 */

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  Cloud,
  Droplets,
  Gauge,
  Leaf,
  RefreshCw,
  Sun,
  Thermometer,
  Wind,
} from 'lucide-react';

interface SensorReading {
  id: string;
  deviceId: string;
  deviceName: string;
  sensor: string;
  value: number;
  unit: string;
  timestamp: string;
  trend: 'up' | 'down' | 'stable';
}

// Simulated live data
const generateReadings = (): SensorReading[] => [
  {
    id: '1',
    deviceId: 'DEV-001',
    deviceName: 'Weather Station Alpha',
    sensor: 'temperature',
    value: 24.5 + (Math.random() - 0.5) * 2,
    unit: '°C',
    timestamp: new Date().toISOString(),
    trend: Math.random() > 0.5 ? 'up' : 'down',
  },
  {
    id: '2',
    deviceId: 'DEV-001',
    deviceName: 'Weather Station Alpha',
    sensor: 'humidity',
    value: 65 + (Math.random() - 0.5) * 10,
    unit: '%',
    timestamp: new Date().toISOString(),
    trend: 'stable',
  },
  {
    id: '3',
    deviceId: 'DEV-001',
    deviceName: 'Weather Station Alpha',
    sensor: 'pressure',
    value: 1013 + (Math.random() - 0.5) * 5,
    unit: 'hPa',
    timestamp: new Date().toISOString(),
    trend: Math.random() > 0.5 ? 'up' : 'down',
  },
  {
    id: '4',
    deviceId: 'DEV-001',
    deviceName: 'Weather Station Alpha',
    sensor: 'wind_speed',
    value: 12 + Math.random() * 8,
    unit: 'km/h',
    timestamp: new Date().toISOString(),
    trend: 'up',
  },
  {
    id: '5',
    deviceId: 'DEV-002',
    deviceName: 'Soil Probe B1',
    sensor: 'soil_moisture',
    value: 42 + (Math.random() - 0.5) * 5,
    unit: '%',
    timestamp: new Date().toISOString(),
    trend: 'down',
  },
  {
    id: '6',
    deviceId: 'DEV-002',
    deviceName: 'Soil Probe B1',
    sensor: 'soil_temp',
    value: 18 + (Math.random() - 0.5) * 2,
    unit: '°C',
    timestamp: new Date().toISOString(),
    trend: 'stable',
  },
  {
    id: '7',
    deviceId: 'DEV-002',
    deviceName: 'Soil Probe B1',
    sensor: 'ec',
    value: 1.2 + (Math.random() - 0.5) * 0.3,
    unit: 'dS/m',
    timestamp: new Date().toISOString(),
    trend: 'stable',
  },
  {
    id: '8',
    deviceId: 'DEV-002',
    deviceName: 'Soil Probe B1',
    sensor: 'ph',
    value: 6.5 + (Math.random() - 0.5) * 0.5,
    unit: '',
    timestamp: new Date().toISOString(),
    trend: 'stable',
  },
  {
    id: '9',
    deviceId: 'DEV-004',
    deviceName: 'Plant Sensor P1',
    sensor: 'leaf_wetness',
    value: Math.random() * 100,
    unit: '%',
    timestamp: new Date().toISOString(),
    trend: 'down',
  },
  {
    id: '10',
    deviceId: 'DEV-004',
    deviceName: 'Plant Sensor P1',
    sensor: 'par',
    value: 800 + Math.random() * 400,
    unit: 'µmol/m²/s',
    timestamp: new Date().toISOString(),
    trend: 'up',
  },
  {
    id: '11',
    deviceId: 'DEV-005',
    deviceName: 'Water Level Sensor',
    sensor: 'water_level',
    value: 75 + (Math.random() - 0.5) * 5,
    unit: '%',
    timestamp: new Date().toISOString(),
    trend: 'down',
  },
  {
    id: '12',
    deviceId: 'DEV-005',
    deviceName: 'Water Level Sensor',
    sensor: 'flow_rate',
    value: 2.5 + Math.random() * 1.5,
    unit: 'L/min',
    timestamp: new Date().toISOString(),
    trend: 'stable',
  },
];

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
  const [readings, setReadings] = useState<SensorReading[]>(generateReadings());
  const [selectedDevice, setSelectedDevice] = useState<string>('all');
  const [isLive, setIsLive] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Simulate live updates
  useEffect(() => {
    if (!isLive) return;
    
    const interval = setInterval(() => {
      setReadings(generateReadings());
      setLastUpdate(new Date());
    }, 3000);

    return () => clearInterval(interval);
  }, [isLive]);

  const devices = [...new Set(readings.map(r => r.deviceId))];
  
  const filteredReadings = selectedDevice === 'all' 
    ? readings 
    : readings.filter(r => r.deviceId === selectedDevice);

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return '↑';
    if (trend === 'down') return '↓';
    return '→';
  };

  const getTrendColor = (trend: string) => {
    if (trend === 'up') return 'text-green-500';
    if (trend === 'down') return 'text-red-500';
    return 'text-gray-500';
  };

  // Group readings by device
  const groupedByDevice = filteredReadings.reduce((acc, reading) => {
    if (!acc[reading.deviceId]) {
      acc[reading.deviceId] = {
        deviceName: reading.deviceName,
        readings: [],
      };
    }
    acc[reading.deviceId].readings.push(reading);
    return acc;
  }, {} as Record<string, { deviceName: string; readings: SensorReading[] }>);

  return (
    <div className="space-y-6 animate-fade-in">
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
            {devices.map(deviceId => {
              const device = readings.find(r => r.deviceId === deviceId);
              return (
                <SelectItem key={deviceId} value={deviceId}>
                  {device?.deviceName || deviceId}
                </SelectItem>
              );
            })}
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
                      {sensorIcons[reading.sensor]}
                      <span className="text-sm">{sensorLabels[reading.sensor]}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-bold">
                        {reading.value.toFixed(reading.sensor === 'ph' ? 1 : reading.sensor === 'ec' ? 2 : 1)}
                      </span>
                      <span className="text-muted-foreground">{reading.unit}</span>
                      <span className={`text-sm ${getTrendColor(reading.trend)}`}>
                        {getTrendIcon(reading.trend)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default LiveData;

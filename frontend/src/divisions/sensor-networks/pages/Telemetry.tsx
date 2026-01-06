/**
 * Telemetry Viewer Page
 *
 * Time-series visualization of sensor data using BrAPI IoT Extension.
 * Endpoint: /brapi/v2/extensions/iot/telemetry
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Activity, Calendar, Download, RefreshCw, TrendingUp } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface TelemetryReading {
  timestamp: string;
  value: number;
  quality: string;
}

interface TelemetryData {
  sensorDbId: string;
  deviceDbId: string;
  sensorType: string;
  unit: string;
  readings: TelemetryReading[];
}

interface Device {
  deviceDbId: string;
  deviceName: string;
  deviceType: string;
  status: string;
}

export function Telemetry() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [telemetryData, setTelemetryData] = useState<TelemetryData[]>([]);
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [downsample, setDownsample] = useState<string>('5min');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch devices
  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const res = await fetch('/brapi/v2/extensions/iot/devices');
        if (res.ok) {
          const data = await res.json();
          setDevices(data.result?.data || []);
          if (data.result?.data?.length > 0) {
            setSelectedDevice(data.result.data[0].deviceDbId);
          }
        }
      } catch (error) {
        console.error('Failed to fetch devices:', error);
        // No data available - show empty state
        setDevices([]);
      } finally {
        setLoading(false);
      }
    };
    fetchDevices();
  }, []);

  // Fetch telemetry when device or time range changes
  useEffect(() => {
    if (!selectedDevice) return;
    
    const fetchTelemetry = async () => {
      setRefreshing(true);
      
      // Calculate time range
      const endTime = new Date();
      const startTime = new Date();
      switch (timeRange) {
        case '1h': startTime.setHours(startTime.getHours() - 1); break;
        case '6h': startTime.setHours(startTime.getHours() - 6); break;
        case '24h': startTime.setHours(startTime.getHours() - 24); break;
        case '7d': startTime.setDate(startTime.getDate() - 7); break;
        case '30d': startTime.setDate(startTime.getDate() - 30); break;
      }
      
      try {
        const params = new URLSearchParams({
          deviceDbId: selectedDevice,
          startTime: startTime.toISOString(),
          endTime: endTime.toISOString(),
          downsample: downsample,
        });
        
        const res = await fetch(`/brapi/v2/extensions/iot/telemetry?${params}`);
        if (res.ok) {
          const data = await res.json();
          setTelemetryData(data.result?.data || []);
        }
      } catch (error) {
        console.error('Failed to fetch telemetry:', error);
        // No data available - show empty state
        setTelemetryData([]);
      } finally {
        setRefreshing(false);
      }
    };
    
    fetchTelemetry();
  }, [selectedDevice, timeRange, downsample]);

  const formatChartData = () => {
    if (telemetryData.length === 0) return [];
    
    // Merge all sensor readings by timestamp
    const dataMap = new Map<string, Record<string, string | number>>();
    
    telemetryData.forEach(sensor => {
      sensor.readings.forEach(reading => {
        const time = new Date(reading.timestamp).toLocaleTimeString();
        if (!dataMap.has(time)) {
          dataMap.set(time, { time });
        }
        dataMap.get(time)![sensor.sensorType] = reading.value;
      });
    });
    
    return Array.from(dataMap.values());
  };

  const sensorColors: Record<string, string> = {
    air_temperature: '#ef4444',
    relative_humidity: '#3b82f6',
    soil_moisture: '#f59e0b',
    soil_temperature: '#10b981',
    atmospheric_pressure: '#8b5cf6',
    wind_speed: '#06b6d4',
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <TrendingUp className="h-8 w-8" />
            Telemetry Viewer
          </h1>
          <p className="text-muted-foreground mt-1">
            Time-series sensor data visualization (BrAPI IoT Extension)
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setRefreshing(true)} disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-2 block">Device</label>
              <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                <SelectTrigger>
                  <SelectValue placeholder="Select device" />
                </SelectTrigger>
                <SelectContent>
                  {devices.map(device => (
                    <SelectItem key={device.deviceDbId} value={device.deviceDbId}>
                      {device.deviceName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-[150px]">
              <label className="text-sm font-medium mb-2 block">Time Range</label>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">Last 1 hour</SelectItem>
                  <SelectItem value="6h">Last 6 hours</SelectItem>
                  <SelectItem value="24h">Last 24 hours</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-[150px]">
              <label className="text-sm font-medium mb-2 block">Downsample</label>
              <Select value={downsample} onValueChange={setDownsample}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1min">1 minute</SelectItem>
                  <SelectItem value="5min">5 minutes</SelectItem>
                  <SelectItem value="1hour">1 hour</SelectItem>
                  <SelectItem value="1day">1 day</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-end">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Sensor Readings
          </CardTitle>
          <CardDescription>
            {telemetryData.length} sensor(s) • {telemetryData[0]?.readings.length || 0} data points
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={formatChartData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                {telemetryData.map(sensor => (
                  <Line
                    key={sensor.sensorDbId}
                    type="monotone"
                    dataKey={sensor.sensorType}
                    name={`${sensor.sensorType.replace('_', ' ')} (${sensor.unit})`}
                    stroke={sensorColors[sensor.sensorType] || '#666'}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Sensor Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {telemetryData.map(sensor => {
          const latest = sensor.readings[sensor.readings.length - 1];
          const values = sensor.readings.map(r => r.value);
          const min = Math.min(...values);
          const max = Math.max(...values);
          const avg = values.reduce((a, b) => a + b, 0) / values.length;
          
          return (
            <Card key={sensor.sensorDbId}>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg capitalize">
                  {sensor.sensorType.replace('_', ' ')}
                </CardTitle>
                <CardDescription>{sensor.sensorDbId}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold mb-2">
                  {latest?.value.toFixed(1)} {sensor.unit}
                </div>
                <div className="grid grid-cols-3 gap-2 text-sm text-muted-foreground">
                  <div>
                    <div className="font-medium">Min</div>
                    <div>{min.toFixed(1)}</div>
                  </div>
                  <div>
                    <div className="font-medium">Avg</div>
                    <div>{avg.toFixed(1)}</div>
                  </div>
                  <div>
                    <div className="font-medium">Max</div>
                    <div>{max.toFixed(1)}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

export default Telemetry;

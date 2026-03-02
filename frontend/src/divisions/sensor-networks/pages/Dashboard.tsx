/**
 * Sensor Networks Dashboard
 *
 * IoT sensors and environmental monitoring network.
 * Connected to /api/v2/sensors endpoints.
 */

import { useState, useEffect } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useActiveWorkspace } from '@/store/workspaceStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Activity,
  AlertTriangle,
  Bell,
  Radio,
  RefreshCw,
  Thermometer,
  Wifi,
  WifiOff,
  Plug,
  Droplets,
  Wind,
  Gauge,
} from 'lucide-react';

interface NetworkStats {
  total_devices: number;
  online: number;
  offline: number;
  warning: number;
  total_readings: number;
  active_alerts: number;
}

interface LiveReading {
  device_id: string;
  device_name: string;
  sensor: string;
  value: number;
  unit: string;
  timestamp: string;
}

export function Dashboard() {
  const activeWorkspace = useActiveWorkspace();
  const [stats, setStats] = useState<NetworkStats | null>(null);
  const [liveReadings, setLiveReadings] = useState<LiveReading[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setError(null);
    try {
      const [statsRes, liveRes] = await Promise.all([
        fetch('/api/v2/sensors/stats'),
        fetch('/api/v2/sensors/readings/live'),
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      } else {
        setStats(null);
      }

      if (liveRes.ok) {
        const liveData = await liveRes.json();
        setLiveReadings(liveData.readings || []);
      } else {
        setLiveReadings([]);
      }
    } catch (err) {
      console.error('Failed to fetch sensor data:', err);
      setError('Failed to load sensor data. Please check your connection.');
      // Zero Mock Data Policy: show empty state on error
      setStats(null);
      setLiveReadings([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (activeWorkspace) {
      fetchData();
      // Auto-refresh every 30 seconds
      const interval = setInterval(fetchData, 30000);
      return () => clearInterval(interval);
    }
  }, [activeWorkspace]);

  if (!activeWorkspace) return <Navigate to="/gateway" />;

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const quickActions = [
    { icon: <Radio className="h-5 w-5" />, label: 'Manage Devices', path: '/sensor-networks/devices' },
    { icon: <Activity className="h-5 w-5" />, label: 'Live Data', path: '/sensor-networks/live' },
    { icon: <Bell className="h-5 w-5" />, label: 'Alerts', path: '/sensor-networks/alerts' },
    // BrAPI IoT Extension
    { icon: <Gauge className="h-5 w-5" />, label: 'Telemetry', path: '/sensor-networks/telemetry' },
    { icon: <Plug className="h-5 w-5" />, label: 'Aggregates', path: '/sensor-networks/aggregates' },
    { icon: <Wifi className="h-5 w-5" />, label: 'Environment Links', path: '/sensor-networks/environment-links' },
  ];

  const getSensorIcon = (sensor: string) => {
    const icons: Record<string, React.ReactNode> = {
      temperature: <Thermometer className="h-4 w-4 text-red-500" />,
      humidity: <Droplets className="h-4 w-4 text-blue-500" />,
      soil_moisture: <Droplets className="h-4 w-4 text-amber-600" />,
      wind_speed: <Wind className="h-4 w-4 text-cyan-500" />,
      pressure: <Gauge className="h-4 w-4 text-purple-500" />,
    };
    return icons[sensor] || <Activity className="h-4 w-4 text-gray-500" />;
  };

  const formatTimestamp = (ts: string) => {
    const date = new Date(ts);
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
    return date.toLocaleTimeString();
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-48" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Radio className="h-8 w-8" />
            Sensor Networks
          </h1>
          <p className="text-muted-foreground mt-1">
            IoT sensors and environmental monitoring network
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing} aria-label="Refresh sensor data">
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
              {refreshing ? <RefreshCw className="h-4 w-4 animate-spin" /> : 'Retry'}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Radio className="h-6 w-6 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{stats?.total_devices || 0}</p>
                <p className="text-xs text-muted-foreground">Total Devices</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Wifi className="h-6 w-6 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{stats?.online || 0}</p>
                <p className="text-xs text-muted-foreground">Online</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Activity className="h-6 w-6 text-yellow-500" />
              <div>
                <p className="text-2xl font-bold">{stats?.warning || 0}</p>
                <p className="text-xs text-muted-foreground">Warning</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <WifiOff className="h-6 w-6 text-gray-500" />
              <div>
                <p className="text-2xl font-bold">{stats?.offline || 0}</p>
                <p className="text-xs text-muted-foreground">Offline</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 text-red-500" />
              <div>
                <p className="text-2xl font-bold">{stats?.active_alerts || 0}</p>
                <p className="text-xs text-muted-foreground">Active Alerts</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {quickActions.map((action, i) => (
              <Link key={i} to={action.path}>
                <Button variant="outline" className="gap-2">
                  {action.icon}
                  {action.label}
                </Button>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Recent Readings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Thermometer className="h-5 w-5" />
              Live Readings
            </CardTitle>
            <CardDescription>Real-time sensor data</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {liveReadings.slice(0, 6).map((reading, i) => (
                <div key={i} className="flex items-center justify-between p-2 border rounded">
                  <div className="flex items-center gap-2">
                    {getSensorIcon(reading.sensor)}
                    <div>
                      <div className="font-medium capitalize">{reading.sensor.replace('_', ' ')}</div>
                      <div className="text-xs text-muted-foreground">{reading.device_name}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold">{reading.value}{reading.unit}</div>
                    <div className="text-xs text-muted-foreground">{formatTimestamp(reading.timestamp)}</div>
                  </div>
                </div>
              ))}
              {liveReadings.length === 0 && (
                <p className="text-center text-muted-foreground py-4">No live readings available</p>
              )}
            </div>
            <Link to="/sensor-networks/live">
              <Button variant="outline" className="w-full mt-4">
                View All Live Data
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Integration Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plug className="h-5 w-5 text-primary" />
              Integration Status
            </CardTitle>
            <CardDescription>Connected services and protocols</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-2 border rounded">
                <span>LoRaWAN Gateway</span>
                <Badge className="bg-green-100 text-green-700">Connected</Badge>
              </div>
              <div className="flex items-center justify-between p-2 border rounded">
                <span>MQTT Broker</span>
                <Badge className="bg-green-100 text-green-700">Connected</Badge>
              </div>
              <div className="flex items-center justify-between p-2 border rounded">
                <span>TimescaleDB</span>
                <Badge className="bg-green-100 text-green-700">Connected</Badge>
              </div>
              <div className="flex items-center justify-between p-2 border rounded">
                <span>Weather API</span>
                <Badge className="bg-yellow-100 text-yellow-700">Limited</Badge>
              </div>
            </div>
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                <strong>Total Readings:</strong> {stats?.total_readings?.toLocaleString() || 0}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;

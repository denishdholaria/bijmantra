/**
 * Sensor Networks Dashboard
 *
 * IoT sensors and environmental monitoring network.
 */

import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Activity,
  AlertTriangle,
  Bell,
  Radio,
  Thermometer,
  Wifi,
  WifiOff,
} from 'lucide-react';

export function Dashboard() {
  // Demo stats
  const stats = {
    totalDevices: 7,
    online: 5,
    offline: 1,
    warning: 1,
    activeAlerts: 1,
  };

  const quickActions = [
    { icon: <Radio className="h-5 w-5" />, label: 'Manage Devices', path: '/sensor-networks/devices' },
    { icon: <Activity className="h-5 w-5" />, label: 'Live Data', path: '/sensor-networks/live' },
    { icon: <Bell className="h-5 w-5" />, label: 'Alerts', path: '/sensor-networks/alerts' },
  ];

  const recentReadings = [
    { sensor: 'Temperature', value: '24.5°C', device: 'Weather Station Alpha', time: '2 min ago' },
    { sensor: 'Soil Moisture', value: '42%', device: 'Soil Probe B1', time: '5 min ago' },
    { sensor: 'Humidity', value: '65%', device: 'Weather Station Alpha', time: '2 min ago' },
    { sensor: 'Wind Speed', value: '15 km/h', device: 'Weather Station Alpha', time: '2 min ago' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
          <Radio className="h-8 w-8" />
          Sensor Networks
        </h1>
        <p className="text-muted-foreground mt-1">
          IoT sensors and environmental monitoring network
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Radio className="h-6 w-6 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{stats.totalDevices}</p>
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
                <p className="text-2xl font-bold">{stats.online}</p>
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
                <p className="text-2xl font-bold">{stats.warning}</p>
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
                <p className="text-2xl font-bold">{stats.offline}</p>
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
                <p className="text-2xl font-bold">{stats.activeAlerts}</p>
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
              Recent Readings
            </CardTitle>
            <CardDescription>Latest sensor data</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentReadings.map((reading, i) => (
                <div key={i} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <div className="font-medium">{reading.sensor}</div>
                    <div className="text-xs text-muted-foreground">{reading.device}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold">{reading.value}</div>
                    <div className="text-xs text-muted-foreground">{reading.time}</div>
                  </div>
                </div>
              ))}
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
            <CardTitle>🔌 Integration Status</CardTitle>
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;

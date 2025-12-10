/**
 * Sensor Devices Management
 * 
 * Register, configure, and monitor IoT sensor devices.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Activity,
  Battery,
  MapPin,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Settings,
  Signal,
  Thermometer,
  Wifi,
  WifiOff,
} from 'lucide-react';

interface SensorDevice {
  id: string;
  name: string;
  type: 'weather' | 'soil' | 'plant' | 'water' | 'gateway';
  status: 'online' | 'offline' | 'warning';
  battery: number;
  signal: number;
  location: string;
  fieldId?: string;
  lastSeen: string;
  firmware: string;
  sensors: string[];
}

// Demo data
const devices: SensorDevice[] = [
  {
    id: 'DEV-001',
    name: 'Weather Station Alpha',
    type: 'weather',
    status: 'online',
    battery: 85,
    signal: 92,
    location: 'Field A - North',
    fieldId: 'field-1',
    lastSeen: '2 min ago',
    firmware: 'v2.1.0',
    sensors: ['temperature', 'humidity', 'pressure', 'wind', 'rain'],
  },
  {
    id: 'DEV-002',
    name: 'Soil Probe B1',
    type: 'soil',
    status: 'online',
    battery: 72,
    signal: 78,
    location: 'Field B - Block 1',
    fieldId: 'field-2',
    lastSeen: '5 min ago',
    firmware: 'v1.8.2',
    sensors: ['soil_moisture', 'soil_temp', 'ec', 'ph'],
  },
  {
    id: 'DEV-003',
    name: 'Soil Probe B2',
    type: 'soil',
    status: 'warning',
    battery: 15,
    signal: 65,
    location: 'Field B - Block 2',
    fieldId: 'field-2',
    lastSeen: '10 min ago',
    firmware: 'v1.8.2',
    sensors: ['soil_moisture', 'soil_temp', 'ec'],
  },
  {
    id: 'DEV-004',
    name: 'Plant Sensor P1',
    type: 'plant',
    status: 'online',
    battery: 90,
    signal: 88,
    location: 'Greenhouse 1',
    lastSeen: '1 min ago',
    firmware: 'v3.0.1',
    sensors: ['leaf_wetness', 'canopy_temp', 'par'],
  },
  {
    id: 'DEV-005',
    name: 'Water Level Sensor',
    type: 'water',
    status: 'online',
    battery: 95,
    signal: 90,
    location: 'Irrigation Tank',
    lastSeen: '3 min ago',
    firmware: 'v1.2.0',
    sensors: ['water_level', 'water_temp', 'flow_rate'],
  },
  {
    id: 'GW-001',
    name: 'LoRa Gateway Main',
    type: 'gateway',
    status: 'online',
    battery: 100,
    signal: 100,
    location: 'Central Building',
    lastSeen: 'Just now',
    firmware: 'v4.2.0',
    sensors: [],
  },
  {
    id: 'DEV-006',
    name: 'Weather Station Beta',
    type: 'weather',
    status: 'offline',
    battery: 0,
    signal: 0,
    location: 'Field C - South',
    fieldId: 'field-3',
    lastSeen: '2 days ago',
    firmware: 'v2.0.5',
    sensors: ['temperature', 'humidity', 'pressure'],
  },
];

const deviceTypes = [
  { value: 'weather', label: 'Weather Station', icon: '🌤️' },
  { value: 'soil', label: 'Soil Sensor', icon: '🌱' },
  { value: 'plant', label: 'Plant Sensor', icon: '🌿' },
  { value: 'water', label: 'Water Sensor', icon: '💧' },
  { value: 'gateway', label: 'Gateway', icon: '📡' },
];

export function Devices() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [dialogOpen, setDialogOpen] = useState(false);

  const filteredDevices = devices.filter(device => {
    const matchesSearch = device.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.location.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || device.status === statusFilter;
    const matchesType = typeFilter === 'all' || device.type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const stats = {
    total: devices.length,
    online: devices.filter(d => d.status === 'online').length,
    offline: devices.filter(d => d.status === 'offline').length,
    warning: devices.filter(d => d.status === 'warning').length,
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      online: 'bg-green-100 text-green-700',
      offline: 'bg-gray-100 text-gray-700',
      warning: 'bg-yellow-100 text-yellow-700',
    };
    return <Badge className={styles[status]}>{status}</Badge>;
  };

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      weather: '🌤️',
      soil: '🌱',
      plant: '🌿',
      water: '💧',
      gateway: '📡',
    };
    return icons[type] || '📟';
  };

  const getBatteryColor = (level: number) => {
    if (level > 50) return 'text-green-500';
    if (level > 20) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getSignalColor = (level: number) => {
    if (level > 70) return 'text-green-500';
    if (level > 40) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Radio className="h-8 w-8" />
            Sensor Devices
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor IoT sensor devices
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Device
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Register New Device</DialogTitle>
                <DialogDescription>
                  Add a new sensor device to the network.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Device ID</Label>
                  <Input placeholder="DEV-XXX or scan QR code" />
                </div>
                <div className="space-y-2">
                  <Label>Device Name</Label>
                  <Input placeholder="e.g., Weather Station Field A" />
                </div>
                <div className="space-y-2">
                  <Label>Device Type</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {deviceTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.icon} {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Location</Label>
                  <Input placeholder="e.g., Field A - North" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setDialogOpen(false)}>
                  Register Device
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Radio className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-sm text-muted-foreground">Total Devices</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Wifi className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{stats.online}</p>
                <p className="text-sm text-muted-foreground">Online</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-yellow-500" />
              <div>
                <p className="text-2xl font-bold">{stats.warning}</p>
                <p className="text-sm text-muted-foreground">Warning</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <WifiOff className="h-8 w-8 text-gray-500" />
              <div>
                <p className="text-2xl font-bold">{stats.offline}</p>
                <p className="text-sm text-muted-foreground">Offline</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search devices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="online">Online</SelectItem>
            <SelectItem value="warning">Warning</SelectItem>
            <SelectItem value="offline">Offline</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {deviceTypes.map(type => (
              <SelectItem key={type.value} value={type.value}>
                {type.icon} {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Device Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Device</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Battery</TableHead>
                <TableHead>Signal</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDevices.map(device => (
                <TableRow key={device.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{device.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{device.id}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-lg mr-1">{getTypeIcon(device.type)}</span>
                    <span className="capitalize">{device.type}</span>
                  </TableCell>
                  <TableCell>{getStatusBadge(device.status)}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Battery className={`h-4 w-4 ${getBatteryColor(device.battery)}`} />
                      <span>{device.battery}%</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Signal className={`h-4 w-4 ${getSignalColor(device.signal)}`} />
                      <span>{device.signal}%</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      {device.location}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{device.lastSeen}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon">
                      <Settings className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export default Devices;

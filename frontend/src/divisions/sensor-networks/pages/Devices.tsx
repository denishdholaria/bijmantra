/**
 * Sensor Devices Management
 *
 * Register, configure, and monitor IoT sensor devices.
 * Connected to /api/v2/sensors/devices endpoints.
 */

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
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
  Wifi,
  WifiOff,
  Trash2,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface SensorDevice {
  id: string;
  name: string;
  device_type: string;
  status: 'online' | 'offline' | 'warning';
  battery: number;
  signal: number;
  location: string;
  field_id?: string;
  last_seen: string;
  firmware: string;
  sensors: string[];
}

interface DeviceType {
  value: string;
  label: string;
  icon: string;
}

export function Devices() {
  const [devices, setDevices] = useState<SensorDevice[]>([]);
  const [deviceTypes, setDeviceTypes] = useState<DeviceType[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  // Form state
  const [newDevice, setNewDevice] = useState({
    device_id: '',
    name: '',
    device_type: '',
    location: '',
    sensors: [] as string[],
  });

  const fetchDevices = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.append('status', statusFilter);
      if (typeFilter !== 'all') params.append('device_type', typeFilter);

      const res = await fetch(`/api/v2/sensors/devices?${params}`);
      if (res.ok) {
        const data = await res.json();
        setDevices(data.devices || []);
      }
    } catch (error) {
      console.error('Failed to fetch devices:', error);
      setDevices([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchDeviceTypes = async () => {
    try {
      const res = await fetch('/api/v2/sensors/device-types');
      if (res.ok) {
        const data = await res.json();
        setDeviceTypes(data.types || []);
      }
    } catch {
      setDeviceTypes([
        { value: 'weather', label: 'Weather Station', icon: '🌤️' },
        { value: 'soil', label: 'Soil Sensor', icon: '🌱' },
        { value: 'plant', label: 'Plant Sensor', icon: '🌿' },
        { value: 'water', label: 'Water Sensor', icon: '💧' },
        { value: 'gateway', label: 'Gateway', icon: '📡' },
      ]);
    }
  };

  useEffect(() => {
    fetchDevices();
    fetchDeviceTypes();
  }, [statusFilter, typeFilter]);

  const handleRegisterDevice = async () => {
    if (!newDevice.device_id || !newDevice.name || !newDevice.device_type) {
      toast({ title: 'Error', description: 'Please fill in all required fields', variant: 'destructive' });
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch('/api/v2/sensors/devices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newDevice,
          sensors: getSensorsForType(newDevice.device_type),
        }),
      });

      if (res.ok) {
        toast({ title: 'Success', description: 'Device registered successfully' });
        setDialogOpen(false);
        setNewDevice({ device_id: '', name: '', device_type: '', location: '', sensors: [] });
        fetchDevices();
      } else {
        const error = await res.json();
        toast({ title: 'Error', description: error.detail || 'Failed to register device', variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to register device', variant: 'destructive' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteDevice = async (deviceId: string) => {
    if (!confirm('Are you sure you want to remove this device?')) return;

    try {
      const res = await fetch(`/api/v2/sensors/devices/${deviceId}`, { method: 'DELETE' });
      if (res.ok) {
        toast({ title: 'Success', description: 'Device removed successfully' });
        fetchDevices();
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to remove device', variant: 'destructive' });
    }
  };

  const getSensorsForType = (type: string): string[] => {
    const sensorMap: Record<string, string[]> = {
      weather: ['temperature', 'humidity', 'pressure', 'wind_speed', 'rainfall'],
      soil: ['soil_moisture', 'soil_temp', 'ec', 'ph'],
      plant: ['leaf_wetness', 'canopy_temp', 'par'],
      water: ['water_level', 'water_temp', 'flow_rate'],
      gateway: [],
    };
    return sensorMap[type] || [];
  };

  const filteredDevices = devices.filter(device => {
    const matchesSearch = device.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.location.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
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

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

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
          <Button variant="outline" size="sm" onClick={() => fetchDevices()}>
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
                  <Label>Device ID *</Label>
                  <Input
                    placeholder="DEV-XXX or scan QR code"
                    value={newDevice.device_id}
                    onChange={(e) => setNewDevice({ ...newDevice, device_id: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Device Name *</Label>
                  <Input
                    placeholder="e.g., Weather Station Field A"
                    value={newDevice.name}
                    onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Device Type *</Label>
                  <Select
                    value={newDevice.device_type}
                    onValueChange={(v) => setNewDevice({ ...newDevice, device_type: v })}
                  >
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
                  <Input
                    placeholder="e.g., Field A - North"
                    value={newDevice.location}
                    onChange={(e) => setNewDevice({ ...newDevice, location: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleRegisterDevice} disabled={submitting}>
                  {submitting ? 'Registering...' : 'Register Device'}
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
                <TableHead className="w-[80px]"></TableHead>
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
                    <span className="text-lg mr-1">{getTypeIcon(device.device_type)}</span>
                    <span className="capitalize">{device.device_type}</span>
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
                  <TableCell className="text-muted-foreground">{device.last_seen}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => handleDeleteDevice(device.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {filteredDevices.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                    No devices found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export default Devices;

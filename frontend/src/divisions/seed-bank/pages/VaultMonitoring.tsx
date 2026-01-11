import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
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
  Thermometer,
  Droplets,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Activity,
  Settings,
  Bell,
  History,
  Gauge,
  Snowflake,
  Flame,
} from 'lucide-react';

interface VaultCondition {
  vault_id: string;
  vault_name: string;
  vault_type: string;
  sensor_status: string;
  last_reading: string;
  current_readings: Record<string, number | string>;
  thresholds: Record<string, { min: number; max: number; unit: string }>;
  status: string;
  alerts_count: number;
}

interface Alert {
  id: string;
  vault_id: string;
  vault_name: string;
  sensor_type: string;
  severity: string;
  message: string;
  value: number | string;
  threshold: number | null;
  condition: string;
  timestamp: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
}

interface Reading {
  id: string;
  sensor_id: string;
  vault_id: string;
  sensor_type: string;
  value: number;
  unit: string;
  timestamp: string;
}

interface Statistics {
  total_sensors: number;
  online: number;
  warning: number;
  offline: number;
  by_vault_type: Record<string, number>;
  total_readings_24h: number;
  active_alerts: number;
  critical_alerts: number;
}

export function VaultMonitoring() {
  const [conditions, setConditions] = useState<VaultCondition[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [readings, setReadings] = useState<Reading[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedVault, setSelectedVault] = useState<string>('all');
  const [alertFilter, setAlertFilter] = useState<string>('unacknowledged');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [condRes, alertRes, statsRes, readingsRes] = await Promise.all([
        fetch('/api/v2/vault-sensors/conditions'),
        fetch('/api/v2/vault-sensors/alerts?limit=50'),
        fetch('/api/v2/vault-sensors/statistics'),
        fetch('/api/v2/vault-sensors/readings?hours=24&limit=100'),
      ]);

      if (condRes.ok) {
        const data = await condRes.json();
        setConditions(data.conditions || []);
      }
      if (alertRes.ok) {
        const data = await alertRes.json();
        setAlerts(data.alerts || []);
      }
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStatistics(data);
      }
      if (readingsRes.ok) {
        const data = await readingsRes.json();
        setReadings(data.readings || []);
      }
    } catch (err) {
      console.error('Failed to fetch vault sensor data:', err);
      // Set empty state - no demo data
      setConditions([]);
      setAlerts([]);
      setStatistics(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v2/vault-sensors/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: 'admin' }),
      });
      if (response.ok) {
        fetchData();
      }
    } catch (err) {
      // Update locally for demo
      setAlerts(alerts.map(a => 
        a.id === alertId 
          ? { ...a, acknowledged: true, acknowledged_by: 'admin', acknowledged_at: new Date().toISOString() }
          : a
      ));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical': return <Badge className="bg-red-100 text-red-800">Critical</Badge>;
      case 'warning': return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      case 'info': return <Badge className="bg-blue-100 text-blue-800">Info</Badge>;
      default: return <Badge variant="secondary">{severity}</Badge>;
    }
  };

  const getVaultIcon = (type: string) => {
    switch (type) {
      case 'base': return <Snowflake className="h-5 w-5 text-blue-500" />;
      case 'cryo': return <Snowflake className="h-5 w-5 text-cyan-500" />;
      case 'active': return <Thermometer className="h-5 w-5 text-green-500" />;
      default: return <Gauge className="h-5 w-5" />;
    }
  };

  const filteredAlerts = alerts.filter(a => {
    if (alertFilter === 'unacknowledged') return !a.acknowledged;
    if (alertFilter === 'acknowledged') return a.acknowledged;
    return true;
  }).filter(a => selectedVault === 'all' || a.vault_id === selectedVault);

  const formatTimestamp = (ts: string) => {
    const date = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) return date.toLocaleDateString();
    if (hours > 0) return `${hours}h ${minutes}m ago`;
    return `${minutes}m ago`;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6" />
            Vault Environmental Monitoring
          </h1>
          <p className="text-muted-foreground">
            Real-time monitoring of seed storage conditions
          </p>
        </div>
        <Button onClick={fetchData} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {statistics && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold">{statistics.total_sensors}</p>
              <p className="text-sm text-muted-foreground">Total Sensors</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-600">{statistics.online}</p>
              <p className="text-sm text-muted-foreground">Online</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-yellow-600">{statistics.warning}</p>
              <p className="text-sm text-muted-foreground">Warning</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-red-600">{statistics.active_alerts}</p>
              <p className="text-sm text-muted-foreground">Active Alerts</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold">{statistics.total_readings_24h}</p>
              <p className="text-sm text-muted-foreground">Readings (24h)</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-red-600">{statistics.critical_alerts}</p>
              <p className="text-sm text-muted-foreground">Critical</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="conditions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="conditions">
            <Gauge className="h-4 w-4 mr-2" />
            Conditions
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <Bell className="h-4 w-4 mr-2" />
            Alerts ({alerts.filter(a => !a.acknowledged).length})
          </TabsTrigger>
          <TabsTrigger value="history">
            <History className="h-4 w-4 mr-2" />
            History
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="h-4 w-4 mr-2" />
            Thresholds
          </TabsTrigger>
        </TabsList>

        {/* Conditions Tab */}
        <TabsContent value="conditions">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {conditions.map((vault) => (
              <Card key={vault.vault_id} className={vault.status === 'critical' ? 'border-red-500' : vault.status === 'warning' ? 'border-yellow-500' : ''}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getVaultIcon(vault.vault_type)}
                      <CardTitle className="text-lg">{vault.vault_name}</CardTitle>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(vault.status)}`} />
                  </div>
                  <CardDescription>
                    {vault.vault_type === 'base' && 'Long-term storage (-18°C to -20°C)'}
                    {vault.vault_type === 'active' && 'Working collection (2°C to 8°C)'}
                    {vault.vault_type === 'cryo' && 'Cryopreservation (-196°C)'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Temperature */}
                    <div className="flex items-center justify-between p-2 bg-muted rounded">
                      <div className="flex items-center gap-2">
                        <Thermometer className="h-4 w-4 text-blue-500" />
                        <span className="text-sm">Temperature</span>
                      </div>
                      <span className="font-mono font-bold">
                        {typeof vault.current_readings.temperature === 'number'
                          ? `${vault.current_readings.temperature.toFixed(1)}°C`
                          : 'N/A'}
                      </span>
                    </div>

                    {/* Humidity */}
                    <div className="flex items-center justify-between p-2 bg-muted rounded">
                      <div className="flex items-center gap-2">
                        <Droplets className="h-4 w-4 text-cyan-500" />
                        <span className="text-sm">Humidity</span>
                      </div>
                      <span className="font-mono font-bold">
                        {typeof vault.current_readings.humidity === 'number'
                          ? `${vault.current_readings.humidity.toFixed(1)}%`
                          : 'N/A'}
                      </span>
                    </div>

                    {/* Nitrogen Level (for cryo) */}
                    {vault.current_readings.nitrogen_level !== undefined && (
                      <div className="flex items-center justify-between p-2 bg-muted rounded">
                        <div className="flex items-center gap-2">
                          <Gauge className="h-4 w-4 text-purple-500" />
                          <span className="text-sm">Nitrogen</span>
                        </div>
                        <span className="font-mono font-bold">
                          {vault.current_readings.nitrogen_level}%
                        </span>
                      </div>
                    )}

                    {/* Door Status */}
                    {vault.current_readings.door_status && (
                      <div className="flex items-center justify-between p-2 bg-muted rounded">
                        <span className="text-sm">Door</span>
                        <Badge variant={vault.current_readings.door_status === 'closed' ? 'secondary' : 'destructive'}>
                          {vault.current_readings.door_status}
                        </Badge>
                      </div>
                    )}

                    {/* Alerts */}
                    {vault.alerts_count > 0 && (
                      <div className="flex items-center gap-2 text-yellow-600 text-sm">
                        <AlertTriangle className="h-4 w-4" />
                        {vault.alerts_count} active alert{vault.alerts_count > 1 ? 's' : ''}
                      </div>
                    )}

                    <p className="text-xs text-muted-foreground">
                      Last reading: {formatTimestamp(vault.last_reading)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Alert History</CardTitle>
                <div className="flex gap-2">
                  <Select value={selectedVault} onValueChange={setSelectedVault}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Filter by vault" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Vaults</SelectItem>
                      {conditions.map(v => (
                        <SelectItem key={v.vault_id} value={v.vault_id}>{v.vault_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={alertFilter} onValueChange={setAlertFilter}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Filter status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Alerts</SelectItem>
                      <SelectItem value="unacknowledged">Unacknowledged</SelectItem>
                      <SelectItem value="acknowledged">Acknowledged</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {filteredAlerts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                  <p>No alerts matching your filters</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredAlerts.map((alert) => (
                    <div
                      key={alert.id}
                      className={`p-4 border rounded-lg ${alert.acknowledged ? 'bg-muted/50' : 'bg-background'}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className={`h-5 w-5 mt-0.5 ${
                            alert.severity === 'critical' ? 'text-red-500' :
                            alert.severity === 'warning' ? 'text-yellow-500' : 'text-blue-500'
                          }`} />
                          <div>
                            <p className="font-medium">{alert.message}</p>
                            <p className="text-sm text-muted-foreground">
                              {alert.vault_name} • {alert.sensor_type}
                            </p>
                            <p className="text-sm">
                              Value: <span className="font-mono">{alert.value}</span>
                              {alert.threshold && (
                                <> • Threshold: <span className="font-mono">{alert.threshold}</span></>
                              )}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {formatTimestamp(alert.timestamp)}
                              {alert.acknowledged && alert.acknowledged_by && (
                                <> • Acknowledged by {alert.acknowledged_by}</>
                              )}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getSeverityBadge(alert.severity)}
                          {!alert.acknowledged && (
                            <Button size="sm" variant="outline" onClick={() => acknowledgeAlert(alert.id)}>
                              Acknowledge
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Reading History (Last 24 Hours)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">
                Historical sensor readings for trend analysis
              </p>
              <div className="text-center py-8 text-muted-foreground">
                <History className="h-12 w-12 mx-auto mb-2" />
                <p>Chart visualization coming soon</p>
                <p className="text-sm">{readings.length} readings in the last 24 hours</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Threshold Configuration</CardTitle>
              <CardDescription>
                Configure alert thresholds for each vault type
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {conditions.map((vault) => (
                  <div key={vault.vault_id} className="p-4 border rounded-lg">
                    <h3 className="font-medium mb-3 flex items-center gap-2">
                      {getVaultIcon(vault.vault_type)}
                      {vault.vault_name}
                    </h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      {Object.entries(vault.thresholds).map(([sensor, thresh]) => (
                        <div key={sensor} className="space-y-2">
                          <label className="text-sm font-medium capitalize">{sensor}</label>
                          <div className="flex items-center gap-2">
                            <Input
                              type="number"
                              value={thresh.min}
                              className="w-24"
                              disabled
                            />
                            <span className="text-muted-foreground">to</span>
                            <Input
                              type="number"
                              value={thresh.max}
                              className="w-24"
                              disabled
                            />
                            <span className="text-sm text-muted-foreground">{thresh.unit}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default VaultMonitoring;

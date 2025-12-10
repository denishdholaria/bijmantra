/**
 * Sensor Alerts
 * 
 * Configure and manage sensor threshold alerts.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  Bell,
  BellOff,
  Check,
  CheckCircle,
  Clock,
  Plus,
  Settings,
  Thermometer,
  Trash2,
  XCircle,
} from 'lucide-react';

interface AlertRule {
  id: string;
  name: string;
  sensor: string;
  condition: 'above' | 'below' | 'equals';
  threshold: number;
  unit: string;
  severity: 'critical' | 'warning' | 'info';
  enabled: boolean;
  notifyEmail: boolean;
  notifySms: boolean;
  notifyPush: boolean;
}

interface AlertEvent {
  id: string;
  ruleId: string;
  ruleName: string;
  deviceId: string;
  deviceName: string;
  sensor: string;
  value: number;
  threshold: number;
  condition: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
}

// Demo data
const alertRules: AlertRule[] = [
  {
    id: 'rule-1',
    name: 'High Temperature Alert',
    sensor: 'temperature',
    condition: 'above',
    threshold: 35,
    unit: '°C',
    severity: 'critical',
    enabled: true,
    notifyEmail: true,
    notifySms: true,
    notifyPush: true,
  },
  {
    id: 'rule-2',
    name: 'Low Soil Moisture',
    sensor: 'soil_moisture',
    condition: 'below',
    threshold: 30,
    unit: '%',
    severity: 'warning',
    enabled: true,
    notifyEmail: true,
    notifySms: false,
    notifyPush: true,
  },
  {
    id: 'rule-3',
    name: 'Frost Warning',
    sensor: 'temperature',
    condition: 'below',
    threshold: 2,
    unit: '°C',
    severity: 'critical',
    enabled: true,
    notifyEmail: true,
    notifySms: true,
    notifyPush: true,
  },
  {
    id: 'rule-4',
    name: 'High Humidity',
    sensor: 'humidity',
    condition: 'above',
    threshold: 90,
    unit: '%',
    severity: 'warning',
    enabled: true,
    notifyEmail: true,
    notifySms: false,
    notifyPush: true,
  },
  {
    id: 'rule-5',
    name: 'Low Battery',
    sensor: 'battery',
    condition: 'below',
    threshold: 20,
    unit: '%',
    severity: 'warning',
    enabled: true,
    notifyEmail: true,
    notifySms: false,
    notifyPush: false,
  },
];

const alertEvents: AlertEvent[] = [
  {
    id: 'event-1',
    ruleId: 'rule-2',
    ruleName: 'Low Soil Moisture',
    deviceId: 'DEV-003',
    deviceName: 'Soil Probe B2',
    sensor: 'soil_moisture',
    value: 25,
    threshold: 30,
    condition: 'below',
    severity: 'warning',
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
    acknowledged: false,
  },
  {
    id: 'event-2',
    ruleId: 'rule-5',
    ruleName: 'Low Battery',
    deviceId: 'DEV-003',
    deviceName: 'Soil Probe B2',
    sensor: 'battery',
    value: 15,
    threshold: 20,
    condition: 'below',
    severity: 'warning',
    timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
    acknowledged: true,
    acknowledgedBy: 'admin@bijmantra.org',
    acknowledgedAt: new Date(Date.now() - 1 * 3600000).toISOString(),
  },
  {
    id: 'event-3',
    ruleId: 'rule-1',
    ruleName: 'High Temperature Alert',
    deviceId: 'DEV-001',
    deviceName: 'Weather Station Alpha',
    sensor: 'temperature',
    value: 38.5,
    threshold: 35,
    condition: 'above',
    severity: 'critical',
    timestamp: new Date(Date.now() - 5 * 3600000).toISOString(),
    acknowledged: true,
    acknowledgedBy: 'admin@bijmantra.org',
    acknowledgedAt: new Date(Date.now() - 4 * 3600000).toISOString(),
  },
];

const sensorOptions = [
  { value: 'temperature', label: 'Temperature' },
  { value: 'humidity', label: 'Humidity' },
  { value: 'soil_moisture', label: 'Soil Moisture' },
  { value: 'soil_temp', label: 'Soil Temperature' },
  { value: 'pressure', label: 'Pressure' },
  { value: 'wind_speed', label: 'Wind Speed' },
  { value: 'battery', label: 'Battery Level' },
  { value: 'signal', label: 'Signal Strength' },
];

export function Alerts() {
  const [rules, setRules] = useState(alertRules);
  const [events, setEvents] = useState(alertEvents);
  const [dialogOpen, setDialogOpen] = useState(false);

  const activeAlerts = events.filter(e => !e.acknowledged);
  const acknowledgedAlerts = events.filter(e => e.acknowledged);

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      critical: 'bg-red-100 text-red-700',
      warning: 'bg-yellow-100 text-yellow-700',
      info: 'bg-blue-100 text-blue-700',
    };
    return <Badge className={styles[severity]}>{severity}</Badge>;
  };

  const getConditionText = (condition: string, threshold: number, unit: string) => {
    const conditionMap: Record<string, string> = {
      above: `> ${threshold}${unit}`,
      below: `< ${threshold}${unit}`,
      equals: `= ${threshold}${unit}`,
    };
    return conditionMap[condition];
  };

  const toggleRule = (ruleId: string) => {
    setRules(rules.map(r => 
      r.id === ruleId ? { ...r, enabled: !r.enabled } : r
    ));
  };

  const acknowledgeAlert = (eventId: string) => {
    setEvents(events.map(e =>
      e.id === eventId ? {
        ...e,
        acknowledged: true,
        acknowledgedBy: 'admin@bijmantra.org',
        acknowledgedAt: new Date().toISOString(),
      } : e
    ));
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 3600000) {
      return `${Math.floor(diff / 60000)} min ago`;
    } else if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)} hours ago`;
    }
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Bell className="h-8 w-8" />
            Sensor Alerts
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure thresholds and manage alert notifications
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Alert Rule
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Alert Rule</DialogTitle>
              <DialogDescription>
                Set up a new threshold-based alert.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Rule Name</Label>
                <Input placeholder="e.g., High Temperature Alert" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Sensor</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select sensor" />
                    </SelectTrigger>
                    <SelectContent>
                      {sensorOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Condition</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select condition" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="above">Above</SelectItem>
                      <SelectItem value="below">Below</SelectItem>
                      <SelectItem value="equals">Equals</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Threshold Value</Label>
                  <Input type="number" placeholder="e.g., 35" />
                </div>
                <div className="space-y-2">
                  <Label>Severity</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select severity" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="warning">Warning</SelectItem>
                      <SelectItem value="info">Info</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-3">
                <Label>Notifications</Label>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Email</span>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">SMS</span>
                  <Switch />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Push Notification</span>
                  <Switch defaultChecked />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => setDialogOpen(false)}>
                Create Rule
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <div>
                <p className="text-2xl font-bold">{activeAlerts.length}</p>
                <p className="text-sm text-muted-foreground">Active Alerts</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{acknowledgedAlerts.length}</p>
                <p className="text-sm text-muted-foreground">Acknowledged</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Bell className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{rules.filter(r => r.enabled).length}</p>
                <p className="text-sm text-muted-foreground">Active Rules</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <BellOff className="h-8 w-8 text-gray-500" />
              <div>
                <p className="text-2xl font-bold">{rules.filter(r => !r.enabled).length}</p>
                <p className="text-sm text-muted-foreground">Disabled Rules</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active" className="relative">
            Active Alerts
            {activeAlerts.length > 0 && (
              <span className="ml-2 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                {activeAlerts.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="history">Alert History</TabsTrigger>
          <TabsTrigger value="rules">Alert Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4 mt-4">
          {activeAlerts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
                <h3 className="text-lg font-medium">All Clear</h3>
                <p className="text-muted-foreground mt-1">
                  No active alerts at this time
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {activeAlerts.map(event => (
                <Card key={event.id} className={`border-l-4 ${
                  event.severity === 'critical' ? 'border-l-red-500' : 'border-l-yellow-500'
                }`}>
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className={`h-5 w-5 mt-0.5 ${
                          event.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'
                        }`} />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{event.ruleName}</span>
                            {getSeverityBadge(event.severity)}
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">
                            {event.deviceName} ({event.deviceId})
                          </p>
                          <p className="text-sm mt-1">
                            Value: <span className="font-medium">{event.value}</span> 
                            {' '}(threshold: {event.condition} {event.threshold})
                          </p>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-2">
                            <Clock className="h-3 w-3" />
                            {formatTime(event.timestamp)}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => acknowledgeAlert(event.id)}
                      >
                        <Check className="h-4 w-4 mr-1" />
                        Acknowledge
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4 mt-4">
          <div className="space-y-3">
            {events.map(event => (
              <Card key={event.id} className="opacity-75">
                <CardContent className="py-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {event.acknowledged ? (
                        <CheckCircle className="h-5 w-5 mt-0.5 text-green-500" />
                      ) : (
                        <AlertTriangle className={`h-5 w-5 mt-0.5 ${
                          event.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'
                        }`} />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{event.ruleName}</span>
                          {getSeverityBadge(event.severity)}
                          {event.acknowledged && (
                            <Badge variant="outline" className="text-green-600">
                              Acknowledged
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {event.deviceName}
                        </p>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground mt-2">
                          <Clock className="h-3 w-3" />
                          {formatTime(event.timestamp)}
                          {event.acknowledgedBy && (
                            <span className="ml-2">
                              • Ack by {event.acknowledgedBy}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="rules" className="space-y-4 mt-4">
          <div className="space-y-3">
            {rules.map(rule => (
              <Card key={rule.id}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Switch
                        checked={rule.enabled}
                        onCheckedChange={() => toggleRule(rule.id)}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{rule.name}</span>
                          {getSeverityBadge(rule.severity)}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {rule.sensor} {getConditionText(rule.condition, rule.threshold, rule.unit)}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          {rule.notifyEmail && <Badge variant="outline">Email</Badge>}
                          {rule.notifySms && <Badge variant="outline">SMS</Badge>}
                          {rule.notifyPush && <Badge variant="outline">Push</Badge>}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="icon">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-red-500">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default Alerts;

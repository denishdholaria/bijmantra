/**
 * Sensor Alerts
 *
 * Configure and manage sensor threshold alerts.
 * Connected to /api/v2/sensors/alerts endpoints.
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  Bell,
  BellOff,
  Check,
  CheckCircle,
  Clock,
  Plus,
  RefreshCw,
  Settings,
  Trash2,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface AlertRule {
  id: string;
  name: string;
  sensor: string;
  condition: 'above' | 'below' | 'equals';
  threshold: number;
  unit: string;
  severity: 'critical' | 'warning' | 'info';
  enabled: boolean;
  notify_email: boolean;
  notify_sms: boolean;
  notify_push: boolean;
}

interface AlertEvent {
  id: string;
  rule_id: string;
  rule_name: string;
  device_id: string;
  device_name: string;
  sensor: string;
  value: number;
  threshold: number;
  condition: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
}

type AlertCondition = AlertRule['condition'];
type AlertSeverity = AlertRule['severity'];

const normalizeAlertCondition = (condition?: string): AlertCondition => {
  if (condition === 'below' || condition === 'equals') {
    return condition;
  }

  return 'above';
};

const normalizeAlertSeverity = (severity?: string): AlertSeverity => {
  if (severity === 'critical' || severity === 'info') {
    return severity;
  }

  return 'warning';
};

const sensorOptions = [
  { value: 'temperature', label: 'Temperature', unit: '°C' },
  { value: 'humidity', label: 'Humidity', unit: '%' },
  { value: 'soil_moisture', label: 'Soil Moisture', unit: '%' },
  { value: 'soil_temp', label: 'Soil Temperature', unit: '°C' },
  { value: 'pressure', label: 'Pressure', unit: 'hPa' },
  { value: 'wind_speed', label: 'Wind Speed', unit: 'km/h' },
  { value: 'battery', label: 'Battery Level', unit: '%' },
  { value: 'signal', label: 'Signal Strength', unit: '%' },
];

export function Alerts() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const user = useAuthStore((state) => state.user);
  const { toast } = useToast();

  // New rule form state
  const [newRule, setNewRule] = useState({
    name: '',
    sensor: '',
    condition: 'above' as const,
    threshold: 0,
    severity: 'warning' as const,
    notify_email: true,
    notify_sms: false,
    notify_push: true,
  });

  const fetchRules = async () => {
    try {
      const data = await apiClient.sensorService.getSensorAlertRules();
      const mappedRules: AlertRule[] = (data.rules || []).map((rule) => ({
        ...rule,
        condition: normalizeAlertCondition(rule.condition),
        severity: normalizeAlertSeverity(rule.severity),
      }));
      setRules(mappedRules);
      return mappedRules;
    } catch {
      console.error('Failed to fetch alert rules');
      setRules([]);
      return [] as AlertRule[];
    }
  };

  const fetchEvents = async (activeRules: AlertRule[] = rules) => {
    try {
      const data = await apiClient.sensorService.getSensorAlertEvents({ limit: 50 });
      const mappedEvents: AlertEvent[] = (data.events || []).map((event) => {
        const matchingRule = activeRules.find((rule) => rule.id === event.rule_id);

        return {
          ...event,
          device_name: event.device_id,
          condition: matchingRule?.condition ?? 'threshold',
          severity: normalizeAlertSeverity(event.severity),
        };
      });
      setEvents(mappedEvents);
    } catch {
      console.error('Failed to fetch alert events');
      setEvents([]);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    try {
      const latestRules = await fetchRules();
      await fetchEvents(latestRules);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    refreshData().finally(() => setLoading(false));
  }, []);

  const handleCreateRule = async () => {
    if (!newRule.name || !newRule.sensor) {
      toast({ title: 'Error', description: 'Please fill in all required fields', variant: 'destructive' });
      return;
    }

    setSubmitting(true);
    try {
      const sensorInfo = sensorOptions.find(s => s.value === newRule.sensor);
      await apiClient.sensorService.createSensorAlertRule({
        ...newRule,
        unit: sensorInfo?.unit || '',
      });
      toast({ title: 'Success', description: 'Alert rule created successfully' });
      setDialogOpen(false);
      setNewRule({ name: '', sensor: '', condition: 'above', threshold: 0, severity: 'warning', notify_email: true, notify_sms: false, notify_push: true });
      await fetchRules();
    } catch {
      toast({ title: 'Error', description: 'Failed to create rule', variant: 'destructive' });
    } finally {
      setSubmitting(false);
    }
  };

  const toggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await apiClient.sensorService.updateSensorAlertRule(ruleId, { enabled });
      setRules((currentRules) => currentRules.map((rule) => rule.id === ruleId ? { ...rule, enabled } : rule));
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to update alert rule. The current state was not changed.',
        variant: 'destructive',
      });
    }
  };

  const deleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) return;

    try {
      await apiClient.sensorService.deleteSensorAlertRule(ruleId);
      toast({ title: 'Success', description: 'Rule deleted successfully' });
      setRules((currentRules) => currentRules.filter((rule) => rule.id !== ruleId));
    } catch {
      toast({ title: 'Error', description: 'Failed to delete rule', variant: 'destructive' });
    }
  };

  const acknowledgeAlert = async (eventId: string) => {
    try {
      const acknowledgedEvent = await apiClient.sensorService.acknowledgeSensorAlert(
        eventId,
        user?.email,
      );
      setEvents((currentEvents) => currentEvents.map((event) =>
        event.id === eventId
          ? {
              ...event,
              acknowledged: Boolean(acknowledgedEvent.acknowledged),
              acknowledged_by: acknowledgedEvent.acknowledged_by,
              acknowledged_at: acknowledgedEvent.acknowledged_at,
            }
          : event
      ));
      toast({ title: 'Success', description: 'Alert acknowledged' });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to acknowledge alert. The alert remains active until the server confirms the update.',
        variant: 'destructive',
      });
    }
  };

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

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return date.toLocaleDateString();
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
            <Bell className="h-8 w-8" />
            Sensor Alerts
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure thresholds and manage alert notifications
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => void refreshData()} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
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
                <DialogDescription>Set up a new threshold-based alert.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Rule Name *</Label>
                  <Input
                    placeholder="e.g., High Temperature Alert"
                    value={newRule.name}
                    onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Sensor *</Label>
                    <Select value={newRule.sensor} onValueChange={(v) => setNewRule({ ...newRule, sensor: v })}>
                      <SelectTrigger><SelectValue placeholder="Select sensor" /></SelectTrigger>
                      <SelectContent>
                        {sensorOptions.map(opt => (
                          <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Condition</Label>
                    <Select value={newRule.condition} onValueChange={(v: any) => setNewRule({ ...newRule, condition: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
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
                    <Input
                      type="number"
                      placeholder="e.g., 35"
                      value={newRule.threshold}
                      onChange={(e) => setNewRule({ ...newRule, threshold: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Severity</Label>
                    <Select value={newRule.severity} onValueChange={(v: any) => setNewRule({ ...newRule, severity: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
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
                    <Switch checked={newRule.notify_email} onCheckedChange={(v) => setNewRule({ ...newRule, notify_email: v })} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">SMS</span>
                    <Switch checked={newRule.notify_sms} onCheckedChange={(v) => setNewRule({ ...newRule, notify_sms: v })} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Push Notification</span>
                    <Switch checked={newRule.notify_push} onCheckedChange={(v) => setNewRule({ ...newRule, notify_push: v })} />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleCreateRule} disabled={submitting}>
                  {submitting ? 'Creating...' : 'Create Rule'}
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
              <span className="ml-2 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">{activeAlerts.length}</span>
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
                <p className="text-muted-foreground mt-1">No active alerts at this time</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {activeAlerts.map(event => (
                <Card key={event.id} className={`border-l-4 ${event.severity === 'critical' ? 'border-l-red-500' : 'border-l-yellow-500'}`}>
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className={`h-5 w-5 mt-0.5 ${event.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'}`} />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{event.rule_name}</span>
                            {getSeverityBadge(event.severity)}
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{event.device_name} ({event.device_id})</p>
                          <p className="text-sm mt-1">Value: <span className="font-medium">{event.value}</span> (threshold: {event.condition} {event.threshold})</p>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-2">
                            <Clock className="h-3 w-3" />
                            {formatTime(event.timestamp)}
                          </div>
                        </div>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => acknowledgeAlert(event.id)}>
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
                  <div className="flex items-start gap-3">
                    {event.acknowledged ? (
                      <CheckCircle className="h-5 w-5 mt-0.5 text-green-500" />
                    ) : (
                      <AlertTriangle className={`h-5 w-5 mt-0.5 ${event.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'}`} />
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{event.rule_name}</span>
                        {getSeverityBadge(event.severity)}
                        {event.acknowledged && <Badge variant="outline" className="text-green-600">Acknowledged</Badge>}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{event.device_name}</p>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-2">
                        <Clock className="h-3 w-3" />
                        {formatTime(event.timestamp)}
                        {event.acknowledged_by && <span className="ml-2">• Ack by {event.acknowledged_by}</span>}
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
                      <Switch checked={rule.enabled} onCheckedChange={(v) => toggleRule(rule.id, v)} />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{rule.name}</span>
                          {getSeverityBadge(rule.severity)}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{rule.sensor} {getConditionText(rule.condition, rule.threshold, rule.unit)}</p>
                        <div className="flex items-center gap-2 mt-2">
                          {rule.notify_email && <Badge variant="outline">Email</Badge>}
                          {rule.notify_sms && <Badge variant="outline">SMS</Badge>}
                          {rule.notify_push && <Badge variant="outline">Push</Badge>}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="icon" aria-label={`Settings for ${rule.name}`}><Settings className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="icon" onClick={() => deleteRule(rule.id)} aria-label={`Delete ${rule.name}`}><Trash2 className="h-4 w-4 text-red-500" /></Button>
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

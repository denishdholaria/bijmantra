/**
 * Stock Alerts Page - Inventory alerts and notifications
 * Connected to /api/v2/seed-inventory/alerts endpoint
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertTriangle, RefreshCw, Bell, Package, 
  TrendingDown, FlaskConical, Clock, CheckCircle 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface Alert {
  id: string;
  type: 'low_stock' | 'low_viability' | 'overdue_test' | 'expiring_cert';
  severity: 'critical' | 'warning' | 'info';
  lot_id: string;
  variety?: string;
  message: string;
  value?: number;
  threshold?: number;
  created_at: string;
  acknowledged?: boolean;
}

export function StockAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getSeedInventoryAlerts();
      // Transform API response to our Alert format
      const transformedAlerts: Alert[] = (res.alerts || []).map((a: any, i: number) => ({
        id: `alert-${i}`,
        type: a.type || 'low_stock',
        severity: a.severity || 'warning',
        lot_id: a.lot_id,
        variety: a.variety,
        message: a.message,
        value: a.value,
        threshold: a.threshold,
        created_at: a.created_at || new Date().toISOString(),
        acknowledged: false,
      }));
      setAlerts(transformedAlerts);
    } catch (err) {
      // No data available - show empty state
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const acknowledgeAlert = (alertId: string) => {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, acknowledged: true } : a));
  };

  const filteredAlerts = alerts.filter(a => {
    if (activeTab === 'all') return !a.acknowledged;
    if (activeTab === 'acknowledged') return a.acknowledged;
    return a.type === activeTab && !a.acknowledged;
  });

  const alertCounts = {
    all: alerts.filter(a => !a.acknowledged).length,
    low_stock: alerts.filter(a => a.type === 'low_stock' && !a.acknowledged).length,
    low_viability: alerts.filter(a => a.type === 'low_viability' && !a.acknowledged).length,
    overdue_test: alerts.filter(a => a.type === 'overdue_test' && !a.acknowledged).length,
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'low_stock': return <TrendingDown className="h-5 w-5" />;
      case 'low_viability': return <FlaskConical className="h-5 w-5" />;
      case 'overdue_test': return <Clock className="h-5 w-5" />;
      case 'expiring_cert': return <AlertTriangle className="h-5 w-5" />;
      default: return <Bell className="h-5 w-5" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-50 border-red-200 text-red-700';
      case 'warning': return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      default: return 'bg-blue-50 border-blue-200 text-blue-700';
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical': return <Badge className="bg-red-100 text-red-700">Critical</Badge>;
      case 'warning': return <Badge className="bg-yellow-100 text-yellow-700">Warning</Badge>;
      default: return <Badge className="bg-blue-100 text-blue-700">Info</Badge>;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6 text-yellow-600" />
            Stock Alerts
          </h1>
          <p className="text-gray-500 text-sm">Monitor inventory levels and quality alerts</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchAlerts} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className={alertCounts.all > 0 ? 'border-yellow-300' : ''}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
              <Bell className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{alertCounts.all}</p>
              <p className="text-sm text-gray-500">Active Alerts</p>
            </div>
          </CardContent>
        </Card>
        <Card className={alertCounts.low_stock > 0 ? 'border-red-300' : ''}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
              <TrendingDown className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{alertCounts.low_stock}</p>
              <p className="text-sm text-gray-500">Low Stock</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-50 flex items-center justify-center">
              <FlaskConical className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{alertCounts.low_viability}</p>
              <p className="text-sm text-gray-500">Low Viability</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
              <Clock className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{alertCounts.overdue_test}</p>
              <p className="text-sm text-gray-500">Overdue Tests</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts List */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All ({alertCounts.all})</TabsTrigger>
          <TabsTrigger value="low_stock">Low Stock</TabsTrigger>
          <TabsTrigger value="low_viability">Low Viability</TabsTrigger>
          <TabsTrigger value="overdue_test">Overdue Tests</TabsTrigger>
          <TabsTrigger value="acknowledged">Acknowledged</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          {loading ? (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                Loading alerts...
              </CardContent>
            </Card>
          ) : filteredAlerts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-300" />
                <p>No alerts in this category</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredAlerts.map((alert) => (
                <Card key={alert.id} className={`border ${getSeverityColor(alert.severity)} ${alert.acknowledged ? 'opacity-60' : ''}`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          alert.severity === 'critical' ? 'bg-red-100 text-red-600' :
                          alert.severity === 'warning' ? 'bg-yellow-100 text-yellow-600' :
                          'bg-blue-100 text-blue-600'
                        }`}>
                          {getAlertIcon(alert.type)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{alert.lot_id}</p>
                            {alert.variety && <span className="text-gray-500">• {alert.variety}</span>}
                            {getSeverityBadge(alert.severity)}
                          </div>
                          <p className="text-sm mt-1">{alert.message}</p>
                          {alert.value !== undefined && alert.threshold !== undefined && (
                            <p className="text-xs text-gray-500 mt-1">
                              Current: {alert.value} | Threshold: {alert.threshold}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(alert.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      {!alert.acknowledged && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default StockAlerts;

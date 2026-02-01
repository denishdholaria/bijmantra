import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Thermometer, Droplets, AlertTriangle, CheckCircle, RefreshCw, Activity } from 'lucide-react';

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

interface VaultSensorWidgetProps {
  compact?: boolean;
  onViewDetails?: () => void;
}

export function VaultSensorWidget({ compact = false, onViewDetails }: VaultSensorWidgetProps) {
  const [conditions, setConditions] = useState<VaultCondition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConditions = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v2/vault-sensors/conditions');
      if (!response.ok) throw new Error('Failed to fetch conditions');
      const data = await response.json();
      setConditions(data.conditions || []);
      setError(null);
    } catch (err) {
      setError('Unable to load vault conditions');
      // No data available - show empty state
      setConditions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConditions();
    const interval = setInterval(fetchConditions, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'normal': return <Badge className="bg-green-100 text-green-800">Normal</Badge>;
      case 'warning': return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      case 'critical': return <Badge className="bg-red-100 text-red-800">Critical</Badge>;
      default: return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const getVaultTypeLabel = (type: string) => {
    switch (type) {
      case 'base': return 'Base Collection (-18°C)';
      case 'active': return 'Active Collection (4°C)';
      case 'cryo': return 'Cryopreservation (-196°C)';
      default: return type;
    }
  };

  const totalAlerts = conditions.reduce((sum, c) => sum + c.alerts_count, 0);
  const criticalVaults = conditions.filter(c => c.status === 'critical').length;
  const warningVaults = conditions.filter(c => c.status === 'warning').length;

  if (compact) {
    return (
      <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={onViewDetails}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Activity className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium">Vault Monitoring</p>
                <p className="text-sm text-muted-foreground">{conditions.length} vaults</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {criticalVaults > 0 && (
                <Badge className="bg-red-100 text-red-800">{criticalVaults} Critical</Badge>
              )}
              {warningVaults > 0 && (
                <Badge className="bg-yellow-100 text-yellow-800">{warningVaults} Warning</Badge>
              )}
              {criticalVaults === 0 && warningVaults === 0 && (
                <Badge className="bg-green-100 text-green-800">All Normal</Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Vault Environmental Monitoring
        </CardTitle>
        <Button variant="ghost" size="sm" onClick={fetchConditions} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </CardHeader>
      <CardContent>
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="text-center p-2 bg-muted rounded-lg">
            <p className="text-2xl font-bold">{conditions.length}</p>
            <p className="text-xs text-muted-foreground">Vaults</p>
          </div>
          <div className="text-center p-2 bg-green-50 rounded-lg">
            <p className="text-2xl font-bold text-green-600">
              {conditions.filter(c => c.status === 'normal').length}
            </p>
            <p className="text-xs text-muted-foreground">Normal</p>
          </div>
          <div className="text-center p-2 bg-yellow-50 rounded-lg">
            <p className="text-2xl font-bold text-yellow-600">{warningVaults}</p>
            <p className="text-xs text-muted-foreground">Warning</p>
          </div>
          <div className="text-center p-2 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">{totalAlerts}</p>
            <p className="text-xs text-muted-foreground">Alerts</p>
          </div>
        </div>

        {/* Vault List */}
        <div className="space-y-3">
          {conditions.map((vault) => (
            <div
              key={vault.vault_id}
              className="p-3 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(vault.status)}`} />
                  <span className="font-medium">{vault.vault_name}</span>
                </div>
                {getStatusBadge(vault.status)}
              </div>
              
              <p className="text-xs text-muted-foreground mb-2">
                {getVaultTypeLabel(vault.vault_type)}
              </p>

              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <Thermometer className="h-4 w-4 text-blue-500" />
                  <span>
                    {typeof vault.current_readings.temperature === 'number' 
                      ? `${vault.current_readings.temperature.toFixed(1)}°C`
                      : 'N/A'}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <Droplets className="h-4 w-4 text-cyan-500" />
                  <span>
                    {typeof vault.current_readings.humidity === 'number'
                      ? `${vault.current_readings.humidity.toFixed(1)}%`
                      : 'N/A'}
                  </span>
                </div>
                {vault.alerts_count > 0 && (
                  <div className="flex items-center gap-1 text-yellow-600">
                    <AlertTriangle className="h-4 w-4" />
                    <span>{vault.alerts_count} alert{vault.alerts_count > 1 ? 's' : ''}</span>
                  </div>
                )}
                {vault.alerts_count === 0 && vault.status === 'normal' && (
                  <div className="flex items-center gap-1 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    <span>OK</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {onViewDetails && (
          <Button variant="outline" className="w-full mt-4" onClick={onViewDetails}>
            View Full Monitoring Dashboard
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export default VaultSensorWidget;

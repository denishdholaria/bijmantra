/**
 * Gene Bank Dashboard
 * 
 * Workspace-specific dashboard for Gene Bank workspace.
 * Shows vault conditions, viability alerts, regeneration queue, and exchanges.
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiClient } from '@/lib/api-client';
import { 
  Building2, Thermometer, AlertTriangle, RefreshCw,
  ArrowRight, Plus, FileText, Sprout,
  CloudSun, Radio, Package, Send
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function GeneBankDashboard() {
  const { data: stats } = useQuery({
    queryKey: ['gene-bank-dashboard'],
    queryFn: async () => {
      const [
        summary,
        sensorStats,
        regenerationTasks,
        exchanges,
        vaultConditionsResponse,
        viabilityTests
      ] = await Promise.all([
        apiClient.inventoryService.getSummary(),
        apiClient.sensorService.getSensorNetworkStats(),
        apiClient.regenerationService.getRegenerationTasks(undefined, 'pending'),
        apiClient.exchangeService.getExchanges(undefined, 'pending'),
        apiClient.vaultService.getVaultConditions(),
        apiClient.viabilityService.getViabilityTests()
      ]);

      return {
        totalAccessions: summary.total_lots,
        viabilityDue: summary.lots_needing_test,
        vaultAlerts: sensorStats.active_alerts,
        regenerationQueue: regenerationTasks.length,
        pendingExchanges: exchanges.length,
        vaultConditions: vaultConditionsResponse.conditions,
        viabilityTests: viabilityTests
      };
    }
  });

  const vaultAlerts = stats?.vaultAlerts || 0;
  const viabilityDue = stats?.viabilityDue || 0;
  const regenerationQueue = stats?.regenerationQueue || 0;
  const pendingExchanges = stats?.pendingExchanges || 0;
  const totalAccessions = stats?.totalAccessions || 0;

  const vaultConditions = stats?.vaultConditions || [];
  const viabilityTests = stats?.viabilityTests || [];

  // Filter viability tests
  const pendingTests = viabilityTests.filter((t: any) => t.status === 'pending' || t.status === 'scheduled').slice(0, 3);
  const completedTests = viabilityTests.filter((t: any) => t.status === 'completed').slice(0, 3);
  const recentTests = [...pendingTests, ...completedTests].slice(0, 3);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'text-red-600';
      case 'warning': return 'text-amber-600';
      case 'normal': return 'text-green-600';
      default: return 'text-muted-foreground';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'critical': return <Badge variant="destructive">Alert</Badge>;
      case 'warning': return <Badge variant="outline" className="text-amber-600 border-amber-300">Warning</Badge>;
      case 'normal': return <Badge className="bg-green-100 text-green-800 hover:bg-green-200">Normal</Badge>;
      default: return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const getCardStyle = (status: string) => {
    switch (status) {
      case 'critical': return 'border-red-200 bg-red-50/50 dark:bg-red-950/20';
      case 'warning': return 'border-amber-200 bg-amber-50/50 dark:bg-amber-950/20';
      case 'normal': return 'border hover:bg-muted/50 transition-colors';
      default: return 'border hover:bg-muted/50 transition-colors';
    }
  };

  const getThermometerBg = (status: string) => {
    switch (status) {
      case 'critical': return 'bg-red-100 dark:bg-red-900/30';
      case 'warning': return 'bg-amber-100 dark:bg-amber-900/30';
      case 'normal': return 'bg-green-100 dark:bg-green-900/30';
      default: return 'bg-gray-100 dark:bg-gray-800';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-amber-600" />
            Gene Bank Dashboard
          </h1>
          <p className="text-muted-foreground">
            Conservation, vault monitoring, and germplasm exchange
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/seed-bank/accessions/new">
              <Plus className="h-4 w-4 mr-2" />
              New Accession
            </Link>
          </Button>
          <Button asChild>
            <Link to="/seed-bank/viability">
              <RefreshCw className="h-4 w-4 mr-2" />
              Log Viability
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Accessions</CardTitle>
            <Sprout className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAccessions.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">In conservation</p>
          </CardContent>
        </Card>

        <Card className={vaultAlerts > 0 ? 'border-red-200 bg-red-50/50 dark:bg-red-950/20' : ''}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Vault Alerts</CardTitle>
            <Thermometer className={`h-4 w-4 ${vaultAlerts > 0 ? 'text-red-600' : 'text-muted-foreground'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{vaultAlerts}</div>
            <p className="text-xs text-muted-foreground">Environmental issues</p>
          </CardContent>
        </Card>

        <Card className={viabilityDue > 10 ? 'border-amber-200 bg-amber-50/50 dark:bg-amber-950/20' : ''}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Viability Due</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${viabilityDue > 10 ? 'text-amber-600' : 'text-muted-foreground'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{viabilityDue}</div>
            <p className="text-xs text-muted-foreground">Tests scheduled</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Regeneration Queue</CardTitle>
            <RefreshCw className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{regenerationQueue}</div>
            <p className="text-xs text-muted-foreground">Awaiting regeneration</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending Exchanges</CardTitle>
            <Send className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingExchanges}</div>
            <p className="text-xs text-muted-foreground">MTA requests</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vault Conditions */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Vault Conditions</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/seed-bank/monitoring">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Real-time environmental monitoring</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {vaultConditions.length === 0 ? (
                <div className="text-center text-muted-foreground py-4">
                  No vaults monitored
                </div>
              ) : (
                vaultConditions.map((condition: any) => (
                  <div
                    key={condition.vault_id}
                    className={`flex items-center justify-between p-3 rounded-lg ${getCardStyle(condition.status)}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${getThermometerBg(condition.status)}`}>
                        <Thermometer className={`h-4 w-4 ${getStatusColor(condition.status)}`} />
                      </div>
                      <div>
                        <div className="font-medium">{condition.vault_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {condition.current_readings.temperature !== undefined && (
                            <span>Temp: {condition.current_readings.temperature}°C</span>
                          )}
                          {condition.current_readings.humidity !== undefined && (
                            <span> • RH: {condition.current_readings.humidity}%</span>
                          )}
                        </div>
                      </div>
                    </div>
                    {getStatusBadge(condition.status)}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Viability Testing */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Viability Testing</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/seed-bank/viability">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Upcoming and recent tests</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentTests.length === 0 ? (
                <div className="text-center text-muted-foreground py-4">
                  No recent tests
                </div>
              ) : (
                recentTests.map((test: any) => (
                  <div key={test.test_id || test.id} className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                    <div>
                      <div className="font-medium">{test.lot_id}</div>
                      <div className="text-sm text-muted-foreground">
                        {test.status === 'completed'
                          ? `Completed: ${test.germination_percent}% germination`
                          : `Due: ${new Date(test.test_date).toLocaleDateString()}`
                        }
                      </div>
                    </div>
                    {test.status === 'completed' ? (
                      <Badge className="bg-green-100 text-green-800">Passed</Badge>
                    ) : (
                       new Date(test.test_date) < new Date() ? (
                        <Badge variant="outline" className="text-amber-600 border-amber-300">Overdue</Badge>
                       ) : (
                        <Badge variant="secondary">Scheduled</Badge>
                       )
                    )}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
          <CardDescription>Common gene bank tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/seed-bank/regeneration">
                <RefreshCw className="h-5 w-5 mb-2" />
                <span>Schedule Regeneration</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/seed-bank/mta">
                <FileText className="h-5 w-5 mb-2" />
                <span>Process MTA</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/earth-systems/weather">
                <CloudSun className="h-5 w-5 mb-2" />
                <span>Check Weather</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/sensor-networks">
                <Radio className="h-5 w-5 mb-2" />
                <span>Sensor Status</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default GeneBankDashboard;

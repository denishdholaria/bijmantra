/**
 * Gene Bank Dashboard
 * 
 * Workspace-specific dashboard for Gene Bank workspace.
 * Shows vault conditions, viability alerts, regeneration queue, and exchanges.
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { 
  Building2, Thermometer, AlertTriangle, RefreshCw,
  ArrowRight, Plus, FileText, Sprout,
  CloudSun, Radio, Package, Send
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

export function GeneBankDashboard() {
  // TODO: Connect to real APIs when available
  const vaultAlerts = 0;
  const viabilityDue = 0;
  const regenerationQueue = 0;
  const pendingExchanges = 0;
  const totalAccessions = 0;

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
              <div className="flex items-center justify-between p-3 rounded-lg border border-red-200 bg-red-50/50 dark:bg-red-950/20">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
                    <Thermometer className="h-4 w-4 text-red-600" />
                  </div>
                  <div>
                    <div className="font-medium">Base Collection Vault A</div>
                    <div className="text-sm text-muted-foreground">Temp: -16°C (Target: -18°C)</div>
                  </div>
                </div>
                <Badge variant="destructive">Alert</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
                    <Thermometer className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <div className="font-medium">Active Collection Vault</div>
                    <div className="text-sm text-muted-foreground">Temp: 4°C • RH: 35%</div>
                  </div>
                </div>
                <Badge className="bg-green-100 text-green-800">Normal</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                    <Thermometer className="h-4 w-4 text-amber-600" />
                  </div>
                  <div>
                    <div className="font-medium">Cryopreservation Unit</div>
                    <div className="text-sm text-muted-foreground">LN2 Level: 45% (Refill soon)</div>
                  </div>
                </div>
                <Badge variant="outline" className="text-amber-600 border-amber-300">Warning</Badge>
              </div>
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
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div>
                  <div className="font-medium">ACC-2024-0892 (Rice)</div>
                  <div className="text-sm text-muted-foreground">Due: Today</div>
                </div>
                <Badge variant="outline" className="text-amber-600 border-amber-300">Due Today</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div>
                  <div className="font-medium">ACC-2024-0756 (Wheat)</div>
                  <div className="text-sm text-muted-foreground">Due: Tomorrow</div>
                </div>
                <Badge variant="secondary">Scheduled</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div>
                  <div className="font-medium">ACC-2024-0634 (Maize)</div>
                  <div className="text-sm text-muted-foreground">Completed: 92% germination</div>
                </div>
                <Badge className="bg-green-100 text-green-800">Passed</Badge>
              </div>
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

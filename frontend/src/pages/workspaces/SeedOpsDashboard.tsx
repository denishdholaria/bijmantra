/**
 * Seed Operations Dashboard
 * 
 * Workspace-specific dashboard for Seed Industry workspace.
 * Shows inventory, dispatches, lab queue, and quality metrics.
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { 
  Factory, Package, Truck, FlaskConical,
  ArrowRight, Plus, AlertTriangle, CheckCircle2,
  Clock, BarChart3, QrCode
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

export function SeedOpsDashboard() {
  // TODO: Connect to real APIs when available
  const inventoryAlerts = 0;
  const pendingDispatches = 0;
  const labQueueCount = 0;
  const qualityPassRate = 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Factory className="h-6 w-6 text-blue-600" />
            Seed Industry Dashboard
          </h1>
          <p className="text-muted-foreground">
            Manage inventory, dispatches, and quality testing
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/seed-operations/dispatch">
              <Truck className="h-4 w-4 mr-2" />
              New Dispatch
            </Link>
          </Button>
          <Button asChild>
            <Link to="/seed-operations/samples">
              <FlaskConical className="h-4 w-4 mr-2" />
              Log Test
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className={inventoryAlerts > 0 ? 'border-amber-200 bg-amber-50/50 dark:bg-amber-950/20' : ''}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Inventory Alerts</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${inventoryAlerts > 0 ? 'text-amber-600' : 'text-muted-foreground'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{inventoryAlerts}</div>
            <p className="text-xs text-muted-foreground">Low stock / expiring items</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending Dispatches</CardTitle>
            <Truck className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingDispatches}</div>
            <p className="text-xs text-muted-foreground">Awaiting shipment</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Lab Queue</CardTitle>
            <FlaskConical className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{labQueueCount}</div>
            <p className="text-xs text-muted-foreground">Samples awaiting testing</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Quality Pass Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{qualityPassRate}%</div>
            <Progress value={qualityPassRate} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Inventory Alerts */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Inventory Alerts</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/seed-operations/alerts">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Items requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20">
                <div>
                  <div className="font-medium">Rice IR64 - Lot #2024-001</div>
                  <div className="text-sm text-muted-foreground">Low stock: 50kg remaining</div>
                </div>
                <Badge variant="outline" className="text-amber-600 border-amber-300">Low Stock</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border border-red-200 bg-red-50/50 dark:bg-red-950/20">
                <div>
                  <div className="font-medium">Wheat HD2967 - Lot #2023-089</div>
                  <div className="text-sm text-muted-foreground">Expires in 30 days</div>
                </div>
                <Badge variant="outline" className="text-red-600 border-red-300">Expiring</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20">
                <div>
                  <div className="font-medium">Maize NK6240 - Lot #2024-015</div>
                  <div className="text-sm text-muted-foreground">Viability test due</div>
                </div>
                <Badge variant="outline" className="text-amber-600 border-amber-300">Test Due</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pending Dispatches */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Pending Dispatches</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/seed-operations/dispatch-history">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Orders awaiting shipment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div>
                  <div className="font-medium">Order #D-2024-156</div>
                  <div className="text-sm text-muted-foreground">AgriCorp Ltd • 500kg Rice</div>
                </div>
                <Badge>Ready</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div>
                  <div className="font-medium">Order #D-2024-157</div>
                  <div className="text-sm text-muted-foreground">FarmFirst Inc • 200kg Wheat</div>
                </div>
                <Badge variant="secondary">Packing</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div>
                  <div className="font-medium">Order #D-2024-158</div>
                  <div className="text-sm text-muted-foreground">SeedMart • 100kg Maize</div>
                </div>
                <Badge variant="secondary">Processing</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
          <CardDescription>Common seed operations tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/seed-operations/quality-gate">
                <CheckCircle2 className="h-5 w-5 mb-2" />
                <span>Quality Gate</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/barcode">
                <QrCode className="h-5 w-5 mb-2" />
                <span>Scan Barcode</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/inventory">
                <Package className="h-5 w-5 mb-2" />
                <span>Check Stock</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/reports">
                <BarChart3 className="h-5 w-5 mb-2" />
                <span>Generate Report</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default SeedOpsDashboard;

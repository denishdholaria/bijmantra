/**
 * Warehouse Page - Storage locations and capacity management
 * Connected to /api/v2/warehouse endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Warehouse as WarehouseIcon, RefreshCw, Plus, 
  Thermometer, Droplets, Package, AlertTriangle 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useQuery } from '@tanstack/react-query';

interface StorageLocation {
  id: string;
  code: string;
  name: string;
  storage_type: 'cold' | 'ambient' | 'controlled' | 'cryo';
  capacity_kg: number;
  used_kg: number;
  current_temperature?: number | null;
  current_humidity?: number | null;
  lot_count: number;
  status: 'normal' | 'warning' | 'critical' | 'maintenance';
  utilization_percent: number;
}

export function Warehouse() {
  const { data: locations = [], isLoading, refetch } = useQuery({
    queryKey: ['warehouse-locations'],
    queryFn: () => apiClient.warehouseService.getLocations(),
  });

  const { data: summary } = useQuery({
    queryKey: ['warehouse-summary'],
    queryFn: () => apiClient.warehouseService.getSummary(),
  });

  const totalCapacity = summary?.total_capacity_kg || locations.reduce((sum, l) => sum + l.capacity_kg, 0);
  const totalUsed = summary?.total_used_kg || locations.reduce((sum, l) => sum + l.used_kg, 0);
  const totalLots = summary?.total_lots || locations.reduce((sum, l) => sum + l.lot_count, 0);
  const utilizationPercent = summary?.utilization_percent || (totalCapacity > 0 ? (totalUsed / totalCapacity) * 100 : 0);
  const alertsCount = summary?.alerts_count || locations.filter(l => l.status !== 'normal').length;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300';
      case 'warning': return 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300';
      case 'maintenance': return 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300';
      default: return 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'cold': return 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300';
      case 'controlled': return 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300';
      case 'cryo': return 'bg-cyan-100 dark:bg-cyan-900/40 text-cyan-700 dark:text-cyan-300';
      default: return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Warehouse</h1>
          <p className="text-muted-foreground text-sm">Storage locations and capacity management</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button><Plus className="h-4 w-4 mr-2" />Add Location</Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                <WarehouseIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{locations.length}</p>
                <p className="text-sm text-muted-foreground">Locations</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-50 dark:bg-green-900/30 flex items-center justify-center">
                <Package className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{totalLots}</p>
                <p className="text-sm text-muted-foreground">Total Lots</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground mb-1">Total Capacity</p>
            <p className="text-xl font-bold text-foreground">{(totalCapacity / 1000).toFixed(0)}t</p>
            <Progress value={utilizationPercent} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-1">{utilizationPercent.toFixed(0)}% utilized</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-yellow-50 dark:bg-yellow-900/30 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{alertsCount}</p>
                <p className="text-sm text-muted-foreground">Alerts</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Storage Locations */}
      <div className="grid md:grid-cols-2 gap-4">
        {isLoading ? (
          <Card className="col-span-2">
            <CardContent className="py-12 text-center text-muted-foreground">
              Loading warehouse data...
            </CardContent>
          </Card>
        ) : locations.length === 0 ? (
          <Card className="col-span-2">
            <CardContent className="py-12 text-center text-muted-foreground">
              <WarehouseIcon className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
              <p>No storage locations configured</p>
              <Button className="mt-4"><Plus className="h-4 w-4 mr-2" />Add First Location</Button>
            </CardContent>
          </Card>
        ) : (
          locations.map((location) => {
            const usagePercent = location.utilization_percent || (location.used_kg / location.capacity_kg) * 100;
            return (
              <Card key={location.id} className={location.status === 'critical' ? 'border-red-300 dark:border-red-700' : location.status === 'warning' ? 'border-yellow-300 dark:border-yellow-700' : ''}>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg text-foreground">{location.name}</CardTitle>
                      <div className="flex gap-2 mt-1">
                        <Badge className={getTypeColor(location.storage_type)}>{location.storage_type}</Badge>
                        <Badge className={getStatusColor(location.status)}>{location.status}</Badge>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">{location.code}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Capacity Bar */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Capacity</span>
                        <span className="font-medium text-foreground">{(location.used_kg / 1000).toFixed(1)}t / {(location.capacity_kg / 1000).toFixed(0)}t</span>
                      </div>
                      <Progress 
                        value={usagePercent} 
                        className={`h-3 ${usagePercent > 90 ? '[&>div]:bg-red-500' : usagePercent > 75 ? '[&>div]:bg-yellow-500' : ''}`}
                      />
                    </div>

                    {/* Environment */}
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="p-2 bg-muted/50 rounded">
                        <div className="flex items-center justify-center gap-1 text-foreground">
                          <Thermometer className="h-4 w-4" />
                          <span className="font-medium">{location.current_temperature ?? '-'}°C</span>
                        </div>
                        <p className="text-xs text-muted-foreground">Temp</p>
                      </div>
                      <div className="p-2 bg-muted/50 rounded">
                        <div className="flex items-center justify-center gap-1 text-foreground">
                          <Droplets className="h-4 w-4" />
                          <span className="font-medium">{location.current_humidity ?? '-'}%</span>
                        </div>
                        <p className="text-xs text-muted-foreground">Humidity</p>
                      </div>
                      <div className="p-2 bg-muted/50 rounded">
                        <div className="flex items-center justify-center gap-1 text-foreground">
                          <Package className="h-4 w-4" />
                          <span className="font-medium">{location.lot_count}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">Lots</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}

export default Warehouse;

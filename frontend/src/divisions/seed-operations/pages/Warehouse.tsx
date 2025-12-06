/**
 * Warehouse Page - Storage locations and capacity management
 * Connected to /api/v2/seed-inventory endpoints
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

interface StorageLocation {
  id: string;
  name: string;
  type: 'cold' | 'ambient' | 'controlled';
  capacity_kg: number;
  used_kg: number;
  temperature?: number;
  humidity?: number;
  lot_count: number;
  status: 'normal' | 'warning' | 'critical';
}

export function Warehouse() {
  const [locations, setLocations] = useState<StorageLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [storageTypes, setStorageTypes] = useState<any[]>([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const typesRes = await apiClient.getStorageTypes();
      setStorageTypes(typesRes.storage_types || []);
      
      // Demo warehouse data (would come from a warehouse API in production)
      setLocations([
        { id: 'WH-A', name: 'Warehouse A - Cold Storage', type: 'cold', capacity_kg: 50000, used_kg: 35000, temperature: -5, humidity: 45, lot_count: 45, status: 'normal' },
        { id: 'WH-B', name: 'Warehouse B - Ambient', type: 'ambient', capacity_kg: 100000, used_kg: 82000, temperature: 25, humidity: 55, lot_count: 120, status: 'warning' },
        { id: 'WH-C', name: 'Warehouse C - Controlled', type: 'controlled', capacity_kg: 30000, used_kg: 12000, temperature: 15, humidity: 40, lot_count: 28, status: 'normal' },
        { id: 'WH-D', name: 'Warehouse D - Long-term', type: 'cold', capacity_kg: 20000, used_kg: 19500, temperature: -18, humidity: 30, lot_count: 85, status: 'critical' },
      ]);
    } catch (err) {
      // Use demo data
      setLocations([
        { id: 'WH-A', name: 'Warehouse A - Cold Storage', type: 'cold', capacity_kg: 50000, used_kg: 35000, temperature: -5, humidity: 45, lot_count: 45, status: 'normal' },
        { id: 'WH-B', name: 'Warehouse B - Ambient', type: 'ambient', capacity_kg: 100000, used_kg: 82000, temperature: 25, humidity: 55, lot_count: 120, status: 'warning' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const totalCapacity = locations.reduce((sum, l) => sum + l.capacity_kg, 0);
  const totalUsed = locations.reduce((sum, l) => sum + l.used_kg, 0);
  const totalLots = locations.reduce((sum, l) => sum + l.lot_count, 0);
  const utilizationPercent = totalCapacity > 0 ? (totalUsed / totalCapacity) * 100 : 0;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'bg-red-100 text-red-700';
      case 'warning': return 'bg-yellow-100 text-yellow-700';
      default: return 'bg-green-100 text-green-700';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'cold': return 'bg-blue-100 text-blue-700';
      case 'controlled': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Warehouse</h1>
          <p className="text-gray-500 text-sm">Storage locations and capacity management</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
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
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                <WarehouseIcon className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{locations.length}</p>
                <p className="text-sm text-gray-500">Locations</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                <Package className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalLots}</p>
                <p className="text-sm text-gray-500">Total Lots</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500 mb-1">Total Capacity</p>
            <p className="text-xl font-bold">{(totalCapacity / 1000).toFixed(0)}t</p>
            <Progress value={utilizationPercent} className="mt-2 h-2" />
            <p className="text-xs text-gray-500 mt-1">{utilizationPercent.toFixed(0)}% utilized</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{locations.filter(l => l.status !== 'normal').length}</p>
                <p className="text-sm text-gray-500">Alerts</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Storage Locations */}
      <div className="grid md:grid-cols-2 gap-4">
        {loading ? (
          <Card className="col-span-2">
            <CardContent className="py-12 text-center text-gray-500">
              Loading warehouse data...
            </CardContent>
          </Card>
        ) : locations.length === 0 ? (
          <Card className="col-span-2">
            <CardContent className="py-12 text-center text-gray-500">
              <WarehouseIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No storage locations configured</p>
            </CardContent>
          </Card>
        ) : (
          locations.map((location) => {
            const usagePercent = (location.used_kg / location.capacity_kg) * 100;
            return (
              <Card key={location.id} className={location.status === 'critical' ? 'border-red-300' : location.status === 'warning' ? 'border-yellow-300' : ''}>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{location.name}</CardTitle>
                      <div className="flex gap-2 mt-1">
                        <Badge className={getTypeColor(location.type)}>{location.type}</Badge>
                        <Badge className={getStatusColor(location.status)}>{location.status}</Badge>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500">{location.id}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Capacity Bar */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-500">Capacity</span>
                        <span className="font-medium">{(location.used_kg / 1000).toFixed(1)}t / {(location.capacity_kg / 1000).toFixed(0)}t</span>
                      </div>
                      <Progress 
                        value={usagePercent} 
                        className={`h-3 ${usagePercent > 90 ? '[&>div]:bg-red-500' : usagePercent > 75 ? '[&>div]:bg-yellow-500' : ''}`}
                      />
                    </div>

                    {/* Environment */}
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="p-2 bg-gray-50 rounded">
                        <div className="flex items-center justify-center gap-1 text-gray-600">
                          <Thermometer className="h-4 w-4" />
                          <span className="font-medium">{location.temperature}°C</span>
                        </div>
                        <p className="text-xs text-gray-500">Temp</p>
                      </div>
                      <div className="p-2 bg-gray-50 rounded">
                        <div className="flex items-center justify-center gap-1 text-gray-600">
                          <Droplets className="h-4 w-4" />
                          <span className="font-medium">{location.humidity}%</span>
                        </div>
                        <p className="text-xs text-gray-500">Humidity</p>
                      </div>
                      <div className="p-2 bg-gray-50 rounded">
                        <div className="flex items-center justify-center gap-1 text-gray-600">
                          <Package className="h-4 w-4" />
                          <span className="font-medium">{location.lot_count}</span>
                        </div>
                        <p className="text-xs text-gray-500">Lots</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Storage Types Reference */}
      {storageTypes.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Storage Types Reference</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {storageTypes.map((type) => (
                <div key={type.id} className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium">{type.name}</p>
                  <p className="text-sm text-gray-500">{type.temperature}</p>
                  <p className="text-xs text-gray-400 mt-1">{type.expected_viability}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default Warehouse;

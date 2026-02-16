/**
 * Vault Management Page
 * 
 * Manage seed storage vaults, monitor conditions, and track capacity.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

interface Vault {
  id: string;
  name: string;
  type: 'base' | 'active' | 'cryo';
  temperature: number;
  humidity: number;
  capacity: number;
  used: number;
  status: 'optimal' | 'warning' | 'critical';
  lastInspection: string;
}

export function VaultManagement() {
  const [selectedVault, setSelectedVault] = useState<string | null>(null);

  const { data: vaults, isLoading } = useQuery<Vault[]>({
    queryKey: ['seed-bank', 'vaults'],
    queryFn: async () => [
      { id: 'V001', name: 'Base Collection A', type: 'base', temperature: -18, humidity: 15, capacity: 50000, used: 42500, status: 'optimal', lastInspection: '2024-11-15' },
      { id: 'V002', name: 'Base Collection B', type: 'base', temperature: -18, humidity: 14, capacity: 50000, used: 38200, status: 'optimal', lastInspection: '2024-11-14' },
      { id: 'V003', name: 'Active Collection', type: 'active', temperature: 4, humidity: 25, capacity: 20000, used: 18500, status: 'warning', lastInspection: '2024-11-10' },
      { id: 'V004', name: 'Cryo Storage', type: 'cryo', temperature: -196, humidity: 0, capacity: 10000, used: 3200, status: 'optimal', lastInspection: '2024-11-12' },
    ],
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'optimal': return 'bg-green-100 text-green-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'base': return '🏛️';
      case 'active': return '📦';
      case 'cryo': return '❄️';
      default: return '📦';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Vault Management</h1>
          <p className="text-gray-600 mt-1">Monitor and manage seed storage facilities</p>
        </div>
        <Button>➕ Add Vault</Button>
      </div>

      {/* Vault Grid */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 gap-6">
          {Array(4).fill(0).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-6 w-48 mb-4" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-3/4" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {vaults?.map((vault) => (
            <Card 
              key={vault.id} 
              className={`cursor-pointer transition-all ${selectedVault === vault.id ? 'ring-2 ring-green-500' : 'hover:shadow-lg'}`}
              onClick={() => setSelectedVault(vault.id)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getTypeIcon(vault.type)}</span>
                    <CardTitle className="text-lg">{vault.name}</CardTitle>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(vault.status)}`}>
                    {vault.status}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                {/* Capacity Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Capacity</span>
                    <span className="font-medium">{((vault.used / vault.capacity) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${vault.used / vault.capacity > 0.9 ? 'bg-red-500' : vault.used / vault.capacity > 0.75 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${(vault.used / vault.capacity) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>{vault.used.toLocaleString()} accessions</span>
                    <span>{vault.capacity.toLocaleString()} max</span>
                  </div>
                </div>

                {/* Conditions */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-blue-600 font-medium">🌡️ Temperature</div>
                    <div className="text-xl font-bold text-blue-800">{vault.temperature}°C</div>
                  </div>
                  <div className="bg-cyan-50 p-3 rounded-lg">
                    <div className="text-cyan-600 font-medium">💧 Humidity</div>
                    <div className="text-xl font-bold text-cyan-800">{vault.humidity}%</div>
                  </div>
                </div>

                {/* Last Inspection */}
                <div className="mt-4 pt-4 border-t text-sm text-gray-500">
                  Last inspection: {new Date(vault.lastInspection).toLocaleDateString()}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Vault Types Legend */}
      <Card>
        <CardHeader>
          <CardTitle>Storage Types</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">🏛️</span>
              <div>
                <h4 className="font-medium">Base Collection</h4>
                <p className="text-sm text-gray-600">Long-term storage at -18°C for genetic security</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-2xl">📦</span>
              <div>
                <h4 className="font-medium">Active Collection</h4>
                <p className="text-sm text-gray-600">Medium-term storage at 4°C for distribution</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-2xl">❄️</span>
              <div>
                <h4 className="font-medium">Cryo Storage</h4>
                <p className="text-sm text-gray-600">Ultra-long-term in liquid nitrogen (-196°C)</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default VaultManagement;

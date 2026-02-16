/**
 * Lineage Page - Parent/child lot tracking
 * Connected to /api/v2/traceability endpoints
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  GitBranch, Search, Loader2, ArrowUp, ArrowDown, 
  Package, Calendar, MapPin, AlertCircle, RefreshCw 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface LotNode {
  lot_id: string;
  variety_name: string;
  crop: string;
  seed_class: string;
  production_year: number;
  quantity_kg: number;
  status: string;
}

interface LineageData {
  current: LotNode;
  parents: LotNode[];
  descendants: LotNode[];
}

export function Lineage() {
  const [lotNumber, setLotNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lineageData, setLineageData] = useState<LineageData | null>(null);

  const handleSearch = async () => {
    if (!lotNumber.trim()) return;

    setLoading(true);
    setError(null);
    setLineageData(null);

    try {
      // Fetch lot details, lineage, and descendants
      const [lotRes, lineageRes, descendantsRes] = await Promise.all([
        apiClient.traceabilityService.getTraceabilityLot(lotNumber),
        apiClient.traceabilityService.traceLotLineage(lotNumber),
        apiClient.traceabilityService.getLotDescendants(lotNumber),
      ]);

      if (lotRes.status !== 'success' || !lotRes.data) {
        throw new Error('Lot not found');
      }

      setLineageData({
        current: lotRes.data,
        parents: lineageRes.data?.parents || [],
        descendants: descendantsRes.data || [],
      });
    } catch (err: any) {
      setError(err.message || 'Lot not found. Please check the lot number and try again.');
    } finally {
      setLoading(false);
    }
  };

  const getSeedClassColor = (seedClass: string) => {
    switch (seedClass) {
      case 'breeder': return 'bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-700';
      case 'foundation': return 'bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600';
      case 'certified': return 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700';
      case 'truthful': return 'bg-green-100 text-green-700 border-green-300 dark:bg-green-900/30 dark:text-green-400 dark:border-green-700';
      default: return 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Active</Badge>;
      case 'depleted': return <Badge className="bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400">Depleted</Badge>;
      case 'expired': return <Badge className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">Expired</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  const LotCard = ({ lot, direction }: { lot: LotNode; direction?: 'parent' | 'child' }) => (
    <Card className={`${direction === 'parent' ? 'border-l-4 border-l-purple-400' : direction === 'child' ? 'border-l-4 border-l-green-400' : 'border-l-4 border-l-blue-400'}`}>
      <CardContent className="p-4">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2">
              <p className="font-medium">{lot.lot_id}</p>
              <Badge className={getSeedClassColor(lot.seed_class)}>{lot.seed_class}</Badge>
            </div>
            <p className="text-sm text-gray-500">{lot.variety_name} • {lot.crop}</p>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {lot.production_year}
              </span>
              <span className="flex items-center gap-1">
                <Package className="h-3 w-3" />
                {lot.quantity_kg} kg
              </span>
            </div>
          </div>
          {getStatusBadge(lot.status)}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <GitBranch className="h-6 w-6 text-purple-600" />
          Seed Lineage
        </h1>
        <p className="text-gray-500 text-sm">Track parent and descendant seed lots</p>
      </div>

      {/* Search */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Lineage Lookup</CardTitle>
          <CardDescription>Enter a lot number to view its seed multiplication chain</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Enter lot number (e.g., LOT-2024-001)..."
              value={lotNumber}
              onChange={(e) => setLotNumber(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={loading || !lotNumber.trim()}>
              {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="flex items-center justify-between p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={handleSearch}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      )}

      {/* Lineage Display */}
      {lineageData && (
        <div className="space-y-6">
          {/* Parents (Ancestors) */}
          {lineageData.parents.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <ArrowUp className="h-5 w-5 text-purple-600" />
                <h2 className="font-semibold text-gray-700">Parent Lots ({lineageData.parents.length})</h2>
              </div>
              <div className="space-y-3 pl-6 border-l-2 border-purple-200">
                {lineageData.parents.map((parent, index) => (
                  <div key={parent.lot_id} className="relative">
                    <div className="absolute -left-[25px] top-4 w-4 h-0.5 bg-purple-200" />
                    <LotCard lot={parent} direction="parent" />
                    {index < lineageData.parents.length - 1 && (
                      <div className="flex justify-center my-2">
                        <ArrowUp className="h-4 w-4 text-purple-300" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Current Lot */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Package className="h-5 w-5 text-blue-600" />
              <h2 className="font-semibold text-gray-700">Current Lot</h2>
            </div>
            <Card className="border-2 border-blue-400 bg-blue-50">
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-lg font-bold">{lineageData.current.lot_id}</p>
                      <Badge className={getSeedClassColor(lineageData.current.seed_class)}>
                        {lineageData.current.seed_class}
                      </Badge>
                    </div>
                    <p className="text-gray-600">{lineageData.current.variety_name} • {lineageData.current.crop}</p>
                    <div className="flex items-center gap-4 mt-2 text-gray-600">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {lineageData.current.production_year}
                      </span>
                      <span className="flex items-center gap-1">
                        <Package className="h-4 w-4" />
                        {lineageData.current.quantity_kg} kg
                      </span>
                    </div>
                  </div>
                  {getStatusBadge(lineageData.current.status)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Descendants (Children) */}
          {lineageData.descendants.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <ArrowDown className="h-5 w-5 text-green-600" />
                <h2 className="font-semibold text-gray-700">Descendant Lots ({lineageData.descendants.length})</h2>
              </div>
              <div className="space-y-3 pl-6 border-l-2 border-green-200">
                {lineageData.descendants.map((child) => (
                  <div key={child.lot_id} className="relative">
                    <div className="absolute -left-[25px] top-4 w-4 h-0.5 bg-green-200" />
                    <LotCard lot={child} direction="child" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          <Card className="bg-gray-50">
            <CardContent className="p-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-purple-600">{lineageData.parents.length}</p>
                  <p className="text-sm text-gray-500">Parent Generations</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-blue-600">1</p>
                  <p className="text-sm text-gray-500">Current Lot</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-600">{lineageData.descendants.length}</p>
                  <p className="text-sm text-gray-500">Descendant Lots</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State */}
      {!lineageData && !loading && !error && (
        <Card>
          <CardContent className="py-12 text-center text-gray-500">
            <GitBranch className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Enter a lot number to view its lineage</p>
            <p className="text-sm mt-1">Track seed multiplication from breeder to certified</p>
          </CardContent>
        </Card>
      )}

      {/* Seed Class Legend */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Seed Class Hierarchy</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Badge className="bg-purple-100 text-purple-700">Breeder</Badge>
              <span className="text-gray-500">→</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-white dark:bg-slate-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">Foundation</Badge>
              <span className="text-gray-500 dark:text-gray-400">→</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-blue-100 text-blue-700">Certified</Badge>
              <span className="text-gray-500">→</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-green-100 text-green-700">Truthfully Labeled</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Lineage;

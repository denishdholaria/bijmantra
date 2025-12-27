/**
 * Seed Lots Page - Inventory management
 * Connected to /api/v2/seed-inventory and /api/v2/traceability endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Package, Plus, Search, RefreshCw, AlertCircle, Warehouse, TrendingDown, CheckCircle } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface SeedLot {
  lot_id: string;
  variety_name?: string;
  variety?: string;
  crop?: string;
  species?: string;
  seed_class?: string;
  quantity_kg?: number;
  quantity?: number;
  storage_location?: string;
  status?: string;
  germination_percent?: number;
  purity_percent?: number;
  moisture_percent?: number;
  production_year?: number;
  harvest_date?: string;
}

interface InventorySummary {
  total_lots: number;
  total_quantity_kg: number;
  low_stock_count: number;
  active_lots: number;
}

export function SeedLots() {
  const [lots, setLots] = useState<SeedLot[]>([]);
  const [summary, setSummary] = useState<InventorySummary>({ total_lots: 0, total_quantity_kg: 0, low_stock_count: 0, active_lots: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showNewLotDialog, setShowNewLotDialog] = useState(false);
  const [newLot, setNewLot] = useState({
    variety_id: '',
    variety_name: '',
    crop: 'Rice',
    seed_class: 'certified',
    production_year: new Date().getFullYear(),
    production_season: 'Kharif',
    production_location: '',
    producer_id: 'PROD-001',
    producer_name: '',
    quantity_kg: 100,
    germination_percent: 90,
    purity_percent: 98,
    moisture_percent: 10,
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Try traceability API first (more comprehensive)
      const [lotsRes, summaryRes] = await Promise.all([
        apiClient.getTraceabilityLots(),
        apiClient.getTraceabilityStatistics(),
      ]);
      
      if (lotsRes.status === 'success') {
        setLots(lotsRes.data || []);
        if (summaryRes.status === 'success') {
          setSummary({
            total_lots: summaryRes.data.total_lots || lotsRes.data.length,
            total_quantity_kg: summaryRes.data.total_quantity_kg || 0,
            low_stock_count: summaryRes.data.low_stock_count || 0,
            active_lots: summaryRes.data.active_lots || lotsRes.data.length,
          });
        }
      } else {
        throw new Error('Failed to load lots');
      }
    } catch (err: any) {
      // Fallback to seed inventory API
      try {
        const invRes = await apiClient.getSeedInventoryLots();
        setLots(invRes.lots || []);
        const sumRes = await apiClient.getSeedInventorySummary();
        setSummary({
          total_lots: sumRes.total_lots || invRes.lots?.length || 0,
          total_quantity_kg: sumRes.total_quantity || 0,
          low_stock_count: sumRes.low_stock_count || 0,
          active_lots: sumRes.active_lots || invRes.lots?.length || 0,
        });
      } catch {
        // No data available - show empty state
        setError('Unable to load seed lots. Please check your connection.');
        setLots([]);
        setSummary({ total_lots: 0, total_quantity_kg: 0, low_stock_count: 0, active_lots: 0 });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateLot = async () => {
    try {
      await apiClient.registerTraceabilityLot(newLot);
      setShowNewLotDialog(false);
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to create lot');
    }
  };

  const filteredLots = lots.filter(lot => 
    lot.lot_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (lot.variety_name || lot.variety || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (lot.crop || lot.species || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (lot: SeedLot) => {
    if (lot.status === 'low_stock' || (lot.quantity_kg && lot.quantity_kg < 100)) {
      return <Badge className="bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300">Low Stock</Badge>;
    }
    if (lot.germination_percent && lot.germination_percent < 80) {
      return <Badge className="bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300">Low Viability</Badge>;
    }
    return <Badge className="bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300">Active</Badge>;
  };

  const getSeedClassBadge = (seedClass?: string) => {
    const colors: Record<string, string> = {
      foundation: 'bg-white dark:bg-slate-700 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300',
      certified: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
      truthful: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
      research: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
    };
    return <Badge className={colors[seedClass || 'certified'] || colors.certified}>{seedClass || 'Certified'}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Seed Lots</h1>
          <p className="text-muted-foreground text-sm">Manage seed lot inventory and traceability</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={showNewLotDialog} onOpenChange={setShowNewLotDialog}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Lot</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Register New Seed Lot</DialogTitle>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-4 py-4">
                <div className="space-y-2">
                  <Label>Variety Name</Label>
                  <Input value={newLot.variety_name} onChange={(e) => setNewLot({...newLot, variety_name: e.target.value, variety_id: e.target.value.toUpperCase().replace(/\s/g, '-')})} placeholder="IR64" />
                </div>
                <div className="space-y-2">
                  <Label>Crop</Label>
                  <Select value={newLot.crop} onValueChange={(v) => setNewLot({...newLot, crop: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Rice">Rice</SelectItem>
                      <SelectItem value="Wheat">Wheat</SelectItem>
                      <SelectItem value="Maize">Maize</SelectItem>
                      <SelectItem value="Soybean">Soybean</SelectItem>
                      <SelectItem value="Cotton">Cotton</SelectItem>
                      <SelectItem value="Sorghum">Sorghum</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Seed Class</Label>
                  <Select value={newLot.seed_class} onValueChange={(v) => setNewLot({...newLot, seed_class: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="foundation">Foundation</SelectItem>
                      <SelectItem value="certified">Certified</SelectItem>
                      <SelectItem value="truthful">Truthfully Labeled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Quantity (kg)</Label>
                  <Input type="number" value={newLot.quantity_kg} onChange={(e) => setNewLot({...newLot, quantity_kg: Number(e.target.value)})} />
                </div>
                <div className="space-y-2">
                  <Label>Production Location</Label>
                  <Input value={newLot.production_location} onChange={(e) => setNewLot({...newLot, production_location: e.target.value})} placeholder="Farm A, District" />
                </div>
                <div className="space-y-2">
                  <Label>Producer Name</Label>
                  <Input value={newLot.producer_name} onChange={(e) => setNewLot({...newLot, producer_name: e.target.value})} placeholder="ABC Seeds" />
                </div>
                <div className="space-y-2">
                  <Label>Germination %</Label>
                  <Input type="number" value={newLot.germination_percent} onChange={(e) => setNewLot({...newLot, germination_percent: Number(e.target.value)})} />
                </div>
                <div className="space-y-2">
                  <Label>Purity %</Label>
                  <Input type="number" value={newLot.purity_percent} onChange={(e) => setNewLot({...newLot, purity_percent: Number(e.target.value)})} />
                </div>
                <div className="col-span-2">
                  <Button onClick={handleCreateLot} className="w-full">Register Lot</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg text-yellow-800 dark:text-yellow-300 text-sm">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
              <Package className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{summary.total_lots}</p>
              <p className="text-sm text-muted-foreground">Total Lots</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-50 dark:bg-green-900/30 flex items-center justify-center">
              <Warehouse className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{(summary.total_quantity_kg / 1000).toFixed(1)}t</p>
              <p className="text-sm text-muted-foreground">Total Stock</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-yellow-50 dark:bg-yellow-900/30 flex items-center justify-center">
              <TrendingDown className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{summary.low_stock_count}</p>
              <p className="text-sm text-muted-foreground">Low Stock</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{summary.active_lots}</p>
              <p className="text-sm text-muted-foreground">Active Lots</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input 
          placeholder="Search lots by ID, variety, or crop..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Lots Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading seed lots...</div>
          ) : filteredLots.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
              <p>No seed lots found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50 border-b border-border">
                  <tr>
                    <th className="text-left p-4 font-medium text-foreground">Lot ID</th>
                    <th className="text-left p-4 font-medium text-foreground">Variety</th>
                    <th className="text-left p-4 font-medium text-foreground">Crop</th>
                    <th className="text-left p-4 font-medium text-foreground">Class</th>
                    <th className="text-right p-4 font-medium text-foreground">Quantity</th>
                    <th className="text-center p-4 font-medium text-foreground">Germ %</th>
                    <th className="text-left p-4 font-medium text-foreground">Location</th>
                    <th className="text-left p-4 font-medium text-foreground">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredLots.map((lot) => (
                    <tr key={lot.lot_id} className="hover:bg-muted/50">
                      <td className="p-4 font-medium text-foreground">{lot.lot_id}</td>
                      <td className="p-4 text-foreground">{lot.variety_name || lot.variety || '-'}</td>
                      <td className="p-4 text-foreground">{lot.crop || lot.species || '-'}</td>
                      <td className="p-4">{getSeedClassBadge(lot.seed_class)}</td>
                      <td className="p-4 text-right text-foreground">{lot.quantity_kg || lot.quantity || 0} kg</td>
                      <td className="p-4 text-center">
                        <span className={lot.germination_percent && lot.germination_percent < 80 ? 'text-red-600 dark:text-red-400 font-medium' : 'text-foreground'}>
                          {lot.germination_percent || '-'}%
                        </span>
                      </td>
                      <td className="p-4 text-muted-foreground">{lot.storage_location || '-'}</td>
                      <td className="p-4">{getStatusBadge(lot)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default SeedLots;

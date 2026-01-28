/**
 * Input Log Page
 *
 * Track field inputs: fertilizers, pesticides, amendments.
 * Connected to backend: /api/v2/field-environment/input-logs
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface InputLogEntry {
  id: string;
  field_id: string;
  input_type: string;
  product_name: string;
  application_date: string;
  quantity: number;
  unit: string;
  area_applied: number;
  method: string;
  cost: number | null;
  notes: string;
}

const INPUT_TYPE_ICONS: Record<string, string> = {
  fertilizer: '🌱',
  pesticide: '🐛',
  herbicide: '🌿',
  fungicide: '🍄',
  amendment: '🪨',
  seed: '🌾',
  water: '💧',
  other: '📦',
};

export function InputLog() {
  const [logs, setLogs] = useState<InputLogEntry[]>([]);
  const [inputTypes, setInputTypes] = useState<{value: string; name: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    field_id: 'field-001',
    input_type: 'fertilizer',
    product_name: '',
    quantity: 0,
    unit: 'kg',
    area_applied: 1.0,
    method: '',
    cost: 0,
  });

  useEffect(() => {
    fetchData();
  }, [filterType]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const typeParam = filterType !== 'all' ? `?input_type=${filterType}` : '';
      const [logsRes, typesRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/field-environment/input-logs${typeParam}`),
        fetch(`${API_BASE}/api/v2/field-environment/input-types`),
      ]);
      if (logsRes.ok) setLogs(await logsRes.json());
      if (typesRes.ok) {
        const data = await typesRes.json();
        setInputTypes(data.input_types || []);
      }
    } catch (error) {
      console.error('Failed to fetch input logs:', error);
      setError('Failed to load input logs. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddLog = async () => {
    if (!formData.product_name) {
      toast({ title: 'Error', description: 'Product name required', variant: 'destructive' });
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v2/field-environment/input-logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        toast({ title: 'Success', description: 'Input logged' });
        setDialogOpen(false);
        setFormData({ ...formData, product_name: '', quantity: 0, method: '', cost: 0 });
        fetchData();
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to add log', variant: 'destructive' });
    }
  };

  const totalCost = logs.reduce((sum, l) => sum + (l.cost || 0), 0);

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">Input Log</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Track fertilizers, pesticides, and field inputs</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild><Button>+ Log Input</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Log Field Input</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Field ID</Label><Input value={formData.field_id} onChange={(e) => setFormData({...formData, field_id: e.target.value})} /></div>
                <div><Label>Input Type</Label>
                  <Select value={formData.input_type} onValueChange={(v) => setFormData({...formData, input_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{inputTypes.map((t) => (<SelectItem key={t.value} value={t.value}>{INPUT_TYPE_ICONS[t.value] || '📦'} {t.name}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
              </div>
              <div><Label>Product Name</Label><Input placeholder="Urea 46-0-0" value={formData.product_name} onChange={(e) => setFormData({...formData, product_name: e.target.value})} /></div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>Quantity</Label><Input type="number" value={formData.quantity} onChange={(e) => setFormData({...formData, quantity: parseFloat(e.target.value)})} /></div>
                <div><Label>Unit</Label>
                  <Select value={formData.unit} onValueChange={(v) => setFormData({...formData, unit: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="kg">kg</SelectItem>
                      <SelectItem value="L">L</SelectItem>
                      <SelectItem value="g">g</SelectItem>
                      <SelectItem value="mL">mL</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Area (ha)</Label><Input type="number" step="0.1" value={formData.area_applied} onChange={(e) => setFormData({...formData, area_applied: parseFloat(e.target.value)})} /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Method</Label><Input placeholder="broadcast, foliar spray..." value={formData.method} onChange={(e) => setFormData({...formData, method: e.target.value})} /></div>
                <div><Label>Cost</Label><Input type="number" value={formData.cost} onChange={(e) => setFormData({...formData, cost: parseFloat(e.target.value)})} /></div>
              </div>
              <Button onClick={handleAddLog} className="w-full">Log Input</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><p className="text-2xl font-bold">{logs.length}</p><p className="text-sm text-gray-600">Total Entries</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-2xl font-bold">{logs.filter(l => l.input_type === 'fertilizer').length}</p><p className="text-sm text-gray-600">Fertilizers</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-2xl font-bold">{logs.filter(l => l.input_type === 'pesticide').length}</p><p className="text-sm text-gray-600">Pesticides</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-2xl font-bold">₹{totalCost.toLocaleString()}</p><p className="text-sm text-gray-600">Total Cost</p></CardContent></Card>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <Label>Filter:</Label>
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {inputTypes.map((t) => (<SelectItem key={t.value} value={t.value}>{t.name}</SelectItem>))}
          </SelectContent>
        </Select>
      </div>

      {/* Log Table */}
      <Card>
        <CardHeader><CardTitle>📋 Input History</CardTitle></CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {loading ? <p className="p-4 text-gray-500">Loading...</p> : logs.length === 0 ? <p className="p-4 text-gray-500">No inputs logged yet</p> : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Field</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-600">{log.application_date}</td>
                    <td className="px-4 py-3"><span className="inline-flex items-center gap-1">{INPUT_TYPE_ICONS[log.input_type] || '📦'} <span className="capitalize">{log.input_type}</span></span></td>
                    <td className="px-4 py-3 font-medium">{log.product_name}</td>
                    <td className="px-4 py-3">{log.field_id}</td>
                    <td className="px-4 py-3 text-right">{log.quantity} {log.unit}</td>
                    <td className="px-4 py-3 text-gray-600">{log.method || '-'}</td>
                    <td className="px-4 py-3 text-right">{log.cost ? `₹${log.cost}` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default InputLog;

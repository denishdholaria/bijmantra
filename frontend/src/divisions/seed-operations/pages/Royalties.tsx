/**
 * Royalties Page - Payment tracking and revenue management
 * 
 * Connects to /api/v2/licensing endpoints for royalty tracking.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import {
  DollarSign, Plus, Search, Calendar, TrendingUp, TrendingDown,
  CheckCircle2, Clock, AlertCircle, FileText, Download, Building2,
} from 'lucide-react';

interface License {
  id: string;
  variety_id: string;
  variety_name?: string;
  licensee_name: string;
  royalty_rate_percent: number;
  status: string;
}

interface Variety {
  id: string;
  variety_name: string;
  crop: string;
}

interface RoyaltySummary {
  variety_id: string;
  variety_name: string;
  total_royalties: number;
  total_paid: number;
  total_pending: number;
  license_count: number;
  royalty_records: RoyaltyRecord[];
}

interface RoyaltyRecord {
  id: string;
  license_id: string;
  licensee_name?: string;
  variety_name?: string;
  period_start: string;
  period_end: string;
  sales_quantity_kg: number;
  sales_value: number;
  royalty_amount: number;
  payment_status: string;
  created_at: string;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  invoiced: 'bg-blue-100 text-blue-800',
  paid: 'bg-green-100 text-green-800',
  overdue: 'bg-red-100 text-red-800',
};

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Clock className="h-3 w-3" />,
  invoiced: <FileText className="h-3 w-3" />,
  paid: <CheckCircle2 className="h-3 w-3" />,
  overdue: <AlertCircle className="h-3 w-3" />,
};

export function Royalties() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedVariety, setSelectedVariety] = useState<string>('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newRoyalty, setNewRoyalty] = useState({
    license_id: '',
    period_start: '',
    period_end: '',
    sales_quantity_kg: '',
    sales_value: '',
    royalty_amount: '',
  });

  // Fetch varieties for selection
  const { data: varietiesResponse } = useQuery({
    queryKey: ['licensing-varieties'],
    queryFn: () => apiClient.getLicensingVarieties(),
  });
  const varieties: Variety[] = varietiesResponse?.data || [];

  // Fetch licenses for dropdown
  const { data: licensesResponse } = useQuery({
    queryKey: ['licenses', 'active'],
    queryFn: () => apiClient.getLicenses(undefined, undefined, undefined, 'active'),
  });
  const licenses: License[] = licensesResponse?.data || [];

  // Fetch royalty summary for selected variety
  const { data: summaryResponse, isLoading } = useQuery({
    queryKey: ['royalty-summary', selectedVariety],
    queryFn: () => selectedVariety ? apiClient.getVarietyRoyaltySummary(selectedVariety) : null,
    enabled: !!selectedVariety,
  });
  const summary: RoyaltySummary | null = summaryResponse?.data || null;

  // Fetch licensing statistics
  const { data: statsResponse } = useQuery({
    queryKey: ['licensing-statistics'],
    queryFn: () => apiClient.getLicensingStatistics(),
  });
  const stats = statsResponse?.data || {
    total_varieties: 0,
    total_licenses: 0,
    active_licenses: 0,
    total_royalties_collected: 0,
  };

  // Record royalty mutation
  const recordMutation = useMutation({
    mutationFn: async (data: typeof newRoyalty) => {
      return apiClient.recordRoyalty(data.license_id, {
        period_start: data.period_start,
        period_end: data.period_end,
        sales_quantity_kg: parseFloat(data.sales_quantity_kg) || 0,
        sales_value: parseFloat(data.sales_value) || 0,
        royalty_amount: parseFloat(data.royalty_amount) || 0,
        payment_status: 'pending',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['royalty-summary'] });
      queryClient.invalidateQueries({ queryKey: ['licensing-statistics'] });
      toast.success('Royalty recorded successfully');
      setIsDialogOpen(false);
      setNewRoyalty({
        license_id: '', period_start: '', period_end: '',
        sales_quantity_kg: '', sales_value: '', royalty_amount: '',
      });
    },
    onError: () => toast.error('Failed to record royalty'),
  });

  // Calculate royalty amount based on sales and rate
  const calculateRoyalty = () => {
    const license = licenses.find(l => l.id === newRoyalty.license_id);
    if (license && newRoyalty.sales_value) {
      const amount = (parseFloat(newRoyalty.sales_value) * license.royalty_rate_percent / 100).toFixed(2);
      setNewRoyalty({ ...newRoyalty, royalty_amount: amount });
    }
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
  };

  // Filter royalty records
  const royaltyRecords = summary?.royalty_records || [];
  const filteredRecords = royaltyRecords.filter((r) => {
    const matchesSearch = (r.licensee_name?.toLowerCase().includes(search.toLowerCase()) ?? true);
    const matchesStatus = statusFilter === 'all' || r.payment_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Calculate totals
  const totals = {
    total: summary?.total_royalties || stats.total_royalties_collected || 0,
    paid: summary?.total_paid || 0,
    pending: summary?.total_pending || 0,
    outstanding: (summary?.total_royalties || 0) - (summary?.total_paid || 0),
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <DollarSign className="h-6 w-6" />Royalties
          </h1>
          <p className="text-muted-foreground">Track royalty payments and revenue from licensed varieties</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />Record Royalty</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>Record Royalty Payment</DialogTitle></DialogHeader>
              <form onSubmit={(e) => { e.preventDefault(); recordMutation.mutate(newRoyalty); }} className="space-y-4">
                <div className="space-y-2">
                  <Label>License Agreement *</Label>
                  <Select value={newRoyalty.license_id} onValueChange={(v) => setNewRoyalty({ ...newRoyalty, license_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select license" /></SelectTrigger>
                    <SelectContent>
                      {licenses.map((l) => (
                        <SelectItem key={l.id} value={l.id}>
                          {l.variety_name || 'Variety'} - {l.licensee_name} ({l.royalty_rate_percent}%)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Period Start *</Label>
                    <Input type="date" value={newRoyalty.period_start} onChange={(e) => setNewRoyalty({ ...newRoyalty, period_start: e.target.value })} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Period End *</Label>
                    <Input type="date" value={newRoyalty.period_end} onChange={(e) => setNewRoyalty({ ...newRoyalty, period_end: e.target.value })} required />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Sales Quantity (kg)</Label>
                    <Input type="number" value={newRoyalty.sales_quantity_kg} onChange={(e) => setNewRoyalty({ ...newRoyalty, sales_quantity_kg: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Sales Value *</Label>
                    <Input type="number" step="0.01" value={newRoyalty.sales_value} onChange={(e) => setNewRoyalty({ ...newRoyalty, sales_value: e.target.value })} onBlur={calculateRoyalty} required />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Royalty Amount *</Label>
                  <Input type="number" step="0.01" value={newRoyalty.royalty_amount} onChange={(e) => setNewRoyalty({ ...newRoyalty, royalty_amount: e.target.value })} required />
                  <p className="text-xs text-muted-foreground">Auto-calculated based on sales value and royalty rate</p>
                </div>
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                  <Button type="submit" disabled={recordMutation.isPending}>{recordMutation.isPending ? 'Recording...' : 'Record'}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-blue-100 rounded-lg"><DollarSign className="h-5 w-5 text-blue-600" /></div><div><p className="text-2xl font-bold">{formatCurrency(totals.total)}</p><p className="text-xs text-muted-foreground">Total Royalties</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-green-100 rounded-lg"><TrendingUp className="h-5 w-5 text-green-600" /></div><div><p className="text-2xl font-bold">{formatCurrency(totals.paid)}</p><p className="text-xs text-muted-foreground">Collected</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-yellow-100 rounded-lg"><Clock className="h-5 w-5 text-yellow-600" /></div><div><p className="text-2xl font-bold">{formatCurrency(totals.pending)}</p><p className="text-xs text-muted-foreground">Pending</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-red-100 rounded-lg"><TrendingDown className="h-5 w-5 text-red-600" /></div><div><p className="text-2xl font-bold">{formatCurrency(totals.outstanding)}</p><p className="text-xs text-muted-foreground">Outstanding</p></div></div></CardContent></Card>
      </div>

      <div className="flex gap-4">
        <Select value={selectedVariety} onValueChange={setSelectedVariety}>
          <SelectTrigger className="w-[250px]"><SelectValue placeholder="Select variety to view" /></SelectTrigger>
          <SelectContent>
            {varieties.map((v) => <SelectItem key={v.id} value={v.id}>{v.variety_name} ({v.crop})</SelectItem>)}
          </SelectContent>
        </Select>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search by licensee..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="invoiced">Invoiced</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
            <SelectItem value="overdue">Overdue</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {!selectedVariety ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <DollarSign className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Select a variety to view royalty records</p>
            <p className="text-sm mt-1">Choose from the dropdown above</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Royalty Records - {summary?.variety_name || 'Loading...'}</CardTitle>
            <CardDescription>
              {summary?.license_count || 0} active licenses • {filteredRecords.length} records
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>
            ) : filteredRecords.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <DollarSign className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No royalty records found</p>
                <p className="text-sm">Record your first royalty payment</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Licensee</TableHead>
                    <TableHead>Period</TableHead>
                    <TableHead>Sales (kg)</TableHead>
                    <TableHead>Sales Value</TableHead>
                    <TableHead>Royalty</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRecords.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3 text-muted-foreground" />
                          {record.licensee_name || '-'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="flex items-center gap-1 text-sm">
                          <Calendar className="h-3 w-3" />
                          {record.period_start} - {record.period_end}
                        </span>
                      </TableCell>
                      <TableCell>{record.sales_quantity_kg?.toLocaleString() || '-'}</TableCell>
                      <TableCell>{formatCurrency(record.sales_value)}</TableCell>
                      <TableCell className="font-medium">{formatCurrency(record.royalty_amount)}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[record.payment_status] || 'bg-gray-100'}>
                          <span className="flex items-center gap-1">
                            {statusIcons[record.payment_status]}
                            {record.payment_status}
                          </span>
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {/* Quick Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Licensing Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="p-4 bg-muted/50 rounded-lg">
              <p className="text-3xl font-bold">{stats.total_varieties}</p>
              <p className="text-sm text-muted-foreground">Registered Varieties</p>
            </div>
            <div className="p-4 bg-muted/50 rounded-lg">
              <p className="text-3xl font-bold">{stats.total_licenses}</p>
              <p className="text-sm text-muted-foreground">Total Licenses</p>
            </div>
            <div className="p-4 bg-muted/50 rounded-lg">
              <p className="text-3xl font-bold">{stats.active_licenses}</p>
              <p className="text-sm text-muted-foreground">Active Licenses</p>
            </div>
            <div className="p-4 bg-muted/50 rounded-lg">
              <p className="text-3xl font-bold">{formatCurrency(stats.total_royalties_collected)}</p>
              <p className="text-sm text-muted-foreground">Total Collected</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Royalties;

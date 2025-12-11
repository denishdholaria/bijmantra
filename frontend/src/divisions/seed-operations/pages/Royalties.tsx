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
import { Textarea } from '@/components/ui/textarea';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import {
  DollarSign,
  Plus,
  Search,
  Calendar,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Download,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Royalty {
  id: string;
  agreement_id: string;
  agreement_name?: string;
  variety_name?: string;
  licensee?: string;
  period_start: string;
  period_end: string;
  sales_quantity?: number;
  sales_value?: number;
  royalty_amount: number;
  currency: string;
  status: string;
  payment_date?: string;
  notes?: string;
  created_at: string;
}

interface Agreement {
  id: string;
  variety_name?: string;
  licensee: string;
  royalty_rate?: number;
}

interface RoyaltySummary {
  total_due: number;
  total_paid: number;
  total_pending: number;
  by_variety: Record<string, number>;
  by_licensee: Record<string, number>;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  invoiced: 'bg-blue-100 text-blue-800',
  paid: 'bg-green-100 text-green-800',
  overdue: 'bg-red-100 text-red-800',
  disputed: 'bg-orange-100 text-orange-800',
};

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Clock className="h-3 w-3" />,
  invoiced: <FileText className="h-3 w-3" />,
  paid: <CheckCircle2 className="h-3 w-3" />,
  overdue: <AlertCircle className="h-3 w-3" />,
  disputed: <AlertCircle className="h-3 w-3" />,
};

export function Royalties() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<string>(new Date().getFullYear().toString());
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newRoyalty, setNewRoyalty] = useState({
    agreement_id: '',
    period_start: '',
    period_end: '',
    sales_quantity: '',
    sales_value: '',
    royalty_amount: '',
    currency: 'USD',
    notes: '',
  });

  // Fetch royalties
  const { data: royalties = [], isLoading } = useQuery<Royalty[]>({
    queryKey: ['royalties', yearFilter],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/royalties?year=${yearFilter}`);
      if (!res.ok) throw new Error('Failed to fetch royalties');
      return res.json();
    },
  });

  // Fetch agreements for dropdown
  const { data: agreements = [] } = useQuery<Agreement[]>({
    queryKey: ['agreements'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/agreements?status=active`);
      if (!res.ok) throw new Error('Failed to fetch agreements');
      return res.json();
    },
  });

  // Fetch royalty summary
  const { data: summary } = useQuery<RoyaltySummary>({
    queryKey: ['royalty-summary', yearFilter],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/royalties/summary?year=${yearFilter}`);
      if (!res.ok) throw new Error('Failed to fetch summary');
      return res.json();
    },
  });

  // Record royalty mutation
  const recordMutation = useMutation({
    mutationFn: async (data: typeof newRoyalty) => {
      const payload = {
        ...data,
        sales_quantity: data.sales_quantity ? parseInt(data.sales_quantity) : undefined,
        sales_value: data.sales_value ? parseFloat(data.sales_value) : undefined,
        royalty_amount: parseFloat(data.royalty_amount),
      };
      const res = await fetch(`${API_BASE}/api/v2/licensing/royalties`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to record royalty');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['royalties'] });
      queryClient.invalidateQueries({ queryKey: ['royalty-summary'] });
      toast.success('Royalty recorded successfully');
      setIsDialogOpen(false);
      setNewRoyalty({
        agreement_id: '',
        period_start: '',
        period_end: '',
        sales_quantity: '',
        sales_value: '',
        royalty_amount: '',
        currency: 'USD',
        notes: '',
      });
    },
    onError: () => {
      toast.error('Failed to record royalty');
    },
  });

  // Mark as paid mutation
  const markPaidMutation = useMutation({
    mutationFn: async (royaltyId: string) => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/royalties/${royaltyId}/pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payment_date: new Date().toISOString().split('T')[0] }),
      });
      if (!res.ok) throw new Error('Failed to mark as paid');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['royalties'] });
      queryClient.invalidateQueries({ queryKey: ['royalty-summary'] });
      toast.success('Royalty marked as paid');
    },
    onError: () => {
      toast.error('Failed to update royalty');
    },
  });

  // Filter royalties
  const filteredRoyalties = royalties.filter((r) => {
    const matchesSearch =
      (r.variety_name?.toLowerCase().includes(search.toLowerCase()) ?? false) ||
      (r.licensee?.toLowerCase().includes(search.toLowerCase()) ?? false);
    const matchesStatus = statusFilter === 'all' || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Calculate totals
  const totals = {
    due: summary?.total_due || royalties.filter(r => r.status !== 'paid').reduce((sum, r) => sum + r.royalty_amount, 0),
    paid: summary?.total_paid || royalties.filter(r => r.status === 'paid').reduce((sum, r) => sum + r.royalty_amount, 0),
    pending: summary?.total_pending || royalties.filter(r => r.status === 'pending').reduce((sum, r) => sum + r.royalty_amount, 0),
    total: royalties.reduce((sum, r) => sum + r.royalty_amount, 0),
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    recordMutation.mutate(newRoyalty);
  };

  // Generate year options
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => (currentYear - i).toString());

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <DollarSign className="h-6 w-6" />
            Royalties
          </h1>
          <p className="text-muted-foreground">
            Track royalty payments and revenue from licensed varieties
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Record Royalty
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Record Royalty Payment</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Agreement *</Label>
                  <Select
                    value={newRoyalty.agreement_id}
                    onValueChange={(v) => setNewRoyalty({ ...newRoyalty, agreement_id: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select agreement" />
                    </SelectTrigger>
                    <SelectContent>
                      {agreements.map((a) => (
                        <SelectItem key={a.id} value={a.id}>
                          {a.variety_name || 'Variety'} - {a.licensee}
                          {a.royalty_rate && ` (${a.royalty_rate}%)`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Period Start *</Label>
                    <Input
                      type="date"
                      value={newRoyalty.period_start}
                      onChange={(e) => setNewRoyalty({ ...newRoyalty, period_start: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Period End *</Label>
                    <Input
                      type="date"
                      value={newRoyalty.period_end}
                      onChange={(e) => setNewRoyalty({ ...newRoyalty, period_end: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Sales Quantity</Label>
                    <Input
                      type="number"
                      value={newRoyalty.sales_quantity}
                      onChange={(e) => setNewRoyalty({ ...newRoyalty, sales_quantity: e.target.value })}
                      placeholder="Units sold"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Sales Value</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={newRoyalty.sales_value}
                      onChange={(e) => setNewRoyalty({ ...newRoyalty, sales_value: e.target.value })}
                      placeholder="Total sales"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Royalty Amount *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={newRoyalty.royalty_amount}
                      onChange={(e) => setNewRoyalty({ ...newRoyalty, royalty_amount: e.target.value })}
                      placeholder="Amount due"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Currency</Label>
                    <Select
                      value={newRoyalty.currency}
                      onValueChange={(v) => setNewRoyalty({ ...newRoyalty, currency: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="EUR">EUR</SelectItem>
                        <SelectItem value="INR">INR</SelectItem>
                        <SelectItem value="GBP">GBP</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea
                    value={newRoyalty.notes}
                    onChange={(e) => setNewRoyalty({ ...newRoyalty, notes: e.target.value })}
                    placeholder="Additional notes..."
                    rows={2}
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={recordMutation.isPending}>
                    {recordMutation.isPending ? 'Recording...' : 'Record Royalty'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <DollarSign className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCurrency(totals.total)}</p>
                <p className="text-xs text-muted-foreground">Total {yearFilter}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCurrency(totals.paid)}</p>
                <p className="text-xs text-muted-foreground">Collected</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCurrency(totals.pending)}</p>
                <p className="text-xs text-muted-foreground">Pending</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <TrendingDown className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCurrency(totals.due - totals.paid)}</p>
                <p className="text-xs text-muted-foreground">Outstanding</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by variety or licensee..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={yearFilter} onValueChange={setYearFilter}>
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Year" />
          </SelectTrigger>
          <SelectContent>
            {years.map((year) => (
              <SelectItem key={year} value={year}>
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="invoiced">Invoiced</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
            <SelectItem value="overdue">Overdue</SelectItem>
            <SelectItem value="disputed">Disputed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Royalty Records</CardTitle>
          <CardDescription>
            {filteredRoyalties.length} records for {yearFilter}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : filteredRoyalties.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <DollarSign className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No royalty records found</p>
              <p className="text-sm">Record your first royalty payment</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Variety</TableHead>
                  <TableHead>Licensee</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead>Sales</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRoyalties.map((royalty) => (
                  <TableRow key={royalty.id}>
                    <TableCell className="font-medium">
                      {royalty.variety_name || '-'}
                    </TableCell>
                    <TableCell>{royalty.licensee || '-'}</TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1 text-sm">
                        <Calendar className="h-3 w-3" />
                        {royalty.period_start} - {royalty.period_end}
                      </span>
                    </TableCell>
                    <TableCell>
                      {royalty.sales_quantity && (
                        <div className="text-sm">
                          <div>{royalty.sales_quantity.toLocaleString()} units</div>
                          {royalty.sales_value && (
                            <div className="text-muted-foreground">
                              {formatCurrency(royalty.sales_value, royalty.currency)}
                            </div>
                          )}
                        </div>
                      )}
                      {!royalty.sales_quantity && '-'}
                    </TableCell>
                    <TableCell className="font-medium">
                      {formatCurrency(royalty.royalty_amount, royalty.currency)}
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[royalty.status] || 'bg-gray-100'}>
                        <span className="flex items-center gap-1">
                          {statusIcons[royalty.status]}
                          {royalty.status}
                        </span>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {royalty.status !== 'paid' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => markPaidMutation.mutate(royalty.id)}
                          disabled={markPaidMutation.isPending}
                        >
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Mark Paid
                        </Button>
                      )}
                      {royalty.status === 'paid' && royalty.payment_date && (
                        <span className="text-xs text-muted-foreground">
                          Paid {royalty.payment_date}
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default Royalties;

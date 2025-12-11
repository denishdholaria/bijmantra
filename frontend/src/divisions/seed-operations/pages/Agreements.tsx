/**
 * Agreements Page - License agreements management
 * 
 * Connects to /api/v2/licensing endpoints for license agreement tracking.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
  FileText,
  Plus,
  Search,
  Calendar,
  Building2,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Agreement {
  id: string;
  variety_id: string;
  variety_name?: string;
  licensee: string;
  license_type: string;
  territory?: string;
  start_date: string;
  end_date?: string;
  royalty_rate?: number;
  status: string;
  created_at: string;
}

interface LicenseType {
  code: string;
  name: string;
  description: string;
}

interface Variety {
  id: string;
  name: string;
  crop: string;
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800',
  expired: 'bg-yellow-100 text-yellow-800',
  terminated: 'bg-red-100 text-red-800',
  pending: 'bg-blue-100 text-blue-800',
};

const statusIcons: Record<string, React.ReactNode> = {
  draft: <FileText className="h-3 w-3" />,
  active: <CheckCircle2 className="h-3 w-3" />,
  expired: <AlertTriangle className="h-3 w-3" />,
  terminated: <XCircle className="h-3 w-3" />,
  pending: <Clock className="h-3 w-3" />,
};

const licenseTypeColors: Record<string, string> = {
  exclusive: 'bg-purple-100 text-purple-800',
  'non-exclusive': 'bg-blue-100 text-blue-800',
  research: 'bg-green-100 text-green-800',
  evaluation: 'bg-yellow-100 text-yellow-800',
};

export function Agreements() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newAgreement, setNewAgreement] = useState({
    variety_id: '',
    licensee: '',
    license_type: '',
    territory: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    royalty_rate: '',
  });

  // Fetch agreements
  const { data: agreements = [], isLoading } = useQuery<Agreement[]>({
    queryKey: ['agreements'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/agreements`);
      if (!res.ok) throw new Error('Failed to fetch agreements');
      return res.json();
    },
  });

  // Fetch varieties for dropdown
  const { data: varieties = [] } = useQuery<Variety[]>({
    queryKey: ['varieties'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/varieties`);
      if (!res.ok) throw new Error('Failed to fetch varieties');
      return res.json();
    },
  });

  // Fetch license types
  const { data: licenseTypes = [] } = useQuery<LicenseType[]>({
    queryKey: ['license-types'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/license-types`);
      if (!res.ok) throw new Error('Failed to fetch license types');
      return res.json();
    },
  });

  // Create agreement mutation
  const createMutation = useMutation({
    mutationFn: async (data: typeof newAgreement) => {
      const payload = {
        ...data,
        royalty_rate: data.royalty_rate ? parseFloat(data.royalty_rate) : undefined,
        end_date: data.end_date || undefined,
      };
      const res = await fetch(`${API_BASE}/api/v2/licensing/agreements`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to create agreement');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agreements'] });
      toast.success('Agreement created successfully');
      setIsDialogOpen(false);
      setNewAgreement({
        variety_id: '',
        licensee: '',
        license_type: '',
        territory: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        royalty_rate: '',
      });
    },
    onError: () => {
      toast.error('Failed to create agreement');
    },
  });

  // Activate agreement mutation
  const activateMutation = useMutation({
    mutationFn: async (agreementId: string) => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/agreements/${agreementId}/activate`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to activate agreement');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agreements'] });
      toast.success('Agreement activated');
    },
    onError: () => {
      toast.error('Failed to activate agreement');
    },
  });

  // Filter agreements
  const filteredAgreements = agreements.filter((a) => {
    const matchesSearch =
      a.licensee.toLowerCase().includes(search.toLowerCase()) ||
      (a.variety_name?.toLowerCase().includes(search.toLowerCase()) ?? false);
    const matchesStatus = statusFilter === 'all' || a.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Stats
  const stats = {
    total: agreements.length,
    active: agreements.filter((a) => a.status === 'active').length,
    pending: agreements.filter((a) => a.status === 'pending' || a.status === 'draft').length,
    expiring: agreements.filter((a) => {
      if (!a.end_date) return false;
      const endDate = new Date(a.end_date);
      const thirtyDays = new Date();
      thirtyDays.setDate(thirtyDays.getDate() + 30);
      return endDate <= thirtyDays && a.status === 'active';
    }).length,
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(newAgreement);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="h-6 w-6" />
            License Agreements
          </h1>
          <p className="text-muted-foreground">
            Manage licensing contracts and royalty arrangements
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Agreement
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Create License Agreement</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Variety *</Label>
                <Select
                  value={newAgreement.variety_id}
                  onValueChange={(v) => setNewAgreement({ ...newAgreement, variety_id: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select variety" />
                  </SelectTrigger>
                  <SelectContent>
                    {varieties.map((v) => (
                      <SelectItem key={v.id} value={v.id}>
                        {v.name} ({v.crop})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Licensee *</Label>
                <Input
                  value={newAgreement.licensee}
                  onChange={(e) => setNewAgreement({ ...newAgreement, licensee: e.target.value })}
                  placeholder="Company or organization name"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>License Type *</Label>
                  <Select
                    value={newAgreement.license_type}
                    onValueChange={(v) => setNewAgreement({ ...newAgreement, license_type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {licenseTypes.map((lt) => (
                        <SelectItem key={lt.code} value={lt.code}>
                          {lt.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Territory</Label>
                  <Input
                    value={newAgreement.territory}
                    onChange={(e) => setNewAgreement({ ...newAgreement, territory: e.target.value })}
                    placeholder="e.g., India, Global"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Start Date *</Label>
                  <Input
                    type="date"
                    value={newAgreement.start_date}
                    onChange={(e) => setNewAgreement({ ...newAgreement, start_date: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>End Date</Label>
                  <Input
                    type="date"
                    value={newAgreement.end_date}
                    onChange={(e) => setNewAgreement({ ...newAgreement, end_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Royalty Rate (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={newAgreement.royalty_rate}
                  onChange={(e) => setNewAgreement({ ...newAgreement, royalty_rate: e.target.value })}
                  placeholder="e.g., 5.0"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Agreement'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-muted-foreground">Total Agreements</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.active}</p>
                <p className="text-xs text-muted-foreground">Active</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Clock className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.pending}</p>
                <p className="text-xs text-muted-foreground">Pending</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.expiring}</p>
                <p className="text-xs text-muted-foreground">Expiring Soon</p>
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
            placeholder="Search by licensee or variety..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
            <SelectItem value="terminated">Terminated</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Agreement Registry</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : filteredAgreements.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No agreements found</p>
              <p className="text-sm">Create your first license agreement</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Variety</TableHead>
                  <TableHead>Licensee</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Territory</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead>Royalty</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAgreements.map((agreement) => (
                  <TableRow key={agreement.id}>
                    <TableCell className="font-medium">
                      {agreement.variety_name || agreement.variety_id}
                    </TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1">
                        <Building2 className="h-3 w-3 text-muted-foreground" />
                        {agreement.licensee}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge className={licenseTypeColors[agreement.license_type] || 'bg-gray-100'}>
                        {agreement.license_type}
                      </Badge>
                    </TableCell>
                    <TableCell>{agreement.territory || 'Global'}</TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1 text-sm">
                        <Calendar className="h-3 w-3" />
                        {agreement.start_date}
                        {agreement.end_date && ` - ${agreement.end_date}`}
                      </span>
                    </TableCell>
                    <TableCell>
                      {agreement.royalty_rate ? `${agreement.royalty_rate}%` : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[agreement.status] || 'bg-gray-100'}>
                        <span className="flex items-center gap-1">
                          {statusIcons[agreement.status]}
                          {agreement.status}
                        </span>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {(agreement.status === 'draft' || agreement.status === 'pending') && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => activateMutation.mutate(agreement.id)}
                          disabled={activateMutation.isPending}
                        >
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Activate
                        </Button>
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

export default Agreements;

/**
 * Agreements Page - License agreements management
 * 
 * Connects to /api/v2/licensing endpoints for license agreement tracking.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
  FileText, Plus, Search, Calendar, Building2, CheckCircle2,
  Clock, XCircle, AlertTriangle, DollarSign, Globe, Play,
} from 'lucide-react';

interface License {
  id: string;
  variety_id: string;
  variety_name?: string;
  licensee_id: string;
  licensee_name: string;
  license_type: string;
  territory: string[];
  start_date: string;
  end_date: string;
  royalty_rate_percent: number;
  minimum_royalty?: number;
  upfront_fee?: number;
  terms?: string;
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
  variety_name: string;
  crop: string;
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  pending: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  expired: 'bg-yellow-100 text-yellow-800',
  terminated: 'bg-red-100 text-red-800',
};

const statusIcons: Record<string, React.ReactNode> = {
  draft: <FileText className="h-3 w-3" />,
  pending: <Clock className="h-3 w-3" />,
  active: <CheckCircle2 className="h-3 w-3" />,
  expired: <AlertTriangle className="h-3 w-3" />,
  terminated: <XCircle className="h-3 w-3" />,
};

const licenseTypeColors: Record<string, string> = {
  exclusive: 'bg-purple-100 text-purple-800',
  non_exclusive: 'bg-blue-100 text-blue-800',
  research: 'bg-green-100 text-green-800',
  evaluation: 'bg-yellow-100 text-yellow-800',
  production: 'bg-orange-100 text-orange-800',
  marketing: 'bg-pink-100 text-pink-800',
};

export function Agreements() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newLicense, setNewLicense] = useState({
    variety_id: '',
    licensee_id: '',
    licensee_name: '',
    license_type: '',
    territory: 'India',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    royalty_rate_percent: '',
    minimum_royalty: '',
    upfront_fee: '',
    terms: '',
  });

  const { data: licensesResponse, isLoading } = useQuery({
    queryKey: ['licenses'],
    queryFn: () => apiClient.getLicenses(),
  });
  const licenses: License[] = licensesResponse?.data || [];

  const { data: varietiesResponse } = useQuery({
    queryKey: ['licensing-varieties'],
    queryFn: () => apiClient.getLicensingVarieties(),
  });
  const varieties: Variety[] = varietiesResponse?.data || [];

  const { data: licenseTypesResponse } = useQuery({
    queryKey: ['license-types'],
    queryFn: () => apiClient.getLicenseTypes(),
  });
  const licenseTypes: LicenseType[] = licenseTypesResponse?.data || [];

  const createMutation = useMutation({
    mutationFn: async (data: typeof newLicense) => {
      const variety = varieties.find(v => v.id === data.variety_id);
      return apiClient.createLicense({
        variety_id: data.variety_id,
        licensee_id: data.licensee_id || `licensee-${Date.now()}`,
        licensee_name: data.licensee_name,
        license_type: data.license_type,
        territory: data.territory.split(',').map(t => t.trim()),
        start_date: data.start_date,
        end_date: data.end_date,
        royalty_rate_percent: parseFloat(data.royalty_rate_percent) || 0,
        minimum_royalty: data.minimum_royalty ? parseFloat(data.minimum_royalty) : undefined,
        upfront_fee: data.upfront_fee ? parseFloat(data.upfront_fee) : undefined,
        terms: data.terms || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['licenses'] });
      toast.success('License agreement created');
      setIsDialogOpen(false);
      setNewLicense({
        variety_id: '', licensee_id: '', licensee_name: '', license_type: '',
        territory: 'India', start_date: new Date().toISOString().split('T')[0],
        end_date: '', royalty_rate_percent: '', minimum_royalty: '', upfront_fee: '', terms: '',
      });
    },
    onError: () => toast.error('Failed to create agreement'),
  });

  const activateMutation = useMutation({
    mutationFn: (licenseId: string) => apiClient.activateLicense(licenseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['licenses'] });
      toast.success('License activated');
    },
    onError: () => toast.error('Failed to activate'),
  });

  const filteredLicenses = licenses.filter((l) => {
    const matchesSearch = l.licensee_name.toLowerCase().includes(search.toLowerCase()) ||
      (l.variety_name?.toLowerCase().includes(search.toLowerCase()) ?? false);
    const matchesStatus = statusFilter === 'all' || l.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const stats = {
    total: licenses.length,
    active: licenses.filter(l => l.status === 'active').length,
    pending: licenses.filter(l => l.status === 'pending' || l.status === 'draft').length,
    expiring: licenses.filter(l => {
      if (!l.end_date || l.status !== 'active') return false;
      const endDate = new Date(l.end_date);
      const thirtyDays = new Date();
      thirtyDays.setDate(thirtyDays.getDate() + 30);
      return endDate <= thirtyDays;
    }).length,
  };

  const getVarietyName = (varietyId: string) => {
    const variety = varieties.find(v => v.id === varietyId);
    return variety?.variety_name || varietyId;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="h-6 w-6" />License Agreements
          </h1>
          <p className="text-muted-foreground">Manage licensing contracts and royalty arrangements</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-2" />New Agreement</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Create License Agreement</DialogTitle></DialogHeader>
            <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(newLicense); }} className="space-y-4">
              <div className="space-y-2">
                <Label>Variety *</Label>
                <Select value={newLicense.variety_id} onValueChange={(v) => setNewLicense({ ...newLicense, variety_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Select variety" /></SelectTrigger>
                  <SelectContent>
                    {varieties.map((v) => <SelectItem key={v.id} value={v.id}>{v.variety_name} ({v.crop})</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Licensee Name *</Label>
                <Input value={newLicense.licensee_name} onChange={(e) => setNewLicense({ ...newLicense, licensee_name: e.target.value })} placeholder="Company name" required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>License Type *</Label>
                  <Select value={newLicense.license_type} onValueChange={(v) => setNewLicense({ ...newLicense, license_type: v })}>
                    <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                    <SelectContent>
                      {licenseTypes.map((lt) => <SelectItem key={lt.code} value={lt.code}>{lt.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Territory</Label>
                  <Input value={newLicense.territory} onChange={(e) => setNewLicense({ ...newLicense, territory: e.target.value })} placeholder="India, USA" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Start Date *</Label>
                  <Input type="date" value={newLicense.start_date} onChange={(e) => setNewLicense({ ...newLicense, start_date: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label>End Date *</Label>
                  <Input type="date" value={newLicense.end_date} onChange={(e) => setNewLicense({ ...newLicense, end_date: e.target.value })} required />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Royalty Rate (%) *</Label>
                  <Input type="number" step="0.1" value={newLicense.royalty_rate_percent} onChange={(e) => setNewLicense({ ...newLicense, royalty_rate_percent: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label>Min Royalty</Label>
                  <Input type="number" value={newLicense.minimum_royalty} onChange={(e) => setNewLicense({ ...newLicense, minimum_royalty: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Upfront Fee</Label>
                  <Input type="number" value={newLicense.upfront_fee} onChange={(e) => setNewLicense({ ...newLicense, upfront_fee: e.target.value })} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Terms & Conditions</Label>
                <Textarea value={newLicense.terms} onChange={(e) => setNewLicense({ ...newLicense, terms: e.target.value })} rows={2} />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={createMutation.isPending}>{createMutation.isPending ? 'Creating...' : 'Create'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-blue-100 rounded-lg"><FileText className="h-5 w-5 text-blue-600" /></div><div><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-green-100 rounded-lg"><CheckCircle2 className="h-5 w-5 text-green-600" /></div><div><p className="text-2xl font-bold">{stats.active}</p><p className="text-xs text-muted-foreground">Active</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-blue-100 rounded-lg"><Clock className="h-5 w-5 text-blue-600" /></div><div><p className="text-2xl font-bold">{stats.pending}</p><p className="text-xs text-muted-foreground">Pending</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-yellow-100 rounded-lg"><AlertTriangle className="h-5 w-5 text-yellow-600" /></div><div><p className="text-2xl font-bold">{stats.expiring}</p><p className="text-xs text-muted-foreground">Expiring</p></div></div></CardContent></Card>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search by licensee or variety..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
            <SelectItem value="terminated">Terminated</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader><CardTitle>Agreement Registry</CardTitle><CardDescription>{filteredLicenses.length} agreements</CardDescription></CardHeader>
        <CardContent>
          {isLoading ? <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div> : filteredLicenses.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground"><FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No agreements found</p></div>
          ) : (
            <Table>
              <TableHeader><TableRow><TableHead>Variety</TableHead><TableHead>Licensee</TableHead><TableHead>Type</TableHead><TableHead>Territory</TableHead><TableHead>Period</TableHead><TableHead>Royalty</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
              <TableBody>
                {filteredLicenses.map((license) => (
                  <TableRow key={license.id}>
                    <TableCell className="font-medium">{license.variety_name || getVarietyName(license.variety_id)}</TableCell>
                    <TableCell><span className="flex items-center gap-1"><Building2 className="h-3 w-3 text-muted-foreground" />{license.licensee_name}</span></TableCell>
                    <TableCell><Badge className={licenseTypeColors[license.license_type] || 'bg-gray-100'}>{license.license_type.replace('_', ' ')}</Badge></TableCell>
                    <TableCell><span className="flex items-center gap-1 text-sm"><Globe className="h-3 w-3" />{license.territory?.join(', ') || 'Global'}</span></TableCell>
                    <TableCell><span className="flex items-center gap-1 text-sm"><Calendar className="h-3 w-3" />{license.start_date} - {license.end_date}</span></TableCell>
                    <TableCell><span className="flex items-center gap-1"><DollarSign className="h-3 w-3" />{license.royalty_rate_percent}%</span></TableCell>
                    <TableCell><Badge className={statusColors[license.status] || 'bg-gray-100'}><span className="flex items-center gap-1">{statusIcons[license.status]}{license.status}</span></Badge></TableCell>
                    <TableCell>
                      {(license.status === 'draft' || license.status === 'pending') && (
                        <Button size="sm" variant="outline" onClick={() => activateMutation.mutate(license.id)} disabled={activateMutation.isPending}>
                          <Play className="h-3 w-3 mr-1" />Activate
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

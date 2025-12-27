/**
 * Varieties Page - Registered varieties for licensing
 * 
 * Connects to /api/v2/licensing endpoints for variety protection management.
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
import { apiClient } from '@/lib/api-client';
import {
  Sprout, Plus, Search, Shield, Calendar, FileCheck,
  Clock, CheckCircle2, XCircle, AlertCircle, Building2, User, Tag,
} from 'lucide-react';

interface Variety {
  id: string;
  variety_name: string;
  crop: string;
  breeder_id: string;
  breeder_name: string;
  organization_id: string;
  organization_name: string;
  description: string;
  key_traits: string[];
  release_date?: string;
  status: string;
  created_at: string;
}

interface Protection {
  id: string;
  variety_id: string;
  protection_type: string;
  application_number: string;
  filing_date: string;
  territory: string[];
  authority: string;
  status: string;
  certificate_number?: string;
  grant_date?: string;
  expiry_date?: string;
}

interface ProtectionType {
  code: string;
  name: string;
  description: string;
  duration_years: number;
}

const statusColors: Record<string, string> = {
  registered: 'bg-blue-100 text-blue-800',
  pending: 'bg-yellow-100 text-yellow-800',
  filed: 'bg-indigo-100 text-indigo-800',
  granted: 'bg-green-100 text-green-800',
  expired: 'bg-gray-100 text-gray-800',
  rejected: 'bg-red-100 text-red-800',
};

const statusIcons: Record<string, React.ReactNode> = {
  registered: <Sprout className="h-3 w-3" />,
  pending: <Clock className="h-3 w-3" />,
  filed: <FileCheck className="h-3 w-3" />,
  granted: <CheckCircle2 className="h-3 w-3" />,
  expired: <AlertCircle className="h-3 w-3" />,
  rejected: <XCircle className="h-3 w-3" />,
};

const protectionTypeColors: Record<string, string> = {
  pvp: 'bg-purple-100 text-purple-800',
  pbr: 'bg-blue-100 text-blue-800',
  patent: 'bg-green-100 text-green-800',
  trademark: 'bg-orange-100 text-orange-800',
  trade_secret: 'bg-gray-100 text-gray-800',
};

export function Varieties() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isFileProtectionOpen, setIsFileProtectionOpen] = useState(false);
  const [selectedVariety, setSelectedVariety] = useState<Variety | null>(null);
  
  const [newVariety, setNewVariety] = useState({
    variety_name: '', crop: '', breeder_id: 'breeder-1', breeder_name: '',
    organization_id: 'org-1', organization_name: '', description: '',
    key_traits: '', release_date: '',
  });

  const [protectionForm, setProtectionForm] = useState({
    protection_type: '', application_number: '',
    filing_date: new Date().toISOString().split('T')[0],
    territory: 'India', authority: '',
  });

  const { data: varietiesResponse, isLoading } = useQuery({
    queryKey: ['licensing-varieties'],
    queryFn: () => apiClient.getLicensingVarieties(),
  });
  const varieties: Variety[] = varietiesResponse?.data || [];

  const { data: protectionsResponse } = useQuery({
    queryKey: ['protections'],
    queryFn: () => apiClient.getProtections(),
  });
  const protections: Protection[] = protectionsResponse?.data || [];

  const { data: protectionTypesResponse } = useQuery({
    queryKey: ['protection-types'],
    queryFn: () => apiClient.getProtectionTypes(),
  });
  const protectionTypes: ProtectionType[] = protectionTypesResponse?.data || [];

  const registerMutation = useMutation({
    mutationFn: async (data: typeof newVariety) => {
      return apiClient.registerVariety({
        ...data,
        key_traits: data.key_traits.split(',').map(t => t.trim()).filter(Boolean),
        release_date: data.release_date || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['licensing-varieties'] });
      toast.success('Variety registered successfully');
      setIsRegisterOpen(false);
      setNewVariety({
        variety_name: '', crop: '', breeder_id: 'breeder-1', breeder_name: '',
        organization_id: 'org-1', organization_name: '', description: '',
        key_traits: '', release_date: '',
      });
    },
    onError: () => toast.error('Failed to register variety'),
  });

  const fileProtectionMutation = useMutation({
    mutationFn: async () => {
      if (!selectedVariety) return;
      return apiClient.fileProtection({
        variety_id: selectedVariety.id,
        protection_type: protectionForm.protection_type,
        application_number: protectionForm.application_number,
        filing_date: protectionForm.filing_date,
        territory: protectionForm.territory.split(',').map(t => t.trim()),
        authority: protectionForm.authority,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['protections'] });
      queryClient.invalidateQueries({ queryKey: ['licensing-varieties'] });
      toast.success('Protection filed successfully');
      setIsFileProtectionOpen(false);
      setSelectedVariety(null);
    },
    onError: () => toast.error('Failed to file protection'),
  });

  const getVarietyProtection = (varietyId: string) => protections.find(p => p.variety_id === varietyId);

  const filteredVarieties = varieties.filter((v) => {
    const matchesSearch = v.variety_name.toLowerCase().includes(search.toLowerCase()) ||
      v.crop.toLowerCase().includes(search.toLowerCase()) ||
      v.breeder_name.toLowerCase().includes(search.toLowerCase());
    if (statusFilter === 'all') return matchesSearch;
    const protection = getVarietyProtection(v.id);
    if (statusFilter === 'protected') return matchesSearch && protection?.status === 'granted';
    if (statusFilter === 'filed') return matchesSearch && protection?.status === 'filed';
    if (statusFilter === 'unprotected') return matchesSearch && !protection;
    return matchesSearch;
  });

  const stats = {
    total: varieties.length,
    protected: protections.filter(p => p.status === 'granted').length,
    filed: protections.filter(p => p.status === 'filed').length,
    unprotected: varieties.length - protections.length,
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Sprout className="h-6 w-6" />Registered Varieties
          </h1>
          <p className="text-muted-foreground">Manage variety registrations and IP protection</p>
        </div>
        <Dialog open={isRegisterOpen} onOpenChange={setIsRegisterOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-2" />Register Variety</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Register New Variety</DialogTitle></DialogHeader>
            <form onSubmit={(e) => { e.preventDefault(); registerMutation.mutate(newVariety); }} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Variety Name *</Label>
                  <Input value={newVariety.variety_name} onChange={(e) => setNewVariety({ ...newVariety, variety_name: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label>Crop *</Label>
                  <Input value={newVariety.crop} onChange={(e) => setNewVariety({ ...newVariety, crop: e.target.value })} required />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Breeder Name *</Label>
                  <Input value={newVariety.breeder_name} onChange={(e) => setNewVariety({ ...newVariety, breeder_name: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label>Organization *</Label>
                  <Input value={newVariety.organization_name} onChange={(e) => setNewVariety({ ...newVariety, organization_name: e.target.value })} required />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Key Traits (comma-separated)</Label>
                <Input value={newVariety.key_traits} onChange={(e) => setNewVariety({ ...newVariety, key_traits: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Description *</Label>
                <Textarea value={newVariety.description} onChange={(e) => setNewVariety({ ...newVariety, description: e.target.value })} rows={3} required />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsRegisterOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={registerMutation.isPending}>{registerMutation.isPending ? 'Registering...' : 'Register'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-blue-100 rounded-lg"><Sprout className="h-5 w-5 text-blue-600" /></div><div><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-green-100 rounded-lg"><Shield className="h-5 w-5 text-green-600" /></div><div><p className="text-2xl font-bold">{stats.protected}</p><p className="text-xs text-muted-foreground">Protected</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-indigo-100 rounded-lg"><FileCheck className="h-5 w-5 text-indigo-600" /></div><div><p className="text-2xl font-bold">{stats.filed}</p><p className="text-xs text-muted-foreground">Filed</p></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-yellow-100 rounded-lg"><Clock className="h-5 w-5 text-yellow-600" /></div><div><p className="text-2xl font-bold">{stats.unprotected}</p><p className="text-xs text-muted-foreground">Unprotected</p></div></div></CardContent></Card>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search varieties..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Filter" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="protected">Protected</SelectItem>
            <SelectItem value="filed">Filed</SelectItem>
            <SelectItem value="unprotected">Unprotected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader><CardTitle>Variety Registry</CardTitle><CardDescription>{filteredVarieties.length} varieties</CardDescription></CardHeader>
        <CardContent>
          {isLoading ? <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div> : filteredVarieties.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground"><Sprout className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No varieties found</p></div>
          ) : (
            <Table>
              <TableHeader><TableRow><TableHead>Variety</TableHead><TableHead>Crop</TableHead><TableHead>Breeder</TableHead><TableHead>Organization</TableHead><TableHead>Protection</TableHead><TableHead>Traits</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
              <TableBody>
                {filteredVarieties.map((variety) => {
                  const protection = getVarietyProtection(variety.id);
                  return (
                    <TableRow key={variety.id}>
                      <TableCell className="font-medium">{variety.variety_name}</TableCell>
                      <TableCell><Badge variant="outline">{variety.crop}</Badge></TableCell>
                      <TableCell><span className="flex items-center gap-1"><User className="h-3 w-3 text-muted-foreground" />{variety.breeder_name}</span></TableCell>
                      <TableCell><span className="flex items-center gap-1"><Building2 className="h-3 w-3 text-muted-foreground" />{variety.organization_name}</span></TableCell>
                      <TableCell>
                        {protection ? (
                          <div className="space-y-1">
                            <Badge className={protectionTypeColors[protection.protection_type] || 'bg-gray-100'}>{protection.protection_type.toUpperCase()}</Badge>
                            <Badge className={statusColors[protection.status] || 'bg-gray-100'}><span className="flex items-center gap-1">{statusIcons[protection.status]}{protection.status}</span></Badge>
                          </div>
                        ) : <span className="text-muted-foreground text-sm">None</span>}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-[200px]">
                          {variety.key_traits?.slice(0, 2).map((trait, i) => <Badge key={i} variant="secondary" className="text-xs"><Tag className="h-2 w-2 mr-1" />{trait}</Badge>)}
                          {variety.key_traits?.length > 2 && <Badge variant="secondary" className="text-xs">+{variety.key_traits.length - 2}</Badge>}
                        </div>
                      </TableCell>
                      <TableCell>
                        {!protection && <Button size="sm" variant="outline" onClick={() => { setSelectedVariety(variety); setIsFileProtectionOpen(true); }}><Shield className="h-3 w-3 mr-1" />File</Button>}
                        {protection?.status === 'filed' && <span className="text-xs text-muted-foreground flex items-center gap-1"><Calendar className="h-3 w-3" />Filed {protection.filing_date}</span>}
                        {protection?.status === 'granted' && <span className="text-xs text-green-600 flex items-center gap-1"><CheckCircle2 className="h-3 w-3" />Until {protection.expiry_date}</span>}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={isFileProtectionOpen} onOpenChange={setIsFileProtectionOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>File Protection for {selectedVariety?.variety_name}</DialogTitle></DialogHeader>
          <form onSubmit={(e) => { e.preventDefault(); fileProtectionMutation.mutate(); }} className="space-y-4">
            <div className="space-y-2">
              <Label>Protection Type *</Label>
              <Select value={protectionForm.protection_type} onValueChange={(v) => setProtectionForm({ ...protectionForm, protection_type: v })}>
                <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                <SelectContent>{protectionTypes.map((pt) => <SelectItem key={pt.code} value={pt.code}>{pt.name} ({pt.duration_years}y)</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Application # *</Label><Input value={protectionForm.application_number} onChange={(e) => setProtectionForm({ ...protectionForm, application_number: e.target.value })} required /></div>
              <div className="space-y-2"><Label>Filing Date *</Label><Input type="date" value={protectionForm.filing_date} onChange={(e) => setProtectionForm({ ...protectionForm, filing_date: e.target.value })} required /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Territory</Label><Input value={protectionForm.territory} onChange={(e) => setProtectionForm({ ...protectionForm, territory: e.target.value })} /></div>
              <div className="space-y-2"><Label>Authority *</Label><Input value={protectionForm.authority} onChange={(e) => setProtectionForm({ ...protectionForm, authority: e.target.value })} required /></div>
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsFileProtectionOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={fileProtectionMutation.isPending}>{fileProtectionMutation.isPending ? 'Filing...' : 'File'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default Varieties;

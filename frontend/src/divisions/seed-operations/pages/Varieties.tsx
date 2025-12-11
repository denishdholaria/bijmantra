/**
 * Varieties Page - Registered varieties for licensing
 * 
 * Connects to /api/v2/licensing endpoints for variety protection management.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
  Sprout,
  Plus,
  Search,
  Shield,
  Calendar,
  FileCheck,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Variety {
  id: string;
  name: string;
  crop: string;
  breeder: string;
  description?: string;
  protection_type?: string;
  protection_status: string;
  filing_date?: string;
  grant_date?: string;
  expiry_date?: string;
  registration_number?: string;
  created_at: string;
}

interface ProtectionType {
  code: string;
  name: string;
  description: string;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  filed: 'bg-blue-100 text-blue-800',
  granted: 'bg-green-100 text-green-800',
  expired: 'bg-gray-100 text-gray-800',
  rejected: 'bg-red-100 text-red-800',
};

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Clock className="h-3 w-3" />,
  filed: <FileCheck className="h-3 w-3" />,
  granted: <CheckCircle2 className="h-3 w-3" />,
  expired: <AlertCircle className="h-3 w-3" />,
  rejected: <XCircle className="h-3 w-3" />,
};

export function Varieties() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newVariety, setNewVariety] = useState({
    name: '',
    crop: '',
    breeder: '',
    description: '',
    protection_type: '',
  });

  // Fetch varieties
  const { data: varieties = [], isLoading } = useQuery<Variety[]>({
    queryKey: ['varieties'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/varieties`);
      if (!res.ok) throw new Error('Failed to fetch varieties');
      return res.json();
    },
  });

  // Fetch protection types
  const { data: protectionTypes = [] } = useQuery<ProtectionType[]>({
    queryKey: ['protection-types'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/protection-types`);
      if (!res.ok) throw new Error('Failed to fetch protection types');
      return res.json();
    },
  });

  // Register variety mutation
  const registerMutation = useMutation({
    mutationFn: async (data: typeof newVariety) => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/varieties`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to register variety');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['varieties'] });
      toast.success('Variety registered successfully');
      setIsDialogOpen(false);
      setNewVariety({ name: '', crop: '', breeder: '', description: '', protection_type: '' });
    },
    onError: () => {
      toast.error('Failed to register variety');
    },
  });

  // File protection mutation
  const fileMutation = useMutation({
    mutationFn: async (varietyId: string) => {
      const res = await fetch(`${API_BASE}/api/v2/licensing/varieties/${varietyId}/file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filing_date: new Date().toISOString().split('T')[0] }),
      });
      if (!res.ok) throw new Error('Failed to file protection');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['varieties'] });
      toast.success('Protection filed successfully');
    },
    onError: () => {
      toast.error('Failed to file protection');
    },
  });

  // Filter varieties
  const filteredVarieties = varieties.filter((v) => {
    const matchesSearch =
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.crop.toLowerCase().includes(search.toLowerCase()) ||
      v.breeder.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || v.protection_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Stats
  const stats = {
    total: varieties.length,
    granted: varieties.filter((v) => v.protection_status === 'granted').length,
    pending: varieties.filter((v) => v.protection_status === 'pending').length,
    filed: varieties.filter((v) => v.protection_status === 'filed').length,
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    registerMutation.mutate(newVariety);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Sprout className="h-6 w-6" />
            Registered Varieties
          </h1>
          <p className="text-muted-foreground">
            Manage variety registrations and intellectual property protection
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Register Variety
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Register New Variety</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Variety Name *</Label>
                <Input
                  value={newVariety.name}
                  onChange={(e) => setNewVariety({ ...newVariety, name: e.target.value })}
                  placeholder="e.g., Golden Rice 2024"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Crop *</Label>
                  <Input
                    value={newVariety.crop}
                    onChange={(e) => setNewVariety({ ...newVariety, crop: e.target.value })}
                    placeholder="e.g., Rice"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Breeder *</Label>
                  <Input
                    value={newVariety.breeder}
                    onChange={(e) => setNewVariety({ ...newVariety, breeder: e.target.value })}
                    placeholder="e.g., IRRI"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Protection Type</Label>
                <Select
                  value={newVariety.protection_type}
                  onValueChange={(v) => setNewVariety({ ...newVariety, protection_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select protection type" />
                  </SelectTrigger>
                  <SelectContent>
                    {protectionTypes.map((pt) => (
                      <SelectItem key={pt.code} value={pt.code}>
                        {pt.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={newVariety.description}
                  onChange={(e) => setNewVariety({ ...newVariety, description: e.target.value })}
                  placeholder="Key characteristics and traits..."
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={registerMutation.isPending}>
                  {registerMutation.isPending ? 'Registering...' : 'Register'}
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
                <Sprout className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-muted-foreground">Total Varieties</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Shield className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.granted}</p>
                <p className="text-xs text-muted-foreground">Protected</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileCheck className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.filed}</p>
                <p className="text-xs text-muted-foreground">Filed</p>
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
                <p className="text-2xl font-bold">{stats.pending}</p>
                <p className="text-xs text-muted-foreground">Pending</p>
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
            placeholder="Search varieties..."
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
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="filed">Filed</SelectItem>
            <SelectItem value="granted">Granted</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Variety Registry</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : filteredVarieties.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Sprout className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No varieties found</p>
              <p className="text-sm">Register your first variety to get started</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Variety</TableHead>
                  <TableHead>Crop</TableHead>
                  <TableHead>Breeder</TableHead>
                  <TableHead>Protection</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Filing Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredVarieties.map((variety) => (
                  <TableRow key={variety.id}>
                    <TableCell className="font-medium">{variety.name}</TableCell>
                    <TableCell>{variety.crop}</TableCell>
                    <TableCell>{variety.breeder}</TableCell>
                    <TableCell>
                      {variety.protection_type ? (
                        <Badge variant="outline">{variety.protection_type}</Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[variety.protection_status] || 'bg-gray-100'}>
                        <span className="flex items-center gap-1">
                          {statusIcons[variety.protection_status]}
                          {variety.protection_status}
                        </span>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {variety.filing_date ? (
                        <span className="flex items-center gap-1 text-sm">
                          <Calendar className="h-3 w-3" />
                          {variety.filing_date}
                        </span>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {variety.protection_status === 'pending' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => fileMutation.mutate(variety.id)}
                          disabled={fileMutation.isPending}
                        >
                          <FileCheck className="h-3 w-3 mr-1" />
                          File
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

export default Varieties;

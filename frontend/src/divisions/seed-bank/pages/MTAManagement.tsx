/**
 * Material Transfer Agreement (MTA) Management Page
 * 
 * Manage MTAs for germplasm exchange under ITPGRFA and institutional agreements.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import {
  FileText, Plus, Search, Building2, Globe, Calendar, CheckCircle2,
  Clock, XCircle, AlertTriangle, FileSignature, Shield, Users,
} from 'lucide-react';

const API_BASE = '/api/v2/mta';

interface MTA {
  id: string;
  mta_number: string;
  type: string;
  status: string;
  provider: { institution: string; country: string; contact: string; email: string };
  recipient: { institution: string; country: string; contact: string; email: string };
  accessions: string[];
  accession_count: number;
  crops: string[];
  purpose: string;
  benefit_sharing: { type: string; details: string; royalty_rate?: number };
  created_date: string;
  signed_date?: string;
  effective_date?: string;
  expiry_date?: string;
  exchange_id?: string;
}

interface MTATemplate {
  id: string;
  name: string;
  type: string;
  description: string;
  clause_count: number;
  benefit_sharing: string;
  duration_years: number | null;
  requires_approval: boolean;
}


export function MTAManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedMTA, setSelectedMTA] = useState<MTA | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch MTAs
  const { data: mtasData, isLoading } = useQuery({
    queryKey: ['mtas', typeFilter, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (typeFilter !== 'all') params.append('mta_type', typeFilter);
      if (statusFilter !== 'all') params.append('status', statusFilter);
      const res = await fetch(`${API_BASE}?${params}`);
      return res.json();
    },
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['mta-stats'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/statistics`);
      return res.json();
    },
  });

  // Fetch templates
  const { data: templatesData } = useQuery({
    queryKey: ['mta-templates'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/templates`);
      return res.json();
    },
  });

  const mtas: MTA[] = mtasData?.mtas || [];
  const templates: MTATemplate[] = templatesData?.templates || [];

  const filteredMTAs = mtas.filter(mta =>
    mta.mta_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    mta.provider.institution.toLowerCase().includes(searchTerm.toLowerCase()) ||
    mta.recipient.institution.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode }> = {
      draft: { color: 'bg-gray-100 text-gray-800', icon: <FileText className="w-3 h-3" /> },
      pending_review: { color: 'bg-yellow-100 text-yellow-800', icon: <Clock className="w-3 h-3" /> },
      pending_signature: { color: 'bg-blue-100 text-blue-800', icon: <FileSignature className="w-3 h-3" /> },
      active: { color: 'bg-green-100 text-green-800', icon: <CheckCircle2 className="w-3 h-3" /> },
      expired: { color: 'bg-orange-100 text-orange-800', icon: <AlertTriangle className="w-3 h-3" /> },
      terminated: { color: 'bg-red-100 text-red-800', icon: <XCircle className="w-3 h-3" /> },
      rejected: { color: 'bg-red-100 text-red-800', icon: <XCircle className="w-3 h-3" /> },
    };
    const c = config[status] || config.draft;
    return (
      <Badge className={`${c.color} flex items-center gap-1`}>
        {c.icon}
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const getTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      smta: 'bg-emerald-100 text-emerald-800',
      institutional: 'bg-blue-100 text-blue-800',
      research: 'bg-purple-100 text-purple-800',
      commercial: 'bg-amber-100 text-amber-800',
    };
    return <Badge className={colors[type] || 'bg-gray-100'}>{type.toUpperCase()}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-8 h-8 text-green-600" />
            Material Transfer Agreements
          </h1>
          <p className="text-gray-600 mt-1">Manage MTAs for germplasm exchange compliance</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="w-4 h-4" /> New MTA
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <CreateMTADialog
              templates={templates}
              onClose={() => setShowCreateDialog(false)}
              onSuccess={() => {
                queryClient.invalidateQueries({ queryKey: ['mtas'] });
                queryClient.invalidateQueries({ queryKey: ['mta-stats'] });
                setShowCreateDialog(false);
                toast({ title: 'MTA Created', description: 'Material Transfer Agreement created successfully' });
              }}
            />
          </DialogContent>
        </Dialog>
      </div>


      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.total || 0}</p>
                <p className="text-sm text-gray-500">Total MTAs</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.active || 0}</p>
                <p className="text-sm text-gray-500">Active</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.pending || 0}</p>
                <p className="text-sm text-gray-500">Pending</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.institutions || 0}</p>
                <p className="text-sm text-gray-500">Institutions</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search by MTA number or institution..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="smta">SMTA</SelectItem>
            <SelectItem value="institutional">Institutional</SelectItem>
            <SelectItem value="research">Research</SelectItem>
            <SelectItem value="commercial">Commercial</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="pending_review">Pending Review</SelectItem>
            <SelectItem value="pending_signature">Pending Signature</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
            <SelectItem value="terminated">Terminated</SelectItem>
          </SelectContent>
        </Select>
      </div>


      {/* MTA List */}
      <Card>
        <CardHeader>
          <CardTitle>Agreements</CardTitle>
          <CardDescription>
            {filteredMTAs.length} agreement{filteredMTAs.length !== 1 ? 's' : ''} found
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : filteredMTAs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No MTAs found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">MTA #</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recipient</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Accessions</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Effective</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredMTAs.map((mta) => (
                    <tr key={mta.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <span className="font-medium text-green-600">{mta.mta_number}</span>
                      </td>
                      <td className="px-4 py-3">{getTypeBadge(mta.type)}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="font-medium text-sm">{mta.provider.institution}</p>
                            <p className="text-xs text-gray-500">{mta.provider.country}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Globe className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="font-medium text-sm">{mta.recipient.institution}</p>
                            <p className="text-xs text-gray-500">{mta.recipient.country}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge variant="outline">{mta.accession_count}</Badge>
                      </td>
                      <td className="px-4 py-3 text-center">{getStatusBadge(mta.status)}</td>
                      <td className="px-4 py-3">
                        {mta.effective_date ? (
                          <div className="flex items-center gap-1 text-sm">
                            <Calendar className="w-3 h-3 text-gray-400" />
                            {new Date(mta.effective_date).toLocaleDateString()}
                          </div>
                        ) : (
                          <span className="text-gray-400 text-sm">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedMTA(mta)}
                        >
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* MTA Detail Dialog */}
      {selectedMTA && (
        <Dialog open={!!selectedMTA} onOpenChange={() => setSelectedMTA(null)}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <MTADetailView
              mta={selectedMTA}
              onClose={() => setSelectedMTA(null)}
              onUpdate={() => {
                queryClient.invalidateQueries({ queryKey: ['mtas'] });
                queryClient.invalidateQueries({ queryKey: ['mta-stats'] });
              }}
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}


// Create MTA Dialog Component
function CreateMTADialog({
  templates,
  onClose,
  onSuccess,
}: {
  templates: MTATemplate[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    mta_type: 'smta',
    provider: { institution: 'Bijmantra Seed Bank', country: 'India', contact: '', email: '' },
    recipient: { institution: '', country: '', contact: '', email: '' },
    accessions: '',
    crops: '',
    purpose: '',
    benefit_sharing: { type: 'none', details: '', royalty_rate: 0 },
  });

  const selectedTemplate = templates.find(t => t.type === formData.mta_type);

  const handleSubmit = async () => {
    try {
      const payload = {
        ...formData,
        accessions: formData.accessions.split(',').map(a => a.trim()).filter(Boolean),
        crops: formData.crops.split(',').map(c => c.trim()).filter(Boolean),
      };
      const res = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to create MTA');
      onSuccess();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Create Material Transfer Agreement</DialogTitle>
        <DialogDescription>Step {step} of 3</DialogDescription>
      </DialogHeader>

      {step === 1 && (
        <div className="space-y-4 py-4">
          <div>
            <Label>MTA Type</Label>
            <Select value={formData.mta_type} onValueChange={(v) => setFormData({ ...formData, mta_type: v })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {templates.map(t => (
                  <SelectItem key={t.id} value={t.type}>
                    <div className="flex flex-col">
                      <span>{t.name}</span>
                      <span className="text-xs text-gray-500">{t.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {selectedTemplate && (
            <Card className="bg-gray-50">
              <CardContent className="pt-4 text-sm">
                <p><strong>Clauses:</strong> {selectedTemplate.clause_count}</p>
                <p><strong>Duration:</strong> {selectedTemplate.duration_years ? `${selectedTemplate.duration_years} years` : 'Perpetual'}</p>
                <p><strong>Benefit Sharing:</strong> {selectedTemplate.benefit_sharing}</p>
                <p><strong>Approval Required:</strong> {selectedTemplate.requires_approval ? 'Yes' : 'No (Auto-approved)'}</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-3">
              <h4 className="font-medium flex items-center gap-2"><Building2 className="w-4 h-4" /> Provider</h4>
              <Input placeholder="Institution" value={formData.provider.institution}
                onChange={(e) => setFormData({ ...formData, provider: { ...formData.provider, institution: e.target.value } })} />
              <Input placeholder="Country" value={formData.provider.country}
                onChange={(e) => setFormData({ ...formData, provider: { ...formData.provider, country: e.target.value } })} />
              <Input placeholder="Contact Person" value={formData.provider.contact}
                onChange={(e) => setFormData({ ...formData, provider: { ...formData.provider, contact: e.target.value } })} />
              <Input placeholder="Email" type="email" value={formData.provider.email}
                onChange={(e) => setFormData({ ...formData, provider: { ...formData.provider, email: e.target.value } })} />
            </div>
            <div className="space-y-3">
              <h4 className="font-medium flex items-center gap-2"><Globe className="w-4 h-4" /> Recipient</h4>
              <Input placeholder="Institution" value={formData.recipient.institution}
                onChange={(e) => setFormData({ ...formData, recipient: { ...formData.recipient, institution: e.target.value } })} />
              <Input placeholder="Country" value={formData.recipient.country}
                onChange={(e) => setFormData({ ...formData, recipient: { ...formData.recipient, country: e.target.value } })} />
              <Input placeholder="Contact Person" value={formData.recipient.contact}
                onChange={(e) => setFormData({ ...formData, recipient: { ...formData.recipient, contact: e.target.value } })} />
              <Input placeholder="Email" type="email" value={formData.recipient.email}
                onChange={(e) => setFormData({ ...formData, recipient: { ...formData.recipient, email: e.target.value } })} />
            </div>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4 py-4">
          <div>
            <Label>Accession Numbers (comma-separated)</Label>
            <Input placeholder="ACC-001, ACC-002, ACC-003" value={formData.accessions}
              onChange={(e) => setFormData({ ...formData, accessions: e.target.value })} />
          </div>
          <div>
            <Label>Crops (comma-separated)</Label>
            <Input placeholder="Rice, Wheat, Maize" value={formData.crops}
              onChange={(e) => setFormData({ ...formData, crops: e.target.value })} />
          </div>
          <div>
            <Label>Purpose</Label>
            <Textarea placeholder="Describe the purpose of this material transfer..."
              value={formData.purpose}
              onChange={(e) => setFormData({ ...formData, purpose: e.target.value })} />
          </div>
          {formData.mta_type === 'commercial' && (
            <div>
              <Label>Royalty Rate (%)</Label>
              <Input type="number" placeholder="3.0" value={formData.benefit_sharing.royalty_rate}
                onChange={(e) => setFormData({
                  ...formData,
                  benefit_sharing: { ...formData.benefit_sharing, royalty_rate: parseFloat(e.target.value) }
                })} />
            </div>
          )}
        </div>
      )}

      <DialogFooter>
        {step > 1 && <Button variant="outline" onClick={() => setStep(step - 1)}>Back</Button>}
        {step < 3 ? (
          <Button onClick={() => setStep(step + 1)}>Next</Button>
        ) : (
          <Button onClick={handleSubmit}>Create MTA</Button>
        )}
      </DialogFooter>
    </>
  );
}


// MTA Detail View Component
function MTADetailView({
  mta,
  onClose,
  onUpdate,
}: {
  mta: MTA;
  onClose: () => void;
  onUpdate: () => void;
}) {
  const { toast } = useToast();
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const performAction = async (action: string, body?: object) => {
    setActionLoading(action);
    try {
      const res = await fetch(`${API_BASE}/${mta.id}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Action failed');
      }
      toast({ title: 'Success', description: `MTA ${action} completed` });
      onUpdate();
      onClose();
    } catch (error: any) {
      toast({ title: 'Error', description: error.message, variant: 'destructive' });
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode }> = {
      draft: { color: 'bg-gray-100 text-gray-800', icon: <FileText className="w-4 h-4" /> },
      pending_review: { color: 'bg-yellow-100 text-yellow-800', icon: <Clock className="w-4 h-4" /> },
      pending_signature: { color: 'bg-blue-100 text-blue-800', icon: <FileSignature className="w-4 h-4" /> },
      active: { color: 'bg-green-100 text-green-800', icon: <CheckCircle2 className="w-4 h-4" /> },
      expired: { color: 'bg-orange-100 text-orange-800', icon: <AlertTriangle className="w-4 h-4" /> },
      terminated: { color: 'bg-red-100 text-red-800', icon: <XCircle className="w-4 h-4" /> },
      rejected: { color: 'bg-red-100 text-red-800', icon: <XCircle className="w-4 h-4" /> },
    };
    const c = config[status] || config.draft;
    return (
      <Badge className={`${c.color} flex items-center gap-2 text-base px-3 py-1`}>
        {c.icon}
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  return (
    <>
      <DialogHeader>
        <div className="flex items-center justify-between">
          <DialogTitle className="text-xl">{mta.mta_number}</DialogTitle>
          {getStatusBadge(mta.status)}
        </div>
        <DialogDescription>{mta.purpose}</DialogDescription>
      </DialogHeader>

      <Tabs defaultValue="details" className="mt-4">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="parties">Parties</TabsTrigger>
          <TabsTrigger value="material">Material</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="space-y-4 mt-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-gray-500">Type</Label>
              <p className="font-medium">{mta.type.toUpperCase()}</p>
            </div>
            <div>
              <Label className="text-gray-500">Created</Label>
              <p className="font-medium">{new Date(mta.created_date).toLocaleDateString()}</p>
            </div>
            <div>
              <Label className="text-gray-500">Effective Date</Label>
              <p className="font-medium">{mta.effective_date ? new Date(mta.effective_date).toLocaleDateString() : '—'}</p>
            </div>
            <div>
              <Label className="text-gray-500">Expiry Date</Label>
              <p className="font-medium">{mta.expiry_date ? new Date(mta.expiry_date).toLocaleDateString() : 'Perpetual'}</p>
            </div>
          </div>
          <div>
            <Label className="text-gray-500">Benefit Sharing</Label>
            <p className="font-medium">{mta.benefit_sharing.type.replace('_', ' ')}</p>
            {mta.benefit_sharing.details && <p className="text-sm text-gray-600">{mta.benefit_sharing.details}</p>}
            {mta.benefit_sharing.royalty_rate && <p className="text-sm text-green-600">Royalty: {mta.benefit_sharing.royalty_rate}%</p>}
          </div>
        </TabsContent>

        <TabsContent value="parties" className="space-y-4 mt-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Building2 className="w-4 h-4" /> Provider
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-medium">{mta.provider.institution}</p>
              <p className="text-sm text-gray-600">{mta.provider.country}</p>
              <p className="text-sm">{mta.provider.contact}</p>
              <p className="text-sm text-blue-600">{mta.provider.email}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Globe className="w-4 h-4" /> Recipient
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-medium">{mta.recipient.institution}</p>
              <p className="text-sm text-gray-600">{mta.recipient.country}</p>
              <p className="text-sm">{mta.recipient.contact}</p>
              <p className="text-sm text-blue-600">{mta.recipient.email}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="material" className="space-y-4 mt-4">
          <div>
            <Label className="text-gray-500">Accessions ({mta.accession_count})</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {mta.accessions.map((acc, i) => (
                <Badge key={i} variant="outline">{acc}</Badge>
              ))}
            </div>
          </div>
          <div>
            <Label className="text-gray-500">Crops</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {[...new Set(mta.crops)].map((crop, i) => (
                <Badge key={i} className="bg-green-100 text-green-800">{crop}</Badge>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="compliance" className="mt-4">
          <ComplianceCheck mtaId={mta.id} />
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex gap-2 mt-6 pt-4 border-t">
        {mta.status === 'draft' && (
          <Button onClick={() => performAction('submit')} disabled={!!actionLoading}>
            {actionLoading === 'submit' ? 'Submitting...' : 'Submit for Review'}
          </Button>
        )}
        {mta.status === 'pending_review' && (
          <>
            <Button onClick={() => performAction('approve', { approver: 'Current User' })} disabled={!!actionLoading}>
              {actionLoading === 'approve' ? 'Approving...' : 'Approve'}
            </Button>
            <Button variant="destructive" onClick={() => performAction('reject', { reason: 'Rejected', rejector: 'Current User' })} disabled={!!actionLoading}>
              Reject
            </Button>
          </>
        )}
        {mta.status === 'pending_signature' && (
          <Button onClick={() => performAction('sign', { signatory: 'Current User' })} disabled={!!actionLoading}>
            {actionLoading === 'sign' ? 'Signing...' : 'Sign & Activate'}
          </Button>
        )}
        {mta.status === 'active' && (
          <Button variant="destructive" onClick={() => performAction('terminate', { reason: 'Terminated by user', terminator: 'Current User' })} disabled={!!actionLoading}>
            Terminate
          </Button>
        )}
      </div>
    </>
  );
}


// Compliance Check Component
function ComplianceCheck({ mtaId }: { mtaId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['mta-compliance', mtaId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/${mtaId}/compliance`);
      return res.json();
    },
  });

  if (isLoading) return <div className="text-center py-4">Checking compliance...</div>;

  return (
    <div className="space-y-4">
      <div className={`p-4 rounded-lg ${data?.compliant ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
        <div className="flex items-center gap-2">
          {data?.compliant ? (
            <>
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span className="font-medium text-green-800">Compliant</span>
            </>
          ) : (
            <>
              <XCircle className="w-5 h-5 text-red-600" />
              <span className="font-medium text-red-800">Non-Compliant</span>
            </>
          )}
        </div>
      </div>

      {data?.issues?.length > 0 && (
        <div>
          <Label className="text-red-600">Issues</Label>
          <ul className="list-disc list-inside text-sm text-red-700 mt-1">
            {data.issues.map((issue: string, i: number) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
        </div>
      )}

      {data?.warnings?.length > 0 && (
        <div>
          <Label className="text-yellow-600">Warnings</Label>
          <ul className="list-disc list-inside text-sm text-yellow-700 mt-1">
            {data.warnings.map((warning: string, i: number) => (
              <li key={i}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-gray-500">
        Last checked: {data?.checked_at ? new Date(data.checked_at).toLocaleString() : '—'}
      </p>
    </div>
  );
}

export default MTAManagement;

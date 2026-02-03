/**
 * Firms Page - Dealer/Customer management
 * Connected to /api/v2/dispatch/firms endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Building2, Plus, Search, RefreshCw, Phone, Mail, 
  MapPin, User, AlertCircle 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface Firm {
  firm_id: string;
  firm_code: string;
  name: string;
  firm_type: string;
  address: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  contact_person: string;
  phone: string;
  email: string;
  gst_number?: string;
  credit_limit: number;
  credit_used: number;
  status: string;
}

interface FirmType {
  id: string;
  name: string;
  description: string;
}

export function Firms() {
  const [firms, setFirms] = useState<Firm[]>([]);
  const [firmTypes, setFirmTypes] = useState<FirmType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('');
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newFirm, setNewFirm] = useState({
    name: '',
    firm_type: 'dealer',
    address: '',
    city: '',
    state: '',
    country: 'India',
    postal_code: '',
    contact_person: '',
    phone: '',
    email: '',
    gst_number: '',
    credit_limit: 100000,
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [firmsRes, typesRes] = await Promise.all([
        apiClient.dispatchService.getFirms(filterType || undefined),
        apiClient.dispatchService.getFirmTypes(),
      ]);
      setFirms(firmsRes.data || []);
      setFirmTypes(typesRes.data || []);
    } catch (err: any) {
      setError('Backend unavailable - no data to display');
      setFirms([]);
      setFirmTypes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filterType]);

  const handleCreateFirm = async () => {
    try {
      await apiClient.dispatchService.createFirm(newFirm);
      setShowNewDialog(false);
      setNewFirm({
        name: '', firm_type: 'dealer', address: '', city: '', state: '', country: 'India',
        postal_code: '', contact_person: '', phone: '', email: '', gst_number: '', credit_limit: 100000,
      });
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to create firm');
    }
  };

  const filteredFirms = firms.filter(f =>
    f.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.firm_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.contact_person.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      dealer: 'bg-blue-100 text-blue-700',
      distributor: 'bg-purple-100 text-purple-700',
      retailer: 'bg-green-100 text-green-700',
      farmer: 'bg-yellow-100 text-yellow-700',
      institution: 'bg-orange-100 text-orange-700',
      government: 'bg-red-100 text-red-700',
    };
    return <Badge className={colors[type] || 'bg-gray-100 text-gray-700'}>{type}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-blue-600" />
            Firms & Dealers
          </h1>
          <p className="text-gray-500 text-sm">Manage customers, dealers, and distributors</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />Add Firm</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Add New Firm</DialogTitle>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-4 py-4 max-h-96 overflow-y-auto">
                <div className="col-span-2 space-y-2">
                  <Label>Firm Name *</Label>
                  <Input value={newFirm.name} onChange={(e) => setNewFirm({...newFirm, name: e.target.value})} placeholder="Company name" />
                </div>
                <div className="space-y-2">
                  <Label>Type *</Label>
                  <Select value={newFirm.firm_type} onValueChange={(v) => setNewFirm({...newFirm, firm_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {firmTypes.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Credit Limit</Label>
                  <Input type="number" value={newFirm.credit_limit} onChange={(e) => setNewFirm({...newFirm, credit_limit: Number(e.target.value)})} />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label>Address *</Label>
                  <Input value={newFirm.address} onChange={(e) => setNewFirm({...newFirm, address: e.target.value})} placeholder="Street address" />
                </div>
                <div className="space-y-2">
                  <Label>City *</Label>
                  <Input value={newFirm.city} onChange={(e) => setNewFirm({...newFirm, city: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>State *</Label>
                  <Input value={newFirm.state} onChange={(e) => setNewFirm({...newFirm, state: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Postal Code *</Label>
                  <Input value={newFirm.postal_code} onChange={(e) => setNewFirm({...newFirm, postal_code: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>GST Number</Label>
                  <Input value={newFirm.gst_number} onChange={(e) => setNewFirm({...newFirm, gst_number: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Contact Person *</Label>
                  <Input value={newFirm.contact_person} onChange={(e) => setNewFirm({...newFirm, contact_person: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Phone *</Label>
                  <Input value={newFirm.phone} onChange={(e) => setNewFirm({...newFirm, phone: e.target.value})} />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label>Email *</Label>
                  <Input type="email" value={newFirm.email} onChange={(e) => setNewFirm({...newFirm, email: e.target.value})} />
                </div>
                <div className="col-span-2">
                  <Button onClick={handleCreateFirm} className="w-full">Create Firm</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {error && (
        <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-300 text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Retry
          </Button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{firms.length}</p>
            <p className="text-sm text-gray-500">Total Firms</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{firms.filter(f => f.firm_type === 'dealer').length}</p>
            <p className="text-sm text-gray-500">Dealers</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{firms.filter(f => f.firm_type === 'distributor').length}</p>
            <p className="text-sm text-gray-500">Distributors</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{firms.filter(f => f.status === 'active').length}</p>
            <p className="text-sm text-gray-500">Active</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search firms..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={filterType || "all"} onValueChange={(v) => setFilterType(v === "all" ? "" : v)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {firmTypes.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {/* Firms List */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <Card className="col-span-full">
            <CardContent className="py-12 text-center text-gray-500">Loading firms...</CardContent>
          </Card>
        ) : filteredFirms.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="py-12 text-center text-gray-500">
              <Building2 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No firms found</p>
            </CardContent>
          </Card>
        ) : (
          filteredFirms.map((firm) => (
            <Card key={firm.firm_id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{firm.name}</CardTitle>
                    <p className="text-sm text-gray-500">{firm.firm_code}</p>
                  </div>
                  {getTypeBadge(firm.firm_type)}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start gap-2 text-sm">
                  <User className="h-4 w-4 text-gray-400 mt-0.5" />
                  <span>{firm.contact_person}</span>
                </div>
                <div className="flex items-start gap-2 text-sm">
                  <MapPin className="h-4 w-4 text-gray-400 mt-0.5" />
                  <span>{firm.city}, {firm.state}</span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-1">
                    <Phone className="h-3 w-3 text-gray-400" />
                    {firm.phone}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-sm">
                  <Mail className="h-3 w-3 text-gray-400" />
                  <span className="truncate">{firm.email}</span>
                </div>
                <div className="pt-2 border-t">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Credit Used</span>
                    <span className="font-medium">₹{(firm.credit_used / 1000).toFixed(0)}K / ₹{(firm.credit_limit / 1000).toFixed(0)}K</span>
                  </div>
                  <div className="mt-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${firm.credit_used / firm.credit_limit > 0.8 ? 'bg-red-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min((firm.credit_used / firm.credit_limit) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

export default Firms;

/**
 * Barcode Management Page
 * 
 * Generate, scan, and manage barcodes for seed lots, accessions, samples, etc.
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
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { BarcodeScanner } from '@/components/BarcodeScanner';
import {
  QrCode, Plus, Printer, Search, Package, Leaf, TestTube, Warehouse,
  Truck, FileText, BarChart3, Camera, History, CheckCircle2, XCircle,
} from 'lucide-react';

const API_BASE = '/api/v2/barcode';

interface Barcode {
  id: string;
  barcode_value: string;
  format: string;
  entity_type: string;
  entity_id: string;
  entity_name: string;
  data: Record<string, unknown>;
  created_at: string;
  scan_count: number;
  last_scanned: string | null;
  active: boolean;
}

interface EntityType {
  value: string;
  name: string;
  prefix: string;
}


export function BarcodeManagement() {
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch barcodes
  const { data: barcodesData, isLoading } = useQuery({
    queryKey: ['barcodes', typeFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (typeFilter !== 'all') params.append('entity_type', typeFilter);
      const res = await fetch(`${API_BASE}?${params}`);
      return res.json();
    },
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['barcode-stats'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/statistics`);
      return res.json();
    },
  });

  // Fetch entity types
  const { data: typesData } = useQuery({
    queryKey: ['barcode-types'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/entity-types/reference`);
      return res.json();
    },
  });

  // Fetch scan history
  const { data: scansData } = useQuery({
    queryKey: ['barcode-scans'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/scans?limit=20`);
      return res.json();
    },
  });

  const barcodes: Barcode[] = barcodesData?.barcodes || [];
  const entityTypes: EntityType[] = typesData?.entity_types || [];
  const scans = scansData?.scans || [];

  const filteredBarcodes = barcodes.filter(b =>
    b.barcode_value.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.entity_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getEntityIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      seed_lot: <Package className="w-4 h-4" />,
      accession: <Leaf className="w-4 h-4" />,
      sample: <TestTube className="w-4 h-4" />,
      vault: <Warehouse className="w-4 h-4" />,
      batch: <BarChart3 className="w-4 h-4" />,
      dispatch: <Truck className="w-4 h-4" />,
      mta: <FileText className="w-4 h-4" />,
    };
    return icons[type] || <QrCode className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <QrCode className="w-8 h-8 text-blue-600" />
            Barcode Management
          </h1>
          <p className="text-gray-600 mt-1">Generate, scan, and manage barcodes</p>
        </div>
        <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="w-4 h-4" /> Generate Barcode
            </Button>
          </DialogTrigger>
          <DialogContent>
            <GenerateBarcodeDialog
              entityTypes={entityTypes}
              onClose={() => setShowGenerateDialog(false)}
              onSuccess={() => {
                queryClient.invalidateQueries({ queryKey: ['barcodes'] });
                queryClient.invalidateQueries({ queryKey: ['barcode-stats'] });
                setShowGenerateDialog(false);
                toast({ title: 'Barcode Generated', description: 'New barcode created successfully' });
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
                <QrCode className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.total_barcodes || 0}</p>
                <p className="text-sm text-gray-500">Total Barcodes</p>
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
                <p className="text-2xl font-bold">{stats?.active_barcodes || 0}</p>
                <p className="text-sm text-gray-500">Active</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Camera className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.total_scans || 0}</p>
                <p className="text-sm text-gray-500">Total Scans</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <BarChart3 className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.scan_success_rate || 0}%</p>
                <p className="text-sm text-gray-500">Success Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>


      {/* Main Content Tabs */}
      <Tabs defaultValue="scanner" className="space-y-4">
        <TabsList>
          <TabsTrigger value="scanner" className="gap-2">
            <Camera className="w-4 h-4" /> Scanner
          </TabsTrigger>
          <TabsTrigger value="barcodes" className="gap-2">
            <QrCode className="w-4 h-4" /> Barcodes
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <History className="w-4 h-4" /> Scan History
          </TabsTrigger>
        </TabsList>

        {/* Scanner Tab */}
        <TabsContent value="scanner">
          <div className="grid md:grid-cols-2 gap-6">
            <BarcodeScanner
              onScan={(result) => {
                queryClient.invalidateQueries({ queryKey: ['barcode-scans'] });
                queryClient.invalidateQueries({ queryKey: ['barcode-stats'] });
              }}
            />
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex items-start gap-2">
                  <div className="p-1 bg-blue-100 rounded">
                    <Camera className="w-3 h-3 text-blue-600" />
                  </div>
                  <p>Hold the barcode steady within the scanning area</p>
                </div>
                <div className="flex items-start gap-2">
                  <div className="p-1 bg-green-100 rounded">
                    <CheckCircle2 className="w-3 h-3 text-green-600" />
                  </div>
                  <p>A beep sound confirms successful scan</p>
                </div>
                <div className="flex items-start gap-2">
                  <div className="p-1 bg-purple-100 rounded">
                    <Search className="w-3 h-3 text-purple-600" />
                  </div>
                  <p>Use manual entry for damaged or unreadable codes</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Barcodes Tab */}
        <TabsContent value="barcodes">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search barcodes..."
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
                {entityTypes.map(t => (
                  <SelectItem key={t.value} value={t.value}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Barcode List */}
          <Card>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="p-8 text-center text-gray-500">Loading...</div>
              ) : filteredBarcodes.length === 0 ? (
                <div className="p-8 text-center text-gray-500">No barcodes found</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Barcode</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Entity</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Scans</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {filteredBarcodes.map((barcode) => (
                        <tr key={barcode.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <Badge variant="outline" className="font-mono">{barcode.barcode_value}</Badge>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              {getEntityIcon(barcode.entity_type)}
                              <span className="text-sm">{barcode.entity_type}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 font-medium">{barcode.entity_name}</td>
                          <td className="px-4 py-3 text-center">
                            <Badge variant="secondary">{barcode.scan_count}</Badge>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {new Date(barcode.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {barcode.active ? (
                              <Badge className="bg-green-100 text-green-800">Active</Badge>
                            ) : (
                              <Badge className="bg-gray-100 text-gray-800">Inactive</Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Recent Scans</CardTitle>
              <CardDescription>Last 20 barcode scans</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {scans.length === 0 ? (
                <div className="p-8 text-center text-gray-500">No scan history</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Barcode</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Result</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Entity</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Scanned By</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {scans.map((scan: any) => (
                        <tr key={scan.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {new Date(scan.scanned_at).toLocaleString()}
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant="outline" className="font-mono">{scan.barcode_value}</Badge>
                          </td>
                          <td className="px-4 py-3 text-center">
                            {scan.found ? (
                              <CheckCircle2 className="w-5 h-5 text-green-500 mx-auto" />
                            ) : (
                              <XCircle className="w-5 h-5 text-red-500 mx-auto" />
                            )}
                          </td>
                          <td className="px-4 py-3">{scan.entity_name || '—'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{scan.scanned_by}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}


// Generate Barcode Dialog
function GenerateBarcodeDialog({
  entityTypes,
  onClose,
  onSuccess,
}: {
  entityTypes: EntityType[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    entity_type: 'seed_lot',
    entity_id: '',
    entity_name: '',
    format: 'qr_code',
    data: {},
  });

  const handleSubmit = async () => {
    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error('Failed to generate barcode');
      onSuccess();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Generate New Barcode</DialogTitle>
      </DialogHeader>
      <div className="space-y-4 py-4">
        <div>
          <Label>Entity Type</Label>
          <Select
            value={formData.entity_type}
            onValueChange={(v) => setFormData({ ...formData, entity_type: v })}
          >
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {entityTypes.map(t => (
                <SelectItem key={t.value} value={t.value}>
                  {t.name} ({t.prefix})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Entity ID</Label>
          <Input
            placeholder="e.g., lot-001"
            value={formData.entity_id}
            onChange={(e) => setFormData({ ...formData, entity_id: e.target.value })}
          />
        </div>
        <div>
          <Label>Entity Name</Label>
          <Input
            placeholder="e.g., SL-2024-001"
            value={formData.entity_name}
            onChange={(e) => setFormData({ ...formData, entity_name: e.target.value })}
          />
        </div>
        <div>
          <Label>Barcode Format</Label>
          <Select
            value={formData.format}
            onValueChange={(v) => setFormData({ ...formData, format: v })}
          >
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="qr_code">QR Code</SelectItem>
              <SelectItem value="code_128">Code 128</SelectItem>
              <SelectItem value="data_matrix">Data Matrix</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit}>Generate</Button>
      </DialogFooter>
    </>
  );
}

export default BarcodeManagement;

/**
 * Certificates Page - Issue and manage quality certificates
 * Connected to /api/v2/quality endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  FileCheck, Search, Plus, RefreshCw, Download, 
  Printer, CheckCircle, Clock, AlertCircle 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface Certificate {
  certificate_id: string;
  sample_id: string;
  lot_id: string;
  variety: string;
  seed_class: string;
  issue_date: string;
  expiry_date: string;
  status: 'valid' | 'expired' | 'revoked';
  test_results?: Record<string, number>;
}

interface PassedSample {
  sample_id: string;
  lot_id: string;
  variety: string;
}

export function Certificates() {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [passedSamples, setPassedSamples] = useState<PassedSample[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showIssueDialog, setShowIssueDialog] = useState(false);
  const [issuing, setIssuing] = useState(false);
  const [newCert, setNewCert] = useState({
    sample_id: '',
    seed_class: 'certified',
    valid_months: 12,
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Get passed samples that can be certified
      const samplesRes = await apiClient.getQCSamples('passed');
      setPassedSamples(samplesRes.samples || []);
      
      // Get certificates from API
      const certsRes = await apiClient.getQCCertificates();
      setCertificates(certsRes.certificates || []);
    } catch (err) {
      console.error('Failed to fetch certificates:', err);
      setError('Failed to load certificates. Please check your connection.');
      setPassedSamples([]);
      setCertificates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleIssueCertificate = async () => {
    if (!newCert.sample_id) {
      alert('Please select a sample');
      return;
    }

    setIssuing(true);
    try {
      await apiClient.issueQCCertificate(newCert);
      setShowIssueDialog(false);
      setNewCert({ sample_id: '', seed_class: 'certified', valid_months: 12 });
      fetchData();
      alert('Certificate issued successfully');
    } catch (err: any) {
      alert(err.message || 'Failed to issue certificate');
    } finally {
      setIssuing(false);
    }
  };

  const filteredCertificates = certificates.filter(c =>
    c.certificate_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.lot_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.variety.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const validCount = certificates.filter(c => c.status === 'valid').length;
  const expiredCount = certificates.filter(c => c.status === 'expired').length;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'valid': return <Badge className="bg-green-100 text-green-700">Valid</Badge>;
      case 'expired': return <Badge className="bg-red-100 text-red-700">Expired</Badge>;
      case 'revoked': return <Badge className="bg-gray-100 text-gray-700">Revoked</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  const getSeedClassBadge = (seedClass: string) => {
    const colors: Record<string, string> = {
      foundation: 'bg-white border border-gray-300 text-gray-700',
      certified: 'bg-blue-100 text-blue-700',
      truthful: 'bg-green-100 text-green-700',
    };
    return <Badge className={colors[seedClass] || colors.certified}>{seedClass}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
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

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileCheck className="h-6 w-6 text-green-600" />
            Certificates
          </h1>
          <p className="text-gray-500 text-sm">Issue and manage seed quality certificates</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
            <DialogTrigger asChild>
              <Button className="bg-green-600 hover:bg-green-700">
                <Plus className="h-4 w-4 mr-2" />
                Issue Certificate
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Issue Quality Certificate</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Sample (Passed QC)</Label>
                  <Select value={newCert.sample_id} onValueChange={(v) => setNewCert({...newCert, sample_id: v})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select passed sample" />
                    </SelectTrigger>
                    <SelectContent>
                      {passedSamples.map((s) => (
                        <SelectItem key={s.sample_id} value={s.sample_id}>
                          {s.sample_id} - {s.lot_id} ({s.variety})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Seed Class</Label>
                  <Select value={newCert.seed_class} onValueChange={(v) => setNewCert({...newCert, seed_class: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="foundation">Foundation Seed</SelectItem>
                      <SelectItem value="certified">Certified Seed</SelectItem>
                      <SelectItem value="truthful">Truthfully Labeled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Validity Period (months)</Label>
                  <Select value={String(newCert.valid_months)} onValueChange={(v) => setNewCert({...newCert, valid_months: parseInt(v)})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="6">6 months</SelectItem>
                      <SelectItem value="9">9 months</SelectItem>
                      <SelectItem value="12">12 months</SelectItem>
                      <SelectItem value="18">18 months</SelectItem>
                      <SelectItem value="24">24 months</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleIssueCertificate} disabled={issuing || !newCert.sample_id} className="w-full">
                  {issuing ? 'Issuing...' : 'Issue Certificate'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
              <FileCheck className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{certificates.length}</p>
              <p className="text-sm text-gray-500">Total Certificates</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{validCount}</p>
              <p className="text-sm text-gray-500">Valid</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
              <AlertCircle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{expiredCount}</p>
              <p className="text-sm text-gray-500">Expired</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
              <Clock className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{passedSamples.length}</p>
              <p className="text-sm text-gray-500">Pending Issue</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search certificates..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Certificates List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading certificates...</div>
          ) : filteredCertificates.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <FileCheck className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No certificates found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left p-4 font-medium text-gray-600">Certificate ID</th>
                    <th className="text-left p-4 font-medium text-gray-600">Lot / Variety</th>
                    <th className="text-left p-4 font-medium text-gray-600">Class</th>
                    <th className="text-left p-4 font-medium text-gray-600">Issue Date</th>
                    <th className="text-left p-4 font-medium text-gray-600">Expiry Date</th>
                    <th className="text-left p-4 font-medium text-gray-600">Status</th>
                    <th className="text-right p-4 font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredCertificates.map((cert) => (
                    <tr key={cert.certificate_id} className="hover:bg-gray-50">
                      <td className="p-4">
                        <p className="font-medium">{cert.certificate_id}</p>
                        <p className="text-xs text-gray-500">{cert.sample_id}</p>
                      </td>
                      <td className="p-4">
                        <p className="font-medium">{cert.lot_id}</p>
                        <p className="text-sm text-gray-500">{cert.variety}</p>
                      </td>
                      <td className="p-4">{getSeedClassBadge(cert.seed_class)}</td>
                      <td className="p-4 text-gray-600">{cert.issue_date}</td>
                      <td className="p-4 text-gray-600">{cert.expiry_date}</td>
                      <td className="p-4">{getStatusBadge(cert.status)}</td>
                      <td className="p-4 text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" title="Download">
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" title="Print">
                            <Printer className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default Certificates;

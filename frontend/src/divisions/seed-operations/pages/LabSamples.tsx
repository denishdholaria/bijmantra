/**
 * Lab Samples Page
 * Sample registration and management for LIMS
 * Connected to /api/v2/quality endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FlaskConical, Plus, Search, QrCode, RefreshCw, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface QCSample {
  sample_id: string;
  lot_id: string;
  variety: string;
  sample_date: string;
  sample_weight: number;
  source: string;
  status: 'pending' | 'passed' | 'failed';
  tests: any[];
}

interface QCSummary {
  total_samples: number;
  pending: number;
  passed: number;
  failed: number;
}

export function LabSamples() {
  const [searchTerm, setSearchTerm] = useState('');
  const [samples, setSamples] = useState<QCSample[]>([]);
  const [summary, setSummary] = useState<QCSummary>({ total_samples: 0, pending: 0, passed: 0, failed: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('all');
  const [showRegisterDialog, setShowRegisterDialog] = useState(false);
  const [newSample, setNewSample] = useState({
    lot_id: '',
    variety: '',
    sample_date: new Date().toISOString().split('T')[0],
    sample_weight: 500,
    source: '',
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [samplesRes, summaryRes] = await Promise.all([
        apiClient.qualityControlService.getQCSamples(activeTab === 'all' ? undefined : activeTab),
        apiClient.qualityControlService.getQCSummary(),
      ]);
      setSamples(samplesRes.samples || []);
      setSummary(summaryRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load samples');
      // Zero Mock Data Policy - show empty state
      setSamples([]);
      setSummary({ total_samples: 0, pending: 0, passed: 0, failed: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const handleRegisterSample = async () => {
    try {
      await apiClient.qualityControlService.registerQCSample(newSample); // Note: registerQCSample might be mapped to inventory or QC. Checking service...
      setShowRegisterDialog(false);
      setNewSample({ lot_id: '', variety: '', sample_date: new Date().toISOString().split('T')[0], sample_weight: 500, source: '' });
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to register sample');
    }
  };

  const filteredSamples = samples.filter(s => 
    s.sample_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.lot_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.variety.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lab Samples</h1>
          <p className="text-gray-500 text-sm mt-1">Register and manage samples for quality testing</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={showRegisterDialog} onOpenChange={setShowRegisterDialog}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                Register Sample
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Register New Sample</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Lot ID</Label>
                  <Input value={newSample.lot_id} onChange={(e) => setNewSample({...newSample, lot_id: e.target.value})} placeholder="LOT-2024-0001" />
                </div>
                <div className="space-y-2">
                  <Label>Variety</Label>
                  <Input value={newSample.variety} onChange={(e) => setNewSample({...newSample, variety: e.target.value})} placeholder="IR64" />
                </div>
                <div className="space-y-2">
                  <Label>Sample Date</Label>
                  <Input type="date" value={newSample.sample_date} onChange={(e) => setNewSample({...newSample, sample_date: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Sample Weight (g)</Label>
                  <Input type="number" value={newSample.sample_weight} onChange={(e) => setNewSample({...newSample, sample_weight: Number(e.target.value)})} />
                </div>
                <div className="space-y-2">
                  <Label>Source</Label>
                  <Input value={newSample.source} onChange={(e) => setNewSample({...newSample, source: e.target.value})} placeholder="Processing Plant A" />
                </div>
                <Button onClick={handleRegisterSample} className="w-full">Register Sample</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center gap-2">
            {error}
            <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Samples" value={summary.total_samples} />
        <StatCard label="Pending" value={summary.pending} color="yellow" />
        <StatCard label="Passed" value={summary.passed} color="green" />
        <StatCard label="Failed" value={summary.failed} color="red" />
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <div className="flex flex-col sm:flex-row justify-between gap-4">
          <TabsList>
            <TabsTrigger value="all">All Samples</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
            <TabsTrigger value="passed">Passed</TabsTrigger>
            <TabsTrigger value="failed">Failed</TabsTrigger>
          </TabsList>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input 
              placeholder="Search samples..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
        </div>

        <TabsContent value={activeTab} className="space-y-4">
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-8 text-center text-gray-500">Loading samples...</div>
              ) : filteredSamples.length === 0 ? (
                <div className="p-8 text-center text-gray-500">No samples found</div>
              ) : (
                <div className="divide-y">
                  {filteredSamples.map((sample) => (
                    <SampleRow key={sample.sample_id} sample={sample} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatCard({ label, value, color = 'gray' }: { label: string; value: number; color?: string }) {
  const colors: Record<string, string> = {
    gray: 'text-gray-600',
    blue: 'text-blue-600',
    yellow: 'text-yellow-600',
    green: 'text-green-600',
    red: 'text-red-600',
  };
  
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-2xl font-bold">{value}</p>
        <p className={`text-sm ${colors[color]}`}>{label}</p>
      </CardContent>
    </Card>
  );
}

function SampleRow({ sample }: { sample: QCSample }) {
  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-700',
    passed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  };

  return (
    <div className="flex items-center justify-between p-4 hover:bg-gray-50">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
          <FlaskConical className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <p className="font-medium text-gray-900">{sample.sample_id}</p>
          <p className="text-sm text-gray-500">{sample.lot_id}</p>
        </div>
      </div>
      <div className="hidden md:block">
        <p className="text-sm text-gray-900">{sample.variety}</p>
        <p className="text-sm text-gray-500">{sample.source}</p>
      </div>
      <div className="hidden md:block text-sm text-gray-500">
        {sample.sample_date}
      </div>
      <Badge className={statusColors[sample.status]}>
        {sample.status.charAt(0).toUpperCase() + sample.status.slice(1)}
      </Badge>
      <Button variant="ghost" size="sm">
        <QrCode className="h-4 w-4" />
      </Button>
    </div>
  );
}

export default LabSamples;

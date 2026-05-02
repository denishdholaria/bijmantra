/**
 * Lab Testing Page - Record test results
 * Connected to /api/v2/quality endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  FlaskConical, Search, CheckCircle, XCircle, 
  AlertCircle, RefreshCw, Plus 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface TestType {
  id: string;
  name: string;
  description: string;
  unit: string;
}

interface Sample {
  sample_id: string;
  lot_id: string;
  variety: string;
  status: string;
}

export function LabTesting() {
  const [testTypes, setTestTypes] = useState<TestType[]>([]);
  const [seedClasses, setSeedClasses] = useState<any[]>([]);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSample, setSelectedSample] = useState<Sample | null>(null);
  const [testResult, setTestResult] = useState({
    test_type: '',
    result_value: '',
    tester: '',
    method: '',
    seed_class: 'certified',
    notes: '',
  });
  const [lastResult, setLastResult] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [typesRes, classesRes, samplesRes] = await Promise.all([
        apiClient.qualityControlService.getQCTestTypes(),
        apiClient.qualityControlService.getQCSeedClasses(),
        apiClient.qualityControlService.getQCSamples('pending'),
      ]);
      setTestTypes(typesRes.test_types || []);
      setSeedClasses(classesRes.seed_classes || []);
      setSamples(samplesRes.samples || []);
    } catch (err) {
      // Show empty state - no demo data
      setTestTypes([]);
      setSeedClasses([]);
      setSamples([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmitTest = async () => {
    if (!selectedSample || !testResult.test_type || !testResult.result_value) {
      alert('Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      const res = await apiClient.qualityControlService.recordQCTest({
        sample_id: selectedSample.sample_id,
        test_type: testResult.test_type,
        result_value: parseFloat(testResult.result_value),
        tester: testResult.tester || 'Lab Technician',
        method: testResult.method || 'Standard method',
        seed_class: testResult.seed_class,
        notes: testResult.notes,
      });
      
      setLastResult(res);
      setTestResult({ test_type: '', result_value: '', tester: '', method: '', seed_class: 'certified', notes: '' });
      fetchData(); // Refresh samples
    } catch (err: any) {
      // Show error - no demo fallback
      alert(err.message || 'Failed to record test result. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredSamples = samples.filter(s =>
    s.sample_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.lot_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.variety.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedTestType = testTypes.find(t => t.id === testResult.test_type);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FlaskConical className="h-6 w-6 text-blue-600" />
            Lab Testing
          </h1>
          <p className="text-gray-500 text-sm">Record quality test results for samples</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Sample Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Select Sample</CardTitle>
            <CardDescription>Choose a pending sample to record test results</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search samples..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="max-h-64 overflow-y-auto space-y-2">
              {loading ? (
                <p className="text-center text-gray-500 py-4">Loading samples...</p>
              ) : filteredSamples.length === 0 ? (
                <p className="text-center text-gray-500 py-4">No pending samples</p>
              ) : (
                filteredSamples.map((sample) => (
                  <div
                    key={sample.sample_id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedSample?.sample_id === sample.sample_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedSample(sample)}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{sample.sample_id}</p>
                        <p className="text-sm text-gray-500">{sample.lot_id} • {sample.variety}</p>
                      </div>
                      <Badge className="bg-yellow-100 text-yellow-700">{sample.status}</Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Test Entry Form */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Record Test Result</CardTitle>
            <CardDescription>
              {selectedSample 
                ? `Recording for ${selectedSample.sample_id}` 
                : 'Select a sample first'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Test Type *</Label>
              <Select 
                value={testResult.test_type} 
                onValueChange={(v) => setTestResult({...testResult, test_type: v})}
                disabled={!selectedSample}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select test type" />
                </SelectTrigger>
                <SelectContent>
                  {testTypes.map((type) => (
                    <SelectItem key={type.id} value={type.id}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedTestType && (
                <p className="text-xs text-gray-500">{selectedTestType.description}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Result Value * {selectedTestType && `(${selectedTestType.unit})`}</Label>
              <Input
                type="number"
                step="0.1"
                value={testResult.result_value}
                onChange={(e) => setTestResult({...testResult, result_value: e.target.value})}
                placeholder={selectedTestType ? `Enter ${selectedTestType.unit}` : 'Enter value'}
                disabled={!selectedSample}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Seed Class</Label>
                <Select 
                  value={testResult.seed_class} 
                  onValueChange={(v) => setTestResult({...testResult, seed_class: v})}
                  disabled={!selectedSample}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {seedClasses.map((sc) => (
                      <SelectItem key={sc.id} value={sc.id}>{sc.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Tester</Label>
                <Input
                  value={testResult.tester}
                  onChange={(e) => setTestResult({...testResult, tester: e.target.value})}
                  placeholder="Your name"
                  disabled={!selectedSample}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Method</Label>
              <Input
                value={testResult.method}
                onChange={(e) => setTestResult({...testResult, method: e.target.value})}
                placeholder="Testing method (e.g., ISTA standard)"
                disabled={!selectedSample}
              />
            </div>

            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={testResult.notes}
                onChange={(e) => setTestResult({...testResult, notes: e.target.value})}
                placeholder="Additional observations..."
                rows={2}
                disabled={!selectedSample}
              />
            </div>

            <Button 
              onClick={handleSubmitTest} 
              disabled={!selectedSample || !testResult.test_type || !testResult.result_value || submitting}
              className="w-full"
            >
              {submitting ? 'Recording...' : 'Record Test Result'}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Last Result */}
      {lastResult && (
        <Card className={lastResult.passed ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              {lastResult.passed ? (
                <CheckCircle className="h-8 w-8 text-green-600" />
              ) : (
                <XCircle className="h-8 w-8 text-red-600" />
              )}
              <div>
                <p className="font-medium">{lastResult.message}</p>
                <p className="text-sm text-gray-600">
                  {lastResult.sample_id} • {lastResult.test_type} • {lastResult.result_value}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Test Types Reference */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Quality Standards Reference</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-3">
            {testTypes.map((type) => (
              <div key={type.id} className="p-3 bg-gray-50 rounded-lg text-center">
                <p className="font-medium text-sm">{type.name}</p>
                <p className="text-xs text-gray-500">{type.unit}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default LabTesting;

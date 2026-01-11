/**
 * Processing Batches Page - Batch management
 * Connected to /api/v2/processing endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Boxes, Plus, Search, RefreshCw, Play, Pause, 
  CheckCircle, XCircle, AlertCircle, ArrowRight 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface ProcessingBatch {
  batch_id: string;
  batch_number: string;
  lot_id: string;
  variety_name: string;
  crop: string;
  seed_class: string;
  input_quantity_kg: number;
  current_quantity_kg: number;
  current_stage: string;
  status: string;
  stages: any[];
  quality_checks: any[];
  created_at: string;
  target_output_kg?: number;
}

interface ProcessingStage {
  id: string;
  name: string;
  order: number;
  description: string;
}

export function ProcessingBatches() {
  const [batches, setBatches] = useState<ProcessingBatch[]>([]);
  const [stages, setStages] = useState<ProcessingStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newBatch, setNewBatch] = useState({
    lot_id: '',
    variety_name: '',
    crop: 'Rice',
    seed_class: 'certified',
    input_quantity_kg: 1000,
    target_output_kg: 850,
    notes: '',
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [batchesRes, stagesRes] = await Promise.all([
        apiClient.getProcessingBatches(filterStatus || undefined),
        apiClient.getProcessingStages(),
      ]);
      setBatches(batchesRes.data || []);
      setStages(stagesRes.data || []);
    } catch (err: any) {
      setError('Backend unavailable - no data to display');
      setBatches([]);
      setStages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filterStatus]);

  const handleCreateBatch = async () => {
    try {
      await apiClient.createProcessingBatch(newBatch);
      setShowNewDialog(false);
      setNewBatch({ lot_id: '', variety_name: '', crop: 'Rice', seed_class: 'certified', input_quantity_kg: 1000, target_output_kg: 850, notes: '' });
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to create batch');
    }
  };

  const filteredBatches = batches.filter(b =>
    b.batch_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.lot_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.variety_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-700',
      in_progress: 'bg-blue-100 text-blue-700',
      on_hold: 'bg-yellow-100 text-yellow-700',
      completed: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700',
    };
    return <Badge className={colors[status] || colors.pending}>{status.replace('_', ' ')}</Badge>;
  };

  const getStageName = (stageId: string) => {
    const stage = stages.find(s => s.id === stageId);
    return stage?.name || stageId;
  };

  const getStageProgress = (currentStage: string) => {
    const stageIndex = stages.findIndex(s => s.id === currentStage);
    return stageIndex >= 0 ? ((stageIndex + 1) / stages.length) * 100 : 0;
  };

  const stats = {
    total: batches.length,
    inProgress: batches.filter(b => b.status === 'in_progress').length,
    completed: batches.filter(b => b.status === 'completed').length,
    onHold: batches.filter(b => b.status === 'on_hold').length,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Boxes className="h-6 w-6 text-blue-600" />
            Processing Batches
          </h1>
          <p className="text-gray-500 text-sm">Manage seed processing batches through stages</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Batch</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Processing Batch</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Lot ID *</Label>
                    <Input value={newBatch.lot_id} onChange={(e) => setNewBatch({...newBatch, lot_id: e.target.value})} placeholder="LOT-2024-001" />
                  </div>
                  <div className="space-y-2">
                    <Label>Variety *</Label>
                    <Input value={newBatch.variety_name} onChange={(e) => setNewBatch({...newBatch, variety_name: e.target.value})} placeholder="IR64" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Crop</Label>
                    <Select value={newBatch.crop} onValueChange={(v) => setNewBatch({...newBatch, crop: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Rice">Rice</SelectItem>
                        <SelectItem value="Wheat">Wheat</SelectItem>
                        <SelectItem value="Maize">Maize</SelectItem>
                        <SelectItem value="Soybean">Soybean</SelectItem>
                        <SelectItem value="Cotton">Cotton</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Seed Class</Label>
                    <Select value={newBatch.seed_class} onValueChange={(v) => setNewBatch({...newBatch, seed_class: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="foundation">Foundation</SelectItem>
                        <SelectItem value="certified">Certified</SelectItem>
                        <SelectItem value="truthful">Truthfully Labeled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Input Quantity (kg) *</Label>
                    <Input type="number" value={newBatch.input_quantity_kg} onChange={(e) => setNewBatch({...newBatch, input_quantity_kg: Number(e.target.value)})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Target Output (kg)</Label>
                    <Input type="number" value={newBatch.target_output_kg} onChange={(e) => setNewBatch({...newBatch, target_output_kg: Number(e.target.value)})} />
                  </div>
                </div>
                <Button onClick={handleCreateBatch} className="w-full">Create Batch</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
              <Boxes className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-sm text-gray-500">Total Batches</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
              <Play className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.inProgress}</p>
              <p className="text-sm text-gray-500">In Progress</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.completed}</p>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-50 flex items-center justify-center">
              <Pause className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.onHold}</p>
              <p className="text-sm text-gray-500">On Hold</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search batches..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={filterStatus || "all"} onValueChange={(v) => setFilterStatus(v === "all" ? "" : v)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="on_hold">On Hold</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Batches List */}
      <div className="space-y-4">
        {loading ? (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">Loading batches...</CardContent>
          </Card>
        ) : filteredBatches.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              <Boxes className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No batches found</p>
            </CardContent>
          </Card>
        ) : (
          filteredBatches.map((batch) => {
            const yieldPercent = (batch.current_quantity_kg / batch.input_quantity_kg) * 100;
            const stageProgress = getStageProgress(batch.current_stage);
            
            return (
              <Card key={batch.batch_id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center">
                        <Boxes className="h-6 w-6 text-blue-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{batch.batch_number}</p>
                          {getStatusBadge(batch.status)}
                        </div>
                        <p className="text-sm text-gray-500">{batch.lot_id} • {batch.variety_name} • {batch.crop}</p>
                      </div>
                    </div>
                    
                    <div className="flex-1 max-w-md">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-500">Stage: {getStageName(batch.current_stage)}</span>
                        <span className="font-medium">{Math.round(stageProgress)}%</span>
                      </div>
                      <Progress value={stageProgress} className="h-2" />
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <div className="text-center">
                        <p className="text-lg font-bold">{batch.current_quantity_kg} kg</p>
                        <p className="text-xs text-gray-500">Current</p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-gray-300" />
                      <div className="text-center">
                        <p className="text-lg font-bold text-gray-400">{batch.target_output_kg || '-'} kg</p>
                        <p className="text-xs text-gray-500">Target</p>
                      </div>
                      <div className="text-center">
                        <p className={`text-lg font-bold ${yieldPercent >= 85 ? 'text-green-600' : yieldPercent >= 75 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {yieldPercent.toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-500">Yield</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Processing Stages Reference */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Processing Stages</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {stages.map((stage, index) => (
              <div key={stage.id} className="flex items-center">
                <Badge variant="outline" className="text-xs">{stage.name}</Badge>
                {index < stages.length - 1 && <ArrowRight className="h-3 w-3 mx-1 text-gray-300" />}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ProcessingBatches;

/**
 * Processing Stages Page
 * 
 * Displays the 10-stage seed processing workflow and allows tracking
 * of batches through each stage with real API data and animations.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import {
  Cog,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowRight,
  Package,
  Droplets,
  Wind,
  Scale,
  Sparkles,
  Shield,
  Box,
  Tag,
  Truck,
  ClipboardCheck,
  Play,
  Pause,
  RotateCcw,
  XCircle,
} from 'lucide-react';

interface ProcessingBatch {
  id: string;
  batch_number: string;
  lot_id: string;
  variety_name?: string;
  crop?: string;
  seed_class?: string;
  input_quantity_kg: number;
  current_quantity_kg: number;
  current_stage: string;
  status: string;
  stages: ProcessingStage[];
  quality_checks: QualityCheck[];
  created_at: string;
  updated_at: string;
}

interface ProcessingStage {
  id: string;
  stage: string;
  status: string;
  operator: string;
  equipment?: string;
  input_quantity_kg?: number;
  output_quantity_kg?: number;
  loss_kg?: number;
  started_at: string;
  completed_at?: string;
  notes?: string;
}

interface QualityCheck {
  id: string;
  check_type: string;
  result_value: number;
  passed: boolean;
  checked_by: string;
  checked_at: string;
}

// Processing stage definitions with icons and descriptions
const STAGE_DEFINITIONS = [
  { 
    name: 'receiving', 
    label: 'Receiving', 
    icon: Package, 
    description: 'Initial receipt and documentation of raw seed',
    color: 'bg-blue-500',
    gradient: 'from-blue-500 to-blue-600'
  },
  { 
    name: 'pre_cleaning', 
    label: 'Pre-Cleaning', 
    icon: Wind, 
    description: 'Remove large debris, straw, and foreign matter',
    color: 'bg-cyan-500',
    gradient: 'from-cyan-500 to-cyan-600'
  },
  { 
    name: 'drying', 
    label: 'Drying', 
    icon: Droplets, 
    description: 'Reduce moisture content to safe storage levels',
    color: 'bg-yellow-500',
    gradient: 'from-yellow-500 to-yellow-600'
  },
  { 
    name: 'cleaning', 
    label: 'Cleaning', 
    icon: Sparkles, 
    description: 'Fine cleaning using air-screen cleaners',
    color: 'bg-green-500',
    gradient: 'from-green-500 to-green-600'
  },
  { 
    name: 'grading', 
    label: 'Grading', 
    icon: Scale, 
    description: 'Size and density separation for uniformity',
    color: 'bg-purple-500',
    gradient: 'from-purple-500 to-purple-600'
  },
  { 
    name: 'treating', 
    label: 'Treating', 
    icon: Shield, 
    description: 'Apply fungicide/insecticide seed treatment',
    color: 'bg-red-500',
    gradient: 'from-red-500 to-red-600'
  },
  { 
    name: 'quality_testing', 
    label: 'Quality Testing', 
    icon: ClipboardCheck, 
    description: 'Germination, purity, and moisture testing',
    color: 'bg-orange-500',
    gradient: 'from-orange-500 to-orange-600'
  },
  { 
    name: 'packaging', 
    label: 'Packaging', 
    icon: Box, 
    description: 'Pack into bags with proper labeling',
    color: 'bg-indigo-500',
    gradient: 'from-indigo-500 to-indigo-600'
  },
  { 
    name: 'labeling', 
    label: 'Labeling', 
    icon: Tag, 
    description: 'Apply certification tags and lot labels',
    color: 'bg-pink-500',
    gradient: 'from-pink-500 to-pink-600'
  },
  { 
    name: 'storage', 
    label: 'Storage/Dispatch', 
    icon: Truck, 
    description: 'Store in warehouse or dispatch to dealers',
    color: 'bg-gray-500',
    gradient: 'from-gray-500 to-gray-600'
  },
];

const statusColors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  on_hold: 'bg-yellow-100 text-yellow-800',
  rejected: 'bg-red-100 text-red-800',
};

export function ProcessingStages() {
  const queryClient = useQueryClient();
  const [selectedBatch, setSelectedBatch] = useState<string>('');
  const [isStartStageOpen, setIsStartStageOpen] = useState(false);
  const [stageForm, setStageForm] = useState({
    operator: '',
    equipment: '',
    input_quantity_kg: '',
  });

  // Fetch batches
  const { data: batchesResponse, isLoading } = useQuery({
    queryKey: ['processing-batches'],
    queryFn: () => apiClient.processingService.getProcessingBatches(),
  });

  const batches: ProcessingBatch[] = batchesResponse?.data || [];

  // Get selected batch details
  const currentBatch = batches.find(b => b.id === selectedBatch);

  // Start stage mutation
  const startStageMutation = useMutation({
    mutationFn: async ({ batchId, stage }: { batchId: string; stage: string }) => {
      return apiClient.processingService.startProcessingStage(batchId, {
        stage,
        operator: stageForm.operator,
        equipment: stageForm.equipment || undefined,
        input_quantity_kg: stageForm.input_quantity_kg ? parseFloat(stageForm.input_quantity_kg) : undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['processing-batches'] });
      toast.success('Stage started successfully');
      setIsStartStageOpen(false);
      setStageForm({ operator: '', equipment: '', input_quantity_kg: '' });
    },
    onError: () => {
      toast.error('Failed to start stage');
    },
  });

  // Hold batch mutation
  const holdMutation = useMutation({
    mutationFn: (batchId: string) => apiClient.processingService.holdBatch(batchId, 'Quality issue'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['processing-batches'] });
      toast.success('Batch put on hold');
    },
  });

  // Resume batch mutation
  const resumeMutation = useMutation({
    mutationFn: (batchId: string) => apiClient.processingService.resumeBatch(batchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['processing-batches'] });
      toast.success('Batch resumed');
    },
  });

  // Calculate stage status for a batch
  const getStageStatus = (stageName: string, batch?: ProcessingBatch) => {
    if (!batch) return 'pending';
    const stage = batch.stages?.find(s => s.stage === stageName);
    if (stage) return stage.status;
    
    const currentIndex = STAGE_DEFINITIONS.findIndex(s => s.name === batch.current_stage);
    const stageIndex = STAGE_DEFINITIONS.findIndex(s => s.name === stageName);
    
    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'in_progress';
    return 'pending';
  };

  // Calculate overall progress
  const calculateProgress = (batch?: ProcessingBatch) => {
    if (!batch) return 0;
    const completedStages = batch.stages?.filter(s => s.status === 'completed').length || 0;
    return Math.round((completedStages / STAGE_DEFINITIONS.length) * 100);
  };

  // Calculate yield percentage
  const calculateYield = (batch?: ProcessingBatch) => {
    if (!batch || !batch.input_quantity_kg) return 0;
    return Math.round((batch.current_quantity_kg / batch.input_quantity_kg) * 100);
  };

  // Get next stage
  const getNextStage = (batch?: ProcessingBatch) => {
    if (!batch) return null;
    const currentIndex = STAGE_DEFINITIONS.findIndex(s => s.name === batch.current_stage);
    if (currentIndex < STAGE_DEFINITIONS.length - 1) {
      return STAGE_DEFINITIONS[currentIndex + 1];
    }
    return null;
  };

  const nextStage = getNextStage(currentBatch);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Cog className="h-6 w-6" />
            Processing Stages
          </h1>
          <p className="text-muted-foreground">
            10-stage seed processing workflow from receiving to dispatch
          </p>
        </div>
        <Select value={selectedBatch} onValueChange={setSelectedBatch}>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Select a batch to track" />
          </SelectTrigger>
          <SelectContent>
            {batches.map((batch) => (
              <SelectItem key={batch.id} value={batch.id}>
                <span className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {batch.status}
                  </Badge>
                  {batch.batch_number} - {batch.variety_name || batch.crop || 'Unknown'}
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Batch Summary */}
      {currentBatch && (
        <Card className="border-2 border-primary/20">
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {currentBatch.batch_number}
                  <Badge className={statusColors[currentBatch.status]}>
                    {currentBatch.status.replace('_', ' ')}
                  </Badge>
                </CardTitle>
                <CardDescription>
                  {currentBatch.variety_name || currentBatch.crop} 
                  {currentBatch.seed_class && ` • ${currentBatch.seed_class}`}
                  {' • Lot: '}{currentBatch.lot_id}
                </CardDescription>
              </div>
              <div className="flex gap-2">
                {currentBatch.status === 'in_progress' && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => holdMutation.mutate(currentBatch.id)}
                    disabled={holdMutation.isPending}
                  >
                    <Pause className="h-4 w-4 mr-1" />
                    Hold
                  </Button>
                )}
                {currentBatch.status === 'on_hold' && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => resumeMutation.mutate(currentBatch.id)}
                    disabled={resumeMutation.isPending}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Resume
                  </Button>
                )}
                {nextStage && currentBatch.status === 'in_progress' && (
                  <Dialog open={isStartStageOpen} onOpenChange={setIsStartStageOpen}>
                    <DialogTrigger asChild>
                      <Button size="sm">
                        <ArrowRight className="h-4 w-4 mr-1" />
                        Start {nextStage.label}
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Start {nextStage.label} Stage</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label>Operator *</Label>
                          <Input
                            value={stageForm.operator}
                            onChange={(e) => setStageForm({ ...stageForm, operator: e.target.value })}
                            placeholder="Operator name"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Equipment</Label>
                          <Input
                            value={stageForm.equipment}
                            onChange={(e) => setStageForm({ ...stageForm, equipment: e.target.value })}
                            placeholder="Equipment used"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Input Quantity (kg)</Label>
                          <Input
                            type="number"
                            value={stageForm.input_quantity_kg}
                            onChange={(e) => setStageForm({ ...stageForm, input_quantity_kg: e.target.value })}
                            placeholder={currentBatch.current_quantity_kg.toString()}
                          />
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" onClick={() => setIsStartStageOpen(false)}>
                            Cancel
                          </Button>
                          <Button
                            onClick={() => startStageMutation.mutate({
                              batchId: currentBatch.id,
                              stage: nextStage.name,
                            })}
                            disabled={!stageForm.operator || startStageMutation.isPending}
                          >
                            {startStageMutation.isPending ? 'Starting...' : 'Start Stage'}
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="p-3 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">Initial Quantity</p>
                <p className="text-xl font-semibold">{currentBatch.input_quantity_kg.toLocaleString()} kg</p>
              </div>
              <div className="p-3 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">Current Quantity</p>
                <p className="text-xl font-semibold">{currentBatch.current_quantity_kg.toLocaleString()} kg</p>
              </div>
              <div className="p-3 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">Yield</p>
                <p className="text-xl font-semibold">{calculateYield(currentBatch)}%</p>
              </div>
              <div className="p-3 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">Progress</p>
                <p className="text-xl font-semibold">{calculateProgress(currentBatch)}%</p>
              </div>
            </div>
            <Progress value={calculateProgress(currentBatch)} className="h-3" />
          </CardContent>
        </Card>
      )}

      {/* Stage Pipeline */}
      <Card>
        <CardHeader>
          <CardTitle>Processing Pipeline</CardTitle>
          <CardDescription>
            Track seed batches through each processing stage
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              <div className="flex gap-4 overflow-x-auto pb-4">
                {Array.from({ length: 10 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-20 flex-shrink-0" />
                ))}
              </div>
              <div className="grid grid-cols-5 gap-3">
                {Array.from({ length: 10 }).map((_, i) => (
                  <Skeleton key={i} className="h-32" />
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Visual Pipeline */}
              <div className="flex items-center justify-between overflow-x-auto pb-4">
                {STAGE_DEFINITIONS.map((stage, index) => {
                  const status = getStageStatus(stage.name, currentBatch);
                  const Icon = stage.icon;
                  const isActive = currentBatch?.current_stage === stage.name;
                  const stageData = currentBatch?.stages?.find(s => s.stage === stage.name);
                  
                  return (
                    <div key={stage.name} className="flex items-center">
                      <div className={`
                        flex flex-col items-center min-w-[90px]
                        transition-all duration-500 ease-in-out
                        ${isActive ? 'scale-110' : ''}
                      `}>
                        <div className={`
                          w-14 h-14 rounded-full flex items-center justify-center
                          transition-all duration-500 ease-in-out
                          ${status === 'completed' ? 'bg-green-100 shadow-green-200 shadow-md' : ''}
                          ${status === 'in_progress' ? `bg-gradient-to-br ${stage.gradient} text-white shadow-lg animate-pulse` : ''}
                          ${status === 'pending' ? 'bg-gray-100' : ''}
                          ${isActive ? 'ring-4 ring-offset-2 ring-blue-400' : ''}
                        `}>
                          {status === 'completed' ? (
                            <CheckCircle2 className="h-7 w-7 text-green-600" />
                          ) : status === 'in_progress' ? (
                            <Icon className="h-7 w-7 animate-bounce" />
                          ) : (
                            <Icon className="h-7 w-7 text-gray-400" />
                          )}
                        </div>
                        <span className={`
                          text-xs mt-2 text-center font-medium
                          transition-colors duration-300
                          ${isActive ? 'text-blue-600 font-bold' : 'text-muted-foreground'}
                        `}>
                          {stage.label}
                        </span>
                        {stageData?.output_quantity_kg && (
                          <span className="text-xs text-muted-foreground">
                            {stageData.output_quantity_kg.toLocaleString()} kg
                          </span>
                        )}
                      </div>
                      {index < STAGE_DEFINITIONS.length - 1 && (
                        <div className={`
                          h-1 w-8 mx-1 rounded transition-all duration-500
                          ${status === 'completed' ? 'bg-green-500' : 'bg-gray-200'}
                        `} />
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Stage Details Grid */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-6">
                {STAGE_DEFINITIONS.map((stage) => {
                  const status = getStageStatus(stage.name, currentBatch);
                  const Icon = stage.icon;
                  const stageData = currentBatch?.stages?.find(s => s.stage === stage.name);
                  const isActive = currentBatch?.current_stage === stage.name;
                  
                  return (
                    <Card key={stage.name} className={`
                      transition-all duration-300
                      ${isActive ? 'border-blue-500 border-2 shadow-lg shadow-blue-100' : ''}
                      ${status === 'completed' ? 'border-green-200 bg-green-50/30' : ''}
                      hover:shadow-md
                    `}>
                      <CardContent className="p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <div className={`p-1.5 rounded bg-gradient-to-br ${stage.gradient} bg-opacity-20`}>
                            <Icon className="h-4 w-4 text-white" />
                          </div>
                          <span className="text-sm font-medium truncate">{stage.label}</span>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                          {stage.description}
                        </p>
                        <div className="flex items-center gap-1">
                          {status === 'completed' && (
                            <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Done
                            </Badge>
                          )}
                          {status === 'in_progress' && (
                            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200 animate-pulse">
                              <Clock className="h-3 w-3 mr-1" />
                              Active
                            </Badge>
                          )}
                          {status === 'pending' && (
                            <Badge variant="outline" className="text-xs">
                              Pending
                            </Badge>
                          )}
                        </div>
                        {stageData && (
                          <div className="mt-2 pt-2 border-t text-xs text-muted-foreground space-y-1">
                            {stageData.operator && (
                              <p>By: {stageData.operator}</p>
                            )}
                            {stageData.output_quantity_kg && (
                              <p>Output: {stageData.output_quantity_kg.toLocaleString()} kg</p>
                            )}
                            {stageData.loss_kg && stageData.loss_kg > 0 && (
                              <p className="text-red-600">Loss: {stageData.loss_kg.toLocaleString()} kg</p>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quality Checks */}
      {currentBatch && currentBatch.quality_checks && currentBatch.quality_checks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Quality Checks</CardTitle>
            <CardDescription>Quality control results for this batch</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {currentBatch.quality_checks.map((check) => (
                <div
                  key={check.id}
                  className={`p-3 rounded-lg border ${
                    check.passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium capitalize">
                      {check.check_type.replace('_', ' ')}
                    </span>
                    {check.passed ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-600" />
                    )}
                  </div>
                  <p className="text-lg font-bold">{check.result_value}%</p>
                  <p className="text-xs text-muted-foreground">By {check.checked_by}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stage Reference */}
      <Card>
        <CardHeader>
          <CardTitle>Stage Reference Guide</CardTitle>
          <CardDescription>
            Standard operating procedures for each processing stage
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {STAGE_DEFINITIONS.map((stage, index) => {
              const Icon = stage.icon;
              return (
                <div key={stage.name} className="flex gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                  <div className={`p-2 rounded-lg bg-gradient-to-br ${stage.gradient} h-fit`}>
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground font-mono">Stage {index + 1}</span>
                      <span className="font-medium">{stage.label}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {stage.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Empty State */}
      {!selectedBatch && batches.length === 0 && !isLoading && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Cog className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No processing batches found</p>
            <p className="text-sm mt-1">Create a batch from the Processing Batches page</p>
            <Button variant="outline" className="mt-4" asChild>
              <a href="/seed-operations/batches">Go to Batches</a>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default ProcessingStages;

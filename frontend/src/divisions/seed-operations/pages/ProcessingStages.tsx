/**
 * Processing Stages Page
 * 
 * Displays the 10-stage seed processing workflow and allows tracking
 * of batches through each stage.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ProcessingBatch {
  id: string;
  batch_number: string;
  source_lot_id: string;
  source_lot_number?: string;
  crop?: string;
  variety?: string;
  initial_quantity: number;
  current_quantity: number;
  current_stage: string;
  status: string;
  stages: ProcessingStage[];
  created_at: string;
}

interface ProcessingStage {
  id: string;
  stage_name: string;
  stage_order: number;
  status: string;
  started_at?: string;
  completed_at?: string;
  input_quantity?: number;
  output_quantity?: number;
  loss_quantity?: number;
  notes?: string;
}

// Processing stage definitions with icons and descriptions
const STAGE_DEFINITIONS = [
  { 
    name: 'receiving', 
    label: 'Receiving', 
    icon: Package, 
    description: 'Initial receipt and documentation of raw seed',
    color: 'bg-blue-500'
  },
  { 
    name: 'pre_cleaning', 
    label: 'Pre-Cleaning', 
    icon: Wind, 
    description: 'Remove large debris, straw, and foreign matter',
    color: 'bg-cyan-500'
  },
  { 
    name: 'drying', 
    label: 'Drying', 
    icon: Droplets, 
    description: 'Reduce moisture content to safe storage levels',
    color: 'bg-yellow-500'
  },
  { 
    name: 'cleaning', 
    label: 'Cleaning', 
    icon: Sparkles, 
    description: 'Fine cleaning using air-screen cleaners',
    color: 'bg-green-500'
  },
  { 
    name: 'grading', 
    label: 'Grading', 
    icon: Scale, 
    description: 'Size and density separation for uniformity',
    color: 'bg-purple-500'
  },
  { 
    name: 'treating', 
    label: 'Treating', 
    icon: Shield, 
    description: 'Apply fungicide/insecticide seed treatment',
    color: 'bg-red-500'
  },
  { 
    name: 'quality_testing', 
    label: 'Quality Testing', 
    icon: ClipboardCheck, 
    description: 'Germination, purity, and moisture testing',
    color: 'bg-orange-500'
  },
  { 
    name: 'packaging', 
    label: 'Packaging', 
    icon: Box, 
    description: 'Pack into bags with proper labeling',
    color: 'bg-indigo-500'
  },
  { 
    name: 'labeling', 
    label: 'Labeling', 
    icon: Tag, 
    description: 'Apply certification tags and lot labels',
    color: 'bg-pink-500'
  },
  { 
    name: 'storage', 
    label: 'Storage/Dispatch', 
    icon: Truck, 
    description: 'Store in warehouse or dispatch to dealers',
    color: 'bg-gray-500'
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
  const [selectedBatch, setSelectedBatch] = useState<string>('');

  // Fetch batches
  const { data: batches = [], isLoading } = useQuery<ProcessingBatch[]>({
    queryKey: ['processing-batches'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/processing/batches`);
      if (!res.ok) throw new Error('Failed to fetch batches');
      return res.json();
    },
  });

  // Get selected batch details
  const currentBatch = batches.find(b => b.id === selectedBatch);

  // Calculate stage status for a batch
  const getStageStatus = (stageName: string, batch?: ProcessingBatch) => {
    if (!batch) return 'pending';
    const stage = batch.stages?.find(s => s.stage_name === stageName);
    if (stage) return stage.status;
    
    // Determine based on current stage
    const currentIndex = STAGE_DEFINITIONS.findIndex(s => s.name === batch.current_stage);
    const stageIndex = STAGE_DEFINITIONS.findIndex(s => s.name === stageName);
    
    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'in_progress';
    return 'pending';
  };

  // Calculate overall progress
  const calculateProgress = (batch?: ProcessingBatch) => {
    if (!batch) return 0;
    const currentIndex = STAGE_DEFINITIONS.findIndex(s => s.name === batch.current_stage);
    return Math.round(((currentIndex + 1) / STAGE_DEFINITIONS.length) * 100);
  };

  // Calculate yield percentage
  const calculateYield = (batch?: ProcessingBatch) => {
    if (!batch || !batch.initial_quantity) return 0;
    return Math.round((batch.current_quantity / batch.initial_quantity) * 100);
  };

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
          <SelectTrigger className="w-[280px]">
            <SelectValue placeholder="Select a batch to track" />
          </SelectTrigger>
          <SelectContent>
            {batches.map((batch) => (
              <SelectItem key={batch.id} value={batch.id}>
                {batch.batch_number} - {batch.variety || batch.crop || 'Unknown'}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Batch Summary */}
      {currentBatch && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle>{currentBatch.batch_number}</CardTitle>
                <CardDescription>
                  {currentBatch.variety || currentBatch.crop} • Source: {currentBatch.source_lot_number || currentBatch.source_lot_id}
                </CardDescription>
              </div>
              <Badge className={statusColors[currentBatch.status]}>
                {currentBatch.status.replace('_', ' ')}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-sm text-muted-foreground">Initial Quantity</p>
                <p className="text-lg font-semibold">{currentBatch.initial_quantity.toLocaleString()} kg</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Current Quantity</p>
                <p className="text-lg font-semibold">{currentBatch.current_quantity.toLocaleString()} kg</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Yield</p>
                <p className="text-lg font-semibold">{calculateYield(currentBatch)}%</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Progress</p>
                <p className="text-lg font-semibold">{calculateProgress(currentBatch)}%</p>
              </div>
            </div>
            <Progress value={calculateProgress(currentBatch)} className="h-2" />
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
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : (
            <div className="space-y-4">
              {/* Visual Pipeline */}
              <div className="flex items-center justify-between overflow-x-auto pb-4">
                {STAGE_DEFINITIONS.map((stage, index) => {
                  const status = getStageStatus(stage.name, currentBatch);
                  const Icon = stage.icon;
                  const isActive = currentBatch?.current_stage === stage.name;
                  
                  return (
                    <div key={stage.name} className="flex items-center">
                      <div className={`
                        flex flex-col items-center min-w-[80px]
                        ${isActive ? 'scale-110' : ''}
                        transition-transform
                      `}>
                        <div className={`
                          w-12 h-12 rounded-full flex items-center justify-center
                          ${status === 'completed' ? 'bg-green-100' : ''}
                          ${status === 'in_progress' ? stage.color + ' text-white' : ''}
                          ${status === 'pending' ? 'bg-gray-100' : ''}
                          ${isActive ? 'ring-2 ring-offset-2 ring-blue-500' : ''}
                        `}>
                          {status === 'completed' ? (
                            <CheckCircle2 className="h-6 w-6 text-green-600" />
                          ) : status === 'in_progress' ? (
                            <Icon className="h-6 w-6" />
                          ) : (
                            <Icon className="h-6 w-6 text-gray-400" />
                          )}
                        </div>
                        <span className={`
                          text-xs mt-2 text-center font-medium
                          ${isActive ? 'text-blue-600' : 'text-muted-foreground'}
                        `}>
                          {stage.label}
                        </span>
                      </div>
                      {index < STAGE_DEFINITIONS.length - 1 && (
                        <ArrowRight className={`
                          h-4 w-4 mx-1 flex-shrink-0
                          ${status === 'completed' ? 'text-green-500' : 'text-gray-300'}
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
                  const stageData = currentBatch?.stages?.find(s => s.stage_name === stage.name);
                  
                  return (
                    <Card key={stage.name} className={`
                      ${status === 'in_progress' ? 'border-blue-500 border-2' : ''}
                      ${status === 'completed' ? 'border-green-200' : ''}
                    `}>
                      <CardContent className="p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <div className={`p-1.5 rounded ${stage.color} bg-opacity-20`}>
                            <Icon className={`h-4 w-4 ${stage.color.replace('bg-', 'text-')}`} />
                          </div>
                          <span className="text-sm font-medium">{stage.label}</span>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">
                          {stage.description}
                        </p>
                        <div className="flex items-center gap-1">
                          {status === 'completed' && (
                            <Badge variant="outline" className="text-xs bg-green-50">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Done
                            </Badge>
                          )}
                          {status === 'in_progress' && (
                            <Badge variant="outline" className="text-xs bg-blue-50">
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
                        {stageData && stageData.output_quantity && (
                          <p className="text-xs mt-2 text-muted-foreground">
                            Output: {stageData.output_quantity.toLocaleString()} kg
                          </p>
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
                <div key={stage.name} className="flex gap-3 p-3 rounded-lg border">
                  <div className={`p-2 rounded-lg ${stage.color} bg-opacity-20 h-fit`}>
                    <Icon className={`h-5 w-5 ${stage.color.replace('bg-', 'text-')}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">Stage {index + 1}</span>
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

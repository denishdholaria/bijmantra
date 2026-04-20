/**
 * Breeding Pipeline Tracker
 * 
 * Visual workflow showing germplasm flow through breeding stages.
 * Helps breeders track material from crosses to variety release.
 * Connected to /api/v2/breeding-pipeline endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
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
  DialogFooter,
} from '@/components/ui/dialog';
import {
  GitBranch,
  ArrowRight,
  Plus,
  Search,
  ChevronRight,
  Leaf,
  FlaskConical,
  Target,
  Award,
  Clock,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client'

interface PipelineEntry {
  id: string;
  name: string;
  pedigree: string;
  currentStage: string;
  program: string;
  crop: string;
  year: number;
  status: 'active' | 'advanced' | 'dropped' | 'released';
  traits: string[];
  notes: string;
  stageHistory: { stage: string; date: string; decision: string }[];
}

const PIPELINE_STAGES = [
  { id: 'F1', name: 'F1 Crosses', icon: GitBranch, color: 'bg-purple-500' },
  { id: 'F2', name: 'F2 Population', icon: Leaf, color: 'bg-blue-500' },
  { id: 'F3-F5', name: 'F3-F5 Selection', icon: Target, color: 'bg-cyan-500' },
  { id: 'PYT', name: 'Preliminary Yield Trial', icon: FlaskConical, color: 'bg-green-500' },
  { id: 'AYT', name: 'Advanced Yield Trial', icon: TrendingUp, color: 'bg-yellow-500' },
  { id: 'MLT', name: 'Multi-Location Trial', icon: Target, color: 'bg-orange-500' },
  { id: 'RELEASE', name: 'Variety Release', icon: Award, color: 'bg-red-500' },
];

export function BreedingPipeline() {
  const queryClient = useQueryClient();
  const [selectedStage, setSelectedStage] = useState<string>('all');
  const [selectedCrop, setSelectedCrop] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntry, setSelectedEntry] = useState<PipelineEntry | null>(null);

  // Fetch entries from API
  const { data: entriesData, isLoading: isLoadingEntries, refetch: refetchEntries } = useQuery({
    queryKey: ['breeding-pipeline-entries', selectedStage, selectedCrop, searchQuery],
    queryFn: () => apiClient.breedingPipelineService.getEntries({
      stage: selectedStage !== 'all' ? selectedStage : undefined,
      crop: selectedCrop !== 'all' ? selectedCrop : undefined,
      search: searchQuery || undefined,
      limit: 100,
    }),
  });

  // Fetch statistics from API
  const { data: statsData, isLoading: isLoadingStats } = useQuery({
    queryKey: ['breeding-pipeline-stats'],
    queryFn: () => apiClient.breedingPipelineService.getStatistics(),
  });

  // Fetch crops from API
  const { data: cropsData } = useQuery({
    queryKey: ['breeding-pipeline-crops'],
    queryFn: () => apiClient.breedingPipelineService.getCrops(),
  });

  // Advance stage mutation
  const advanceMutation = useMutation({
    mutationFn: ({ entryId, decision, notes }: { entryId: string; decision: 'Advanced' | 'Dropped'; notes?: string }) =>
      apiClient.breedingPipelineService.advanceStage(entryId, decision, notes),
    onSuccess: () => {
      toast.success('Stage updated successfully');
      queryClient.invalidateQueries({ queryKey: ['breeding-pipeline'] });
      setSelectedEntry(null);
    },
    onError: () => toast.error('Failed to update stage'),
  });

  // Transform API data to component format
  const entries: PipelineEntry[] = (entriesData?.data || []).map((e: any) => ({
    id: e.id,
    name: e.name,
    pedigree: e.pedigree,
    currentStage: e.current_stage,
    program: e.program_name,
    crop: e.crop,
    year: e.year,
    status: e.status,
    traits: e.traits || [],
    notes: e.notes || '',
    stageHistory: (e.stage_history || []).map((h: any) => ({
      stage: h.stage,
      date: h.date,
      decision: h.decision,
    })),
  }));

  const statistics = statsData?.data;
  const crops = cropsData?.data || [];
  const stageCounts = statistics?.stage_counts || {};

  const getStageIndex = (stageId: string) => PIPELINE_STAGES.findIndex(s => s.id === stageId);

  const getStatusBadge = (status: PipelineEntry['status']) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'advanced': return <Badge className="bg-blue-100 text-blue-800">Advanced</Badge>;
      case 'dropped': return <Badge className="bg-red-100 text-red-800">Dropped</Badge>;
      case 'released': return <Badge className="bg-purple-100 text-purple-800">Released</Badge>;
    }
  };

  const totalActive = statistics?.active || 0;
  const totalReleased = statistics?.released || 0;
  const avgPipelineTime = statistics?.avg_years_to_release || 0;
  const isLoading = isLoadingEntries || isLoadingStats;

  if (isLoading && !entriesData) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <GitBranch className="h-6 w-6" />
            Breeding Pipeline
          </h1>
          <p className="text-muted-foreground">
            Track germplasm flow from crosses to variety release
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetchEntries()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Entry
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Leaf className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalActive}</p>
                <p className="text-sm text-muted-foreground">Active Lines</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Award className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalReleased}</p>
                <p className="text-sm text-muted-foreground">Released Varieties</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Clock className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{avgPipelineTime}</p>
                <p className="text-sm text-muted-foreground">Avg Years to Release</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Target className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{crops.length}</p>
                <p className="text-sm text-muted-foreground">Crops</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Stages</CardTitle>
          <CardDescription>Click a stage to filter entries</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between overflow-x-auto pb-4">
            {PIPELINE_STAGES.map((stage, index) => {
              const StageIcon = stage.icon;
              const count = stageCounts[stage.id] || 0;
              const isSelected = selectedStage === stage.id;
              
              return (
                <div key={stage.id} className="flex items-center">
                  <button
                    onClick={() => setSelectedStage(isSelected ? 'all' : stage.id)}
                    className={`flex flex-col items-center p-4 rounded-lg transition-all min-w-[100px] ${
                      isSelected ? 'bg-primary/10 ring-2 ring-primary' : 'hover:bg-muted'
                    }`}
                  >
                    <div className={`p-3 rounded-full ${stage.color} text-white mb-2`}>
                      <StageIcon className="h-5 w-5" />
                    </div>
                    <span className="text-sm font-medium text-center">{stage.name}</span>
                    <Badge variant="secondary" className="mt-1">{count}</Badge>
                  </button>
                  {index < PIPELINE_STAGES.length - 1 && (
                    <ArrowRight className="h-5 w-5 text-muted-foreground mx-2 flex-shrink-0" />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or pedigree..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={selectedCrop} onValueChange={setSelectedCrop}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Crops" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Crops</SelectItem>
            {crops.map((crop: string) => (
              <SelectItem key={crop} value={crop}>{crop}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {(selectedStage !== 'all' || selectedCrop !== 'all' || searchQuery) && (
          <Button variant="ghost" onClick={() => {
            setSelectedStage('all');
            setSelectedCrop('all');
            setSearchQuery('');
          }}>
            Clear Filters
          </Button>
        )}
      </div>

      {/* Entries List */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Entries ({entries.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {entries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Leaf className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No entries match your filters</p>
            </div>
          ) : (
            <div className="space-y-3">
              {entries.map(entry => {
                const stageIndex = getStageIndex(entry.currentStage);
                const progress = ((stageIndex + 1) / PIPELINE_STAGES.length) * 100;
                const currentStage = PIPELINE_STAGES.find(s => s.id === entry.currentStage);
                
                return (
                  <div
                    key={entry.id}
                    className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => setSelectedEntry(entry)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm text-muted-foreground">{entry.id}</span>
                          {getStatusBadge(entry.status)}
                        </div>
                        <h3 className="font-medium mt-1">{entry.name}</h3>
                        <p className="text-sm text-muted-foreground italic">{entry.pedigree}</p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline">{entry.crop}</Badge>
                        <p className="text-xs text-muted-foreground mt-1">{entry.program}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 mb-2">
                      {currentStage && (
                        <Badge className={`${currentStage.color} text-white`}>
                          {currentStage.name}
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        Stage {stageIndex + 1} of {PIPELINE_STAGES.length}
                      </span>
                    </div>
                    
                    <Progress value={progress} className="h-2 mb-2" />
                    
                    <div className="flex flex-wrap gap-1">
                      {entry.traits.map(trait => (
                        <Badge key={trait} variant="secondary" className="text-xs">
                          {trait}
                        </Badge>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Entry Detail Dialog */}
      <Dialog open={!!selectedEntry} onOpenChange={() => setSelectedEntry(null)}>
        <DialogContent className="max-w-2xl">
          {selectedEntry && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Leaf className="h-5 w-5" />
                  {selectedEntry.name}
                </DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Entry ID</p>
                    <p className="font-mono">{selectedEntry.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Status</p>
                    {getStatusBadge(selectedEntry.status)}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Pedigree</p>
                    <p className="italic">{selectedEntry.pedigree}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Program</p>
                    <p>{selectedEntry.program}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Crop</p>
                    <p>{selectedEntry.crop}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Year</p>
                    <p>{selectedEntry.year}</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground mb-2">Target Traits</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedEntry.traits.map(trait => (
                      <Badge key={trait} variant="secondary">{trait}</Badge>
                    ))}
                  </div>
                </div>

                {selectedEntry.notes && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Notes</p>
                    <p className="text-sm bg-muted p-3 rounded">{selectedEntry.notes}</p>
                  </div>
                )}

                <div>
                  <p className="text-sm text-muted-foreground mb-2">Stage History</p>
                  <div className="space-y-2">
                    {selectedEntry.stageHistory.map((history, index) => {
                      const stage = PIPELINE_STAGES.find(s => s.id === history.stage);
                      return (
                        <div key={index} className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${stage?.color || 'bg-gray-400'}`} />
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{stage?.name || history.stage}</span>
                              <span className="text-sm text-muted-foreground">{history.date}</span>
                            </div>
                            <Badge 
                              variant={history.decision === 'In Progress' ? 'default' : 'secondary'}
                              className="text-xs"
                            >
                              {history.decision}
                            </Badge>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setSelectedEntry(null)}>Close</Button>
                {selectedEntry.status === 'active' && (
                  <Button onClick={() => advanceMutation.mutate({ entryId: selectedEntry.id, decision: 'Advanced' })}>
                    <ChevronRight className="h-4 w-4 mr-1" />
                    Advance Stage
                  </Button>
                )}
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default BreedingPipeline;

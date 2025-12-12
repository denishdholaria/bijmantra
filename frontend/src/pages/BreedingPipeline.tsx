/**
 * Breeding Pipeline Tracker
 * 
 * Visual workflow showing germplasm flow through breeding stages.
 * Helps breeders track material from crosses to variety release.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
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
  DialogFooter,
} from '@/components/ui/dialog';
import {
  GitBranch,
  ArrowRight,
  Plus,
  Filter,
  Search,
  ChevronRight,
  Leaf,
  FlaskConical,
  Target,
  Award,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Calendar,
} from 'lucide-react';

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


// Demo data
const DEMO_ENTRIES: PipelineEntry[] = [
  {
    id: 'BM-2024-001',
    name: 'IR-HYB-2024-A',
    pedigree: 'IR64 / Swarna',
    currentStage: 'AYT',
    program: 'Rice Improvement',
    crop: 'Rice',
    year: 2024,
    status: 'active',
    traits: ['High Yield', 'Blast Resistant', 'Short Duration'],
    notes: 'Promising line with 15% yield advantage',
    stageHistory: [
      { stage: 'F1', date: '2021-06', decision: 'Advanced' },
      { stage: 'F2', date: '2021-11', decision: 'Advanced' },
      { stage: 'F3-F5', date: '2022-06', decision: 'Advanced' },
      { stage: 'PYT', date: '2023-06', decision: 'Advanced' },
      { stage: 'AYT', date: '2024-06', decision: 'In Progress' },
    ],
  },
  {
    id: 'BM-2024-002',
    name: 'WH-DUR-2024-B',
    pedigree: 'HD2967 / PBW343',
    currentStage: 'MLT',
    program: 'Wheat Improvement',
    crop: 'Wheat',
    year: 2024,
    status: 'active',
    traits: ['Rust Resistant', 'Heat Tolerant', 'High Protein'],
    notes: 'Excellent rust resistance, testing in 5 locations',
    stageHistory: [
      { stage: 'F1', date: '2020-11', decision: 'Advanced' },
      { stage: 'F2', date: '2021-04', decision: 'Advanced' },
      { stage: 'F3-F5', date: '2021-11', decision: 'Advanced' },
      { stage: 'PYT', date: '2022-11', decision: 'Advanced' },
      { stage: 'AYT', date: '2023-11', decision: 'Advanced' },
      { stage: 'MLT', date: '2024-11', decision: 'In Progress' },
    ],
  },
  {
    id: 'BM-2024-003',
    name: 'MZ-QPM-2024-C',
    pedigree: 'CML144 / CML159',
    currentStage: 'PYT',
    program: 'Maize Improvement',
    crop: 'Maize',
    year: 2024,
    status: 'active',
    traits: ['QPM', 'Drought Tolerant', 'Early Maturity'],
    notes: 'Quality Protein Maize with good combining ability',
    stageHistory: [
      { stage: 'F1', date: '2022-06', decision: 'Advanced' },
      { stage: 'F2', date: '2022-11', decision: 'Advanced' },
      { stage: 'F3-F5', date: '2023-06', decision: 'Advanced' },
      { stage: 'PYT', date: '2024-06', decision: 'In Progress' },
    ],
  },
  {
    id: 'BM-2023-015',
    name: 'IR-SUB-2023-D',
    pedigree: 'Swarna-Sub1 / FR13A',
    currentStage: 'RELEASE',
    program: 'Rice Improvement',
    crop: 'Rice',
    year: 2023,
    status: 'released',
    traits: ['Submergence Tolerant', 'High Yield', 'Good Grain Quality'],
    notes: 'Released as "Bijmantra Sub-1" in 2024',
    stageHistory: [
      { stage: 'F1', date: '2018-06', decision: 'Advanced' },
      { stage: 'F2', date: '2018-11', decision: 'Advanced' },
      { stage: 'F3-F5', date: '2019-06', decision: 'Advanced' },
      { stage: 'PYT', date: '2020-06', decision: 'Advanced' },
      { stage: 'AYT', date: '2021-06', decision: 'Advanced' },
      { stage: 'MLT', date: '2022-06', decision: 'Advanced' },
      { stage: 'RELEASE', date: '2024-01', decision: 'Released' },
    ],
  },
  {
    id: 'BM-2024-004',
    name: 'SB-OIL-2024-E',
    pedigree: 'JS335 / NRC37',
    currentStage: 'F3-F5',
    program: 'Soybean Improvement',
    crop: 'Soybean',
    year: 2024,
    status: 'active',
    traits: ['High Oil', 'Pod Shattering Resistant'],
    notes: 'Selection for oil content ongoing',
    stageHistory: [
      { stage: 'F1', date: '2023-06', decision: 'Advanced' },
      { stage: 'F2', date: '2023-11', decision: 'Advanced' },
      { stage: 'F3-F5', date: '2024-06', decision: 'In Progress' },
    ],
  },
];


export function BreedingPipeline() {
  const [entries, setEntries] = useState<PipelineEntry[]>(DEMO_ENTRIES);
  const [selectedStage, setSelectedStage] = useState<string>('all');
  const [selectedCrop, setSelectedCrop] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntry, setSelectedEntry] = useState<PipelineEntry | null>(null);

  // Calculate stage counts
  const stageCounts = PIPELINE_STAGES.reduce((acc, stage) => {
    acc[stage.id] = entries.filter(e => e.currentStage === stage.id && e.status === 'active').length;
    return acc;
  }, {} as Record<string, number>);

  // Filter entries
  const filteredEntries = entries.filter(entry => {
    if (selectedStage !== 'all' && entry.currentStage !== selectedStage) return false;
    if (selectedCrop !== 'all' && entry.crop !== selectedCrop) return false;
    if (searchQuery && !entry.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !entry.pedigree.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  // Get unique crops
  const crops = [...new Set(entries.map(e => e.crop))];

  const getStageIndex = (stageId: string) => PIPELINE_STAGES.findIndex(s => s.id === stageId);

  const getStatusBadge = (status: PipelineEntry['status']) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'advanced': return <Badge className="bg-blue-100 text-blue-800">Advanced</Badge>;
      case 'dropped': return <Badge className="bg-red-100 text-red-800">Dropped</Badge>;
      case 'released': return <Badge className="bg-purple-100 text-purple-800">Released</Badge>;
    }
  };

  const totalActive = entries.filter(e => e.status === 'active').length;
  const totalReleased = entries.filter(e => e.status === 'released').length;
  const avgPipelineTime = 5.2; // years (calculated from demo data)

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
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Entry
        </Button>
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
            {crops.map(crop => (
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
          <CardTitle>Pipeline Entries ({filteredEntries.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredEntries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Leaf className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No entries match your filters</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredEntries.map(entry => {
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
                {/* Basic Info */}
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

                {/* Traits */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Target Traits</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedEntry.traits.map(trait => (
                      <Badge key={trait} variant="secondary">{trait}</Badge>
                    ))}
                  </div>
                </div>

                {/* Notes */}
                {selectedEntry.notes && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Notes</p>
                    <p className="text-sm bg-muted p-3 rounded">{selectedEntry.notes}</p>
                  </div>
                )}

                {/* Stage History */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Stage History</p>
                  <div className="space-y-2">
                    {selectedEntry.stageHistory.map((history, index) => {
                      const stage = PIPELINE_STAGES.find(s => s.id === history.stage);
                      const isLast = index === selectedEntry.stageHistory.length - 1;
                      
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
                <Button variant="outline" onClick={() => setSelectedEntry(null)}>
                  Close
                </Button>
                <Button>
                  <ChevronRight className="h-4 w-4 mr-1" />
                  Advance Stage
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default BreedingPipeline;

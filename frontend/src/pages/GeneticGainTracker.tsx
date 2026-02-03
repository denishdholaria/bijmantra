/**
 * Genetic Gain Tracker Page
 * 
 * Track breeding program progress, calculate genetic gain over cycles,
 * and project future improvements.
 * Connects to /api/v2/genetic-gain endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  TrendingUp,
  Plus,
  BarChart3,
  Target,
  Calendar,
  Award,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface BreedingProgram {
  id: string;
  name: string;
  crop: string;
  trait: string;
  start_year: number;
  cycles: CycleData[];
  releases: ReleaseData[];
}

interface CycleData {
  cycle: number;
  year: number;
  mean: number;
  variance: number;
  n_entries: number;
  selection_intensity?: number;
}

interface ReleaseData {
  variety_name: string;
  year: number;
  value: number;
}

import { GeneticGainResult } from '@/lib/api-client';

export function GeneticGainTracker() {
  const [selectedProgram, setSelectedProgram] = useState<string | null>(null);
  const [showNewProgram, setShowNewProgram] = useState(false);
  const [showNewCycle, setShowNewCycle] = useState(false);
  const [newProgram, setNewProgram] = useState({ name: '', crop: '', trait: '' });
  const [newCycle, setNewCycle] = useState({ year: new Date().getFullYear(), mean: 0, variance: 0, n_entries: 100 });
  const queryClient = useQueryClient();

  // Fetch programs
  const { data: programsResponse, isLoading: programsLoading } = useQuery({
    queryKey: ['genetic-gain-programs'],
    queryFn: () => apiClient.geneticGainService.getPrograms(),
  });

  const programs = programsResponse?.data || [];

  // Get selected program details
  const program = programs.find(p => p.id === selectedProgram) || programs[0];

  // Calculate genetic gain
  const { data: gainResponse } = useQuery({
    queryKey: ['genetic-gain', program?.id],
    queryFn: () => apiClient.geneticGainService.calculateGain(program!.id),
    enabled: !!program,
  });

  const gainResult = gainResponse?.data;

  // Create program mutation
  const createProgramMutation = useMutation({
    mutationFn: () => apiClient.geneticGainService.createProgram({
      name: newProgram.name,
      crop: newProgram.crop,
      trait: newProgram.trait,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['genetic-gain-programs'] });
      setShowNewProgram(false);
      setNewProgram({ name: '', crop: '', trait: '' });
    },
  });

  // Record cycle mutation
  const recordCycleMutation = useMutation({
    mutationFn: () => apiClient.geneticGainService.recordCycle(program!.id, newCycle),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['genetic-gain-programs'] });
      setShowNewCycle(false);
      setNewCycle({ year: new Date().getFullYear(), mean: 0, variance: 0, n_entries: 100 });
    },
  });

  const getGainTrend = (gain: number) => {
    if (gain > 0) return { icon: ArrowUpRight, color: 'text-green-600', bg: 'bg-green-100' };
    if (gain < 0) return { icon: ArrowDownRight, color: 'text-red-600', bg: 'bg-red-100' };
    return { icon: Minus, color: 'text-gray-600', bg: 'bg-gray-100' };
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <TrendingUp className="h-6 w-6" />
            Genetic Gain Tracker
          </h1>
          <p className="text-muted-foreground">
            Track breeding program progress and calculate genetic gain over cycles
          </p>
        </div>
        <Dialog open={showNewProgram} onOpenChange={setShowNewProgram}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Program
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Breeding Program</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Program Name</Label>
                <Input
                  value={newProgram.name}
                  onChange={(e) => setNewProgram({ ...newProgram, name: e.target.value })}
                  placeholder="e.g., Rice Yield Improvement"
                />
              </div>
              <div>
                <Label>Crop</Label>
                <Input
                  value={newProgram.crop}
                  onChange={(e) => setNewProgram({ ...newProgram, crop: e.target.value })}
                  placeholder="e.g., Rice"
                />
              </div>
              <div>
                <Label>Target Trait</Label>
                <Input
                  value={newProgram.trait}
                  onChange={(e) => setNewProgram({ ...newProgram, trait: e.target.value })}
                  placeholder="e.g., Grain Yield (t/ha)"
                />
              </div>
              <Button onClick={() => createProgramMutation.mutate()} className="w-full">
                Create Program
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Program Selector */}
      <div className="flex gap-2 flex-wrap">
        {programs.map(p => (
          <Button
            key={p.id}
            variant={selectedProgram === p.id || (!selectedProgram && p.id === programs[0]?.id) ? 'default' : 'outline'}
            onClick={() => setSelectedProgram(p.id)}
          >
            {p.name}
          </Button>
        ))}
      </div>


      {program && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${gainResult ? getGainTrend(gainResult.gain_per_cycle).bg : 'bg-gray-100'}`}>
                    <TrendingUp className={`h-5 w-5 ${gainResult ? getGainTrend(gainResult.gain_per_cycle).color : 'text-gray-600'}`} />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {gainResult ? `${gainResult.gain_per_cycle > 0 ? '+' : ''}${gainResult.gain_per_cycle.toFixed(2)}` : '-'}
                    </p>
                    <p className="text-xs text-muted-foreground">Gain per Cycle</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {gainResult ? `${(gainResult.gain_per_cycle / (program.cycles[0]?.mean_value || 1) * 100).toFixed(1)}%` : '-'}
                    </p>
                    <p className="text-xs text-muted-foreground">Percent Gain</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Calendar className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {gainResult ? `${gainResult.gain_per_year > 0 ? '+' : ''}${gainResult.gain_per_year.toFixed(3)}/yr` : '-'}
                    </p>
                    <p className="text-xs text-muted-foreground">Annual Gain</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-100 rounded-lg">
                    <Award className="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{program.releases.length}</p>
                    <p className="text-xs text-muted-foreground">Varieties Released</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Cycle History */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Breeding Cycles</span>
                  <Dialog open={showNewCycle} onOpenChange={setShowNewCycle}>
                    <DialogTrigger asChild>
                      <Button size="sm" variant="outline">
                        <Plus className="h-4 w-4 mr-1" />
                        Record Cycle
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Record Cycle Data</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label>Year</Label>
                          <Input
                            type="number"
                            value={newCycle.year}
                            onChange={(e) => setNewCycle({ ...newCycle, year: parseInt(e.target.value) })}
                          />
                        </div>
                        <div>
                          <Label>Mean Value</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={newCycle.mean}
                            onChange={(e) => setNewCycle({ ...newCycle, mean: parseFloat(e.target.value) })}
                          />
                        </div>
                        <div>
                          <Label>Variance</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={newCycle.variance}
                            onChange={(e) => setNewCycle({ ...newCycle, variance: parseFloat(e.target.value) })}
                          />
                        </div>
                        <div>
                          <Label>Number of Entries</Label>
                          <Input
                            type="number"
                            value={newCycle.n_entries}
                            onChange={(e) => setNewCycle({ ...newCycle, n_entries: parseInt(e.target.value) })}
                          />
                        </div>
                        <Button onClick={() => recordCycleMutation.mutate()} className="w-full">
                          Record Cycle
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </CardTitle>
                <CardDescription>{program.trait}</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cycle</TableHead>
                      <TableHead>Year</TableHead>
                      <TableHead className="text-right">Mean</TableHead>
                      <TableHead className="text-right">Var</TableHead>
                      <TableHead className="text-right">N</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {program.cycles.map((cycle, idx) => {
                      const prevMean = idx > 0 ? program.cycles[idx - 1].mean_value : cycle.mean_value;
                      const change = cycle.mean_value - prevMean;
                      return (
                        <TableRow key={cycle.cycle}>
                          <TableCell>C{cycle.cycle}</TableCell>
                          <TableCell>{cycle.year}</TableCell>
                          <TableCell className="text-right font-mono">
                            {cycle.mean_value.toFixed(2)}
                            {idx > 0 && (
                              <span className={`ml-1 text-xs ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                ({change >= 0 ? '+' : ''}{change.toFixed(2)})
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-right font-mono">{Math.pow(cycle.std_dev, 2).toFixed(2)}</TableCell>
                          <TableCell className="text-right">{cycle.n_entries}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Variety Releases */}
            <Card>
              <CardHeader>
                <CardTitle>Variety Releases</CardTitle>
                <CardDescription>Released varieties from this program</CardDescription>
              </CardHeader>
              <CardContent>
                {program.releases.length > 0 ? (
                  <div className="space-y-3">
                    {program.releases.map((release, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <Award className="h-5 w-5 text-amber-500" />
                          <div>
                            <p className="font-medium">{release.variety_name}</p>
                            <p className="text-sm text-muted-foreground">{release.year}</p>
                          </div>
                        </div>
                        <Badge variant="outline" className="font-mono">
                          {release.trait_value.toFixed(2)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Award className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No varieties released yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Progress Visualization */}
          <Card>
            <CardHeader>
              <CardTitle>Progress Over Time</CardTitle>
              <CardDescription>Visual representation of genetic gain</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-end gap-2">
                {program.cycles.map((cycle, idx) => {
                  const minMean = Math.min(...program.cycles.map(c => c.mean_value));
                  const maxMean = Math.max(...program.cycles.map(c => c.mean_value));
                  const range = maxMean - minMean || 1;
                  const height = ((cycle.mean_value - minMean) / range) * 100 + 20;
                  
                  return (
                    <div key={cycle.cycle} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-gradient-to-t from-green-500 to-green-300 rounded-t-md transition-all hover:from-green-600 hover:to-green-400"
                        style={{ height: `${height}%` }}
                        title={`${cycle.year}: ${cycle.mean_value.toFixed(2)}`}
                      />
                      <p className="text-xs mt-2 text-muted-foreground">{cycle.year}</p>
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between mt-4 text-sm text-muted-foreground">
                <span>Start: {program.cycles[0]?.mean_value.toFixed(2)}</span>
                <span>Current: {program.cycles[program.cycles.length - 1]?.mean_value.toFixed(2)}</span>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

export default GeneticGainTracker;

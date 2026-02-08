/**
 * Breeding Value Calculator Page
 * 
 * Calculate BLUP, GBLUP, and predict cross performance.
 * Connects to /api/v2/breeding-value endpoints.
 */

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Calculator,
  Dna,
  TrendingUp,
  Target,
  Users,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Play,
  Info,
  Award,
} from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';

interface Individual {
  id: string;
  name: string;
  ebv: number;
  accuracy: number;
  rank?: number;
}

interface CrossPrediction {
  parent1: string;
  parent2: string;
  predicted_mean: number;
  predicted_variance: number;
  probability_superior: number;
}

interface BLUPResult {
  individuals: Individual[];
  heritability: number;
  genetic_variance: number;
  residual_variance: number;
}

export function BreedingValueCalculator() {
  const [activeTab, setActiveTab] = useState('blup');
  const [trait, setTrait] = useState('yield');
  const [parent1, setParent1] = useState('');
  const [parent2, setParent2] = useState('');
  const [selectionIntensity, setSelectionIntensity] = useState(20);
  const [blupResult, setBLUPResult] = useState<BLUPResult | null>(null);
  const [crossPrediction, setCrossPrediction] = useState<CrossPrediction | null>(null);

  // New State for Real Data
  const [useRealData, setUseRealData] = useState(false);
  const [selectedStudyIds, setSelectedStudyIds] = useState<string[]>([]);
  const [realTraitId, setRealTraitId] = useState<string>("");

  // Fetch Studies for Real Data
  const { data: studiesData } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.studyService.getStudies(0, 50),
    enabled: useRealData,
    staleTime: 1000 * 60 * 5
  });

  // Fetch Traits for Real Data
  const { data: traitsData } = useQuery({
    queryKey: ['traits'],
    queryFn: () => apiClient.observationService.getObservationVariables(0, 50),
    enabled: useRealData,
    staleTime: 1000 * 60 * 60
  });

  const studies = studiesData?.result?.data || [];
  const realTraits = traitsData?.result?.data || [];

  // Fetch individuals with EBVs
  const { data: individualsData, isLoading } = useQuery({
    queryKey: ['breeding-values', trait],
    queryFn: () => apiClient.breedingValueService.getIndividuals(trait),
  });

  const individuals: Individual[] = individualsData?.data || [];

  // BLUP calculation
  const blupMutation = useMutation({
    mutationFn: async () => {
      if (useRealData) {
         if (selectedStudyIds.length === 0 || !realTraitId) {
             throw new Error("Please select at least one study and a trait");
         }
         return apiClient.breedingValueService.estimateFromDb({
             study_db_ids: selectedStudyIds,
             trait_db_id: realTraitId
         });
      } else {
         return apiClient.breedingValueService.runBLUP({ trait });
      }
    },
    onSuccess: (data) => {
      // Map result to match UI expectation if coming from DB
      if (useRealData) {
          // Transformation needed if backend returns different structure
          // Current backend returns: { trait, heritability_used, method, breeding_values: [...] }
          // UI expects: { individuals: [...], heritability, genetic_variance, residual_variance }
          
          const mappedData: BLUPResult = {
              individuals: data.breeding_values.map((bv: any) => ({
                  id: bv.individual_id,
                  name: bv.individual_id,
                  ebv: bv.ebv,
                  accuracy: bv.reliability || 0.5,
                  rank: bv.rank
              })),
              heritability: data.heritability_used,
              genetic_variance: 0, // Not returned yet
              residual_variance: 0 // Not returned yet
          };
          setBLUPResult(mappedData);
      } else {
          setBLUPResult(data);
      }
      toast.success('BLUP analysis completed');
    },
    onError: (err: any) => toast.error(err.message || 'BLUP analysis failed'),
  });

  // GBLUP calculation
  const gblupMutation = useMutation({
    mutationFn: () => apiClient.breedingValueService.runGBLUP({ trait }),
    onSuccess: (data) => {
      setBLUPResult(data);
      toast.success('GBLUP analysis completed');
    },
    onError: () => toast.error('GBLUP analysis failed'),
  });

  // Cross prediction
  const predictCrossMutation = useMutation({
    mutationFn: () => apiClient.breedingValueService.predictCross({ parent1, parent2, trait }),
    onSuccess: (data) => {
      setCrossPrediction(data);
      toast.success('Cross prediction completed');
    },
    onError: () => toast.error('Cross prediction failed'),
  });

  const getEBVTrend = (ebv: number) => {
    if (ebv > 0.5) return { icon: ArrowUpRight, color: 'text-green-600', bg: 'bg-green-100' };
    if (ebv < -0.5) return { icon: ArrowDownRight, color: 'text-red-600', bg: 'bg-red-100' };
    return { icon: Minus, color: 'text-gray-600', bg: 'bg-gray-100' };
  };

  const getAccuracyColor = (acc: number) => {
    if (acc >= 0.8) return 'text-green-600';
    if (acc >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Calculate selection candidates
  const selectionThreshold = Math.ceil(individuals.length * (selectionIntensity / 100));
  const selectedIndividuals = [...individuals].sort((a, b) => b.ebv - a.ebv).slice(0, selectionThreshold);
  const avgSelectedEBV = selectedIndividuals.length > 0
    ? selectedIndividuals.reduce((sum, i) => sum + i.ebv, 0) / selectedIndividuals.length
    : 0;

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-12 w-full max-w-xl" />
        <div className="grid md:grid-cols-3 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64 md:col-span-2" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Calculator className="h-6 w-6" />
          Breeding Value Calculator
        </h1>
        <p className="text-muted-foreground">
          Calculate BLUP/GBLUP breeding values and predict cross performance
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-4 w-full max-w-xl">
          <TabsTrigger value="blup">
            <Calculator className="h-4 w-4 mr-2" />
            BLUP
          </TabsTrigger>
          <TabsTrigger value="gblup">
            <Dna className="h-4 w-4 mr-2" />
            GBLUP
          </TabsTrigger>
          <TabsTrigger value="predict">
            <TrendingUp className="h-4 w-4 mr-2" />
            Predict Cross
          </TabsTrigger>
          <TabsTrigger value="select">
            <Target className="h-4 w-4 mr-2" />
            Selection
          </TabsTrigger>
        </TabsList>

        {/* BLUP Tab */}
        <TabsContent value="blup">
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="md:col-span-1">
              <CardHeader>
                <CardTitle>BLUP Analysis</CardTitle>
                <CardDescription>
                  Best Linear Unbiased Prediction using pedigree relationships
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 text-blue-500 mt-0.5" />
                    <p className="text-sm text-blue-800 dark:text-blue-300">
                      BLUP uses pedigree information to estimate breeding values. 
                      Accuracy depends on the number of relatives with phenotypes.
                    </p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 pb-2">
                       <Switch 
                           id="data-source-mode" 
                           checked={useRealData}
                           onCheckedChange={setUseRealData}
                       />
                       <Label htmlFor="data-source-mode">Use Database Observations</Label>
                  </div>
                
                 {!useRealData ? (
                  <div>
                    <Label>Target Trait (Simulated)</Label>
                    <Select value={trait} onValueChange={setTrait}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="yield">Grain Yield</SelectItem>
                        <SelectItem value="protein">Protein Content</SelectItem>
                        <SelectItem value="height">Plant Height</SelectItem>
                        <SelectItem value="maturity">Days to Maturity</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                 ) : (
                    <div className="space-y-4">
                         <div>
                            <Label className="mb-2 block">Select Environment (Studies)</Label>
                            <ScrollArea className="h-[150px] w-full rounded-md border p-4">
                                <div className="space-y-2">
                                    {studies.map((study: any) => (
                                        <div key={study.studyDbId} className="flex items-center space-x-2">
                                            <Checkbox 
                                                id={study.studyDbId} 
                                                checked={selectedStudyIds.includes(study.studyDbId)}
                                                onCheckedChange={(checked) => {
                                                    if (checked) {
                                                        setSelectedStudyIds([...selectedStudyIds, study.studyDbId]);
                                                    } else {
                                                        setSelectedStudyIds(selectedStudyIds.filter(id => id !== study.studyDbId));
                                                    }
                                                }}
                                            />
                                            <label
                                                htmlFor={study.studyDbId}
                                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                            >
                                                {study.studyName}
                                            </label>
                                        </div>
                                    ))}
                                    {studies.length === 0 && <p className="text-sm text-muted-foreground">No studies found.</p>}
                                </div>
                            </ScrollArea>
                        </div>
                        <div>
                            <Label>Target Trait (Variable)</Label>
                            <Select value={realTraitId} onValueChange={setRealTraitId}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select a trait" />
                                </SelectTrigger>
                                <SelectContent>
                                    {realTraits.map((t: any) => (
                                        <SelectItem key={t.observationVariableDbId} value={t.observationVariableDbId}>
                                            {t.observationVariableName}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                 )}
                </div>

                <Button 
                  onClick={() => blupMutation.mutate()} 
                  disabled={blupMutation.isPending}
                  className="w-full"
                >
                  <Play className="h-4 w-4 mr-2" />
                  {blupMutation.isPending ? 'Calculating...' : 'Run BLUP'}
                </Button>

                {blupResult && (
                  <div className="space-y-2 pt-4 border-t">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Heritability (h²)</span>
                      <span className="font-mono">{blupResult.heritability.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Genetic Variance</span>
                      <span className="font-mono">{blupResult.genetic_variance.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Residual Variance</span>
                      <span className="font-mono">{blupResult.residual_variance.toFixed(3)}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Estimated Breeding Values</CardTitle>
                <CardDescription>Ranked by EBV for {trait}</CardDescription>
              </CardHeader>
              <CardContent>
                {individuals.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Calculator className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No breeding value data available</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Rank</TableHead>
                        <TableHead>ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead className="text-right">EBV</TableHead>
                        <TableHead className="text-right">Accuracy</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(blupResult?.individuals || individuals).map((ind, idx) => {
                        const trend = getEBVTrend(ind.ebv);
                        const TrendIcon = trend.icon;
                        return (
                          <TableRow key={ind.id}>
                            <TableCell>
                              {idx < 3 ? (
                                <Badge className="bg-amber-100 text-amber-800">
                                  <Award className="h-3 w-3 mr-1" />
                                  {idx + 1}
                                </Badge>
                              ) : (
                                <span className="text-muted-foreground">{idx + 1}</span>
                              )}
                            </TableCell>
                            <TableCell className="font-mono">{ind.id}</TableCell>
                            <TableCell className="font-medium">{ind.name}</TableCell>
                            <TableCell className="text-right">
                              <div className="flex items-center justify-end gap-1">
                                <span className={`font-mono ${trend.color}`}>
                                  {ind.ebv > 0 ? '+' : ''}{ind.ebv.toFixed(2)}
                                </span>
                                <TrendIcon className={`h-4 w-4 ${trend.color}`} />
                              </div>
                            </TableCell>
                            <TableCell className={`text-right font-mono ${getAccuracyColor(ind.accuracy)}`}>
                              {(ind.accuracy * 100).toFixed(0)}%
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* GBLUP Tab */}
        <TabsContent value="gblup">
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="md:col-span-1">
              <CardHeader>
                <CardTitle>GBLUP Analysis</CardTitle>
                <CardDescription>
                  Genomic BLUP using marker-based relationships
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Dna className="h-4 w-4 text-purple-500 mt-0.5" />
                    <p className="text-sm text-purple-800 dark:text-purple-300">
                      GBLUP uses genomic markers to build a relationship matrix, 
                      providing higher accuracy than pedigree-based BLUP.
                    </p>
                  </div>
                </div>
                
                <div>
                  <Label>Target Trait</Label>
                  <Select value={trait} onValueChange={setTrait}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="yield">Grain Yield</SelectItem>
                      <SelectItem value="protein">Protein Content</SelectItem>
                      <SelectItem value="height">Plant Height</SelectItem>
                      <SelectItem value="maturity">Days to Maturity</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={() => gblupMutation.mutate()} 
                  disabled={gblupMutation.isPending}
                  className="w-full"
                >
                  <Play className="h-4 w-4 mr-2" />
                  {gblupMutation.isPending ? 'Calculating...' : 'Run GBLUP'}
                </Button>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Genomic Breeding Values</CardTitle>
                <CardDescription>Higher accuracy with genomic data</CardDescription>
              </CardHeader>
              <CardContent>
                {individuals.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Dna className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No genomic data available</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Rank</TableHead>
                        <TableHead>ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead className="text-right">GEBV</TableHead>
                        <TableHead className="text-right">Accuracy</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(blupResult?.individuals || individuals).map((ind, idx) => {
                        const trend = getEBVTrend(ind.ebv);
                        const TrendIcon = trend.icon;
                        return (
                          <TableRow key={ind.id}>
                            <TableCell>
                              {idx < 3 ? (
                                <Badge className="bg-purple-100 text-purple-800">
                                  <Award className="h-3 w-3 mr-1" />
                                  {idx + 1}
                                </Badge>
                              ) : (
                                <span className="text-muted-foreground">{idx + 1}</span>
                              )}
                            </TableCell>
                            <TableCell className="font-mono">{ind.id}</TableCell>
                            <TableCell className="font-medium">{ind.name}</TableCell>
                            <TableCell className="text-right">
                              <div className="flex items-center justify-end gap-1">
                                <span className={`font-mono ${trend.color}`}>
                                  {ind.ebv > 0 ? '+' : ''}{ind.ebv.toFixed(2)}
                                </span>
                                <TrendIcon className={`h-4 w-4 ${trend.color}`} />
                              </div>
                            </TableCell>
                            <TableCell className={`text-right font-mono ${getAccuracyColor(ind.accuracy)}`}>
                              {(ind.accuracy * 100).toFixed(0)}%
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Predict Cross Tab */}
        <TabsContent value="predict">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Cross Prediction</CardTitle>
                <CardDescription>
                  Predict progeny performance from parent EBVs
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Parent 1</Label>
                  <Select value={parent1} onValueChange={setParent1}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select parent" />
                    </SelectTrigger>
                    <SelectContent>
                      {individuals.map(ind => (
                        <SelectItem key={ind.id} value={ind.id}>
                          {ind.name} (EBV: {ind.ebv.toFixed(2)})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Parent 2</Label>
                  <Select value={parent2} onValueChange={setParent2}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select parent" />
                    </SelectTrigger>
                    <SelectContent>
                      {individuals.filter(i => i.id !== parent1).map(ind => (
                        <SelectItem key={ind.id} value={ind.id}>
                          {ind.name} (EBV: {ind.ebv.toFixed(2)})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={() => predictCrossMutation.mutate()} 
                  disabled={!parent1 || !parent2 || predictCrossMutation.isPending}
                  className="w-full"
                >
                  <TrendingUp className="h-4 w-4 mr-2" />
                  {predictCrossMutation.isPending ? 'Predicting...' : 'Predict Cross'}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Prediction Results</CardTitle>
                <CardDescription>Expected progeny performance</CardDescription>
              </CardHeader>
              <CardContent>
                {crossPrediction ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg text-center">
                      <p className="text-sm text-muted-foreground">Predicted Mean EBV</p>
                      <p className="text-3xl font-bold text-green-700 dark:text-green-400">
                        {crossPrediction.predicted_mean > 0 ? '+' : ''}
                        {crossPrediction.predicted_mean.toFixed(2)}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 border rounded-lg">
                        <p className="text-xs text-muted-foreground">Predicted Variance</p>
                        <p className="text-lg font-mono">{crossPrediction.predicted_variance.toFixed(3)}</p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <p className="text-xs text-muted-foreground">P(Superior)</p>
                        <p className="text-lg font-mono">{(crossPrediction.probability_superior * 100).toFixed(0)}%</p>
                      </div>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-slate-800 rounded-lg">
                      <p className="text-sm font-medium mb-2">Cross: {crossPrediction.parent1} × {crossPrediction.parent2}</p>
                      <p className="text-xs text-muted-foreground">
                        This cross has a {(crossPrediction.probability_superior * 100).toFixed(0)}% probability 
                        of producing progeny superior to the population mean.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Users className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Select parents and predict cross performance</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Selection Tab */}
        <TabsContent value="select">
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="md:col-span-1">
              <CardHeader>
                <CardTitle>Selection Settings</CardTitle>
                <CardDescription>Configure selection intensity</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Selection Intensity (%)</Label>
                  <div className="flex items-center gap-4">
                    <Input
                      type="number"
                      min="1"
                      max="100"
                      value={selectionIntensity}
                      onChange={(e) => setSelectionIntensity(parseInt(e.target.value) || 20)}
                      className="w-24"
                    />
                    <span className="text-sm text-muted-foreground">
                      Top {selectionThreshold} of {individuals.length}
                    </span>
                  </div>
                </div>

                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-sm text-muted-foreground">Average EBV of Selected</p>
                  <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                    {avgSelectedEBV > 0 ? '+' : ''}{avgSelectedEBV.toFixed(2)}
                  </p>
                </div>

                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-sm text-muted-foreground">Selection Differential</p>
                  <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                    {avgSelectedEBV.toFixed(2)}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Expected genetic gain per generation
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Selection Candidates</CardTitle>
                <CardDescription>
                  Top {selectionIntensity}% selected (highlighted in green)
                </CardDescription>
              </CardHeader>
              <CardContent>
                {individuals.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Target className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No candidates available</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Rank</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead className="text-right">EBV</TableHead>
                        <TableHead className="text-right">Accuracy</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {[...individuals].sort((a, b) => b.ebv - a.ebv).map((ind, idx) => {
                        const isSelected = idx < selectionThreshold;
                        return (
                          <TableRow key={ind.id} className={isSelected ? 'bg-green-50' : ''}>
                            <TableCell>{idx + 1}</TableCell>
                            <TableCell className="font-medium">{ind.name}</TableCell>
                            <TableCell className="text-right font-mono">
                              {ind.ebv > 0 ? '+' : ''}{ind.ebv.toFixed(2)}
                            </TableCell>
                            <TableCell className="text-right font-mono">
                              {(ind.accuracy * 100).toFixed(0)}%
                            </TableCell>
                            <TableCell>
                              {isSelected ? (
                                <Badge className="bg-green-100 text-green-800">Selected</Badge>
                              ) : (
                                <Badge variant="outline">Not Selected</Badge>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default BreedingValueCalculator;

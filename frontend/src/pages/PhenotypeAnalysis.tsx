/**
 * Phenotype Analysis Page
 * 
 * Statistical analysis of phenotypic data including heritability,
 * genetic correlation, and selection response.
 * Connects to /api/v2/phenotype endpoints.
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart3,
  Calculator,
  TrendingUp,
  Percent,
  Target,
  ArrowUpRight,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface StatsResult {
  trait_name: string;
  n: number;
  mean: number;
  std: number;
  min: number;
  max: number;
  range: number;
  cv: number;
}

interface HeritabilityResult {
  trait_name: string;
  h2_broad: number;
  vg: number;
  ve: number;
  vp: number;
  interpretation: string;
}

interface SelectionResult {
  trait_name: string;
  selection_intensity: number;
  response: number;
  new_mean: number;
  percent_gain: number;
}

export function PhenotypeAnalysis() {
  const [activeTab, setActiveTab] = useState('stats');
  
  // Stats state
  const [statsValues, setStatsValues] = useState('4.5, 5.2, 4.8, 5.1, 4.9, 5.3, 4.7, 5.0');
  const [statsTraitName, setStatsTraitName] = useState('Yield');
  const [statsResult, setStatsResult] = useState<StatsResult | null>(null);
  
  // Heritability state
  const [heritabilityData, setHeritabilityData] = useState(`G1: 4.5, 4.8, 4.6
G2: 5.2, 5.0, 5.3
G3: 4.1, 4.3, 4.0
G4: 5.5, 5.4, 5.6`);
  const [heritabilityTraitName, setHeritabilityTraitName] = useState('Yield');
  const [heritabilityResult, setHeritabilityResult] = useState<HeritabilityResult | null>(null);
  
  // Selection response state
  const [selHeritability, setSelHeritability] = useState('0.6');
  const [selStd, setSelStd] = useState('0.8');
  const [selProportion, setSelProportion] = useState('0.1');
  const [selMean, setSelMean] = useState('5.0');
  const [selTraitName, setSelTraitName] = useState('Yield');
  const [selectionResult, setSelectionResult] = useState<SelectionResult | null>(null);
  
  // Correlation state
  const [corrTrait1, setCorrTrait1] = useState('G1: 4.5, G2: 5.2, G3: 4.1, G4: 5.5');
  const [corrTrait2, setCorrTrait2] = useState('G1: 12.3, G2: 14.1, G3: 11.8, G4: 15.2');
  const [corrTrait1Name, setCorrTrait1Name] = useState('Yield');
  const [corrTrait2Name, setCorrTrait2Name] = useState('Plant Height');
  const [correlationResult, setCorrelationResult] = useState<{ correlation: number; interpretation: string } | null>(null);

  // Stats mutation
  const statsMutation = useMutation({
    mutationFn: async () => {
      const values = statsValues.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v));
      const res = await fetch(`${API_BASE}/api/v2/phenotype/stats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ values, trait_name: statsTraitName }),
      });
      if (!res.ok) throw new Error('Failed to calculate statistics');
      return res.json();
    },
    onSuccess: (data) => {
      setStatsResult(data);
    },
  });

  // Heritability mutation
  const heritabilityMutation = useMutation({
    mutationFn: async () => {
      // Parse genotype data
      const lines = heritabilityData.trim().split('\n');
      const genotype_data: Record<string, number[]> = {};
      for (const line of lines) {
        const [geno, values] = line.split(':');
        if (geno && values) {
          genotype_data[geno.trim()] = values.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v));
        }
      }
      
      const res = await fetch(`${API_BASE}/api/v2/phenotype/heritability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ genotype_data, trait_name: heritabilityTraitName }),
      });
      if (!res.ok) throw new Error('Failed to estimate heritability');
      return res.json();
    },
    onSuccess: (data) => {
      setHeritabilityResult(data);
    },
  });

  // Selection response mutation
  const selectionMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/phenotype/selection-response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          heritability: parseFloat(selHeritability),
          phenotypic_std: parseFloat(selStd),
          selection_proportion: parseFloat(selProportion),
          trait_mean: parseFloat(selMean),
          trait_name: selTraitName,
        }),
      });
      if (!res.ok) throw new Error('Failed to calculate selection response');
      return res.json();
    },
    onSuccess: (data) => {
      setSelectionResult(data);
    },
  });

  // Correlation mutation
  const correlationMutation = useMutation({
    mutationFn: async () => {
      // Parse trait data
      const parseTrait = (str: string): Record<string, number> => {
        const result: Record<string, number> = {};
        const pairs = str.split(',');
        for (const pair of pairs) {
          const [geno, value] = pair.split(':');
          if (geno && value) {
            result[geno.trim()] = parseFloat(value.trim());
          }
        }
        return result;
      };
      
      const res = await fetch(`${API_BASE}/api/v2/phenotype/correlation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trait1_means: parseTrait(corrTrait1),
          trait2_means: parseTrait(corrTrait2),
          trait1_name: corrTrait1Name,
          trait2_name: corrTrait2Name,
        }),
      });
      if (!res.ok) throw new Error('Failed to calculate correlation');
      return res.json();
    },
    onSuccess: (data) => {
      setCorrelationResult(data);
    },
  });

  const getHeritabilityColor = (h2: number): string => {
    if (h2 >= 0.6) return 'text-green-600';
    if (h2 >= 0.3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCorrelationColor = (r: number): string => {
    const abs = Math.abs(r);
    if (abs >= 0.7) return r > 0 ? 'text-green-600' : 'text-red-600';
    if (abs >= 0.4) return 'text-yellow-600';
    return 'text-gray-600';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <BarChart3 className="h-6 w-6" />
          Phenotype Analysis
        </h1>
        <p className="text-muted-foreground">
          Statistical analysis of phenotypic data for breeding decisions
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Calculator className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-lg font-bold">6</p>
                <p className="text-xs text-muted-foreground">Analysis Methods</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Percent className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-lg font-bold">H²</p>
                <p className="text-xs text-muted-foreground">Heritability</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-lg font-bold">R</p>
                <p className="text-xs text-muted-foreground">Selection Response</p>
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
                <p className="text-lg font-bold">rg</p>
                <p className="text-xs text-muted-foreground">Genetic Correlation</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>


      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-4 w-full">
          <TabsTrigger value="stats">
            <Calculator className="h-4 w-4 mr-2" />
            Statistics
          </TabsTrigger>
          <TabsTrigger value="heritability">
            <Percent className="h-4 w-4 mr-2" />
            Heritability
          </TabsTrigger>
          <TabsTrigger value="selection">
            <ArrowUpRight className="h-4 w-4 mr-2" />
            Selection
          </TabsTrigger>
          <TabsTrigger value="correlation">
            <TrendingUp className="h-4 w-4 mr-2" />
            Correlation
          </TabsTrigger>
        </TabsList>

        {/* Stats Tab */}
        <TabsContent value="stats">
          <Card>
            <CardHeader>
              <CardTitle>Descriptive Statistics</CardTitle>
              <CardDescription>Calculate mean, standard deviation, CV, and range</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Trait Name</Label>
                  <Input
                    value={statsTraitName}
                    onChange={(e) => setStatsTraitName(e.target.value)}
                    placeholder="Yield"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Values (comma-separated)</Label>
                  <Input
                    value={statsValues}
                    onChange={(e) => setStatsValues(e.target.value)}
                    placeholder="4.5, 5.2, 4.8, 5.1"
                  />
                </div>
              </div>
              <Button
                onClick={() => statsMutation.mutate()}
                disabled={!statsValues || statsMutation.isPending}
              >
                {statsMutation.isPending ? 'Calculating...' : 'Calculate Statistics'}
              </Button>

              {statsResult && (
                <div className="grid grid-cols-3 md:grid-cols-6 gap-4 mt-4">
                  <div className="p-3 border rounded-lg text-center">
                    <p className="text-xl font-bold">{statsResult.n}</p>
                    <p className="text-xs text-muted-foreground">N</p>
                  </div>
                  <div className="p-3 border rounded-lg text-center">
                    <p className="text-xl font-bold">{statsResult.mean.toFixed(2)}</p>
                    <p className="text-xs text-muted-foreground">Mean</p>
                  </div>
                  <div className="p-3 border rounded-lg text-center">
                    <p className="text-xl font-bold">{statsResult.std.toFixed(3)}</p>
                    <p className="text-xs text-muted-foreground">Std Dev</p>
                  </div>
                  <div className="p-3 border rounded-lg text-center">
                    <p className="text-xl font-bold">{statsResult.cv.toFixed(1)}%</p>
                    <p className="text-xs text-muted-foreground">CV</p>
                  </div>
                  <div className="p-3 border rounded-lg text-center">
                    <p className="text-xl font-bold">{statsResult.min.toFixed(2)}</p>
                    <p className="text-xs text-muted-foreground">Min</p>
                  </div>
                  <div className="p-3 border rounded-lg text-center">
                    <p className="text-xl font-bold">{statsResult.max.toFixed(2)}</p>
                    <p className="text-xs text-muted-foreground">Max</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Heritability Tab */}
        <TabsContent value="heritability">
          <Card>
            <CardHeader>
              <CardTitle>Heritability Estimation</CardTitle>
              <CardDescription>Estimate broad-sense heritability (H²) from replicated data</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Trait Name</Label>
                <Input
                  value={heritabilityTraitName}
                  onChange={(e) => setHeritabilityTraitName(e.target.value)}
                  placeholder="Yield"
                />
              </div>
              <div className="space-y-2">
                <Label>Genotype Data (Genotype: rep1, rep2, rep3)</Label>
                <Textarea
                  value={heritabilityData}
                  onChange={(e) => setHeritabilityData(e.target.value)}
                  placeholder="G1: 4.5, 4.8, 4.6&#10;G2: 5.2, 5.0, 5.3"
                  className="font-mono h-32"
                />
              </div>
              <Button
                onClick={() => heritabilityMutation.mutate()}
                disabled={!heritabilityData || heritabilityMutation.isPending}
              >
                {heritabilityMutation.isPending ? 'Estimating...' : 'Estimate Heritability'}
              </Button>

              {heritabilityResult && (
                <div className="space-y-4 mt-4">
                  <div className="p-6 border rounded-lg text-center bg-muted/50">
                    <p className={`text-4xl font-bold ${getHeritabilityColor(heritabilityResult.h2_broad)}`}>
                      {(heritabilityResult.h2_broad * 100).toFixed(1)}%
                    </p>
                    <p className="text-sm text-muted-foreground">Broad-sense Heritability (H²)</p>
                    <Badge className="mt-2">{heritabilityResult.interpretation}</Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3 border rounded-lg text-center">
                      <p className="text-lg font-bold">{heritabilityResult.vg.toFixed(4)}</p>
                      <p className="text-xs text-muted-foreground">Genetic Variance (Vg)</p>
                    </div>
                    <div className="p-3 border rounded-lg text-center">
                      <p className="text-lg font-bold">{heritabilityResult.ve.toFixed(4)}</p>
                      <p className="text-xs text-muted-foreground">Error Variance (Ve)</p>
                    </div>
                    <div className="p-3 border rounded-lg text-center">
                      <p className="text-lg font-bold">{heritabilityResult.vp.toFixed(4)}</p>
                      <p className="text-xs text-muted-foreground">Phenotypic Variance (Vp)</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Selection Tab */}
        <TabsContent value="selection">
          <Card>
            <CardHeader>
              <CardTitle>Selection Response</CardTitle>
              <CardDescription>Calculate expected genetic gain: R = i × h² × σp</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Trait Name</Label>
                  <Input
                    value={selTraitName}
                    onChange={(e) => setSelTraitName(e.target.value)}
                    placeholder="Yield"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Current Mean</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={selMean}
                    onChange={(e) => setSelMean(e.target.value)}
                    placeholder="5.0"
                  />
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Heritability (h²)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={selHeritability}
                    onChange={(e) => setSelHeritability(e.target.value)}
                    placeholder="0.6"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phenotypic Std Dev (σp)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={selStd}
                    onChange={(e) => setSelStd(e.target.value)}
                    placeholder="0.8"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Selection Proportion</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max="0.99"
                    value={selProportion}
                    onChange={(e) => setSelProportion(e.target.value)}
                    placeholder="0.1 (top 10%)"
                  />
                </div>
              </div>
              <Button
                onClick={() => selectionMutation.mutate()}
                disabled={selectionMutation.isPending}
              >
                {selectionMutation.isPending ? 'Calculating...' : 'Calculate Response'}
              </Button>

              {selectionResult && (
                <div className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 border rounded-lg text-center">
                      <p className="text-2xl font-bold">{selectionResult.selection_intensity.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Selection Intensity (i)</p>
                    </div>
                    <div className="p-4 border rounded-lg text-center bg-green-50">
                      <p className="text-2xl font-bold text-green-600">+{selectionResult.response.toFixed(3)}</p>
                      <p className="text-xs text-muted-foreground">Response (R)</p>
                    </div>
                    <div className="p-4 border rounded-lg text-center">
                      <p className="text-2xl font-bold">{selectionResult.new_mean.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">New Mean</p>
                    </div>
                    <div className="p-4 border rounded-lg text-center bg-blue-50">
                      <p className="text-2xl font-bold text-blue-600">+{selectionResult.percent_gain.toFixed(1)}%</p>
                      <p className="text-xs text-muted-foreground">Percent Gain</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Correlation Tab */}
        <TabsContent value="correlation">
          <Card>
            <CardHeader>
              <CardTitle>Genetic Correlation</CardTitle>
              <CardDescription>Calculate correlation between two traits at the genetic level</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Trait 1 Name</Label>
                  <Input
                    value={corrTrait1Name}
                    onChange={(e) => setCorrTrait1Name(e.target.value)}
                    placeholder="Yield"
                  />
                  <Label className="text-xs text-muted-foreground">Genotype Means (G1: value, G2: value, ...)</Label>
                  <Input
                    value={corrTrait1}
                    onChange={(e) => setCorrTrait1(e.target.value)}
                    placeholder="G1: 4.5, G2: 5.2, G3: 4.1"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Trait 2 Name</Label>
                  <Input
                    value={corrTrait2Name}
                    onChange={(e) => setCorrTrait2Name(e.target.value)}
                    placeholder="Plant Height"
                  />
                  <Label className="text-xs text-muted-foreground">Genotype Means (G1: value, G2: value, ...)</Label>
                  <Input
                    value={corrTrait2}
                    onChange={(e) => setCorrTrait2(e.target.value)}
                    placeholder="G1: 12.3, G2: 14.1, G3: 11.8"
                  />
                </div>
              </div>
              <Button
                onClick={() => correlationMutation.mutate()}
                disabled={!corrTrait1 || !corrTrait2 || correlationMutation.isPending}
              >
                {correlationMutation.isPending ? 'Calculating...' : 'Calculate Correlation'}
              </Button>

              {correlationResult && (
                <div className="p-6 border rounded-lg text-center bg-muted/50 mt-4">
                  <p className={`text-4xl font-bold ${getCorrelationColor(correlationResult.correlation)}`}>
                    {correlationResult.correlation.toFixed(3)}
                  </p>
                  <p className="text-sm text-muted-foreground">Genetic Correlation (rg)</p>
                  <Badge className="mt-2">{correlationResult.interpretation}</Badge>
                </div>
              )}

              <div className="p-4 border rounded-lg bg-muted/30 mt-4">
                <p className="font-medium mb-2">Interpretation Guide</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>|rg| &gt; 0.7: Strong correlation</div>
                  <div>|rg| 0.4-0.7: Moderate correlation</div>
                  <div>|rg| &lt; 0.4: Weak correlation</div>
                  <div>rg &gt; 0: Positive (traits increase together)</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default PhenotypeAnalysis;

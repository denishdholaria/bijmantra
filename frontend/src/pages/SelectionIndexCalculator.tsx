/**
 * Selection Index Calculator Page
 * 
 * Multi-trait selection index calculations including Smith-Hazel,
 * Desired Gains, Base Index, Independent Culling, and Tandem Selection.
 * Connects to /api/v2/selection endpoints.
 */

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Target,
  Calculator,
  TrendingUp,
  Scale,
  Filter,
  BarChart3,
  Plus,
  Trash2,
  Play,
  Info,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Trait {
  name: string;
  heritability: number;
  phenotypic_variance: number;
  economic_weight: number;
  desired_gain?: number;
  threshold?: number;
}

interface SelectionResult {
  method: string;
  index_coefficients?: Record<string, number>;
  expected_response?: Record<string, number>;
  selection_intensity?: number;
  accuracy?: number;
  selected_individuals?: string[];
  message?: string;
}

// Default traits for demo
const DEFAULT_TRAITS: Trait[] = [
  { name: 'Yield', heritability: 0.35, phenotypic_variance: 100, economic_weight: 1.0, desired_gain: 5, threshold: 80 },
  { name: 'Protein', heritability: 0.55, phenotypic_variance: 4, economic_weight: 0.5, desired_gain: 0.5, threshold: 12 },
  { name: 'Days to Maturity', heritability: 0.70, phenotypic_variance: 25, economic_weight: -0.3, desired_gain: -3, threshold: 120 },
];

export function SelectionIndexCalculator() {
  const [activeTab, setActiveTab] = useState('smith-hazel');
  const [traits, setTraits] = useState<Trait[]>(DEFAULT_TRAITS);
  const [result, setResult] = useState<SelectionResult | null>(null);
  const [selectionIntensity, setSelectionIntensity] = useState(1.4);

  // Fetch available methods
  const { data: methods } = useQuery({
    queryKey: ['selection-methods'],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/selection/methods`);
        if (!res.ok) return null;
        return res.json();
      } catch {
        return null;
      }
    },
  });

  // Fetch default weights
  const { data: defaultWeights } = useQuery({
    queryKey: ['default-weights'],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/selection/default-weights`);
        if (!res.ok) return null;
        return res.json();
      } catch {
        return null;
      }
    },
  });

  // Smith-Hazel calculation
  const smithHazelMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/selection/smith-hazel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          traits: traits.map(t => t.name),
          heritabilities: Object.fromEntries(traits.map(t => [t.name, t.heritability])),
          phenotypic_variances: Object.fromEntries(traits.map(t => [t.name, t.phenotypic_variance])),
          economic_weights: Object.fromEntries(traits.map(t => [t.name, t.economic_weight])),
          genetic_correlations: {},
        }),
      });
      if (!res.ok) throw new Error('Calculation failed');
      return res.json();
    },
    onSuccess: (data) => {
      setResult({ method: 'Smith-Hazel', ...data });
    },
  });

  // Desired Gains calculation
  const desiredGainsMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/selection/desired-gains`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          traits: traits.map(t => t.name),
          heritabilities: Object.fromEntries(traits.map(t => [t.name, t.heritability])),
          phenotypic_variances: Object.fromEntries(traits.map(t => [t.name, t.phenotypic_variance])),
          desired_gains: Object.fromEntries(traits.map(t => [t.name, t.desired_gain || 0])),
          genetic_correlations: {},
        }),
      });
      if (!res.ok) throw new Error('Calculation failed');
      return res.json();
    },
    onSuccess: (data) => {
      setResult({ method: 'Desired Gains (Pesek-Baker)', ...data });
    },
  });

  // Base Index calculation
  const baseIndexMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/selection/base-index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          traits: traits.map(t => t.name),
          weights: Object.fromEntries(traits.map(t => [t.name, t.economic_weight])),
        }),
      });
      if (!res.ok) throw new Error('Calculation failed');
      return res.json();
    },
    onSuccess: (data) => {
      setResult({ method: 'Base Index', ...data });
    },
  });

  // Independent Culling
  const independentCullingMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/selection/independent-culling`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          traits: traits.map(t => t.name),
          thresholds: Object.fromEntries(traits.map(t => [t.name, t.threshold || 0])),
        }),
      });
      if (!res.ok) throw new Error('Calculation failed');
      return res.json();
    },
    onSuccess: (data) => {
      setResult({ method: 'Independent Culling', ...data });
    },
  });

  // Predict Response
  const predictResponseMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/selection/predict-response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          traits: traits.map(t => t.name),
          heritabilities: Object.fromEntries(traits.map(t => [t.name, t.heritability])),
          phenotypic_std: Object.fromEntries(traits.map(t => [t.name, Math.sqrt(t.phenotypic_variance)])),
          selection_intensity: selectionIntensity,
        }),
      });
      if (!res.ok) throw new Error('Calculation failed');
      return res.json();
    },
    onSuccess: (data) => {
      setResult({ method: 'Response Prediction', ...data });
    },
  });

  const addTrait = () => {
    setTraits([...traits, { name: `Trait ${traits.length + 1}`, heritability: 0.5, phenotypic_variance: 10, economic_weight: 1.0, desired_gain: 1, threshold: 50 }]);
  };

  const removeTrait = (index: number) => {
    setTraits(traits.filter((_, i) => i !== index));
  };

  const updateTrait = (index: number, field: keyof Trait, value: string | number) => {
    const updated = [...traits];
    updated[index] = { ...updated[index], [field]: value };
    setTraits(updated);
  };

  const runCalculation = () => {
    setResult(null);
    switch (activeTab) {
      case 'smith-hazel':
        smithHazelMutation.mutate();
        break;
      case 'desired-gains':
        desiredGainsMutation.mutate();
        break;
      case 'base-index':
        baseIndexMutation.mutate();
        break;
      case 'independent-culling':
        independentCullingMutation.mutate();
        break;
      case 'response':
        predictResponseMutation.mutate();
        break;
    }
  };

  const isLoading = smithHazelMutation.isPending || desiredGainsMutation.isPending || 
                    baseIndexMutation.isPending || independentCullingMutation.isPending ||
                    predictResponseMutation.isPending;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Target className="h-6 w-6" />
          Selection Index Calculator
        </h1>
        <p className="text-muted-foreground">
          Multi-trait selection index calculations for breeding programs
        </p>
      </div>

      {/* Method Selection */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-5 w-full">
          <TabsTrigger value="smith-hazel">
            <Scale className="h-4 w-4 mr-2" />
            Smith-Hazel
          </TabsTrigger>
          <TabsTrigger value="desired-gains">
            <TrendingUp className="h-4 w-4 mr-2" />
            Desired Gains
          </TabsTrigger>
          <TabsTrigger value="base-index">
            <Calculator className="h-4 w-4 mr-2" />
            Base Index
          </TabsTrigger>
          <TabsTrigger value="independent-culling">
            <Filter className="h-4 w-4 mr-2" />
            Ind. Culling
          </TabsTrigger>
          <TabsTrigger value="response">
            <BarChart3 className="h-4 w-4 mr-2" />
            Response
          </TabsTrigger>
        </TabsList>


        {/* Method Descriptions */}
        <TabsContent value="smith-hazel">
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="font-medium">Smith-Hazel Index (Optimal Index)</p>
                  <p className="text-sm text-muted-foreground">
                    Maximizes genetic gain by weighting traits based on heritability, variance, and economic importance.
                    Formula: I = b₁P₁ + b₂P₂ + ... where b = P⁻¹Ga
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="desired-gains">
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="font-medium">Desired Gains Index (Pesek-Baker)</p>
                  <p className="text-sm text-muted-foreground">
                    Calculates index coefficients to achieve specified genetic gains for each trait.
                    Useful when you have specific breeding targets.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="base-index">
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="font-medium">Base Index (Weighted Sum)</p>
                  <p className="text-sm text-muted-foreground">
                    Simple weighted sum of phenotypic values. I = w₁P₁ + w₂P₂ + ...
                    Easy to implement but less efficient than Smith-Hazel.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="independent-culling">
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="font-medium">Independent Culling Levels</p>
                  <p className="text-sm text-muted-foreground">
                    Set minimum thresholds for each trait. Individuals must meet ALL thresholds to be selected.
                    Simple but can be inefficient with many traits.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="response">
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="font-medium">Selection Response Prediction</p>
                  <p className="text-sm text-muted-foreground">
                    Predict genetic gain using the breeder's equation: R = i × h² × σₚ
                    where i = selection intensity, h² = heritability, σₚ = phenotypic std dev.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Trait Input */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Trait Parameters</span>
              <Button size="sm" variant="outline" onClick={addTrait}>
                <Plus className="h-4 w-4 mr-1" />
                Add Trait
              </Button>
            </CardTitle>
            <CardDescription>Define traits and their parameters</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {traits.map((trait, index) => (
                <div key={index} className="p-3 border rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <Input
                      value={trait.name}
                      onChange={(e) => updateTrait(index, 'name', e.target.value)}
                      className="w-40 font-medium"
                    />
                    <Button size="sm" variant="ghost" onClick={() => removeTrait(index)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs">Heritability (h²)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={trait.heritability}
                        onChange={(e) => updateTrait(index, 'heritability', parseFloat(e.target.value))}
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Phenotypic Variance</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={trait.phenotypic_variance}
                        onChange={(e) => updateTrait(index, 'phenotypic_variance', parseFloat(e.target.value))}
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Economic Weight</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={trait.economic_weight}
                        onChange={(e) => updateTrait(index, 'economic_weight', parseFloat(e.target.value))}
                      />
                    </div>
                    {activeTab === 'desired-gains' && (
                      <div>
                        <Label className="text-xs">Desired Gain</Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={trait.desired_gain}
                          onChange={(e) => updateTrait(index, 'desired_gain', parseFloat(e.target.value))}
                        />
                      </div>
                    )}
                    {activeTab === 'independent-culling' && (
                      <div>
                        <Label className="text-xs">Threshold</Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={trait.threshold}
                          onChange={(e) => updateTrait(index, 'threshold', parseFloat(e.target.value))}
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {activeTab === 'response' && (
                <div className="p-3 border rounded-lg bg-blue-50">
                  <Label className="text-sm font-medium">Selection Intensity (i)</Label>
                  <div className="flex items-center gap-4 mt-2">
                    <Input
                      type="number"
                      step="0.1"
                      value={selectionIntensity}
                      onChange={(e) => setSelectionIntensity(parseFloat(e.target.value))}
                      className="w-24"
                    />
                    <div className="text-xs text-muted-foreground">
                      <p>Common values:</p>
                      <p>10% selected → i = 1.76</p>
                      <p>20% selected → i = 1.40</p>
                      <p>50% selected → i = 0.80</p>
                    </div>
                  </div>
                </div>
              )}

              <Button onClick={runCalculation} disabled={isLoading} className="w-full">
                <Play className="h-4 w-4 mr-2" />
                {isLoading ? 'Calculating...' : 'Calculate Index'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>
              {result ? `${result.method} calculation results` : 'Run a calculation to see results'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-4">
                <Badge variant="outline" className="text-lg px-3 py-1">
                  {result.method}
                </Badge>

                {result.index_coefficients && (
                  <div>
                    <h4 className="font-medium mb-2">Index Coefficients (b)</h4>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Trait</TableHead>
                          <TableHead className="text-right">Coefficient</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {Object.entries(result.index_coefficients).map(([trait, coef]) => (
                          <TableRow key={trait}>
                            <TableCell>{trait}</TableCell>
                            <TableCell className="text-right font-mono">
                              {typeof coef === 'number' ? coef.toFixed(4) : coef}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {result.expected_response && (
                  <div>
                    <h4 className="font-medium mb-2">Expected Response (R)</h4>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Trait</TableHead>
                          <TableHead className="text-right">Response</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {Object.entries(result.expected_response).map(([trait, resp]) => (
                          <TableRow key={trait}>
                            <TableCell>{trait}</TableCell>
                            <TableCell className="text-right font-mono">
                              {typeof resp === 'number' ? resp.toFixed(3) : resp}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {result.accuracy && (
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium">Selection Accuracy</p>
                    <p className="text-2xl font-bold text-green-700">
                      {(result.accuracy * 100).toFixed(1)}%
                    </p>
                  </div>
                )}

                {result.message && (
                  <p className="text-sm text-muted-foreground">{result.message}</p>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Calculator className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Configure traits and run a calculation</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Reference Table */}
      <Card>
        <CardHeader>
          <CardTitle>Selection Method Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Method</TableHead>
                <TableHead>Best For</TableHead>
                <TableHead>Efficiency</TableHead>
                <TableHead>Complexity</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium">Smith-Hazel</TableCell>
                <TableCell>Maximizing overall genetic gain</TableCell>
                <TableCell><Badge className="bg-green-100 text-green-800">High</Badge></TableCell>
                <TableCell><Badge variant="outline">Medium</Badge></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Desired Gains</TableCell>
                <TableCell>Achieving specific breeding targets</TableCell>
                <TableCell><Badge className="bg-green-100 text-green-800">High</Badge></TableCell>
                <TableCell><Badge variant="outline">Medium</Badge></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Base Index</TableCell>
                <TableCell>Simple weighted selection</TableCell>
                <TableCell><Badge className="bg-yellow-100 text-yellow-800">Medium</Badge></TableCell>
                <TableCell><Badge className="bg-green-100 text-green-800">Low</Badge></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Independent Culling</TableCell>
                <TableCell>Minimum standards for all traits</TableCell>
                <TableCell><Badge className="bg-yellow-100 text-yellow-800">Medium</Badge></TableCell>
                <TableCell><Badge className="bg-green-100 text-green-800">Low</Badge></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Tandem Selection</TableCell>
                <TableCell>Sequential trait improvement</TableCell>
                <TableCell><Badge className="bg-red-100 text-red-800">Low</Badge></TableCell>
                <TableCell><Badge className="bg-green-100 text-green-800">Low</Badge></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export default SelectionIndexCalculator;

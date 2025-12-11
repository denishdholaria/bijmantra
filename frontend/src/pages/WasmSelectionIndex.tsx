import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  Calculator, Target, TrendingUp, Award, Scale, 
  ArrowUpDown, Download, Plus, Trash2, Sparkles
} from 'lucide-react';
import { useWasm, useSelectionIndex } from '@/wasm/hooks';

interface Trait {
  id: string;
  name: string;
  weight: number;
  unit: string;
}

interface Candidate {
  id: string;
  name: string;
  values: number[];
  indexValue?: number;
  rank?: number;
}

function WasmSelectionIndex() {
  const { isReady, version } = useWasm();
  const { calculate, result, isCalculating } = useSelectionIndex();

  const [traits, setTraits] = useState<Trait[]>([
    { id: 't1', name: 'Yield', weight: 1.0, unit: 'kg/ha' },
    { id: 't2', name: 'Protein', weight: 0.5, unit: '%' },
    { id: 't3', name: 'Disease Resistance', weight: 0.3, unit: 'score' },
  ]);

  const [candidates, setCandidates] = useState<Candidate[]>([
    { id: 'C001', name: 'Elite Line 1', values: [4500, 12.5, 7] },
    { id: 'C002', name: 'Elite Line 2', values: [4200, 14.2, 8] },
    { id: 'C003', name: 'Elite Line 3', values: [4800, 11.8, 6] },
    { id: 'C004', name: 'Elite Line 4', values: [4100, 13.5, 9] },
    { id: 'C005', name: 'Elite Line 5', values: [4600, 12.0, 7] },
    { id: 'C006', name: 'Landrace 1', values: [3800, 15.0, 5] },
    { id: 'C007', name: 'Landrace 2', values: [3600, 14.8, 6] },
    { id: 'C008', name: 'Cross F1-1', values: [4300, 13.0, 8] },
    { id: 'C009', name: 'Cross F1-2', values: [4400, 12.8, 7] },
    { id: 'C010', name: 'Cross F1-3', values: [4700, 11.5, 8] },
  ]);

  const [selectionIntensity, setSelectionIntensity] = useState(0.2);
  const [sortBy, setSortBy] = useState<'index' | 'rank'>('rank');
  const [sortDesc, setSortDesc] = useState(false);

  const addTrait = () => {
    const newId = `t${traits.length + 1}`;
    setTraits([...traits, { id: newId, name: `Trait ${traits.length + 1}`, weight: 0.5, unit: '' }]);
    setCandidates(candidates.map(c => ({ ...c, values: [...c.values, 0] })));
  };

  const removeTrait = (id: string) => {
    const idx = traits.findIndex(t => t.id === id);
    if (idx === -1) return;
    setTraits(traits.filter(t => t.id !== id));
    setCandidates(candidates.map(c => ({
      ...c,
      values: c.values.filter((_, i) => i !== idx)
    })));
  };

  const updateTraitWeight = (id: string, weight: number) => {
    setTraits(traits.map(t => t.id === id ? { ...t, weight } : t));
  };

  const updateTraitName = (id: string, name: string) => {
    setTraits(traits.map(t => t.id === id ? { ...t, name } : t));
  };

  const updateCandidateValue = (candidateId: string, traitIdx: number, value: number) => {
    setCandidates(candidates.map(c => 
      c.id === candidateId 
        ? { ...c, values: c.values.map((v, i) => i === traitIdx ? value : v) }
        : c
    ));
  };

  const runSelection = () => {
    // Standardize trait values
    const standardized: number[] = [];
    const means: number[] = [];
    const stds: number[] = [];

    for (let t = 0; t < traits.length; t++) {
      const values = candidates.map(c => c.values[t]);
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const std = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length);
      means.push(mean);
      stds.push(std || 1);
    }

    for (const c of candidates) {
      for (let t = 0; t < traits.length; t++) {
        standardized.push((c.values[t] - means[t]) / stds[t]);
      }
    }

    const weights = traits.map(t => t.weight);
    calculate(standardized, weights, candidates.length, traits.length);
  };

  // Update candidates with results
  const getUpdatedCandidates = (): Candidate[] => {
    if (!result) return candidates;
    
    return candidates.map((c, i) => ({
      ...c,
      indexValue: result.index_values[i],
      rank: result.rankings.indexOf(i) + 1,
    }));
  };

  const sortedCandidates = [...getUpdatedCandidates()].sort((a, b) => {
    if (sortBy === 'index') {
      const aVal = a.indexValue ?? 0;
      const bVal = b.indexValue ?? 0;
      return sortDesc ? aVal - bVal : bVal - aVal;
    }
    const aRank = a.rank ?? 999;
    const bRank = b.rank ?? 999;
    return sortDesc ? bRank - aRank : aRank - bRank;
  });

  const nSelected = Math.ceil(candidates.length * selectionIntensity);
  const selectedCandidates = sortedCandidates.slice(0, nSelected);

  const exportResults = () => {
    const headers = ['ID', 'Name', ...traits.map(t => t.name), 'Index', 'Rank', 'Selected'];
    const rows = sortedCandidates.map(c => [
      c.id,
      c.name,
      ...c.values.map(v => v.toString()),
      c.indexValue?.toFixed(3) ?? '',
      c.rank?.toString() ?? '',
      (c.rank ?? 999) <= nSelected ? 'Yes' : 'No'
    ]);
    
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'selection_index_results.csv';
    a.click();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Scale className="h-8 w-8 text-indigo-500" />
            Selection Index Calculator
          </h1>
          <p className="text-muted-foreground mt-1">
            Multi-trait selection with economic weights and genetic parameters
          </p>
        </div>
        <Badge variant={isReady ? "default" : "secondary"} className={isReady ? "bg-green-500" : ""}>
          {isReady ? `⚡ WebAssembly v${version}` : 'Loading...'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-500" />
              Traits
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{traits.length}</div>
            <p className="text-xs text-muted-foreground">Selection criteria</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Calculator className="h-4 w-4 text-purple-500" />
              Candidates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{candidates.length}</div>
            <p className="text-xs text-muted-foreground">Entries evaluated</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Award className="h-4 w-4 text-yellow-500" />
              Selected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{nSelected}</div>
            <p className="text-xs text-muted-foreground">Top {(selectionIntensity * 100).toFixed(0)}%</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              Selection Differential
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {result ? result.selection_differential.toFixed(3) : '-'}
            </div>
            <p className="text-xs text-muted-foreground">S = μs - μ</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Trait Weights</CardTitle>
              <Button variant="outline" size="sm" onClick={addTrait}>
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            </div>
            <CardDescription>Economic weights for each trait</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {traits.map((trait, idx) => (
              <div key={trait.id} className="space-y-2 p-3 bg-muted rounded-lg">
                <div className="flex items-center justify-between">
                  <Input
                    value={trait.name}
                    onChange={(e) => updateTraitName(trait.id, e.target.value)}
                    className="w-32 h-8"
                  />
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => removeTrait(trait.id)}
                    disabled={traits.length <= 1}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <Slider
                    value={[trait.weight]}
                    onValueChange={([v]) => updateTraitWeight(trait.id, v)}
                    min={0}
                    max={2}
                    step={0.1}
                    className="flex-1"
                  />
                  <span className="w-12 text-sm text-right">{trait.weight.toFixed(1)}</span>
                </div>
              </div>
            ))}

            <div className="space-y-2 pt-4 border-t">
              <Label>Selection Intensity</Label>
              <div className="flex items-center gap-2">
                <Slider
                  value={[selectionIntensity]}
                  onValueChange={([v]) => setSelectionIntensity(v)}
                  min={0.05}
                  max={0.5}
                  step={0.05}
                />
                <span className="w-12 text-sm">{(selectionIntensity * 100).toFixed(0)}%</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Select top {nSelected} of {candidates.length} candidates
              </p>
            </div>

            <Button onClick={runSelection} disabled={!isReady || isCalculating} className="w-full">
              <Sparkles className="h-4 w-4 mr-2" />
              {isCalculating ? 'Calculating...' : 'Calculate Index'}
            </Button>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Selection Results</CardTitle>
                <CardDescription>Candidates ranked by selection index</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={exportResults} disabled={!result}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">Rank</TableHead>
                  <TableHead>ID</TableHead>
                  <TableHead>Name</TableHead>
                  {traits.map(t => (
                    <TableHead key={t.id}>{t.name}</TableHead>
                  ))}
                  <TableHead 
                    className="cursor-pointer hover:bg-muted"
                    onClick={() => {
                      if (sortBy === 'index') setSortDesc(!sortDesc);
                      else { setSortBy('index'); setSortDesc(false); }
                    }}
                  >
                    <div className="flex items-center gap-1">
                      Index
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedCandidates.map((c) => {
                  const isSelected = (c.rank ?? 999) <= nSelected;
                  return (
                    <TableRow 
                      key={c.id} 
                      className={isSelected ? 'bg-green-50 dark:bg-green-950' : ''}
                    >
                      <TableCell>
                        <Badge variant={isSelected ? "default" : "secondary"}>
                          #{c.rank ?? '-'}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">{c.id}</TableCell>
                      <TableCell>{c.name}</TableCell>
                      {c.values.map((v, i) => (
                        <TableCell key={i}>
                          <Input
                            type="number"
                            value={v}
                            onChange={(e) => updateCandidateValue(c.id, i, parseFloat(e.target.value) || 0)}
                            className="w-20 h-8"
                          />
                        </TableCell>
                      ))}
                      <TableCell>
                        {c.indexValue !== undefined ? (
                          <span className={c.indexValue > 0 ? 'text-green-600 font-medium' : 'text-red-600'}>
                            {c.indexValue > 0 ? '+' : ''}{c.indexValue.toFixed(3)}
                          </span>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        {isSelected ? (
                          <Badge className="bg-green-500">
                            <Award className="h-3 w-3 mr-1" />
                            Selected
                          </Badge>
                        ) : (
                          <Badge variant="outline">Not Selected</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Selection Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Selection Differential (S)</div>
                <div className="text-2xl font-bold">{result.selection_differential.toFixed(3)}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Difference between selected and population mean
                </p>
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Expected Response (R)</div>
                <div className="text-2xl font-bold text-green-600">
                  +{result.expected_response.toFixed(3)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  R = h² × S (assuming h² = 0.3)
                </p>
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Selection Intensity (i)</div>
                <div className="text-2xl font-bold">
                  {(result.selection_differential / 1).toFixed(2)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Standardized selection differential
                </p>
              </div>
            </div>

            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <h4 className="font-medium mb-2">Selection Index Formula</h4>
              <p className="text-sm text-muted-foreground">
                I = {traits.map((t, i) => `${t.weight.toFixed(1)} × ${t.name}`).join(' + ')}
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                The selection index combines multiple traits into a single value for ranking candidates.
                Higher index values indicate better overall genetic merit based on the specified economic weights.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default WasmSelectionIndex;
export { WasmSelectionIndex };

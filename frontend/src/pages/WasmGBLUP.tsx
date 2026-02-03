import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Calculator, TrendingUp, BarChart3, Target, Dna, 
  ArrowUpDown, Download, Sparkles, Server, Cpu, Layers
} from 'lucide-react';
import { useWasm, useGBLUP, useGRM } from '@/wasm/hooks';
import { toast } from 'sonner';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Individual {
  id: string;
  name: string;
  phenotype: number;
  gebv?: number;
  reliability?: number;
  accuracy?: number;
}

// Helper for API calls
const apiCall = async (endpoint: string, method: string, body?: any) => {
  const token = localStorage.getItem("auth_token");
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(endpoint, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || 'API request failed');
  }
  return res.json();
};

function WasmGBLUP() {
  const { isReady, version } = useWasm();
  const { calculate: calcGRM, result: grmResult } = useGRM();
  const { calculate: calcGBLUP, result: gblupResult, isCalculating } = useGBLUP();

  const [engine, setEngine] = useState<'wasm' | 'server'>('wasm');
  const [heritability, setHeritability] = useState(0.35);
  const [populationSize, setPopulationSize] = useState(50);
  const [markerCount, setMarkerCount] = useState(500);

  const [individuals, setIndividuals] = useState<Individual[]>([]);
  const [genotypes, setGenotypes] = useState<number[]>([]);
  const [serverGMatrix, setServerGMatrix] = useState<number[][] | null>(null);
  const [serverResults, setServerResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [sortBy, setSortBy] = useState<'gebv' | 'reliability' | 'phenotype'>('gebv');
  const [sortDesc, setSortDesc] = useState(true);

  // Initialize mock data
  useEffect(() => {
    generateNewPopulation();
  }, []);

  const generateNewPopulation = () => {
    const inds: Individual[] = [];
    for (let i = 0; i < populationSize; i++) {
      inds.push({
        id: `G${(i + 1).toString().padStart(3, '0')}`,
        name: `Line ${i + 1}`,
        phenotype: 100 + Math.random() * 40 - 20, // Mean 100, range 80-120
      });
    }
    setIndividuals(inds);

    // Generate genotypes (0, 1, 2)
    const totalMarkers = populationSize * markerCount;
    const genos: number[] = [];
    for (let i = 0; i < totalMarkers; i++) {
      const r = Math.random();
      genos.push(r < 0.25 ? 0 : r < 0.75 ? 1 : 2);
    }
    setGenotypes(genos);

    // Reset results
    setServerGMatrix(null);
    setServerResults(null);
  };

  const runGMatrix = async () => {
    if (engine === 'wasm') {
      calcGRM(genotypes, populationSize, markerCount);
    } else {
      try {
        setLoading(true);
        // Convert flat genotype array to 2D array for server
        const matrix: number[][] = [];
        for (let i = 0; i < populationSize; i++) {
          matrix.push(genotypes.slice(i * markerCount, (i + 1) * markerCount));
        }

        const res = await apiCall('/api/v2/genomic-selection/g-matrix', 'POST', {
          markers: matrix,
          ploidy: 2
        });

        setServerGMatrix(res.matrix);
        toast.success(`Server calculated G-Matrix using ${res.n_markers_used} markers`);
      } catch (err: any) {
        toast.error(`Error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const runAnalysis = async () => {
    if (engine === 'wasm') {
      if (!grmResult) return;
      const phenotypes = individuals.map(ind => ind.phenotype);
      calcGBLUP(phenotypes, grmResult.matrix, individuals.length, heritability);
    } else {
      if (!serverGMatrix) return;
      try {
        setLoading(true);
        const phenotypes = individuals.map(ind => ind.phenotype);

        const res = await apiCall('/api/v2/genomic-selection/gblup', 'POST', {
          phenotypes,
          g_matrix: serverGMatrix,
          heritability
        });

        setServerResults(res);
        toast.success('Server GBLUP analysis complete');
      } catch (err: any) {
        toast.error(`Error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  // Merge results into individuals
  const getResults = () => {
    if (engine === 'wasm') return gblupResult;
    return serverResults;
  };

  const results = getResults();

  const updatedIndividuals = individuals.map((ind, i) => ({
    ...ind,
    gebv: results?.gebv?.[i],
    reliability: results?.reliability?.[i],
    accuracy: results?.accuracy?.[i] // Accuracy might not be in server response, only reliability
  }));

  const sortedIndividuals = [...updatedIndividuals].sort((a, b) => {
    const aVal = sortBy === 'gebv' ? (a.gebv ?? -999) :
                 sortBy === 'reliability' ? (a.reliability ?? -1) : a.phenotype;
    const bVal = sortBy === 'gebv' ? (b.gebv ?? -999) :
                 sortBy === 'reliability' ? (b.reliability ?? -1) : b.phenotype;
    return sortDesc ? bVal - aVal : aVal - bVal;
  });

  const handleSort = (column: 'gebv' | 'reliability' | 'phenotype') => {
    if (sortBy === column) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(column);
      setSortDesc(true);
    }
  };

  const exportResults = () => {
    const csv = [
      ['ID', 'Name', 'Phenotype', 'GEBV', 'Reliability'].join(','),
      ...sortedIndividuals.map(ind => 
        [ind.id, ind.name, ind.phenotype, ind.gebv?.toFixed(3) ?? '', 
         ind.reliability?.toFixed(3) ?? ''].join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gblup_results.csv';
    a.click();
  };

  const gMatrixReady = engine === 'wasm' ? !!grmResult : !!serverGMatrix;

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Calculator className="h-8 w-8 text-primary" />
            Genomic BLUP Calculator
          </h1>
          <p className="text-muted-foreground mt-1">
            Predict breeding values using genomic relationships
          </p>
        </div>

        <div className="flex items-center gap-2">
           <div className="bg-muted p-1 rounded-lg flex">
             <Button
               variant={engine === 'wasm' ? 'default' : 'ghost'}
               size="sm"
               onClick={() => setEngine('wasm')}
               className="gap-2"
             >
               <Cpu className="h-4 w-4" /> WASM
             </Button>
             <Button
               variant={engine === 'server' ? 'default' : 'ghost'}
               size="sm"
               onClick={() => setEngine('server')}
               className="gap-2"
             >
               <Server className="h-4 w-4" /> Server
             </Button>
           </div>
           {engine === 'wasm' && (
             <Badge variant={isReady ? "outline" : "secondary"} className={isReady ? "text-green-600 border-green-600" : ""}>
               {isReady ? `v${version}` : 'Loading...'}
             </Badge>
           )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Dna className="h-4 w-4 text-purple-500" />
              Population Size
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{individuals.length}</div>
            <p className="text-xs text-muted-foreground">Genotyped lines</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Target className="h-4 w-4 text-green-500" />
              Heritability
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(heritability * 100).toFixed(0)}%</div>
            <p className="text-xs text-muted-foreground">h² estimate</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-500" />
              Genetic Variance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {results ? results.genetic_variance.toFixed(2) : '-'}
            </div>
            <p className="text-xs text-muted-foreground">σ²g</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-orange-500" />
              Mean GEBV
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {results ? (results.mean || 0).toFixed(2) : '-'}
            </div>
            <p className="text-xs text-muted-foreground">Population mean</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Analysis parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Population Size</Label>
                  <span className="text-sm text-muted-foreground">{populationSize}</span>
                </div>
                <Slider
                  value={[populationSize]}
                  onValueChange={([v]) => { setPopulationSize(v); generateNewPopulation(); }}
                  min={10}
                  max={200}
                  step={10}
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Heritability (h²)</Label>
                  <span className="text-sm text-muted-foreground">{(heritability * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[heritability]}
                  onValueChange={([v]) => setHeritability(v)}
                  min={0.05}
                  max={0.95}
                  step={0.05}
                />
              </div>

              <Alert>
                <Layers className="h-4 w-4" />
                <AlertTitle>Workflow</AlertTitle>
                <AlertDescription className="text-xs">
                  1. Calculate Genomic Relationship Matrix (G)<br/>
                  2. Solve Mixed Model Equations (GBLUP)
                </AlertDescription>
              </Alert>

            </div>

            <div className="space-y-2">
              <Button 
                onClick={runGMatrix}
                disabled={loading || (engine === 'wasm' && !isReady)}
                className="w-full"
                variant={gMatrixReady ? "outline" : "default"}
              >
                {loading ? 'Processing...' : 'Step 1: Calculate G-Matrix'}
              </Button>

              <Button 
                onClick={runAnalysis}
                disabled={loading || !gMatrixReady}
                variant={gMatrixReady ? "default" : "secondary"}
                className="w-full"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                {loading ? 'Calculating...' : 'Step 2: Run GBLUP'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
           <Tabs defaultValue="table">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Results</CardTitle>
                  <CardDescription>
                    {results ? 'Analysis complete' : 'Waiting for analysis...'}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <TabsList>
                    <TabsTrigger value="table">Table</TabsTrigger>
                    <TabsTrigger value="plot">Plot</TabsTrigger>
                  </TabsList>
                  <Button variant="outline" size="sm" onClick={exportResults} disabled={!results}>
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <TabsContent value="table" className="mt-0">
                <div className="rounded-md border h-[400px] overflow-auto">
                  <Table>
                    <TableHeader className="sticky top-0 bg-background">
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-muted"
                          onClick={() => handleSort('phenotype')}
                        >
                          <div className="flex items-center gap-1">
                            Phenotype
                            <ArrowUpDown className="h-3 w-3" />
                          </div>
                        </TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-muted"
                          onClick={() => handleSort('gebv')}
                        >
                          <div className="flex items-center gap-1">
                            GEBV
                            <ArrowUpDown className="h-3 w-3" />
                          </div>
                        </TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-muted"
                          onClick={() => handleSort('reliability')}
                        >
                          <div className="flex items-center gap-1">
                            Reliability
                            <ArrowUpDown className="h-3 w-3" />
                          </div>
                        </TableHead>
                        <TableHead>Rank</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedIndividuals.map((ind, idx) => (
                        <TableRow key={ind.id}>
                          <TableCell className="font-mono text-xs">{ind.id}</TableCell>
                          <TableCell>{ind.phenotype.toFixed(1)}</TableCell>
                          <TableCell>
                            {ind.gebv !== undefined ? (
                              <span className={ind.gebv > 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                                {ind.gebv > 0 ? '+' : ''}{ind.gebv.toFixed(3)}
                              </span>
                            ) : '-'}
                          </TableCell>
                          <TableCell>
                            {ind.reliability !== undefined ? (
                              <div className="flex items-center gap-2">
                                <div className="w-16 bg-muted rounded-full h-1.5">
                                  <div
                                    className="bg-blue-500 h-1.5 rounded-full"
                                    style={{ width: `${ind.reliability * 100}%` }}
                                  />
                                </div>
                                <span className="text-xs text-muted-foreground">{(ind.reliability * 100).toFixed(0)}%</span>
                              </div>
                            ) : '-'}
                          </TableCell>
                          <TableCell>
                            {results && (
                              <Badge variant={idx < 3 ? "default" : "secondary"} className="h-5 text-[10px]">
                                #{idx + 1}
                              </Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>

              <TabsContent value="plot" className="mt-0">
                <div className="h-[400px] w-full">
                  {results ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                        <CartesianGrid />
                        <XAxis type="number" dataKey="phenotype" name="Phenotype" unit="" label={{ value: 'Phenotype', position: 'bottom', offset: 0 }} />
                        <YAxis type="number" dataKey="gebv" name="GEBV" unit="" label={{ value: 'GEBV', angle: -90, position: 'left' }} />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                        <Scatter name="Individuals" data={updatedIndividuals} fill="#8884d8" />
                      </ScatterChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground">
                      Run analysis to see visualization
                    </div>
                  )}
                </div>
              </TabsContent>
            </CardContent>
          </Tabs>
        </Card>
      </div>
    </div>
  );
}

export default WasmGBLUP;
export { WasmGBLUP };

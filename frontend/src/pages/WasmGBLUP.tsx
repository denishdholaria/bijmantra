import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  Calculator, TrendingUp, BarChart3, Target, Dna, 
  ArrowUpDown, Download, Upload, Sparkles
} from 'lucide-react';
import { useWasm, useGBLUP, useGRM } from '@/wasm/hooks';

interface Individual {
  id: string;
  name: string;
  phenotype: number;
  gebv?: number;
  reliability?: number;
  accuracy?: number;
}

function WasmGBLUP() {
  const { isReady, version } = useWasm();
  const { calculate: calcGRM, result: grmResult } = useGRM();
  const { calculate: calcGBLUP, result: gblupResult, isCalculating } = useGBLUP();

  const [heritability, setHeritability] = useState(0.35);
  const [individuals, setIndividuals] = useState<Individual[]>([
    { id: 'G001', name: 'Elite Line 1', phenotype: 125.5 },
    { id: 'G002', name: 'Elite Line 2', phenotype: 118.2 },
    { id: 'G003', name: 'Elite Line 3', phenotype: 132.8 },
    { id: 'G004', name: 'Elite Line 4', phenotype: 121.0 },
    { id: 'G005', name: 'Elite Line 5', phenotype: 128.3 },
    { id: 'G006', name: 'Landrace 1', phenotype: 98.5 },
    { id: 'G007', name: 'Landrace 2', phenotype: 102.1 },
    { id: 'G008', name: 'Cross F1-1', phenotype: 115.7 },
    { id: 'G009', name: 'Cross F1-2', phenotype: 119.4 },
    { id: 'G010', name: 'Cross F1-3', phenotype: 122.6 },
  ]);
  const [sortBy, setSortBy] = useState<'gebv' | 'reliability' | 'phenotype'>('gebv');
  const [sortDesc, setSortDesc] = useState(true);

  // Generate simulated genotype data
  const generateGenotypes = (n: number, m: number) => {
    const data: number[] = [];
    for (let i = 0; i < n * m; i++) {
      const r = Math.random();
      data.push(r < 0.25 ? 0 : r < 0.75 ? 1 : 2);
    }
    return data;
  };

  const runGBLUP = () => {
    const n = individuals.length;
    const nMarkers = 500;
    
    // Generate genotypes and calculate GRM
    const genotypes = generateGenotypes(n, nMarkers);
    calcGRM(genotypes, n, nMarkers);
  };

  // When GRM is ready, run GBLUP
  const runGBLUPWithGRM = () => {
    if (!grmResult) return;
    
    const phenotypes = individuals.map(ind => ind.phenotype);
    calcGBLUP(phenotypes, grmResult.matrix, individuals.length, heritability);
  };

  // Update individuals with GBLUP results
  const getUpdatedIndividuals = () => {
    if (!gblupResult) return individuals;
    
    return individuals.map((ind, i) => ({
      ...ind,
      gebv: gblupResult.gebv[i],
      reliability: gblupResult.reliability[i],
      accuracy: gblupResult.accuracy[i],
    }));
  };

  const sortedIndividuals = [...getUpdatedIndividuals()].sort((a, b) => {
    const aVal = sortBy === 'gebv' ? (a.gebv ?? 0) : 
                 sortBy === 'reliability' ? (a.reliability ?? 0) : a.phenotype;
    const bVal = sortBy === 'gebv' ? (b.gebv ?? 0) : 
                 sortBy === 'reliability' ? (b.reliability ?? 0) : b.phenotype;
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
      ['ID', 'Name', 'Phenotype', 'GEBV', 'Reliability', 'Accuracy'].join(','),
      ...sortedIndividuals.map(ind => 
        [ind.id, ind.name, ind.phenotype, ind.gebv?.toFixed(3) ?? '', 
         ind.reliability?.toFixed(3) ?? '', ind.accuracy?.toFixed(3) ?? ''].join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gblup_results.csv';
    a.click();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Calculator className="h-8 w-8 text-blue-500" />
            Genomic BLUP Calculator
          </h1>
          <p className="text-muted-foreground mt-1">
            Genomic Best Linear Unbiased Prediction for breeding value estimation
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
              <Dna className="h-4 w-4 text-purple-500" />
              Individuals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{individuals.length}</div>
            <p className="text-xs text-muted-foreground">Genotyped entries</p>
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
              {gblupResult ? gblupResult.genetic_variance.toFixed(2) : '-'}
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
              {gblupResult ? gblupResult.mean.toFixed(2) : '-'}
            </div>
            <p className="text-xs text-muted-foreground">Population mean</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
            <CardDescription>Configure GBLUP analysis</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Heritability (h²)</Label>
                <Slider
                  value={[heritability]}
                  onValueChange={([v]) => setHeritability(v)}
                  min={0.05}
                  max={0.95}
                  step={0.05}
                />
                <div className="text-sm text-muted-foreground text-center">
                  {(heritability * 100).toFixed(0)}%
                </div>
              </div>

              <div className="space-y-2">
                <Label>Simulated Markers</Label>
                <Input value="500" disabled />
                <p className="text-xs text-muted-foreground">
                  SNP markers for GRM calculation
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <Button 
                onClick={runGBLUP} 
                disabled={!isReady || isCalculating}
                className="w-full"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                {isCalculating ? 'Calculating...' : 'Step 1: Calculate GRM'}
              </Button>

              <Button 
                onClick={runGBLUPWithGRM} 
                disabled={!isReady || !grmResult || isCalculating}
                variant="secondary"
                className="w-full"
              >
                <Calculator className="h-4 w-4 mr-2" />
                Step 2: Run GBLUP
              </Button>
            </div>

            {grmResult && (
              <Alert>
                <AlertDescription className="text-sm">
                  GRM calculated: {grmResult.n_markers_used} markers used, 
                  mean diagonal = {grmResult.mean_diagonal.toFixed(3)}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>GEBV Results</CardTitle>
                <CardDescription>Genomic Estimated Breeding Values</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={exportResults} disabled={!gblupResult}>
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Name</TableHead>
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
                    <TableCell className="font-mono text-sm">{ind.id}</TableCell>
                    <TableCell>{ind.name}</TableCell>
                    <TableCell>{ind.phenotype.toFixed(1)}</TableCell>
                    <TableCell>
                      {ind.gebv !== undefined ? (
                        <span className={ind.gebv > 0 ? 'text-green-600' : 'text-red-600'}>
                          {ind.gebv > 0 ? '+' : ''}{ind.gebv.toFixed(3)}
                        </span>
                      ) : '-'}
                    </TableCell>
                    <TableCell>
                      {ind.reliability !== undefined ? (
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-muted rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full" 
                              style={{ width: `${ind.reliability * 100}%` }}
                            />
                          </div>
                          <span className="text-sm">{(ind.reliability * 100).toFixed(0)}%</span>
                        </div>
                      ) : '-'}
                    </TableCell>
                    <TableCell>
                      {gblupResult && (
                        <Badge variant={idx < 3 ? "default" : "secondary"}>
                          #{idx + 1}
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>About GBLUP</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-sm max-w-none">
          <p className="text-muted-foreground">
            Genomic Best Linear Unbiased Prediction (GBLUP) uses genomic relationship information 
            derived from SNP markers to predict breeding values. The genomic relationship matrix (GRM) 
            captures the realized genetic relationships between individuals, providing more accurate 
            predictions than pedigree-based methods.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium">GEBV</h4>
              <p className="text-sm text-muted-foreground">
                Genomic Estimated Breeding Value - the predicted genetic merit of an individual
              </p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium">Reliability</h4>
              <p className="text-sm text-muted-foreground">
                Squared correlation between true and estimated breeding value (r²)
              </p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium">Accuracy</h4>
              <p className="text-sm text-muted-foreground">
                Correlation between true and estimated breeding value (r)
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default WasmGBLUP;
export { WasmGBLUP };

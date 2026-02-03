import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Cpu, Zap, Database, Activity, CheckCircle2, XCircle, 
  Play, BarChart3, Grid3X3, TrendingUp, Dna
} from 'lucide-react';
import { useWasm, useGRM, useDiversity, usePCA } from '@/wasm/hooks';

function WasmGenomics() {
  const { isLoading, isReady, version, error: wasmError } = useWasm();
  const { calculate: calcGRM, result: grmResult, isCalculating: grmCalc } = useGRM();
  const { calculate: calcDiv, result: divResult, isCalculating: divCalc } = useDiversity();
  const { calculate: calcPCA, result: pcaResult, isCalculating: pcaCalc } = usePCA();

  const [nSamples, setNSamples] = useState(100);
  const [nMarkers, setNMarkers] = useState(1000);
  const [benchmarkResults, setBenchmarkResults] = useState<{
    grm?: number;
    diversity?: number;
    pca?: number;
  }>({});

  // Generate random genotype data for testing
  const generateTestData = () => {
    const data: number[] = [];
    for (let i = 0; i < nSamples * nMarkers; i++) {
      const r = Math.random();
      data.push(r < 0.25 ? 0 : r < 0.75 ? 1 : 2);
    }
    return data;
  };

  const runGRMBenchmark = () => {
    const data = generateTestData();
    const start = performance.now();
    calcGRM(data, nSamples, nMarkers);
    const elapsed = performance.now() - start;
    setBenchmarkResults(prev => ({ ...prev, grm: elapsed }));
  };

  const runDiversityBenchmark = () => {
    const data = generateTestData();
    const start = performance.now();
    calcDiv(data, nSamples, nMarkers);
    const elapsed = performance.now() - start;
    setBenchmarkResults(prev => ({ ...prev, diversity: elapsed }));
  };

  const runPCABenchmark = () => {
    const data = generateTestData();
    const start = performance.now();
    calcPCA(data, nSamples, nMarkers);
    const elapsed = performance.now() - start;
    setBenchmarkResults(prev => ({ ...prev, pca: elapsed }));
  };

  const runAllBenchmarks = () => {
    runGRMBenchmark();
    setTimeout(runDiversityBenchmark, 100);
    setTimeout(runPCABenchmark, 200);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Cpu className="h-8 w-8 text-orange-500" />
            Genomics Benchmark
          </h1>
          <p className="text-muted-foreground mt-1">
            High-performance genomic computations at native speed
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isLoading ? (
            <Badge variant="secondary">Loading...</Badge>
          ) : isReady ? (
            <Badge className="bg-green-500">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              ⚡ WebAssembly v{version}
            </Badge>
          ) : (
            <Badge variant="destructive">
              <XCircle className="h-3 w-3 mr-1" />
              Engine Not Available
            </Badge>
          )}
        </div>
      </div>

      {wasmError && (
        <Alert variant="destructive">
          <AlertDescription>
            Compute engine failed to load: {wasmError.message}
          </AlertDescription>
        </Alert>
      )}

      {!isReady && !isLoading && (
        <Alert>
          <AlertDescription>
            Compute engine not built. Run: <code className="bg-muted px-1 rounded">cd rust && ./build.sh</code>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">~100x</div>
            <p className="text-xs text-muted-foreground">Faster than JavaScript</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Database className="h-4 w-4 text-blue-500" />
              Memory Safe
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Rust</div>
            <p className="text-xs text-muted-foreground">No buffer overflows</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-green-500" />
              Functions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">20+</div>
            <p className="text-xs text-muted-foreground">Genomic algorithms</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Dna className="h-4 w-4 text-purple-500" />
              Browser Native
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Local</div>
            <p className="text-xs text-muted-foreground">No server required</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="benchmark" className="space-y-4">
        <TabsList>
          <TabsTrigger value="benchmark">Benchmark</TabsTrigger>
          <TabsTrigger value="grm">GRM Calculator</TabsTrigger>
          <TabsTrigger value="diversity">Diversity</TabsTrigger>
          <TabsTrigger value="pca">PCA</TabsTrigger>
        </TabsList>

        <TabsContent value="benchmark">
          <Card>
            <CardHeader>
              <CardTitle>Performance Benchmark</CardTitle>
              <CardDescription>
                Test WASM performance with simulated genomic data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Number of Samples</Label>
                  <Input
                    type="number"
                    value={nSamples}
                    onChange={(e) => setNSamples(parseInt(e.target.value) || 100)}
                    min={10}
                    max={1000}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Number of Markers</Label>
                  <Input
                    type="number"
                    value={nMarkers}
                    onChange={(e) => setNMarkers(parseInt(e.target.value) || 1000)}
                    min={100}
                    max={10000}
                  />
                </div>
              </div>

              <div className="text-sm text-muted-foreground">
                Matrix size: {nSamples} × {nMarkers} = {(nSamples * nMarkers).toLocaleString()} genotypes
              </div>

              <Button onClick={runAllBenchmarks} disabled={!isReady || grmCalc || divCalc || pcaCalc}>
                <Play className="h-4 w-4 mr-2" />
                Run All Benchmarks
              </Button>

              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <Grid3X3 className="h-4 w-4" />
                      GRM Calculation
                    </span>
                    <span>{benchmarkResults.grm ? `${benchmarkResults.grm.toFixed(2)}ms` : '-'}</span>
                  </div>
                  <Progress value={benchmarkResults.grm ? Math.min(100, 100 - benchmarkResults.grm / 10) : 0} />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      Diversity Metrics
                    </span>
                    <span>{benchmarkResults.diversity ? `${benchmarkResults.diversity.toFixed(2)}ms` : '-'}</span>
                  </div>
                  <Progress value={benchmarkResults.diversity ? Math.min(100, 100 - benchmarkResults.diversity / 10) : 0} />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      PCA Analysis
                    </span>
                    <span>{benchmarkResults.pca ? `${benchmarkResults.pca.toFixed(2)}ms` : '-'}</span>
                  </div>
                  <Progress value={benchmarkResults.pca ? Math.min(100, 100 - benchmarkResults.pca / 10) : 0} />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="grm">
          <Card>
            <CardHeader>
              <CardTitle>Genomic Relationship Matrix</CardTitle>
              <CardDescription>
                Calculate GRM using VanRaden Method 1
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={runGRMBenchmark} disabled={!isReady || grmCalc}>
                {grmCalc ? 'Calculating...' : 'Calculate GRM'}
              </Button>

              {grmResult && (
                <div className="space-y-2">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Samples:</span>{' '}
                      <span className="font-medium">{grmResult.n_samples}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Markers Used:</span>{' '}
                      <span className="font-medium">{grmResult.n_markers_used}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Mean Diagonal:</span>{' '}
                      <span className="font-medium">{grmResult.mean_diagonal.toFixed(4)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Mean Off-diagonal:</span>{' '}
                      <span className="font-medium">{grmResult.mean_off_diagonal.toFixed(4)}</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="diversity">
          <Card>
            <CardHeader>
              <CardTitle>Genetic Diversity Metrics</CardTitle>
              <CardDescription>
                Shannon, Simpson, Nei diversity indices
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={runDiversityBenchmark} disabled={!isReady || divCalc}>
                {divCalc ? 'Calculating...' : 'Calculate Diversity'}
              </Button>

              {divResult && (
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Shannon Index:</span>{' '}
                    <span className="font-medium">{divResult.shannon_index.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Simpson Index:</span>{' '}
                    <span className="font-medium">{divResult.simpson_index.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Nei Diversity:</span>{' '}
                    <span className="font-medium">{divResult.nei_diversity.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Observed Het:</span>{' '}
                    <span className="font-medium">{divResult.observed_heterozygosity.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Expected Het:</span>{' '}
                    <span className="font-medium">{divResult.expected_heterozygosity.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Inbreeding (F):</span>{' '}
                    <span className="font-medium">{divResult.inbreeding_coefficient.toFixed(4)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Effective Alleles:</span>{' '}
                    <span className="font-medium">{divResult.effective_alleles.toFixed(2)}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pca">
          <Card>
            <CardHeader>
              <CardTitle>Principal Component Analysis</CardTitle>
              <CardDescription>
                Population structure analysis using PCA
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={runPCABenchmark} disabled={!isReady || pcaCalc}>
                {pcaCalc ? 'Calculating...' : 'Run PCA'}
              </Button>

              {pcaResult && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">PC1 Variance:</span>{' '}
                      <span className="font-medium">{pcaResult.variance_explained[0]?.toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">PC2 Variance:</span>{' '}
                      <span className="font-medium">{pcaResult.variance_explained[1]?.toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">PC3 Variance:</span>{' '}
                      <span className="font-medium">{pcaResult.variance_explained[2]?.toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    First 3 PCs explain {pcaResult.variance_explained.slice(0, 3).reduce((a, b) => a + b, 0).toFixed(1)}% of variance
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle>Available Functions</CardTitle>
          <CardDescription>High-performance genomic algorithms powered by WebAssembly</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h4 className="font-medium mb-2">Genomics</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Allele Frequencies</li>
                <li>• LD Calculation (r², D')</li>
                <li>• LD Matrix</li>
                <li>• Hardy-Weinberg Test</li>
                <li>• MAF Filtering</li>
                <li>• Missing Imputation</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Matrix Operations</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Genomic Relationship Matrix</li>
                <li>• Pedigree A-Matrix</li>
                <li>• Kinship Coefficient</li>
                <li>• IBS Matrix</li>
                <li>• Eigenvalue Decomposition</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Statistics</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• BLUP Estimation</li>
                <li>• GBLUP (Genomic BLUP)</li>
                <li>• Selection Index</li>
                <li>• Genetic Correlations</li>
                <li>• Heritability Estimation</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Population Genetics</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Diversity Metrics</li>
                <li>• Fst Calculation</li>
                <li>• Genetic Distance</li>
                <li>• PCA Analysis</li>
                <li>• AMMI Analysis</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default WasmGenomics;
export { WasmGenomics };

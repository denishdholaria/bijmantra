import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Users, Globe, BarChart3, Dna, TrendingUp, 
  Layers, GitBranch, Sparkles, Download
} from 'lucide-react';
import { useWasm, useDiversity, useFst, usePCA } from '@/wasm/hooks';

function WasmPopGen() {
  const { isReady, version } = useWasm();
  const { calculate: calcDiv, result: divResult, isCalculating: divCalc } = useDiversity();
  const { calculate: calcFst, result: fstResult, isCalculating: fstCalc } = useFst();
  const { calculate: calcPCA, result: pcaResult, isCalculating: pcaCalc } = usePCA();

  const [nPops, setNPops] = useState(3);
  const [samplesPerPop, setSamplesPerPop] = useState(30);
  const [nMarkers, setNMarkers] = useState(500);
  const [fstLevel, setFstLevel] = useState<'low' | 'medium' | 'high'>('medium');

  // Generate population-structured genotype data
  const generatePopulationData = () => {
    const totalSamples = nPops * samplesPerPop;
    const genotypes: number[] = [];
    const popIds: number[] = [];

    // Differentiation levels
    const fstValues = { low: 0.02, medium: 0.08, high: 0.20 };
    const targetFst = fstValues[fstLevel];

    for (let pop = 0; pop < nPops; pop++) {
      // Generate population-specific allele frequencies
      const popFreqs: number[] = [];
      for (let m = 0; m < nMarkers; m++) {
        // Base frequency with population drift
        const baseFreq = 0.3 + Math.random() * 0.4;
        const drift = (Math.random() - 0.5) * targetFst * 2;
        popFreqs.push(Math.max(0.05, Math.min(0.95, baseFreq + drift * pop)));
      }

      // Generate individuals for this population
      for (let i = 0; i < samplesPerPop; i++) {
        popIds.push(pop);
        for (let m = 0; m < nMarkers; m++) {
          const p = popFreqs[m];
          // Generate genotype based on HWE
          const r1 = Math.random();
          const r2 = Math.random();
          const allele1 = r1 < p ? 1 : 0;
          const allele2 = r2 < p ? 1 : 0;
          genotypes.push(allele1 + allele2);
        }
      }
    }

    return { genotypes, popIds, totalSamples };
  };

  const runDiversityAnalysis = () => {
    const { genotypes, totalSamples } = generatePopulationData();
    calcDiv(genotypes, totalSamples, nMarkers);
  };

  const runFstAnalysis = () => {
    const { genotypes, popIds, totalSamples } = generatePopulationData();
    calcFst(genotypes, popIds, totalSamples, nMarkers);
  };

  const runPCAAnalysis = () => {
    const { genotypes, totalSamples } = generatePopulationData();
    calcPCA(genotypes, totalSamples, nMarkers);
  };

  const runAllAnalyses = () => {
    runDiversityAnalysis();
    setTimeout(runFstAnalysis, 100);
    setTimeout(runPCAAnalysis, 200);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="h-8 w-8 text-green-500" />
            Population Genetics
          </h1>
          <p className="text-muted-foreground mt-1">
            Diversity analysis, Fst, and population structure (PCA)
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
              <Globe className="h-4 w-4 text-blue-500" />
              Populations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{nPops}</div>
            <p className="text-xs text-muted-foreground">Distinct groups</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Users className="h-4 w-4 text-purple-500" />
              Total Samples
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{nPops * samplesPerPop}</div>
            <p className="text-xs text-muted-foreground">Individuals</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Dna className="h-4 w-4 text-orange-500" />
              Markers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{nMarkers}</div>
            <p className="text-xs text-muted-foreground">SNP loci</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-red-500" />
              Fst Level
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{fstLevel}</div>
            <p className="text-xs text-muted-foreground">Differentiation</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Simulation Parameters</CardTitle>
          <CardDescription>Configure population structure simulation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Number of Populations</Label>
              <Input
                type="number"
                value={nPops}
                onChange={(e) => setNPops(parseInt(e.target.value) || 2)}
                min={2}
                max={10}
              />
            </div>
            <div className="space-y-2">
              <Label>Samples per Population</Label>
              <Input
                type="number"
                value={samplesPerPop}
                onChange={(e) => setSamplesPerPop(parseInt(e.target.value) || 20)}
                min={10}
                max={100}
              />
            </div>
            <div className="space-y-2">
              <Label>Number of Markers</Label>
              <Input
                type="number"
                value={nMarkers}
                onChange={(e) => setNMarkers(parseInt(e.target.value) || 500)}
                min={100}
                max={5000}
              />
            </div>
            <div className="space-y-2">
              <Label>Differentiation Level</Label>
              <Select value={fstLevel} onValueChange={(v) => setFstLevel(v as any)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low (Fst ~0.02)</SelectItem>
                  <SelectItem value="medium">Medium (Fst ~0.08)</SelectItem>
                  <SelectItem value="high">High (Fst ~0.20)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4">
            <Button onClick={runAllAnalyses} disabled={!isReady || divCalc || fstCalc || pcaCalc}>
              <Sparkles className="h-4 w-4 mr-2" />
              Run All Analyses
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="diversity" className="space-y-4">
        <TabsList>
          <TabsTrigger value="diversity">Diversity</TabsTrigger>
          <TabsTrigger value="fst">Population Differentiation</TabsTrigger>
          <TabsTrigger value="pca">PCA</TabsTrigger>
        </TabsList>

        <TabsContent value="diversity">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Genetic Diversity Metrics
              </CardTitle>
              <CardDescription>
                Population-level diversity indices
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={runDiversityAnalysis} disabled={!isReady || divCalc} className="mb-4">
                {divCalc ? 'Calculating...' : 'Calculate Diversity'}
              </Button>

              {divResult && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm text-muted-foreground">Shannon Index</div>
                    <div className="text-2xl font-bold">{divResult.shannon_index.toFixed(4)}</div>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm text-muted-foreground">Simpson Index</div>
                    <div className="text-2xl font-bold">{divResult.simpson_index.toFixed(4)}</div>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm text-muted-foreground">Nei's Diversity</div>
                    <div className="text-2xl font-bold">{divResult.nei_diversity.toFixed(4)}</div>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm text-muted-foreground">Effective Alleles</div>
                    <div className="text-2xl font-bold">{divResult.effective_alleles.toFixed(2)}</div>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm text-muted-foreground">Observed Het (Ho)</div>
                    <div className="text-2xl font-bold">{divResult.observed_heterozygosity.toFixed(4)}</div>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm text-muted-foreground">Expected Het (He)</div>
                    <div className="text-2xl font-bold">{divResult.expected_heterozygosity.toFixed(4)}</div>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm text-muted-foreground">Inbreeding (F)</div>
                    <div className={`text-2xl font-bold ${divResult.inbreeding_coefficient > 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {divResult.inbreeding_coefficient.toFixed(4)}
                    </div>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm text-muted-foreground">Ho/He Ratio</div>
                    <div className="text-2xl font-bold">
                      {(divResult.observed_heterozygosity / divResult.expected_heterozygosity).toFixed(3)}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fst">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-5 w-5" />
                Population Differentiation (Fst)
              </CardTitle>
              <CardDescription>
                Fixation indices measuring genetic differentiation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={runFstAnalysis} disabled={!isReady || fstCalc} className="mb-4">
                {fstCalc ? 'Calculating...' : 'Calculate Fst'}
              </Button>

              {fstResult && (
                <div className="space-y-6">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-sm text-muted-foreground">Fst (Global)</div>
                      <div className={`text-3xl font-bold ${
                        fstResult.fst < 0.05 ? 'text-green-500' :
                        fstResult.fst < 0.15 ? 'text-yellow-500' : 'text-red-500'
                      }`}>
                        {fstResult.fst.toFixed(4)}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {fstResult.fst < 0.05 ? 'Little differentiation' :
                         fstResult.fst < 0.15 ? 'Moderate differentiation' :
                         fstResult.fst < 0.25 ? 'Great differentiation' : 'Very great differentiation'}
                      </div>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-sm text-muted-foreground">Fis</div>
                      <div className="text-3xl font-bold">{fstResult.fis.toFixed(4)}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Inbreeding within populations
                      </div>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-sm text-muted-foreground">Fit</div>
                      <div className="text-3xl font-bold">{fstResult.fit.toFixed(4)}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Total inbreeding
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Fst Interpretation Guide</h4>
                    <div className="grid grid-cols-4 gap-2 text-sm">
                      <div className="p-2 bg-green-100 dark:bg-green-900 rounded">
                        <div className="font-medium">0 - 0.05</div>
                        <div className="text-muted-foreground">Little</div>
                      </div>
                      <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded">
                        <div className="font-medium">0.05 - 0.15</div>
                        <div className="text-muted-foreground">Moderate</div>
                      </div>
                      <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded">
                        <div className="font-medium">0.15 - 0.25</div>
                        <div className="text-muted-foreground">Great</div>
                      </div>
                      <div className="p-2 bg-red-100 dark:bg-red-900 rounded">
                        <div className="font-medium">&gt; 0.25</div>
                        <div className="text-muted-foreground">Very Great</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pca">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Principal Component Analysis
              </CardTitle>
              <CardDescription>
                Population structure visualization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={runPCAAnalysis} disabled={!isReady || pcaCalc} className="mb-4">
                {pcaCalc ? 'Calculating...' : 'Run PCA'}
              </Button>

              {pcaResult && (
                <div className="space-y-6">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-sm text-muted-foreground">PC1</div>
                      <div className="text-2xl font-bold text-blue-500">
                        {pcaResult.variance_explained[0]?.toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">Variance explained</div>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-sm text-muted-foreground">PC2</div>
                      <div className="text-2xl font-bold text-green-500">
                        {pcaResult.variance_explained[1]?.toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">Variance explained</div>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-sm text-muted-foreground">PC3</div>
                      <div className="text-2xl font-bold text-purple-500">
                        {pcaResult.variance_explained[2]?.toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">Variance explained</div>
                    </div>
                  </div>

                  <div className="p-4 bg-muted rounded-lg">
                    <div className="text-sm font-medium mb-2">Cumulative Variance</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-background rounded-full h-4 overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 via-green-500 to-purple-500"
                          style={{ 
                            width: `${pcaResult.variance_explained.slice(0, 3).reduce((a, b) => a + b, 0)}%` 
                          }}
                        />
                      </div>
                      <span className="text-sm font-medium">
                        {pcaResult.variance_explained.slice(0, 3).reduce((a, b) => a + b, 0).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      First 3 principal components explain {pcaResult.variance_explained.slice(0, 3).reduce((a, b) => a + b, 0).toFixed(1)}% of total genetic variance
                    </p>
                  </div>

                  <div className="text-sm text-muted-foreground">
                    <p>
                      PCA reveals population structure by identifying axes of maximum genetic variation.
                      Higher variance explained by PC1 indicates stronger population differentiation.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default WasmPopGen;
export { WasmPopGen };

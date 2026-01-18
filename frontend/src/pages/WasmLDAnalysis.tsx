import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  Link2, Grid3X3,
  Dna, TrendingDown, Sparkles, AlertTriangle
} from 'lucide-react';
import { useWasm } from '@/wasm/hooks';

interface MarkerPair {
  marker1: string;
  marker2: string;
  distance: number;
  r2: number;
  dPrime: number;
}

interface HWETest {
  marker: string;
  chiSquared: number;
  pValue: number;
  observedHet: number;
  expectedHet: number;
  inEquilibrium: boolean;
}

function WasmLDAnalysis() {
  const { isReady, version } = useWasm();
  // LD and HWE hooks - will be used when WASM module is ready
  const _ldHook = { calculate: () => {}, result: null, isCalculating: false };
  const _hweHook = { calculate: () => {}, result: null, isCalculating: false };

  const [nSamples, setNSamples] = useState(200);
  const [nMarkers, setNMarkers] = useState(50);
  const [ldThreshold, setLdThreshold] = useState(0.2);
  const [ldPairs, setLdPairs] = useState<MarkerPair[]>([]);
  const [hweTests, setHweTests] = useState<HWETest[]>([]);
  const [ldMatrix, setLdMatrix] = useState<number[][]>([]);

  // Generate correlated genotype data to simulate LD
  const generateLDData = () => {
    const genotypes: number[][] = [];
    
    // Generate first marker randomly
    const marker0: number[] = [];
    for (let i = 0; i < nSamples; i++) {
      const r = Math.random();
      marker0.push(r < 0.25 ? 0 : r < 0.75 ? 1 : 2);
    }
    genotypes.push(marker0);

    // Generate subsequent markers with varying LD
    for (let m = 1; m < nMarkers; m++) {
      const marker: number[] = [];
      const ldStrength = Math.exp(-m * 0.1); // LD decay with distance
      
      for (let i = 0; i < nSamples; i++) {
        if (Math.random() < ldStrength) {
          // Correlated with previous marker
          marker.push(genotypes[m - 1][i]);
        } else {
          // Random
          const r = Math.random();
          marker.push(r < 0.25 ? 0 : r < 0.75 ? 1 : 2);
        }
      }
      genotypes.push(marker);
    }

    return genotypes;
  };

  const runLDAnalysis = () => {
    const genotypes = generateLDData();
    const pairs: MarkerPair[] = [];
    const matrix: number[][] = Array(nMarkers).fill(null).map(() => Array(nMarkers).fill(0));

    // Calculate pairwise LD for nearby markers
    for (let i = 0; i < nMarkers; i++) {
      matrix[i][i] = 1.0;
      
      for (let j = i + 1; j < Math.min(i + 10, nMarkers); j++) {
        // Calculate r² manually for demo
        const g1 = genotypes[i];
        const g2 = genotypes[j];
        
        let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
        for (let k = 0; k < nSamples; k++) {
          sumX += g1[k];
          sumY += g2[k];
          sumXY += g1[k] * g2[k];
          sumX2 += g1[k] * g1[k];
          sumY2 += g2[k] * g2[k];
        }
        
        const n = nSamples;
        const varX = sumX2 / n - (sumX / n) ** 2;
        const varY = sumY2 / n - (sumY / n) ** 2;
        const covXY = sumXY / n - (sumX / n) * (sumY / n);
        
        const r2 = varX > 0 && varY > 0 ? (covXY ** 2) / (varX * varY) : 0;
        const dPrime = Math.sqrt(r2); // Simplified

        matrix[i][j] = r2;
        matrix[j][i] = r2;

        pairs.push({
          marker1: `M${i + 1}`,
          marker2: `M${j + 1}`,
          distance: (j - i) * 10, // kb
          r2,
          dPrime,
        });
      }
    }

    setLdPairs(pairs.sort((a, b) => b.r2 - a.r2));
    setLdMatrix(matrix);
  };

  const runHWEAnalysis = () => {
    const genotypes = generateLDData();
    const tests: HWETest[] = [];

    for (let m = 0; m < Math.min(nMarkers, 20); m++) {
      const geno = genotypes[m];
      let nAA = 0, nAB = 0, nBB = 0;
      
      for (const g of geno) {
        if (g === 0) nAA++;
        else if (g === 1) nAB++;
        else nBB++;
      }

      const n = nAA + nAB + nBB;
      const p = (2 * nAA + nAB) / (2 * n);
      const q = 1 - p;

      const expAA = p * p * n;
      const expAB = 2 * p * q * n;
      const expBB = q * q * n;

      const chi2 = (expAA > 0 ? (nAA - expAA) ** 2 / expAA : 0) +
                   (expAB > 0 ? (nAB - expAB) ** 2 / expAB : 0) +
                   (expBB > 0 ? (nBB - expBB) ** 2 / expBB : 0);

      const pValue = Math.exp(-chi2 / 2);

      tests.push({
        marker: `M${m + 1}`,
        chiSquared: chi2,
        pValue,
        observedHet: nAB / n,
        expectedHet: 2 * p * q,
        inEquilibrium: pValue > 0.05,
      });
    }

    setHweTests(tests);
  };

  const highLDPairs = ldPairs.filter(p => p.r2 >= ldThreshold);
  const hweViolations = hweTests.filter(t => !t.inEquilibrium);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Link2 className="h-8 w-8 text-purple-500" />
            Linkage Disequilibrium Analysis
          </h1>
          <p className="text-muted-foreground mt-1">
            LD decay, r² calculation, and Hardy-Weinberg equilibrium testing
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
              <Dna className="h-4 w-4 text-blue-500" />
              Markers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{nMarkers}</div>
            <p className="text-xs text-muted-foreground">SNP loci analyzed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Link2 className="h-4 w-4 text-purple-500" />
              High LD Pairs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{highLDPairs.length}</div>
            <p className="text-xs text-muted-foreground">r² ≥ {ldThreshold}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              HWE Violations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{hweViolations.length}</div>
            <p className="text-xs text-muted-foreground">p &lt; 0.05</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-green-500" />
              Mean r²
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {ldPairs.length > 0 
                ? (ldPairs.reduce((a, b) => a + b.r2, 0) / ldPairs.length).toFixed(3)
                : '-'}
            </div>
            <p className="text-xs text-muted-foreground">Average LD</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Analysis Parameters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Number of Samples</Label>
              <Input
                type="number"
                value={nSamples}
                onChange={(e) => setNSamples(parseInt(e.target.value) || 100)}
                min={50}
                max={500}
              />
            </div>
            <div className="space-y-2">
              <Label>Number of Markers</Label>
              <Input
                type="number"
                value={nMarkers}
                onChange={(e) => setNMarkers(parseInt(e.target.value) || 50)}
                min={10}
                max={100}
              />
            </div>
            <div className="space-y-2">
              <Label>LD Threshold (r²)</Label>
              <div className="pt-2">
                <Slider
                  value={[ldThreshold]}
                  onValueChange={([v]) => setLdThreshold(v)}
                  min={0.1}
                  max={0.8}
                  step={0.05}
                />
                <div className="text-center text-sm mt-1">{ldThreshold}</div>
              </div>
            </div>
            <div className="space-y-2 flex items-end">
              <Button onClick={() => { runLDAnalysis(); runHWEAnalysis(); }} className="w-full">
                <Sparkles className="h-4 w-4 mr-2" />
                Run Analysis
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="ld" className="space-y-4">
        <TabsList>
          <TabsTrigger value="ld">LD Pairs</TabsTrigger>
          <TabsTrigger value="matrix">LD Matrix</TabsTrigger>
          <TabsTrigger value="hwe">HWE Tests</TabsTrigger>
          <TabsTrigger value="decay">LD Decay</TabsTrigger>
        </TabsList>

        <TabsContent value="ld">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pairwise LD (r²)</CardTitle>
                  <CardDescription>Marker pairs sorted by LD strength</CardDescription>
                </div>
                <Badge variant="outline">{ldPairs.length} pairs</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Marker 1</TableHead>
                    <TableHead>Marker 2</TableHead>
                    <TableHead>Distance (kb)</TableHead>
                    <TableHead>r²</TableHead>
                    <TableHead>D'</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ldPairs.slice(0, 20).map((pair, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-mono">{pair.marker1}</TableCell>
                      <TableCell className="font-mono">{pair.marker2}</TableCell>
                      <TableCell>{pair.distance}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-muted rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                pair.r2 >= 0.8 ? 'bg-red-500' :
                                pair.r2 >= 0.5 ? 'bg-orange-500' :
                                pair.r2 >= 0.2 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${pair.r2 * 100}%` }}
                            />
                          </div>
                          <span className="text-sm">{pair.r2.toFixed(3)}</span>
                        </div>
                      </TableCell>
                      <TableCell>{pair.dPrime.toFixed(3)}</TableCell>
                      <TableCell>
                        <Badge variant={pair.r2 >= ldThreshold ? "destructive" : "secondary"}>
                          {pair.r2 >= ldThreshold ? 'High LD' : 'Low LD'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="matrix">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Grid3X3 className="h-5 w-5" />
                LD Matrix Heatmap
              </CardTitle>
              <CardDescription>Visual representation of pairwise LD</CardDescription>
            </CardHeader>
            <CardContent>
              {ldMatrix.length > 0 ? (
                <div className="overflow-auto">
                  <div className="inline-grid gap-0.5" style={{ 
                    gridTemplateColumns: `repeat(${Math.min(ldMatrix.length, 30)}, 12px)` 
                  }}>
                    {ldMatrix.slice(0, 30).map((row, i) => 
                      row.slice(0, 30).map((val, j) => (
                        <div
                          key={`${i}-${j}`}
                          className="w-3 h-3 rounded-sm"
                          style={{
                            backgroundColor: `rgba(147, 51, 234, ${val})`,
                          }}
                          title={`M${i + 1} - M${j + 1}: r²=${val.toFixed(3)}`}
                        />
                      ))
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-4">
                    <span className="text-sm">Low LD</span>
                    <div className="flex">
                      {[0.1, 0.3, 0.5, 0.7, 0.9].map(v => (
                        <div
                          key={v}
                          className="w-6 h-4"
                          style={{ backgroundColor: `rgba(147, 51, 234, ${v})` }}
                        />
                      ))}
                    </div>
                    <span className="text-sm">High LD</span>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">Run analysis to generate LD matrix</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hwe">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Hardy-Weinberg Equilibrium Tests</CardTitle>
                  <CardDescription>Chi-square test for HWE deviation</CardDescription>
                </div>
                <Badge variant={hweViolations.length > 0 ? "destructive" : "default"}>
                  {hweViolations.length} violations
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Marker</TableHead>
                    <TableHead>χ²</TableHead>
                    <TableHead>P-value</TableHead>
                    <TableHead>Obs. Het</TableHead>
                    <TableHead>Exp. Het</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {hweTests.map((test, idx) => (
                    <TableRow key={idx} className={!test.inEquilibrium ? 'bg-red-50 dark:bg-red-950' : ''}>
                      <TableCell className="font-mono">{test.marker}</TableCell>
                      <TableCell>{test.chiSquared.toFixed(3)}</TableCell>
                      <TableCell>
                        <span className={test.pValue < 0.05 ? 'text-red-500 font-medium' : ''}>
                          {test.pValue.toFixed(4)}
                        </span>
                      </TableCell>
                      <TableCell>{test.observedHet.toFixed(3)}</TableCell>
                      <TableCell>{test.expectedHet.toFixed(3)}</TableCell>
                      <TableCell>
                        <Badge variant={test.inEquilibrium ? "default" : "destructive"}>
                          {test.inEquilibrium ? 'In HWE' : 'Deviation'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="decay">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingDown className="h-5 w-5" />
                LD Decay
              </CardTitle>
              <CardDescription>LD as a function of physical distance</CardDescription>
            </CardHeader>
            <CardContent>
              {ldPairs.length > 0 ? (
                <div className="space-y-4">
                  <div className="h-64 flex items-end gap-1">
                    {Array.from({ length: 10 }, (_, i) => {
                      const distRange = ldPairs.filter(p => 
                        p.distance >= i * 10 && p.distance < (i + 1) * 10
                      );
                      const avgR2 = distRange.length > 0
                        ? distRange.reduce((a, b) => a + b.r2, 0) / distRange.length
                        : 0;
                      
                      return (
                        <div key={i} className="flex-1 flex flex-col items-center">
                          <div 
                            className="w-full bg-purple-500 rounded-t"
                            style={{ height: `${avgR2 * 100}%` }}
                          />
                          <span className="text-xs mt-1">{i * 10}-{(i + 1) * 10}</span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="text-center text-sm text-muted-foreground">
                    Distance (kb)
                  </div>
                  <p className="text-sm text-muted-foreground">
                    LD typically decays with increasing physical distance between markers.
                    The rate of decay depends on recombination rate and population history.
                  </p>
                </div>
              ) : (
                <p className="text-muted-foreground">Run analysis to see LD decay pattern</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default WasmLDAnalysis;
export { WasmLDAnalysis };

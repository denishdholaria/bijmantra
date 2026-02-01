import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Switch } from '@/components/ui/switch';
import { 
  Link2, Grid3X3,
  Dna, TrendingDown, Sparkles, AlertTriangle, Server
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useWasm, useLD, useHWE } from '@/wasm/hooks';
import { apiClient } from '@/lib/api-client';

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

interface LDDecayPoint {
  distance: number;
  mean_r2: number;
  pair_count: number;
}

function WasmLDAnalysis() {
  const { isReady, version, wasm } = useWasm();
  const ldHook = useLD();
  const hweHook = useHWE();

  const [useServer, setUseServer] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const [nSamples, setNSamples] = useState(200);
  const [nMarkers, setNMarkers] = useState(50);
  const [ldThreshold, setLdThreshold] = useState(0.2);
  const [ldPairs, setLdPairs] = useState<MarkerPair[]>([]);
  const [hweTests, setHweTests] = useState<HWETest[]>([]);
  const [ldMatrix, setLdMatrix] = useState<number[][]>([]);
  const [decayData, setDecayData] = useState<LDDecayPoint[]>([]);

  // Generate correlated genotype data to simulate LD (Client Side)
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

  const runAnalysis = async () => {
    setIsProcessing(true);
    try {
      if (useServer) {
        // Server Side Analysis
        const response = await apiClient.post('/api/v2/ld/calculate', {
          window_size: 50,
          variant_set_id: "demo-set" // Trigger backend mock/real logic
        });
        const data = response.data;

        const pairs: MarkerPair[] = data.pairs.map((p: any) => ({
            marker1: p.marker1,
            marker2: p.marker2,
            distance: p.distance,
            r2: p.r2,
            dPrime: p.d_prime || Math.sqrt(p.r2)
        }));

        setLdPairs(pairs);
        setNMarkers(data.marker_count);
        setNSamples(data.sample_count);
        
        // Fetch decay
        try {
            const decayRes = await apiClient.post('/api/v2/ld/decay', {
                max_distance: 100000,
                bin_size: 1000,
                variant_set_id: "demo-set"
            });
            setDecayData(decayRes.data.decay_curve);
        } catch (e) {
            console.error("Failed to fetch decay", e);
        }

        // Fetch matrix
        try {
            const matrixRes = await apiClient.get('/api/v2/ld/matrix/region1?variant_set_id=demo-set');
            setLdMatrix(matrixRes.data.matrix);
        } catch (e) {
            console.error("Failed to fetch matrix", e);
            setLdMatrix([]);
        }

        setHweTests([]);

      } else {
        // Client Side (JS/WASM)
        const genotypes = generateLDData();
        const pairs: MarkerPair[] = [];
        const matrix: number[][] = Array(nMarkers).fill(null).map(() => Array(nMarkers).fill(0));

        // Calculate pairwise LD
        for (let i = 0; i < nMarkers; i++) {
          matrix[i][i] = 1.0;

          for (let j = i + 1; j < Math.min(i + 10, nMarkers); j++) {
            let r2 = 0;
            let dPrime = 0;
            let calculated = false;

            // Try WASM
            if (isReady && wasm) {
                try {
                    const g1 = new Int32Array(genotypes[i]);
                    const g2 = new Int32Array(genotypes[j]);
                    const res = wasm.calculate_ld_pair(g1, g2);
                    r2 = res.r2;
                    dPrime = res.d_prime;
                    calculated = true;
                } catch (e) {
                    // WASM failed, fallback to JS
                }
            }

            if (!calculated) {
                // JS Calculation
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

                r2 = varX > 0 && varY > 0 ? (covXY ** 2) / (varX * varY) : 0;
                dPrime = Math.sqrt(r2);
            }

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

        // Generate client-side decay data from pairs
        const bins: Record<number, {sum: number, count: number}> = {};
        pairs.forEach(p => {
             // distance is in kb in pairs mock
             const bin = Math.floor(p.distance / 10) * 10;
             if (!bins[bin]) bins[bin] = {sum: 0, count: 0};
             bins[bin].sum += p.r2;
             bins[bin].count++;
        });
        const clientDecay = Object.keys(bins).sort((a,b)=>Number(a)-Number(b)).map(d => ({
             distance: Number(d),
             mean_r2: bins[Number(d)].sum / bins[Number(d)].count,
             pair_count: bins[Number(d)].count
        }));
        setDecayData(clientDecay);

        // HWE Analysis
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
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
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
                disabled={useServer}
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
                disabled={useServer}
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
            <div className="space-y-2 flex flex-col justify-end">
              <div className="flex items-center space-x-2 mb-2">
                <Switch
                    id="server-mode"
                    checked={useServer}
                    onCheckedChange={setUseServer}
                />
                <Label htmlFor="server-mode" className="text-xs flex items-center gap-1 cursor-pointer">
                    <Server className="h-3 w-3" />
                    Server-Side
                </Label>
              </div>
              <Button onClick={runAnalysis} className="w-full" disabled={isProcessing}>
                <Sparkles className="h-4 w-4 mr-2" />
                {isProcessing ? 'Analyzing...' : 'Run Analysis'}
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
              {decayData.length > 0 ? (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={decayData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="distance"
                        label={{ value: 'Distance (bp)', position: 'insideBottom', offset: -5 }}
                        tickFormatter={(v) => v >= 1000 ? `${v/1000}k` : v}
                      />
                      <YAxis label={{ value: 'Mean r²', angle: -90, position: 'insideLeft' }} domain={[0, 1]} />
                      <Tooltip
                        labelFormatter={(v) => `${v} bp`}
                        formatter={(v: number) => [v.toFixed(3), "Mean r²"]}
                      />
                      <Line type="monotone" dataKey="mean_r2" stroke="#8884d8" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                  <p className="text-sm text-muted-foreground mt-4 text-center">
                    Based on {decayData.reduce((acc, curr) => acc + curr.pair_count, 0)} pairwise comparisons
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

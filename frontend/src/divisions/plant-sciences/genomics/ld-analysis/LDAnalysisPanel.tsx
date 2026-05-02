/**
 * LDAnalysisPanel
 * Division-owned UI panel for Linkage Disequilibrium analysis
 * Extracted from pages/WasmLDAnalysis.tsx as part of Titanium Path convergence
 */

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
import { useLDAnalysis } from './useLDAnalysis';

export function LDAnalysisPanel() {
  const {
    isProcessing, useServer, serverVariantSetId, analysisMessage,
    nSamples, nMarkers, ldThreshold,
    ldPairs, hweTests, ldMatrix, decayData,
    highLDPairs, hweViolations,
    wasmReady, wasmVersion, syntheticPreviewAvailable,
    update, runAnalysis,
  } = useLDAnalysis();

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
        <Badge variant={wasmReady ? "default" : "secondary"} className={wasmReady ? "bg-green-500" : ""}>
          {wasmReady ? `⚡ WebAssembly v${wasmVersion}` : 'Loading...'}
        </Badge>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Dna className="h-4 w-4 text-blue-500" /> Markers
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
              <Link2 className="h-4 w-4 text-purple-500" /> High LD Pairs
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
              <AlertTriangle className="h-4 w-4 text-orange-500" /> HWE Violations
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
              <TrendingDown className="h-4 w-4 text-green-500" /> Mean r²
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

      {/* Analysis Parameters */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Parameters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`grid grid-cols-1 gap-4 ${useServer ? 'md:grid-cols-5' : 'md:grid-cols-4'}`}>
            <div className="space-y-2">
              <Label>Number of Samples</Label>
              <Input
                type="number" value={nSamples}
                onChange={(e) => update({ nSamples: parseInt(e.target.value) || 100 })}
                min={50} max={500} disabled={useServer}
              />
            </div>
            <div className="space-y-2">
              <Label>Number of Markers</Label>
              <Input
                type="number" value={nMarkers}
                onChange={(e) => update({ nMarkers: parseInt(e.target.value) || 50 })}
                min={10} max={100} disabled={useServer}
              />
            </div>
            {useServer && (
              <div className="space-y-2">
                <Label htmlFor="ld-variant-set-id">Variant Set ID</Label>
                <Input
                  id="ld-variant-set-id"
                  value={serverVariantSetId}
                  onChange={(e) => update({ serverVariantSetId: e.target.value })}
                  placeholder="Enter a VariantSetDbId"
                />
              </div>
            )}
            <div className="space-y-2">
              <Label>LD Threshold (r²)</Label>
              <div className="pt-2">
                <Slider
                  value={[ldThreshold]}
                  onValueChange={([v]) => update({ ldThreshold: v })}
                  min={0.1} max={0.8} step={0.05}
                />
                <div className="text-center text-sm mt-1">{ldThreshold}</div>
              </div>
            </div>
            <div className="space-y-2 flex flex-col justify-end">
              {syntheticPreviewAvailable ? (
                <div className="flex items-center space-x-2 mb-2">
                  <Switch id="server-mode" checked={useServer} onCheckedChange={(v) => update({ useServer: v })} />
                  <Label htmlFor="server-mode" className="text-xs flex items-center gap-1 cursor-pointer">
                    <Server className="h-3 w-3" /> Server-Side
                  </Label>
                </div>
              ) : (
                <p className="mb-2 text-xs text-muted-foreground">
                  Production builds run against stored variant sets only.
                </p>
              )}
              <Button onClick={runAnalysis} className="w-full" disabled={isProcessing}>
                <Sparkles className="h-4 w-4 mr-2" />
                {isProcessing ? 'Analyzing...' : 'Run Analysis'}
              </Button>
            </div>
          </div>
          {analysisMessage && (
            <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200">
              {analysisMessage}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Tabs */}
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
                <Grid3X3 className="h-5 w-5" /> LD Matrix Heatmap
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
                          style={{ backgroundColor: `rgba(147, 51, 234, ${val})` }}
                          title={`M${i + 1} - M${j + 1}: r²=${val.toFixed(3)}`}
                        />
                      ))
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-4">
                    <span className="text-sm">Low LD</span>
                    <div className="flex">
                      {[0.1, 0.3, 0.5, 0.7, 0.9].map(v => (
                        <div key={v} className="w-6 h-4" style={{ backgroundColor: `rgba(147, 51, 234, ${v})` }} />
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
                <TrendingDown className="h-5 w-5" /> LD Decay
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
                        tickFormatter={(v) => v >= 1000 ? `${v / 1000}k` : v}
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

export default LDAnalysisPanel;

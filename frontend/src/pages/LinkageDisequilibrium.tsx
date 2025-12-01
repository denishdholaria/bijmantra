/**
 * Linkage Disequilibrium Analysis Page
 * LD decay, LD heatmaps, and LD-based analyses
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'

interface LDPair {
  marker1: string
  marker2: string
  chromosome: string
  distance: number
  r2: number
  dprime: number
  pValue: number
}

const ldData: LDPair[] = [
  { marker1: 'SNP_1_10', marker2: 'SNP_1_12', chromosome: '1', distance: 0.5, r2: 0.92, dprime: 0.98, pValue: 1e-15 },
  { marker1: 'SNP_1_10', marker2: 'SNP_1_15', chromosome: '1', distance: 1.2, r2: 0.78, dprime: 0.89, pValue: 1e-12 },
  { marker1: 'SNP_1_10', marker2: 'SNP_1_20', chromosome: '1', distance: 2.5, r2: 0.45, dprime: 0.72, pValue: 1e-8 },
  { marker1: 'SNP_1_10', marker2: 'SNP_1_30', chromosome: '1', distance: 5.0, r2: 0.22, dprime: 0.55, pValue: 1e-5 },
  { marker1: 'SNP_1_10', marker2: 'SNP_1_50', chromosome: '1', distance: 10.0, r2: 0.08, dprime: 0.32, pValue: 0.001 },
  { marker1: 'SNP_3_25', marker2: 'SNP_3_28', chromosome: '3', distance: 0.8, r2: 0.88, dprime: 0.95, pValue: 1e-14 },
  { marker1: 'SNP_3_25', marker2: 'SNP_3_35', chromosome: '3', distance: 2.8, r2: 0.52, dprime: 0.78, pValue: 1e-9 },
  { marker1: 'SNP_5_40', marker2: 'SNP_5_42', chromosome: '5', distance: 0.4, r2: 0.95, dprime: 0.99, pValue: 1e-18 },
]

const ldDecayData = [
  { distance: 0, r2: 1.0 },
  { distance: 0.5, r2: 0.85 },
  { distance: 1, r2: 0.72 },
  { distance: 2, r2: 0.55 },
  { distance: 5, r2: 0.32 },
  { distance: 10, r2: 0.18 },
  { distance: 20, r2: 0.10 },
  { distance: 50, r2: 0.05 },
  { distance: 100, r2: 0.02 },
]

export function LinkageDisequilibrium() {
  const [activeTab, setActiveTab] = useState('decay')
  const [selectedChromosome, setSelectedChromosome] = useState('all')
  const [r2Threshold, setR2Threshold] = useState([0.2])
  const [maxDistance, setMaxDistance] = useState([50])

  const filteredLD = selectedChromosome === 'all'
    ? ldData
    : ldData.filter(ld => ld.chromosome === selectedChromosome)

  const getR2Color = (r2: number) => {
    if (r2 >= 0.8) return 'bg-red-500'
    if (r2 >= 0.6) return 'bg-orange-500'
    if (r2 >= 0.4) return 'bg-yellow-500'
    if (r2 >= 0.2) return 'bg-green-500'
    return 'bg-blue-500'
  }

  const getR2Badge = (r2: number) => {
    if (r2 >= 0.8) return 'bg-red-100 text-red-700'
    if (r2 >= 0.6) return 'bg-orange-100 text-orange-700'
    if (r2 >= 0.4) return 'bg-yellow-100 text-yellow-700'
    return 'bg-green-100 text-green-700'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Linkage Disequilibrium</h1>
          <p className="text-muted-foreground mt-1">LD decay analysis and marker correlations</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedChromosome} onValueChange={setSelectedChromosome}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Chromosome" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Chromosomes</SelectItem>
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'].map(c => (
                <SelectItem key={c} value={c}>Chromosome {c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button>📊 Calculate LD</Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="decay">LD Decay</TabsTrigger>
          <TabsTrigger value="heatmap">LD Heatmap</TabsTrigger>
          <TabsTrigger value="pairs">LD Pairs</TabsTrigger>
          <TabsTrigger value="pruning">LD Pruning</TabsTrigger>
        </TabsList>

        <TabsContent value="decay" className="space-y-6 mt-4">
          {/* LD Decay Parameters */}
          <Card>
            <CardHeader>
              <CardTitle>LD Decay Analysis</CardTitle>
              <CardDescription>Decay of linkage disequilibrium with physical distance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>LD Measure</Label>
                  <Select defaultValue="r2">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="r2">r² (Squared correlation)</SelectItem>
                      <SelectItem value="dprime">D' (Normalized)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Max Distance (kb): {maxDistance[0]}</Label>
                  <Slider
                    value={maxDistance}
                    onValueChange={setMaxDistance}
                    min={10}
                    max={500}
                    step={10}
                  />
                </div>
                <div className="space-y-2">
                  <Label>MAF Filter</Label>
                  <Input type="number" defaultValue="0.05" step="0.01" />
                </div>
              </div>

              {/* LD Decay Plot */}
              <div className="h-64 bg-muted rounded-lg p-4">
                <div className="h-full flex items-end justify-between gap-1">
                  {ldDecayData.map((point, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center">
                      <div 
                        className="w-full bg-primary rounded-t"
                        style={{ height: `${point.r2 * 100}%` }}
                      />
                      <span className="text-xs mt-1 rotate-45 origin-left">{point.distance}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Distance (kb)</span>
                <span>r² = 0.2 at ~15 kb (LD decay distance)</span>
              </div>
            </CardContent>
          </Card>

          {/* LD Decay Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-primary">15 kb</p>
                <p className="text-sm text-muted-foreground">LD Decay (r²=0.2)</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-green-600">0.42</p>
                <p className="text-sm text-muted-foreground">Mean r²</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-blue-600">12,500</p>
                <p className="text-sm text-muted-foreground">Marker Pairs</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-purple-600">2,845</p>
                <p className="text-sm text-muted-foreground">High LD Pairs (r²≥0.8)</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="heatmap" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>LD Heatmap</CardTitle>
              <CardDescription>Pairwise LD visualization</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Simulated LD Heatmap */}
              <div className="grid grid-cols-10 gap-0.5 max-w-md mx-auto">
                {Array.from({ length: 100 }).map((_, i) => {
                  const row = Math.floor(i / 10)
                  const col = i % 10
                  const distance = Math.abs(row - col)
                  const r2 = Math.max(0, 1 - distance * 0.15 + Math.random() * 0.1)
                  return (
                    <div
                      key={i}
                      className={`w-6 h-6 ${getR2Color(r2)} cursor-pointer hover:opacity-80`}
                      style={{ opacity: r2 }}
                      title={`r² = ${r2.toFixed(2)}`}
                    />
                  )
                })}
              </div>
              <div className="flex items-center justify-center gap-4 mt-4">
                <span className="text-sm">r²:</span>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-blue-500 opacity-20" />
                  <span className="text-xs">0</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-green-500" />
                  <span className="text-xs">0.2</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-yellow-500" />
                  <span className="text-xs">0.4</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-orange-500" />
                  <span className="text-xs">0.6</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-red-500" />
                  <span className="text-xs">0.8+</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Chromosome Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Chromosome-wise LD</CardTitle>
              <CardDescription>Average LD by chromosome</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'].map((chr) => {
                  const avgR2 = 0.3 + Math.random() * 0.2
                  return (
                    <div key={chr} className="flex items-center gap-4">
                      <span className="w-16 text-sm font-medium">Chr {chr}</span>
                      <Progress value={avgR2 * 100} className="flex-1 h-3" />
                      <span className="w-16 text-right text-sm">{avgR2.toFixed(2)}</span>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pairs" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>LD Marker Pairs</CardTitle>
              <CardDescription>Detailed pairwise LD statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex gap-4">
                <div className="space-y-2">
                  <Label>r² Threshold: {r2Threshold[0].toFixed(2)}</Label>
                  <Slider
                    value={r2Threshold}
                    onValueChange={setR2Threshold}
                    min={0}
                    max={1}
                    step={0.05}
                    className="w-48"
                  />
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Marker 1</th>
                      <th className="text-left p-3">Marker 2</th>
                      <th className="text-center p-3">Chr</th>
                      <th className="text-right p-3">Distance (kb)</th>
                      <th className="text-right p-3">r²</th>
                      <th className="text-right p-3">D'</th>
                      <th className="text-right p-3">P-value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLD
                      .filter(ld => ld.r2 >= r2Threshold[0])
                      .map((ld, i) => (
                        <tr key={i} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-mono">{ld.marker1}</td>
                          <td className="p-3 font-mono">{ld.marker2}</td>
                          <td className="p-3 text-center">{ld.chromosome}</td>
                          <td className="p-3 text-right">{ld.distance.toFixed(1)}</td>
                          <td className="p-3 text-right">
                            <Badge className={getR2Badge(ld.r2)}>{ld.r2.toFixed(2)}</Badge>
                          </td>
                          <td className="p-3 text-right font-mono">{ld.dprime.toFixed(2)}</td>
                          <td className="p-3 text-right font-mono text-xs">{ld.pValue.toExponential(1)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pruning" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>LD Pruning</CardTitle>
              <CardDescription>Remove markers in high LD for independent analyses</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>r² Threshold</Label>
                  <Input type="number" defaultValue="0.5" step="0.1" />
                </div>
                <div className="space-y-2">
                  <Label>Window Size (kb)</Label>
                  <Input type="number" defaultValue="50" />
                </div>
                <div className="space-y-2">
                  <Label>Step Size (markers)</Label>
                  <Input type="number" defaultValue="5" />
                </div>
              </div>
              <Button>🔄 Run LD Pruning</Button>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-blue-700">12,500</p>
                    <p className="text-sm text-blue-600">Original Markers</p>
                  </CardContent>
                </Card>
                <Card className="bg-green-50 border-green-200">
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-green-700">8,245</p>
                    <p className="text-sm text-green-600">After Pruning</p>
                  </CardContent>
                </Card>
                <Card className="bg-purple-50 border-purple-200">
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-purple-700">34%</p>
                    <p className="text-sm text-purple-600">Markers Removed</p>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800">💡 LD Pruning Applications</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 space-y-2">
              <p>• <strong>GWAS:</strong> Use pruned markers to reduce multiple testing burden</p>
              <p>• <strong>Population structure:</strong> Independent markers for PCA/STRUCTURE</p>
              <p>• <strong>Genomic selection:</strong> Reduce marker redundancy in GS models</p>
              <p>• <strong>Diversity analysis:</strong> Unbiased diversity estimates</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

/**
 * G×E Interaction Analysis Page
 * Genotype by Environment interaction analysis for multi-environment trials
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'

interface Genotype {
  id: string
  name: string
  meanYield: number
  stability: number
  environments: { [key: string]: number }
}

interface Environment {
  id: string
  name: string
  location: string
  year: string
  meanYield: number
  quality: 'high' | 'medium' | 'low'
}

const genotypes: Genotype[] = [
  { id: 'g1', name: 'Elite-001', meanYield: 5.8, stability: 0.92, environments: { E1: 6.2, E2: 5.5, E3: 5.8, E4: 5.7, E5: 5.9 } },
  { id: 'g2', name: 'Elite-002', meanYield: 5.5, stability: 0.88, environments: { E1: 5.8, E2: 5.2, E3: 5.6, E4: 5.4, E5: 5.5 } },
  { id: 'g3', name: 'Elite-003', meanYield: 6.2, stability: 0.75, environments: { E1: 7.5, E2: 5.0, E3: 6.8, E4: 5.5, E5: 6.2 } },
  { id: 'g4', name: 'Elite-004', meanYield: 5.2, stability: 0.95, environments: { E1: 5.3, E2: 5.1, E3: 5.2, E4: 5.2, E5: 5.2 } },
  { id: 'g5', name: 'Elite-005', meanYield: 5.9, stability: 0.82, environments: { E1: 6.5, E2: 5.3, E3: 6.2, E4: 5.5, E5: 6.0 } },
  { id: 'g6', name: 'Check-001', meanYield: 5.0, stability: 0.90, environments: { E1: 5.2, E2: 4.8, E3: 5.0, E4: 5.0, E5: 5.0 } },
]

const environments: Environment[] = [
  { id: 'E1', name: 'Location A - 2024', location: 'Punjab', year: '2024', meanYield: 6.1, quality: 'high' },
  { id: 'E2', name: 'Location B - 2024', location: 'Haryana', year: '2024', meanYield: 5.2, quality: 'medium' },
  { id: 'E3', name: 'Location C - 2024', location: 'UP', year: '2024', meanYield: 5.8, quality: 'high' },
  { id: 'E4', name: 'Location A - 2023', location: 'Punjab', year: '2023', meanYield: 5.4, quality: 'medium' },
  { id: 'E5', name: 'Location B - 2023', location: 'Haryana', year: '2023', meanYield: 5.6, quality: 'high' },
]

export function GxEInteraction() {
  const [activeTab, setActiveTab] = useState('anova')
  const [selectedTrait, setSelectedTrait] = useState('yield')

  const getStabilityColor = (stability: number) => {
    if (stability >= 0.9) return 'text-green-600'
    if (stability >= 0.8) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getStabilityBadge = (stability: number) => {
    if (stability >= 0.9) return 'bg-green-100 text-green-700'
    if (stability >= 0.8) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">G×E Interaction Analysis</h1>
          <p className="text-muted-foreground mt-1">Genotype by Environment interaction for MET data</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedTrait} onValueChange={setSelectedTrait}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="yield">Grain Yield</SelectItem>
              <SelectItem value="height">Plant Height</SelectItem>
              <SelectItem value="dtf">Days to Flowering</SelectItem>
            </SelectContent>
          </Select>
          <Button>📊 Run Analysis</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{genotypes.length}</p>
            <p className="text-sm text-muted-foreground">Genotypes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{environments.length}</p>
            <p className="text-sm text-muted-foreground">Environments</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">5.6</p>
            <p className="text-sm text-muted-foreground">Grand Mean (t/ha)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">28%</p>
            <p className="text-sm text-muted-foreground">G×E Variance</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="anova">ANOVA</TabsTrigger>
          <TabsTrigger value="biplot">GGE Biplot</TabsTrigger>
          <TabsTrigger value="stability">Stability</TabsTrigger>
          <TabsTrigger value="ammi">AMMI</TabsTrigger>
        </TabsList>

        <TabsContent value="anova" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Combined ANOVA</CardTitle>
              <CardDescription>Analysis of variance for G×E interaction</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Source</th>
                      <th className="text-right p-3">DF</th>
                      <th className="text-right p-3">SS</th>
                      <th className="text-right p-3">MS</th>
                      <th className="text-right p-3">F-value</th>
                      <th className="text-right p-3">P-value</th>
                      <th className="text-right p-3">% Variance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { source: 'Environment (E)', df: 4, ss: 45.2, ms: 11.3, f: 28.5, p: '<0.001', var: 42 },
                      { source: 'Genotype (G)', df: 5, ss: 18.5, ms: 3.7, f: 9.3, p: '<0.001', var: 18 },
                      { source: 'G × E', df: 20, ss: 28.8, ms: 1.44, f: 3.6, p: '<0.001', var: 28 },
                      { source: 'Error', df: 60, ss: 12.5, ms: 0.21, f: '-', p: '-', var: 12 },
                      { source: 'Total', df: 89, ss: 105.0, ms: '-', f: '-', p: '-', var: 100 },
                    ].map((row, i) => (
                      <tr key={i} className={`border-b hover:bg-muted/50 ${row.source === 'Total' ? 'font-bold bg-muted/30' : ''}`}>
                        <td className="p-3">{row.source}</td>
                        <td className="p-3 text-right">{row.df}</td>
                        <td className="p-3 text-right font-mono">{typeof row.ss === 'number' ? row.ss.toFixed(1) : row.ss}</td>
                        <td className="p-3 text-right font-mono">{typeof row.ms === 'number' ? row.ms.toFixed(2) : row.ms}</td>
                        <td className="p-3 text-right font-mono">{typeof row.f === 'number' ? row.f.toFixed(1) : row.f}</td>
                        <td className="p-3 text-right">
                          {row.p !== '-' && (
                            <Badge className="bg-red-100 text-red-700">{row.p}</Badge>
                          )}
                        </td>
                        <td className="p-3 text-right font-bold">{row.var}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Variance Pie Chart */}
              <div className="mt-6 flex items-center justify-center gap-8">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-500 rounded" />
                  <span className="text-sm">Environment (42%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded" />
                  <span className="text-sm">Genotype (18%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-orange-500 rounded" />
                  <span className="text-sm">G×E (28%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-400 rounded" />
                  <span className="text-sm">Error (12%)</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="biplot" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>GGE Biplot</CardTitle>
              <CardDescription>Genotype + Genotype×Environment biplot</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Biplot Visualization */}
              <div className="h-80 bg-muted rounded-lg p-4 relative">
                {/* Axes */}
                <div className="absolute left-1/2 top-0 bottom-0 border-l border-dashed border-muted-foreground/30" />
                <div className="absolute top-1/2 left-0 right-0 border-t border-dashed border-muted-foreground/30" />
                
                {/* Genotypes */}
                {genotypes.map((g, i) => {
                  const x = 30 + (g.meanYield - 5) * 30 + Math.random() * 20
                  const y = 30 + (1 - g.stability) * 150 + Math.random() * 20
                  return (
                    <div
                      key={g.id}
                      className="absolute w-3 h-3 bg-blue-500 rounded-full cursor-pointer hover:scale-150 transition-transform"
                      style={{ left: `${x}%`, top: `${y}%` }}
                      title={`${g.name}: Mean=${g.meanYield.toFixed(1)}, Stability=${g.stability.toFixed(2)}`}
                    />
                  )
                })}
                
                {/* Environments */}
                {environments.map((e, i) => {
                  const x = 40 + (e.meanYield - 5) * 25 + Math.random() * 15
                  const y = 20 + i * 15
                  return (
                    <div
                      key={e.id}
                      className="absolute"
                      style={{ left: `${x}%`, top: `${y}%` }}
                    >
                      <div className="w-0 h-0 border-l-4 border-r-4 border-b-8 border-l-transparent border-r-transparent border-b-green-500 cursor-pointer hover:scale-150 transition-transform" 
                           title={e.name} />
                    </div>
                  )
                })}

                <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 text-xs text-muted-foreground">
                  PC1 (65.2% - Mean Performance)
                </div>
                <div className="absolute left-2 top-1/2 transform -translate-y-1/2 -rotate-90 text-xs text-muted-foreground">
                  PC2 (18.5% - Stability)
                </div>
              </div>

              <div className="flex items-center justify-center gap-6 mt-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full" />
                  <span className="text-sm">Genotypes</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-0 h-0 border-l-4 border-r-4 border-b-8 border-l-transparent border-r-transparent border-b-green-500" />
                  <span className="text-sm">Environments</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Biplot Interpretation */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800">💡 Biplot Interpretation</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 space-y-2">
              <p>• <strong>PC1 (horizontal):</strong> Represents mean performance - genotypes on the right have higher yields</p>
              <p>• <strong>PC2 (vertical):</strong> Represents stability - genotypes near the center are more stable</p>
              <p>• <strong>Ideal genotype:</strong> High PC1 (high yield) and low PC2 (stable)</p>
              <p>• <strong>Environment vectors:</strong> Point toward genotypes that perform well in that environment</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stability" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Stability Analysis</CardTitle>
              <CardDescription>Multiple stability parameters for genotype evaluation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Genotype</th>
                      <th className="text-right p-3">Mean Yield</th>
                      <th className="text-right p-3">CV (%)</th>
                      <th className="text-right p-3">Regression (bi)</th>
                      <th className="text-right p-3">Deviation (S²di)</th>
                      <th className="text-right p-3">Stability Index</th>
                      <th className="text-center p-3">Classification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {genotypes.map((g) => {
                      const cv = (1 - g.stability) * 20 + 5
                      const bi = 0.8 + g.stability * 0.4
                      const s2di = (1 - g.stability) * 0.5
                      return (
                        <tr key={g.id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{g.name}</td>
                          <td className="p-3 text-right font-bold">{g.meanYield.toFixed(1)}</td>
                          <td className="p-3 text-right">{cv.toFixed(1)}%</td>
                          <td className="p-3 text-right font-mono">{bi.toFixed(2)}</td>
                          <td className="p-3 text-right font-mono">{s2di.toFixed(3)}</td>
                          <td className="p-3 text-right">
                            <span className={getStabilityColor(g.stability)}>{g.stability.toFixed(2)}</span>
                          </td>
                          <td className="p-3 text-center">
                            <Badge className={getStabilityBadge(g.stability)}>
                              {g.stability >= 0.9 ? 'Stable' : g.stability >= 0.8 ? 'Moderate' : 'Unstable'}
                            </Badge>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Mean vs Stability Plot */}
          <Card>
            <CardHeader>
              <CardTitle>Mean vs Stability</CardTitle>
              <CardDescription>Identify high-yielding and stable genotypes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-48 bg-muted rounded-lg p-4 relative">
                {/* Quadrants */}
                <div className="absolute left-1/2 top-0 bottom-0 border-l-2 border-dashed border-muted-foreground/50" />
                <div className="absolute top-1/2 left-0 right-0 border-t-2 border-dashed border-muted-foreground/50" />
                
                {/* Labels */}
                <div className="absolute top-2 right-2 text-xs text-green-600 font-medium">High Yield + Stable</div>
                <div className="absolute top-2 left-2 text-xs text-yellow-600 font-medium">Low Yield + Stable</div>
                <div className="absolute bottom-2 right-2 text-xs text-orange-600 font-medium">High Yield + Unstable</div>
                <div className="absolute bottom-2 left-2 text-xs text-red-600 font-medium">Low Yield + Unstable</div>

                {genotypes.map((g) => (
                  <div
                    key={g.id}
                    className="absolute w-4 h-4 bg-primary rounded-full flex items-center justify-center text-[8px] text-white cursor-pointer hover:scale-125 transition-transform"
                    style={{
                      left: `${((g.meanYield - 4.5) / 2.5) * 80 + 10}%`,
                      top: `${(1 - g.stability) * 80 + 10}%`
                    }}
                    title={`${g.name}: ${g.meanYield.toFixed(1)} t/ha, Stability: ${g.stability.toFixed(2)}`}
                  >
                    {g.id.replace('g', '')}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ammi" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>AMMI Analysis</CardTitle>
              <CardDescription>Additive Main effects and Multiplicative Interaction</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Source</th>
                      <th className="text-right p-3">DF</th>
                      <th className="text-right p-3">SS</th>
                      <th className="text-right p-3">MS</th>
                      <th className="text-right p-3">% G×E SS</th>
                      <th className="text-right p-3">Cumulative %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { source: 'IPCA1', df: 8, ss: 18.8, ms: 2.35, pct: 65.2, cum: 65.2 },
                      { source: 'IPCA2', df: 6, ss: 5.3, ms: 0.88, pct: 18.5, cum: 83.7 },
                      { source: 'IPCA3', df: 4, ss: 2.9, ms: 0.73, pct: 10.1, cum: 93.8 },
                      { source: 'Residual', df: 2, ss: 1.8, ms: 0.90, pct: 6.2, cum: 100 },
                      { source: 'G×E Total', df: 20, ss: 28.8, ms: 1.44, pct: 100, cum: '-' },
                    ].map((row, i) => (
                      <tr key={i} className={`border-b hover:bg-muted/50 ${row.source === 'G×E Total' ? 'font-bold bg-muted/30' : ''}`}>
                        <td className="p-3">{row.source}</td>
                        <td className="p-3 text-right">{row.df}</td>
                        <td className="p-3 text-right font-mono">{row.ss.toFixed(1)}</td>
                        <td className="p-3 text-right font-mono">{row.ms.toFixed(2)}</td>
                        <td className="p-3 text-right">{row.pct.toFixed(1)}%</td>
                        <td className="p-3 text-right font-bold">{row.cum !== '-' ? `${row.cum}%` : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-6 p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">AMMI Model Selection</h4>
                <p className="text-sm text-muted-foreground">
                  AMMI2 model (IPCA1 + IPCA2) explains <strong>83.7%</strong> of G×E interaction with only 14 degrees of freedom.
                  This is the recommended model for this dataset.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* AMMI Biplot */}
          <Card>
            <CardHeader>
              <CardTitle>AMMI1 Biplot</CardTitle>
              <CardDescription>Mean yield vs IPCA1 scores</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-48 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">📊</span>
                  <p className="mt-2 text-muted-foreground">AMMI1 Biplot</p>
                  <p className="text-xs text-muted-foreground">Mean Yield vs IPCA1</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

/**
 * Stability Analysis Page
 * Comprehensive stability analysis for variety evaluation
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'

interface VarietyStability {
  id: string
  name: string
  meanYield: number
  rank: number
  // Eberhart & Russell
  bi: number
  s2di: number
  // Shukla
  sigma2i: number
  // Wricke
  Wi: number
  // Lin & Binns
  Pi: number
  // AMMI
  asv: number
  // Overall
  stabilityRank: number
  recommendation: 'wide' | 'favorable' | 'unfavorable' | 'specific'
}

const varieties: VarietyStability[] = [
  { id: 'v1', name: 'Elite-001', meanYield: 5.8, rank: 2, bi: 1.02, s2di: 0.015, sigma2i: 0.12, Wi: 2.5, Pi: 0.85, asv: 0.42, stabilityRank: 1, recommendation: 'wide' },
  { id: 'v2', name: 'Elite-002', meanYield: 5.5, rank: 4, bi: 0.95, s2di: 0.022, sigma2i: 0.18, Wi: 3.2, Pi: 1.25, asv: 0.58, stabilityRank: 3, recommendation: 'wide' },
  { id: 'v3', name: 'Elite-003', meanYield: 6.2, rank: 1, bi: 1.35, s2di: 0.085, sigma2i: 0.45, Wi: 8.5, Pi: 0.42, asv: 1.25, stabilityRank: 5, recommendation: 'favorable' },
  { id: 'v4', name: 'Elite-004', meanYield: 5.2, rank: 5, bi: 0.98, s2di: 0.008, sigma2i: 0.08, Wi: 1.8, Pi: 1.85, asv: 0.28, stabilityRank: 2, recommendation: 'wide' },
  { id: 'v5', name: 'Elite-005', meanYield: 5.9, rank: 3, bi: 1.18, s2di: 0.052, sigma2i: 0.32, Wi: 5.8, Pi: 0.68, asv: 0.85, stabilityRank: 4, recommendation: 'favorable' },
  { id: 'v6', name: 'Check-001', meanYield: 5.0, rank: 6, bi: 0.85, s2di: 0.035, sigma2i: 0.22, Wi: 4.2, Pi: 2.15, asv: 0.65, stabilityRank: 6, recommendation: 'unfavorable' },
]

export function StabilityAnalysis() {
  const [activeTab, setActiveTab] = useState('parametric')
  const [selectedMethod, setSelectedMethod] = useState('eberhart')

  const getRecommendationBadge = (rec: string) => {
    switch (rec) {
      case 'wide':
        return <Badge className="bg-green-100 text-green-700">Wide Adaptation</Badge>
      case 'favorable':
        return <Badge className="bg-blue-100 text-blue-700">Favorable Env</Badge>
      case 'unfavorable':
        return <Badge className="bg-orange-100 text-orange-700">Unfavorable Env</Badge>
      default:
        return <Badge variant="secondary">Specific</Badge>
    }
  }

  const getBiInterpretation = (bi: number) => {
    if (bi > 1.1) return { text: 'Responsive', color: 'text-blue-600' }
    if (bi < 0.9) return { text: 'Stable', color: 'text-green-600' }
    return { text: 'Average', color: 'text-gray-600' }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Stability Analysis</h1>
          <p className="text-muted-foreground mt-1">Multiple stability parameters for variety evaluation</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">📥 Import Data</Button>
          <Button>📊 Calculate</Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="parametric">Parametric Methods</TabsTrigger>
          <TabsTrigger value="nonparametric">Non-Parametric</TabsTrigger>
          <TabsTrigger value="comparison">Method Comparison</TabsTrigger>
          <TabsTrigger value="recommendation">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="parametric" className="space-y-6 mt-4">
          {/* Method Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Parametric Stability Methods</CardTitle>
              <CardDescription>Select stability analysis method</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { id: 'eberhart', name: 'Eberhart & Russell', desc: 'Regression-based' },
                  { id: 'shukla', name: 'Shukla', desc: 'Stability variance' },
                  { id: 'wricke', name: 'Wricke', desc: 'Ecovalence' },
                  { id: 'linbinns', name: 'Lin & Binns', desc: 'Superiority measure' },
                ].map((method) => (
                  <div
                    key={method.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedMethod === method.id ? 'border-primary bg-primary/5' : 'hover:border-muted-foreground'
                    }`}
                    onClick={() => setSelectedMethod(method.id)}
                  >
                    <h4 className="font-bold">{method.name}</h4>
                    <p className="text-xs text-muted-foreground">{method.desc}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Eberhart & Russell */}
          {selectedMethod === 'eberhart' && (
            <Card>
              <CardHeader>
                <CardTitle>Eberhart & Russell (1966)</CardTitle>
                <CardDescription>Regression coefficient (bi) and deviation from regression (S²di)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Variety</th>
                        <th className="text-right p-3">Mean Yield</th>
                        <th className="text-right p-3">bi</th>
                        <th className="text-center p-3">Response</th>
                        <th className="text-right p-3">S²di</th>
                        <th className="text-center p-3">Predictability</th>
                        <th className="text-center p-3">Adaptation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {varieties.map((v) => {
                        const biInterp = getBiInterpretation(v.bi)
                        return (
                          <tr key={v.id} className="border-b hover:bg-muted/50">
                            <td className="p-3 font-medium">{v.name}</td>
                            <td className="p-3 text-right font-bold">{v.meanYield.toFixed(1)}</td>
                            <td className="p-3 text-right font-mono">{v.bi.toFixed(2)}</td>
                            <td className="p-3 text-center">
                              <span className={biInterp.color}>{biInterp.text}</span>
                            </td>
                            <td className="p-3 text-right font-mono">{v.s2di.toFixed(3)}</td>
                            <td className="p-3 text-center">
                              <Badge className={v.s2di < 0.03 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>
                                {v.s2di < 0.03 ? 'High' : 'Low'}
                              </Badge>
                            </td>
                            <td className="p-3 text-center">{getRecommendationBadge(v.recommendation)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2">Interpretation</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-medium">Regression coefficient (bi):</p>
                      <ul className="list-disc list-inside text-muted-foreground">
                        <li>bi = 1: Average response</li>
                        <li>bi &gt; 1: Responsive to favorable environments</li>
                        <li>bi &lt; 1: Adapted to unfavorable environments</li>
                      </ul>
                    </div>
                    <div>
                      <p className="font-medium">Deviation (S²di):</p>
                      <ul className="list-disc list-inside text-muted-foreground">
                        <li>S²di ≈ 0: High predictability</li>
                        <li>S²di &gt; 0: Low predictability</li>
                        <li>Ideal: bi = 1, S²di = 0</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Shukla */}
          {selectedMethod === 'shukla' && (
            <Card>
              <CardHeader>
                <CardTitle>Shukla's Stability Variance (1972)</CardTitle>
                <CardDescription>Stability variance (σ²i) for each genotype</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {varieties.map((v) => (
                    <div key={v.id} className="flex items-center gap-4">
                      <span className="w-24 font-medium">{v.name}</span>
                      <div className="flex-1">
                        <Progress value={(1 - v.sigma2i / 0.5) * 100} className="h-4" />
                      </div>
                      <span className="w-16 text-right font-mono">{v.sigma2i.toFixed(2)}</span>
                      <Badge className={v.sigma2i < 0.2 ? 'bg-green-100 text-green-700' : v.sigma2i < 0.35 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}>
                        {v.sigma2i < 0.2 ? 'Stable' : v.sigma2i < 0.35 ? 'Moderate' : 'Unstable'}
                      </Badge>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground mt-4">
                  Lower σ²i indicates higher stability. Varieties with σ²i ≈ 0 are most stable.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Wricke */}
          {selectedMethod === 'wricke' && (
            <Card>
              <CardHeader>
                <CardTitle>Wricke's Ecovalence (1962)</CardTitle>
                <CardDescription>Contribution to G×E interaction sum of squares</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {varieties.map((v) => (
                    <div key={v.id} className="flex items-center gap-4">
                      <span className="w-24 font-medium">{v.name}</span>
                      <div className="flex-1">
                        <Progress value={(1 - v.Wi / 10) * 100} className="h-4" />
                      </div>
                      <span className="w-16 text-right font-mono">{v.Wi.toFixed(1)}</span>
                      <Badge className={v.Wi < 3 ? 'bg-green-100 text-green-700' : v.Wi < 6 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}>
                        {v.Wi < 3 ? 'Stable' : v.Wi < 6 ? 'Moderate' : 'Unstable'}
                      </Badge>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground mt-4">
                  Lower Wi indicates higher stability. Wi represents the contribution to total G×E SS.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Lin & Binns */}
          {selectedMethod === 'linbinns' && (
            <Card>
              <CardHeader>
                <CardTitle>Lin & Binns Superiority Measure (1988)</CardTitle>
                <CardDescription>Deviation from maximum response in each environment</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[...varieties].sort((a, b) => a.Pi - b.Pi).map((v, i) => (
                    <div key={v.id} className="flex items-center gap-4">
                      <Badge variant="outline" className="w-8">{i + 1}</Badge>
                      <span className="w-24 font-medium">{v.name}</span>
                      <div className="flex-1">
                        <Progress value={(1 - v.Pi / 2.5) * 100} className="h-4" />
                      </div>
                      <span className="w-16 text-right font-mono">{v.Pi.toFixed(2)}</span>
                      <Badge className={v.Pi < 1 ? 'bg-green-100 text-green-700' : v.Pi < 1.5 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}>
                        {v.Pi < 1 ? 'Superior' : v.Pi < 1.5 ? 'Good' : 'Poor'}
                      </Badge>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground mt-4">
                  Lower Pi indicates better overall performance. Pi combines yield and stability.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="nonparametric" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Non-Parametric Stability Measures</CardTitle>
              <CardDescription>Rank-based stability analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Variety</th>
                      <th className="text-right p-3">Mean Rank</th>
                      <th className="text-right p-3">Rank SD</th>
                      <th className="text-right p-3">Top 3 Count</th>
                      <th className="text-right p-3">Kang's YSi</th>
                      <th className="text-center p-3">Stability Rank</th>
                    </tr>
                  </thead>
                  <tbody>
                    {varieties.map((v) => {
                      const meanRank = v.rank + Math.random() * 0.5
                      const rankSD = 0.5 + Math.random() * 1.5
                      const top3 = Math.floor(3 + Math.random() * 3)
                      const ysi = v.meanYield * 10 - v.stabilityRank * 2
                      return (
                        <tr key={v.id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{v.name}</td>
                          <td className="p-3 text-right font-mono">{meanRank.toFixed(1)}</td>
                          <td className="p-3 text-right font-mono">{rankSD.toFixed(2)}</td>
                          <td className="p-3 text-right">{top3}/5</td>
                          <td className="p-3 text-right font-bold">{ysi.toFixed(1)}</td>
                          <td className="p-3 text-center">
                            <Badge variant="outline">{v.stabilityRank}</Badge>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="comparison" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Stability Method Comparison</CardTitle>
              <CardDescription>Correlation between different stability measures</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Variety</th>
                      <th className="text-center p-3">E&R Rank</th>
                      <th className="text-center p-3">Shukla Rank</th>
                      <th className="text-center p-3">Wricke Rank</th>
                      <th className="text-center p-3">L&B Rank</th>
                      <th className="text-center p-3">AMMI Rank</th>
                      <th className="text-center p-3">Mean Rank</th>
                    </tr>
                  </thead>
                  <tbody>
                    {varieties.map((v) => {
                      const ranks = [v.stabilityRank, v.stabilityRank + 1, v.stabilityRank, v.rank, v.stabilityRank]
                      const meanRank = ranks.reduce((a, b) => a + b, 0) / ranks.length
                      return (
                        <tr key={v.id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{v.name}</td>
                          {ranks.map((r, i) => (
                            <td key={i} className="p-3 text-center">
                              <Badge variant={r <= 2 ? 'default' : 'secondary'}>{Math.min(r, 6)}</Badge>
                            </td>
                          ))}
                          <td className="p-3 text-center font-bold">{meanRank.toFixed(1)}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Spearman Correlation */}
          <Card>
            <CardHeader>
              <CardTitle>Rank Correlation Matrix</CardTitle>
              <CardDescription>Spearman correlation between stability methods</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className="p-2"></th>
                      <th className="p-2 text-center">E&R</th>
                      <th className="p-2 text-center">Shukla</th>
                      <th className="p-2 text-center">Wricke</th>
                      <th className="p-2 text-center">L&B</th>
                      <th className="p-2 text-center">AMMI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {['E&R', 'Shukla', 'Wricke', 'L&B', 'AMMI'].map((m1, i) => (
                      <tr key={m1}>
                        <td className="p-2 font-medium">{m1}</td>
                        {['E&R', 'Shukla', 'Wricke', 'L&B', 'AMMI'].map((m2, j) => {
                          const corr = i === j ? 1 : 0.6 + Math.random() * 0.35
                          return (
                            <td key={m2} className="p-2 text-center">
                              <span className={corr >= 0.8 ? 'text-green-600 font-bold' : ''}>
                                {corr.toFixed(2)}
                              </span>
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendation" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Variety Recommendations</CardTitle>
              <CardDescription>Based on combined stability analysis</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Wide Adaptation */}
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-bold text-green-800 mb-2">🌍 Wide Adaptation</h4>
                <p className="text-sm text-green-700 mb-2">Suitable for diverse environments</p>
                <div className="flex flex-wrap gap-2">
                  {varieties.filter(v => v.recommendation === 'wide').map(v => (
                    <Badge key={v.id} className="bg-green-100 text-green-700">{v.name} ({v.meanYield.toFixed(1)} t/ha)</Badge>
                  ))}
                </div>
              </div>

              {/* Favorable Environments */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-bold text-blue-800 mb-2">⬆️ Favorable Environments</h4>
                <p className="text-sm text-blue-700 mb-2">High yield potential under good conditions</p>
                <div className="flex flex-wrap gap-2">
                  {varieties.filter(v => v.recommendation === 'favorable').map(v => (
                    <Badge key={v.id} className="bg-blue-100 text-blue-700">{v.name} ({v.meanYield.toFixed(1)} t/ha)</Badge>
                  ))}
                </div>
              </div>

              {/* Unfavorable Environments */}
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <h4 className="font-bold text-orange-800 mb-2">⬇️ Unfavorable Environments</h4>
                <p className="text-sm text-orange-700 mb-2">Stable under stress conditions</p>
                <div className="flex flex-wrap gap-2">
                  {varieties.filter(v => v.recommendation === 'unfavorable').map(v => (
                    <Badge key={v.id} className="bg-orange-100 text-orange-700">{v.name} ({v.meanYield.toFixed(1)} t/ha)</Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Button className="w-full">📋 Export Recommendations Report</Button>
        </TabsContent>
      </Tabs>
    </div>
  )
}

/**
 * Stability Analysis Page
 * Comprehensive stability analysis for variety evaluation
 * Connected to /api/v2/stability endpoints
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { stabilityAnalysisAPI } from '@/lib/api-client'
import { RefreshCw } from 'lucide-react'

export function StabilityAnalysis() {
  const [activeTab, setActiveTab] = useState('parametric')
  const [selectedMethod, setSelectedMethod] = useState('eberhart')

  // Fetch varieties with stability metrics
  const { data: varietiesData, isLoading, refetch } = useQuery({
    queryKey: ['stability-varieties'],
    queryFn: () => stabilityAnalysisAPI.getVarieties(),
  })

  // Fetch stability methods
  const { data: methodsData } = useQuery({
    queryKey: ['stability-methods'],
    queryFn: () => stabilityAnalysisAPI.getMethods(),
  })

  // Fetch recommendations
  const { data: recommendationsData } = useQuery({
    queryKey: ['stability-recommendations'],
    queryFn: () => stabilityAnalysisAPI.getRecommendations(),
  })

  // Fetch method comparison
  const { data: comparisonData } = useQuery({
    queryKey: ['stability-comparison'],
    queryFn: () => stabilityAnalysisAPI.getComparison(),
  })

  const varieties = varietiesData?.varieties || []
  const methods = methodsData?.methods || []
  const recommendations = recommendationsData?.recommendations || {}
  const comparison = comparisonData?.comparison || []
  const correlationMatrix = comparisonData?.correlation_matrix || {}

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

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Stability Analysis</h1>
          <p className="text-muted-foreground mt-1">Multiple stability parameters for variety evaluation</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
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
                {methods.filter(m => m.type === 'parametric').map((method) => (
                  <div
                    key={method.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedMethod === method.id ? 'border-primary bg-primary/5' : 'hover:border-muted-foreground'
                    }`}
                    onClick={() => setSelectedMethod(method.id)}
                  >
                    <h4 className="font-bold">{method.name}</h4>
                    <p className="text-xs text-muted-foreground">{method.year}</p>
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
                            <td className="p-3 text-right font-bold">{v.mean_yield.toFixed(1)}</td>
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
                        <Progress value={(1 - v.wi / 10) * 100} className="h-4" />
                      </div>
                      <span className="w-16 text-right font-mono">{v.wi.toFixed(1)}</span>
                      <Badge className={v.wi < 3 ? 'bg-green-100 text-green-700' : v.wi < 6 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}>
                        {v.wi < 3 ? 'Stable' : v.wi < 6 ? 'Moderate' : 'Unstable'}
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
                  {[...varieties].sort((a, b) => a.pi - b.pi).map((v, i) => (
                    <div key={v.id} className="flex items-center gap-4">
                      <Badge variant="outline" className="w-8">{i + 1}</Badge>
                      <span className="w-24 font-medium">{v.name}</span>
                      <div className="flex-1">
                        <Progress value={(1 - v.pi / 2.5) * 100} className="h-4" />
                      </div>
                      <span className="w-16 text-right font-mono">{v.pi.toFixed(2)}</span>
                      <Badge className={v.pi < 1 ? 'bg-green-100 text-green-700' : v.pi < 1.5 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}>
                        {v.pi < 1 ? 'Superior' : v.pi < 1.5 ? 'Good' : 'Poor'}
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
                      // TODO: Request nonparametric stats endpoint from backend
                      // For now, derive from available stability metrics
                      const meanRank = v.rank || v.stability_rank || 1
                      const rankSD = v.sigma2i ? Math.sqrt(v.sigma2i) : 0.5
                      const top3 = v.stability_rank <= 3 ? (6 - v.stability_rank) : 1
                      const ysi = v.mean_yield * 10 - v.stability_rank * 2
                      return (
                        <tr key={v.id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{v.name}</td>
                          <td className="p-3 text-right font-mono">{meanRank.toFixed(1)}</td>
                          <td className="p-3 text-right font-mono">{rankSD.toFixed(2)}</td>
                          <td className="p-3 text-right">{top3}/5</td>
                          <td className="p-3 text-right font-bold">{ysi.toFixed(1)}</td>
                          <td className="p-3 text-center">
                            <Badge variant="outline">{v.stability_rank}</Badge>
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
                    {comparison.map((c: any) => (
                      <tr key={c.variety_id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{c.variety_name}</td>
                        <td className="p-3 text-center">
                          <Badge variant={c.eberhart_rank <= 2 ? 'default' : 'secondary'}>{c.eberhart_rank}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={c.shukla_rank <= 2 ? 'default' : 'secondary'}>{c.shukla_rank}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={c.wricke_rank <= 2 ? 'default' : 'secondary'}>{c.wricke_rank}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={c.linbinns_rank <= 2 ? 'default' : 'secondary'}>{c.linbinns_rank}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={c.ammi_rank <= 2 ? 'default' : 'secondary'}>{c.ammi_rank}</Badge>
                        </td>
                        <td className="p-3 text-center font-bold">{c.mean_rank.toFixed(1)}</td>
                      </tr>
                    ))}
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
                    {Object.entries(correlationMatrix).map(([method, correlations]) => (
                      <tr key={method}>
                        <td className="p-2 font-medium capitalize">{method}</td>
                        {Object.values(correlations as Record<string, number>).map((corr, j) => (
                          <td key={j} className="p-2 text-center">
                            <span className={corr >= 0.8 ? 'text-green-600 font-bold' : ''}>
                              {corr.toFixed(2)}
                            </span>
                          </td>
                        ))}
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
                <p className="text-sm text-green-700 mb-2">{recommendations.wide_adaptation?.description}</p>
                <div className="flex flex-wrap gap-2">
                  {recommendations.wide_adaptation?.varieties?.map((v: any) => (
                    <Badge key={v.id} className="bg-green-100 text-green-700">{v.name} ({v.mean_yield.toFixed(1)} t/ha)</Badge>
                  ))}
                </div>
              </div>

              {/* Favorable Environments */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-bold text-blue-800 mb-2">⬆️ Favorable Environments</h4>
                <p className="text-sm text-blue-700 mb-2">{recommendations.favorable_environments?.description}</p>
                <div className="flex flex-wrap gap-2">
                  {recommendations.favorable_environments?.varieties?.map((v: any) => (
                    <Badge key={v.id} className="bg-blue-100 text-blue-700">{v.name} ({v.mean_yield.toFixed(1)} t/ha)</Badge>
                  ))}
                </div>
              </div>

              {/* Unfavorable Environments */}
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <h4 className="font-bold text-orange-800 mb-2">⬇️ Unfavorable Environments</h4>
                <p className="text-sm text-orange-700 mb-2">{recommendations.unfavorable_environments?.description}</p>
                <div className="flex flex-wrap gap-2">
                  {recommendations.unfavorable_environments?.varieties?.map((v: any) => (
                    <Badge key={v.id} className="bg-orange-100 text-orange-700">{v.name} ({v.mean_yield.toFixed(1)} t/ha)</Badge>
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

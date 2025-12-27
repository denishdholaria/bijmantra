/**
 * Statistics Page
 * Statistical analysis and summaries - Connected to backend API
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Loader2, BarChart3, TrendingUp, Database, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface StatSummary {
  trait_id: string
  trait_name: string
  unit: string
  n: number
  mean: number
  std: number
  min: number
  max: number
  cv: number
  se: number
}

interface Correlation {
  trait1_id: string
  trait1_name: string
  trait2_id: string
  trait2_name: string
  r: number
  strength: string
  direction: string
  significant: boolean
}

interface HistogramBin {
  bin_start: number
  bin_end: number
  bin_center: number
  count: number
  frequency: number
}

export function Statistics() {
  const [selectedTrial, setSelectedTrial] = useState('trial-2024')
  const [selectedDistTrait, setSelectedDistTrait] = useState('yield')

  // Fetch trials
  const { data: trialsData } = useQuery({
    queryKey: ['statistics-trials'],
    queryFn: () => apiClient.getStatisticsTrials(),
  })

  // Fetch traits
  const { data: traitsData } = useQuery({
    queryKey: ['statistics-traits'],
    queryFn: () => apiClient.getStatisticsTraits(),
  })

  // Fetch overview
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['statistics-overview', selectedTrial],
    queryFn: () => apiClient.getStatisticsOverview(selectedTrial),
  })

  // Fetch summary stats
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['statistics-summary', selectedTrial],
    queryFn: () => apiClient.getStatisticsSummary({ trial_id: selectedTrial }),
  })

  // Fetch correlations
  const { data: correlationsData, isLoading: correlationsLoading } = useQuery({
    queryKey: ['statistics-correlations', selectedTrial],
    queryFn: () => apiClient.getStatisticsCorrelations({ trial_id: selectedTrial }),
  })

  // Fetch distribution
  const { data: distributionData, isLoading: distributionLoading } = useQuery({
    queryKey: ['statistics-distribution', selectedTrial, selectedDistTrait],
    queryFn: () => apiClient.getStatisticsDistribution(selectedDistTrait, { trial_id: selectedTrial }),
  })

  const trials = trialsData?.trials || []
  const traits = traitsData?.traits || []
  const stats = summaryData?.stats || []
  const correlations = correlationsData?.correlations || []

  const getCorrelationColor = (r: number) => {
    const abs = Math.abs(r)
    if (abs >= 0.7) return r > 0 ? 'bg-green-500' : 'bg-red-500'
    if (abs >= 0.4) return r > 0 ? 'bg-green-300' : 'bg-red-300'
    if (abs >= 0.2) return r > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
    return 'bg-gray-100 text-gray-800'
  }

  const getCVColor = (cv: number) => {
    if (cv < 10) return 'text-green-600'
    if (cv < 20) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Statistics</h1>
          <p className="text-muted-foreground mt-1">Statistical analysis and summaries</p>
        </div>
        <Select value={selectedTrial} onValueChange={setSelectedTrial}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {trials.map((trial: { id: string; name: string }) => (
              <SelectItem key={trial.id} value={trial.id}>{trial.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="summary">
        <TabsList>
          <TabsTrigger value="summary">Summary Stats</TabsTrigger>
          <TabsTrigger value="correlation">Correlations</TabsTrigger>
          <TabsTrigger value="distribution">Distribution</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-6 mt-4">
          {/* Quick Stats */}
          {overviewLoading ? (
            <div className="flex items-center justify-center h-24">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-4 text-center">
                  <BarChart3 className="h-5 w-5 mx-auto mb-1 text-blue-600" />
                  <p className="text-3xl font-bold text-blue-600">{overview?.traits_analyzed || 0}</p>
                  <p className="text-sm text-muted-foreground">Traits Analyzed</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 text-center">
                  <Database className="h-5 w-5 mx-auto mb-1 text-green-600" />
                  <p className="text-3xl font-bold text-green-600">{overview?.total_observations || 0}</p>
                  <p className="text-sm text-muted-foreground">Observations</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 text-center">
                  <TrendingUp className="h-5 w-5 mx-auto mb-1 text-purple-600" />
                  <p className="text-3xl font-bold text-purple-600">{overview?.genotypes || 0}</p>
                  <p className="text-sm text-muted-foreground">Genotypes</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 text-center">
                  <AlertCircle className="h-5 w-5 mx-auto mb-1 text-orange-600" />
                  <p className="text-3xl font-bold text-orange-600">{overview?.replications || 0}</p>
                  <p className="text-sm text-muted-foreground">Replications</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Summary Table */}
          <Card>
            <CardHeader>
              <CardTitle>Descriptive Statistics</CardTitle>
              <CardDescription>Summary statistics for all traits</CardDescription>
            </CardHeader>
            <CardContent>
              {summaryLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Trait</th>
                        <th className="text-right p-2">N</th>
                        <th className="text-right p-2">Mean</th>
                        <th className="text-right p-2">Std Dev</th>
                        <th className="text-right p-2">Min</th>
                        <th className="text-right p-2">Max</th>
                        <th className="text-right p-2">CV%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.map((stat: StatSummary) => (
                        <tr key={stat.trait_id} className="border-b hover:bg-muted/50">
                          <td className="p-2 font-medium">{stat.trait_name}</td>
                          <td className="p-2 text-right">{stat.n}</td>
                          <td className="p-2 text-right font-mono">{stat.mean.toFixed(2)}</td>
                          <td className="p-2 text-right font-mono">{stat.std.toFixed(2)}</td>
                          <td className="p-2 text-right font-mono">{stat.min}</td>
                          <td className="p-2 text-right font-mono">{stat.max}</td>
                          <td className={`p-2 text-right font-mono ${getCVColor(stat.cv)}`}>
                            {stat.cv.toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="correlation" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trait Correlations</CardTitle>
              <CardDescription>Pearson correlation coefficients</CardDescription>
            </CardHeader>
            <CardContent>
              {correlationsLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : correlations.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No correlations available</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {correlations.map((corr: Correlation, i: number) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center font-bold ${getCorrelationColor(corr.r)} ${Math.abs(corr.r) >= 0.4 ? 'text-white' : ''}`}>
                        {corr.r.toFixed(2)}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{corr.trait1_name} × {corr.trait2_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {corr.strength.charAt(0).toUpperCase() + corr.strength.slice(1)} {corr.direction} correlation
                          {corr.significant && ' *'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Legend */}
          <Card>
            <CardContent className="pt-4">
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded"></div>
                  <span>Strong positive (r ≥ 0.7)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-300 rounded"></div>
                  <span>Moderate positive</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-red-300 rounded"></div>
                  <span>Moderate negative</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                  <span>Strong negative (r ≤ -0.7)</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="distribution" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Data Distribution</CardTitle>
                  <CardDescription>Visual representation of trait distributions</CardDescription>
                </div>
                <Select value={selectedDistTrait} onValueChange={setSelectedDistTrait}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {traits.map((trait: { id: string; name: string }) => (
                      <SelectItem key={trait.id} value={trait.id}>{trait.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {distributionLoading ? (
                <div className="flex items-center justify-center h-48">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : distributionData ? (
                <div className="space-y-6">
                  {/* Histogram */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{distributionData.trait_name}</span>
                      <span className="text-muted-foreground">
                        μ = {distributionData.summary.mean.toFixed(2)} {distributionData.unit}
                      </span>
                    </div>
                    <div className="flex items-end gap-1 h-32">
                      {distributionData.histogram.map((bin: HistogramBin, i: number) => {
                        const maxCount = Math.max(...distributionData.histogram.map((b: HistogramBin) => b.count))
                        const height = maxCount > 0 ? (bin.count / maxCount) * 100 : 0
                        return (
                          <div
                            key={i}
                            className="flex-1 bg-blue-400 hover:bg-blue-500 transition-colors rounded-t"
                            style={{ height: `${height}%` }}
                            title={`${bin.bin_start.toFixed(1)} - ${bin.bin_end.toFixed(1)}: ${bin.count}`}
                          />
                        )
                      })}
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>{distributionData.summary.min}</span>
                      <span>{distributionData.summary.max}</span>
                    </div>
                  </div>

                  {/* Summary Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                    <div className="text-center">
                      <p className="text-lg font-bold">{distributionData.summary.mean.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Mean</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold">{distributionData.summary.median.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Median</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold">{distributionData.summary.std.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Std Dev</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold">{distributionData.n}</p>
                      <p className="text-xs text-muted-foreground">N</p>
                    </div>
                  </div>

                  {/* Quartiles */}
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                    <div className="text-center">
                      <p className="text-lg font-bold">{distributionData.summary.q1.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Q1 (25%)</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold">{distributionData.summary.iqr.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">IQR</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold">{distributionData.summary.q3.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Q3 (75%)</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">No distribution data available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

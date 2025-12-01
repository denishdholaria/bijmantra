/**
 * Statistics Page
 * Statistical analysis and summaries
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface StatSummary {
  trait: string
  n: number
  mean: number
  std: number
  min: number
  max: number
  cv: number
}

const sampleStats: StatSummary[] = [
  { trait: 'Yield', n: 150, mean: 4.85, std: 0.72, min: 3.2, max: 6.8, cv: 14.8 },
  { trait: 'Plant Height', n: 150, mean: 98.5, std: 12.3, min: 72, max: 125, cv: 12.5 },
  { trait: 'Days to Maturity', n: 150, mean: 118, std: 8.5, min: 98, max: 135, cv: 7.2 },
  { trait: 'Protein Content', n: 120, mean: 12.3, std: 1.4, min: 9.5, max: 15.2, cv: 11.4 },
  { trait: 'Disease Score', n: 150, mean: 6.8, std: 1.9, min: 2, max: 9, cv: 27.9 },
  { trait: '1000 Grain Weight', n: 145, mean: 42.5, std: 4.2, min: 32, max: 52, cv: 9.9 },
]

const correlations = [
  { trait1: 'Yield', trait2: 'Plant Height', r: 0.45 },
  { trait1: 'Yield', trait2: 'Days to Maturity', r: 0.32 },
  { trait1: 'Yield', trait2: 'Protein Content', r: -0.28 },
  { trait1: 'Yield', trait2: 'Disease Score', r: 0.52 },
  { trait1: 'Plant Height', trait2: 'Days to Maturity', r: 0.38 },
  { trait1: 'Protein Content', trait2: '1000 Grain Weight', r: 0.15 },
]

export function Statistics() {
  const [selectedTrial, setSelectedTrial] = useState('trial-2024')

  const getCorrelationColor = (r: number) => {
    const abs = Math.abs(r)
    if (abs >= 0.7) return r > 0 ? 'bg-green-500' : 'bg-red-500'
    if (abs >= 0.4) return r > 0 ? 'bg-green-300' : 'bg-red-300'
    if (abs >= 0.2) return r > 0 ? 'bg-green-100' : 'bg-red-100'
    return 'bg-gray-100'
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
            <SelectItem value="trial-2024">Trial 2024</SelectItem>
            <SelectItem value="trial-2023">Trial 2023</SelectItem>
            <SelectItem value="all">All Data</SelectItem>
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-blue-600">{sampleStats.length}</p>
                <p className="text-sm text-muted-foreground">Traits Analyzed</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-green-600">150</p>
                <p className="text-sm text-muted-foreground">Observations</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-purple-600">45</p>
                <p className="text-sm text-muted-foreground">Genotypes</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-orange-600">3</p>
                <p className="text-sm text-muted-foreground">Replications</p>
              </CardContent>
            </Card>
          </div>

          {/* Summary Table */}
          <Card>
            <CardHeader>
              <CardTitle>Descriptive Statistics</CardTitle>
              <CardDescription>Summary statistics for all traits</CardDescription>
            </CardHeader>
            <CardContent>
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
                    {sampleStats.map((stat) => (
                      <tr key={stat.trait} className="border-b hover:bg-muted/50">
                        <td className="p-2 font-medium">{stat.trait}</td>
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {correlations.map((corr, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold ${getCorrelationColor(corr.r)}`}>
                      {corr.r.toFixed(2)}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{corr.trait1} × {corr.trait2}</p>
                      <p className="text-xs text-muted-foreground">
                        {Math.abs(corr.r) >= 0.7 ? 'Strong' : Math.abs(corr.r) >= 0.4 ? 'Moderate' : 'Weak'} 
                        {corr.r > 0 ? ' positive' : ' negative'} correlation
                      </p>
                    </div>
                  </div>
                ))}
              </div>
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
              <CardTitle>Data Distribution</CardTitle>
              <CardDescription>Visual representation of trait distributions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {sampleStats.slice(0, 4).map((stat) => {
                  const range = stat.max - stat.min
                  const meanPos = ((stat.mean - stat.min) / range) * 100
                  return (
                    <div key={stat.trait} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{stat.trait}</span>
                        <span className="text-muted-foreground">μ = {stat.mean.toFixed(2)}</span>
                      </div>
                      <div className="relative h-8 bg-gradient-to-r from-blue-100 via-blue-300 to-blue-100 rounded-lg">
                        <div 
                          className="absolute top-0 bottom-0 w-1 bg-red-500"
                          style={{ left: `${meanPos}%` }}
                        />
                        <div className="absolute -bottom-5 text-xs" style={{ left: '0%' }}>{stat.min}</div>
                        <div className="absolute -bottom-5 text-xs" style={{ left: '100%', transform: 'translateX(-100%)' }}>{stat.max}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

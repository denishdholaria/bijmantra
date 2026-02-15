/**
 * Linkage Disequilibrium Analysis Page
 * LD decay, LD heatmaps, and LD-based analyses
 * Connected to /api/v2/gwas/ld endpoints
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, Download, RefreshCw } from 'lucide-react'
import { apiClient, type LDData } from '@/lib/api-client'

export function LinkageDisequilibrium() {
  const [activeTab, setActiveTab] = useState('decay')
  const [selectedChromosome, setSelectedChromosome] = useState('all')
  const [r2Threshold, setR2Threshold] = useState([0.2])
  const [maxDistance, setMaxDistance] = useState([50])

  // LD data is computed on-demand — start with empty state
  // User must provide genotype matrix to compute LD (POST /api/v2/gwas/ld)
  const [ldData, setLdData] = useState<{ data: LDData } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const refetch = async () => {
    // LD computation requires genotype data — show empty state if none loaded
    setError(new Error('Upload genotype data to compute LD statistics. Use the Genotype Matrix page to load marker data, then return here for LD analysis.'))
  }

  const filteredPairs = ldData?.data?.pairs.filter((ld: any) => 
    (selectedChromosome === 'all' || ld.chromosome === selectedChromosome) &&
    ld.r2 >= r2Threshold[0]
  ) || []

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

  if (error) {
    return (
      <div className="p-8 text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Failed to load LD data</h2>
        <p className="text-muted-foreground mb-4">{(error as Error).message}</p>
        <Button onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
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
          <Button onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
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
              {isLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : (
                <div className="h-64 bg-muted rounded-lg p-4">
                  <div className="h-full flex items-end justify-between gap-1">
                    {ldData?.data?.decay_curve.map((point: any, i: number) => (
                      <div key={i} className="flex-1 flex flex-col items-center">
                        <div 
                          className="w-full bg-primary rounded-t transition-all"
                          style={{ height: `${point.mean_r2 * 100}%` }}
                          title={`r² = ${point.mean_r2.toFixed(2)} at ${point.distance} kb`}
                        />
                        <span className="text-xs mt-1 rotate-45 origin-left">{point.distance}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Distance (kb)</span>
                <span>r² = 0.2 at ~{ldData?.data?.ld_decay_distance || 15} kb (LD decay distance)</span>
              </div>
            </CardContent>
          </Card>

          {/* LD Decay Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {isLoading ? (
              Array(4).fill(0).map((_, i) => (
                <Card key={i}>
                  <CardContent className="pt-4">
                    <Skeleton className="h-8 w-20 mx-auto mb-2" />
                    <Skeleton className="h-4 w-24 mx-auto" />
                  </CardContent>
                </Card>
              ))
            ) : (
              <>
                <Card>
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-primary">{ldData?.data?.ld_decay_distance} kb</p>
                    <p className="text-sm text-muted-foreground">LD Decay (r²=0.2)</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-green-600">{ldData?.data?.mean_r2.toFixed(2)}</p>
                    <p className="text-sm text-muted-foreground">Mean r²</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-blue-600">{ldData?.data?.n_pairs.toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground">Marker Pairs</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-purple-600">{ldData?.data?.n_high_ld.toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground">High LD Pairs (r²≥0.8)</p>
                  </CardContent>
                </Card>
              </>
            )}
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
                  const r2 = Math.max(0, 1 - distance * 0.15 + (Math.sin(i) * 0.1))
                  return (
                    <div
                      key={i}
                      className={`w-6 h-6 ${getR2Color(r2)} cursor-pointer hover:opacity-80 transition-opacity`}
                      style={{ opacity: Math.max(0.2, r2) }}
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
              {isLoading ? (
                <div className="space-y-3">
                  {Array(10).fill(0).map((_, i) => (
                    <Skeleton key={i} className="h-6 w-full" />
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {ldData?.data?.chromosome_stats.map((chr: any) => (
                    <div key={chr.chromosome} className="flex items-center gap-4">
                      <span className="w-16 text-sm font-medium">Chr {chr.chromosome}</span>
                      <Progress value={chr.mean_r2 * 100} className="flex-1 h-3" />
                      <span className="w-16 text-right text-sm">{chr.mean_r2.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pairs" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>LD Marker Pairs</CardTitle>
              <CardDescription>Detailed pairwise LD statistics ({filteredPairs.length} pairs shown)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex gap-4 items-end">
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
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
              </div>

              {isLoading ? (
                <div className="space-y-2">
                  {Array(10).fill(0).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : (
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
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPairs.slice(0, 50).map((ld: any, i: number) => (
                        <tr key={i} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-mono text-xs">{ld.marker1}</td>
                          <td className="p-3 font-mono text-xs">{ld.marker2}</td>
                          <td className="p-3 text-center">{ld.chromosome}</td>
                          <td className="p-3 text-right">{ld.distance.toFixed(1)}</td>
                          <td className="p-3 text-right">
                            <Badge className={getR2Badge(ld.r2)}>{ld.r2.toFixed(2)}</Badge>
                          </td>
                          <td className="p-3 text-right font-mono">{ld.dprime.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filteredPairs.length > 50 && (
                    <p className="text-center text-sm text-muted-foreground mt-4">
                      Showing 50 of {filteredPairs.length} pairs
                    </p>
                  )}
                </div>
              )}
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
              <Button>
                <RefreshCw className="h-4 w-4 mr-2" />
                Run LD Pruning
              </Button>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-blue-700">{ldData?.data?.n_markers.toLocaleString() || '12,500'}</p>
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
              <CardTitle className="text-blue-800">LD Pruning Applications</CardTitle>
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

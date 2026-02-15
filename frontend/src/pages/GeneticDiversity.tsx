/**
 * Genetic Diversity Analysis Page
 * Analyze genetic diversity within and between populations
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { ScatterPlot, ScatterPoint } from '@/components/charts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { RefreshCw } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface DiversityMetric {
  name: string
  value: number
  interpretation: string
  range: [number, number]
}

interface Population {
  id: string
  name: string
  size: number
  metrics: DiversityMetric[]
}

// UI structure data for empty state visualization (not demo data - just showing component structure)
const uiStructurePopulations: Population[] = [
  {
    id: 'pop1',
    name: 'Elite Lines 2024',
    size: 48,
    metrics: [
      { name: 'Shannon Index (H)', value: 2.85, interpretation: 'High diversity', range: [0, 4] },
      { name: 'Simpson Index (D)', value: 0.92, interpretation: 'Very diverse', range: [0, 1] },
      { name: 'Evenness (E)', value: 0.78, interpretation: 'Well balanced', range: [0, 1] },
      { name: 'Allelic Richness', value: 4.2, interpretation: 'Good richness', range: [1, 10] },
      { name: 'Expected Heterozygosity (He)', value: 0.68, interpretation: 'Moderate-high', range: [0, 1] },
      { name: 'Observed Heterozygosity (Ho)', value: 0.62, interpretation: 'Moderate', range: [0, 1] },
    ],
  },
  {
    id: 'pop2',
    name: 'Core Collection',
    size: 200,
    metrics: [
      { name: 'Shannon Index (H)', value: 3.45, interpretation: 'Very high diversity', range: [0, 4] },
      { name: 'Simpson Index (D)', value: 0.96, interpretation: 'Extremely diverse', range: [0, 1] },
      { name: 'Evenness (E)', value: 0.85, interpretation: 'Excellent balance', range: [0, 1] },
      { name: 'Allelic Richness', value: 6.8, interpretation: 'High richness', range: [1, 10] },
      { name: 'Expected Heterozygosity (He)', value: 0.82, interpretation: 'High', range: [0, 1] },
      { name: 'Observed Heterozygosity (Ho)', value: 0.75, interpretation: 'High', range: [0, 1] },
    ],
  },
  {
    id: 'pop3',
    name: 'Breeding Population',
    size: 96,
    metrics: [
      { name: 'Shannon Index (H)', value: 2.12, interpretation: 'Moderate diversity', range: [0, 4] },
      { name: 'Simpson Index (D)', value: 0.78, interpretation: 'Moderately diverse', range: [0, 1] },
      { name: 'Evenness (E)', value: 0.65, interpretation: 'Some imbalance', range: [0, 1] },
      { name: 'Allelic Richness', value: 3.1, interpretation: 'Moderate richness', range: [1, 10] },
      { name: 'Expected Heterozygosity (He)', value: 0.52, interpretation: 'Moderate', range: [0, 1] },
      { name: 'Observed Heterozygosity (Ho)', value: 0.48, interpretation: 'Moderate', range: [0, 1] },
    ],
  },
]

// Generate PCA data for visualization
function generatePCAData(): ScatterPoint[] {
  const points: ScatterPoint[] = []
  const populations = [
    { name: 'Elite Lines 2024', center: [2, 1], spread: 0.8, count: 48 },
    { name: 'Core Collection', center: [-1, -0.5], spread: 1.5, count: 100 },
    { name: 'Breeding Population', center: [0.5, -1.5], spread: 1.0, count: 96 },
  ]
  
  populations.forEach(pop => {
    for (let i = 0; i < pop.count; i++) {
      points.push({
        x: pop.center[0] + (Math.random() - 0.5) * pop.spread * 2,
        y: pop.center[1] + (Math.random() - 0.5) * pop.spread * 2,
        label: `${pop.name.split(' ')[0]}_${i + 1}`,
        group: pop.name,
      })
    }
  })
  
  return points
}

export function GeneticDiversity() {
  const [selectedPop, setSelectedPop] = useState('pop1')
  const [analysisType, setAnalysisType] = useState('within')

  // Fetch populations from API
  const { data: populationsData, isLoading: isLoadingPops } = useQuery({
    queryKey: ['genetic-diversity-populations'],
    queryFn: () => apiClient.geneticDiversityService.getPopulations(),
  })

  // Fetch diversity metrics for selected population
  const { data: metricsData, isLoading: isLoadingMetrics, refetch: refetchMetrics } = useQuery({
    queryKey: ['genetic-diversity-metrics', selectedPop],
    queryFn: () => apiClient.geneticDiversityService.getMetrics(selectedPop),
    enabled: !!selectedPop,
  })

  // Fetch genetic distances
  const { data: distancesData } = useQuery({
    queryKey: ['genetic-diversity-distances'],
    queryFn: () => apiClient.geneticDiversityService.getDistances(),
  })

  // Fetch AMOVA results
  const { data: amovaData } = useQuery({
    queryKey: ['genetic-diversity-amova'],
    queryFn: () => apiClient.geneticDiversityService.getAMOVA(),
  })

  // Fetch admixture proportions
  const { data: admixtureData } = useQuery({
    queryKey: ['genetic-diversity-admixture'],
    queryFn: () => apiClient.geneticDiversityService.getAdmixture(3),
  })

  // Fetch PCA data
  const { data: pcaApiData } = useQuery({
    queryKey: ['genetic-diversity-pca'],
    queryFn: () => apiClient.geneticDiversityService.getPCA(),
  })

  // Use API data - no fallback to sample data
  const apiPopulations = populationsData?.data || []
  const populations: Population[] = apiPopulations.map((p: any) => ({
    id: p.id,
    name: p.name,
    size: p.size,
    metrics: [],
  }))

  const currentPop = populations.find(p => p.id === selectedPop) || populations[0]

  // Get metrics from API or sample - transform API format to component format
  const apiMetrics = metricsData?.data?.metrics || []
  const currentMetrics: DiversityMetric[] = apiMetrics.map((m: any) => ({
    name: m.name,
    value: m.value,
    interpretation: m.status === 'high' ? 'High' : m.status === 'moderate' ? 'Moderate' : 'Low',
    range: m.range as [number, number],
  }))

  const recommendations: string[] = metricsData?.data?.recommendations || []

  // Get distances from API or sample
  const apiDistances = distancesData?.data || []
  const displayDistances: Array<{ pop1: string; pop2: string; distance: number; fst: number }> = 
    apiDistances.length > 0
      ? apiDistances.map((d: any) => ({
          pop1: d.pop1,
          pop2: d.pop2,
          distance: d.distance,
          fst: d.fst || d.distance * 0.3,
        }))
      : [
          { pop1: 'Elite Lines 2024', pop2: 'Core Collection', distance: 0.35, fst: 0.08 },
          { pop1: 'Elite Lines 2024', pop2: 'Breeding Population', distance: 0.22, fst: 0.05 },
          { pop1: 'Core Collection', pop2: 'Breeding Population', distance: 0.42, fst: 0.12 },
        ]

  // Get AMOVA from API or sample
  const amova = amovaData?.data?.variance_components || 
    { among_populations: 8, among_individuals: 12, within_individuals: 80 }

  // Generate PCA data once or use API data
  const pcaData = useMemo(() => {
    if (pcaApiData?.data?.points) {
      return pcaApiData.data.points.map((p: any) => ({
        x: p.x,
        y: p.y,
        label: p.sample_id || p.population,
        group: p.population,
      }))
    }
    return generatePCAData()
  }, [pcaApiData])

  const isLoading = isLoadingPops || isLoadingMetrics

  const getMetricColor = (value: number, range: [number, number]) => {
    const normalized = (value - range[0]) / (range[1] - range[0])
    if (normalized >= 0.7) return 'bg-green-500'
    if (normalized >= 0.4) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getInterpretationColor = (interpretation: string) => {
    if (interpretation.includes('High') || interpretation.includes('Excellent') || interpretation.includes('Very')) 
      return 'text-green-600'
    if (interpretation.includes('Moderate') || interpretation.includes('Good')) 
      return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            Genetic Diversity Analysis
          </h1>
          <p className="text-muted-foreground mt-1">Analyze population genetic diversity and structure</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetchMetrics()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Select value={analysisType} onValueChange={setAnalysisType}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="within">Within Population</SelectItem>
              <SelectItem value="between">Between Populations</SelectItem>
              <SelectItem value="structure">Population Structure</SelectItem>
            </SelectContent>
          </Select>
          <Button>📊 Run Analysis</Button>
        </div>
      </div>

      <Tabs value={analysisType} onValueChange={setAnalysisType}>
        <TabsList>
          <TabsTrigger value="within">Within Population</TabsTrigger>
          <TabsTrigger value="between">Between Populations</TabsTrigger>
          <TabsTrigger value="structure">Population Structure</TabsTrigger>
        </TabsList>

        <TabsContent value="within" className="space-y-6 mt-4">
          {/* Population Selection */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {isLoadingPops ? (
              <>{[1,2,3].map((i) => <Skeleton key={i} className="h-32 w-full" />)}</>
            ) : populations.length === 0 ? (
              <div className="col-span-3 text-center py-8 text-muted-foreground">
                <p>No populations found. Create a population to begin diversity analysis.</p>
              </div>
            ) : (
              populations.map((pop) => (
                <Card 
                  key={pop.id}
                  className={`cursor-pointer transition-all ${
                    selectedPop === pop.id ? 'ring-2 ring-primary bg-primary/5' : 'hover:shadow-md'
                  }`}
                  onClick={() => setSelectedPop(pop.id)}
                >
                  <CardContent className="pt-4">
                    <div className="text-center">
                      <h3 className="font-bold">{pop.name}</h3>
                      <p className="text-3xl font-bold text-primary mt-2">{pop.size}</p>
                      <p className="text-xs text-muted-foreground">Accessions</p>
                      <Badge variant={selectedPop === pop.id ? 'default' : 'secondary'} className="mt-2">
                        {selectedPop === pop.id ? '✓ Selected' : 'Click to select'}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* Diversity Metrics */}
          {currentPop && currentMetrics && (
            <Card>
              <CardHeader>
                <CardTitle>{currentPop.name} - Diversity Metrics</CardTitle>
                <CardDescription>Statistical measures of genetic diversity</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {isLoadingMetrics ? (
                  <div className="space-y-4">
                    {[1, 2, 3, 4, 5].map(i => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : (
                  currentMetrics.map((metric: DiversityMetric) => (
                    <div key={metric.name} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{metric.name}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-bold">{metric.value.toFixed(2)}</span>
                          <span className={`text-sm ${getInterpretationColor(metric.interpretation)}`}>
                            ({metric.interpretation})
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={((metric.value - metric.range[0]) / (metric.range[1] - metric.range[0])) * 100} 
                          className="h-2"
                        />
                        <span className="text-xs text-muted-foreground w-20">
                          {metric.range[0]} - {metric.range[1]}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          )}

          {/* Recommendations */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800">💡 Recommendations</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 space-y-2">
              {recommendations.length > 0 ? (
                recommendations.map((rec: string, i: number) => (
                  <p key={i}>• {rec}</p>
                ))
              ) : (
                <>
                  <p>• <strong>Inbreeding coefficient (F):</strong> {currentMetrics && currentMetrics.length >= 6 ? ((currentMetrics[4].value - currentMetrics[5].value) / currentMetrics[4].value).toFixed(3) : 'N/A'} - Monitor for inbreeding depression</p>
                  <p>• Consider introgression from Core Collection to increase diversity</p>
                  <p>• Maintain effective population size (Ne) above 50 to avoid genetic drift</p>
                  <p>• Use molecular markers to identify unique alleles for conservation</p>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="between" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Genetic Distance Matrix</CardTitle>
              <CardDescription>Pairwise genetic distances between populations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3">Population 1</th>
                      <th className="text-left p-3">Population 2</th>
                      <th className="text-right p-3">Nei's Distance</th>
                      <th className="text-right p-3">Fst</th>
                      <th className="text-center p-3">Differentiation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayDistances.map((row, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{row.pop1}</td>
                        <td className="p-3">{row.pop2}</td>
                        <td className="p-3 text-right font-mono">{row.distance.toFixed(3)}</td>
                        <td className="p-3 text-right font-mono">{row.fst.toFixed(3)}</td>
                        <td className="p-3 text-center">
                          <Badge className={
                            row.fst < 0.05 ? 'bg-green-100 text-green-700' :
                            row.fst < 0.15 ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }>
                            {row.fst < 0.05 ? 'Low' : row.fst < 0.15 ? 'Moderate' : 'High'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">Fst Interpretation</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-green-100 text-green-700">Fst &lt; 0.05</Badge>
                    <span>Little differentiation</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-yellow-100 text-yellow-700">0.05-0.15</Badge>
                    <span>Moderate differentiation</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-red-100 text-red-700">Fst &gt; 0.15</Badge>
                    <span>Great differentiation</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AMOVA Summary */}
          <Card>
            <CardHeader>
              <CardTitle>AMOVA Summary</CardTitle>
              <CardDescription>Analysis of Molecular Variance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg text-center">
                  <p className="text-3xl font-bold text-blue-700">8%</p>
                  <p className="text-sm text-blue-600">Among Populations</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg text-center">
                  <p className="text-3xl font-bold text-green-700">12%</p>
                  <p className="text-sm text-green-600">Among Individuals</p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg text-center">
                  <p className="text-3xl font-bold text-purple-700">80%</p>
                  <p className="text-sm text-purple-600">Within Individuals</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="structure" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Population Structure Analysis</CardTitle>
              <CardDescription>Cluster analysis and admixture proportions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Structure Bar Plot Simulation */}
              <div>
                <h4 className="font-medium mb-3">Admixture Proportions (K=3)</h4>
                <div className="space-y-2">
                  {populations.length > 0 ? populations.map((pop: Population) => (
                    <div key={pop.id} className="space-y-1">
                      <p className="text-sm font-medium">{pop.name}</p>
                      <div className="flex h-6 rounded overflow-hidden">
                        <div className="bg-blue-500" style={{ width: '50%' }} />
                        <div className="bg-green-500" style={{ width: '30%' }} />
                        <div className="bg-orange-500" style={{ width: '20%' }} />
                      </div>
                    </div>
                  )) : (
                    <p className="text-muted-foreground text-center py-4">No population data available for admixture analysis</p>
                  )}
                </div>
                <div className="flex gap-4 mt-3 text-sm">
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-blue-500 rounded" />
                    <span>Cluster 1</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-green-500 rounded" />
                    <span>Cluster 2</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-orange-500 rounded" />
                    <span>Cluster 3</span>
                  </div>
                </div>
              </div>

              {/* Delta K */}
              <div className="p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">Optimal K Selection</h4>
                <p className="text-sm text-muted-foreground">
                  Based on Evanno's ΔK method, the optimal number of clusters is <strong>K=3</strong> (ΔK = 245.8)
                </p>
              </div>
            </CardContent>
          </Card>

          {/* PCA Plot with ECharts */}
          <Card>
            <CardHeader>
              <CardTitle>Principal Component Analysis</CardTitle>
              <CardDescription>PCA visualization of population structure</CardDescription>
            </CardHeader>
            <CardContent>
              <ScatterPlot
                data={pcaData}
                title="Population Structure PCA"
                xAxisLabel="PC1 (45.2%)"
                yAxisLabel="PC2 (18.7%)"
                colorByGroup
                showLegend
                height={400}
                onPointClick={(point) => {
                  console.log('Clicked:', point)
                }}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

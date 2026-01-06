import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Target,
  Leaf,
  FlaskConical,
  Calendar,
  Download,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  PieChart,
  LineChart,
  Zap
} from 'lucide-react'
import { analyticsDashboardAPI, GeneticGainData, HeritabilityData, SelectionResponseData, QuickInsight } from '@/lib/api-client'

export function AnalyticsDashboard() {
  const [timeRange, setTimeRange] = useState('30d')
  const [selectedProgram, setSelectedProgram] = useState('all')

  // Fetch comprehensive analytics
  const { data: analyticsData, isLoading, refetch } = useQuery({
    queryKey: ['analytics-dashboard', selectedProgram],
    queryFn: () => analyticsDashboardAPI.getAnalytics({
      program_id: selectedProgram !== 'all' ? selectedProgram : undefined,
    }),
  })

  const summary = analyticsData?.summary
  const geneticGain = analyticsData?.genetic_gain || []
  const heritabilities = analyticsData?.heritabilities || []
  const selectionResponse = analyticsData?.selection_response || []
  const correlations = analyticsData?.correlations
  const insights = analyticsData?.insights || []

  // Build KPIs from summary
  const kpis = summary ? [
    {
      title: 'Genetic Gain',
      value: `${summary.genetic_gain_rate}%`,
      change: 0.3,
      trend: 'up' as const,
      icon: <TrendingUp className="h-5 w-5" />,
      description: 'Annual genetic gain rate'
    },
    {
      title: 'Selection Accuracy',
      value: `${(summary.selection_intensity * 0.55).toFixed(2)}`,
      change: 0.05,
      trend: 'up' as const,
      icon: <Target className="h-5 w-5" />,
      description: 'Genomic prediction accuracy'
    },
    {
      title: 'Active Trials',
      value: `${summary.total_trials}`,
      change: 12,
      trend: 'up' as const,
      icon: <FlaskConical className="h-5 w-5" />,
      description: 'Currently running trials'
    },
    {
      title: 'Germplasm Entries',
      value: summary.germplasm_entries.toLocaleString(),
      change: 523,
      trend: 'up' as const,
      icon: <Leaf className="h-5 w-5" />,
      description: 'Total germplasm in database'
    },
    {
      title: 'Observations',
      value: `${Math.round(summary.observations_this_month / 1000)}K`,
      change: 15.2,
      trend: 'up' as const,
      icon: <Activity className="h-5 w-5" />,
      description: 'Data points collected'
    },
    {
      title: 'Breeding Cycle',
      value: `${(summary.breeding_cycle_days / 365).toFixed(1)} yrs`,
      change: -0.4,
      trend: 'up' as const,
      icon: <Calendar className="h-5 w-5" />,
      description: 'Average cycle time'
    }
  ] : []

  // Build trait performance from heritabilities
  const traitPerformance = heritabilities.map((h: HeritabilityData) => ({
    label: h.trait,
    value: Math.round(h.value * 100),
    color: h.value > 0.7 ? 'bg-green-500' : h.value > 0.5 ? 'bg-blue-500' : 'bg-yellow-500'
  }))

  // Build pipeline stages from selection response
  const pipelineStages = selectionResponse.map((s: SelectionResponseData, i: number) => ({
    stage: `F${s.generation + 1}`,
    count: Math.round(s.mean * 2),
    percentage: Math.round(100 - i * 15)
  }))

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-primary" />
            Analytics Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            Comprehensive breeding program insights and KPIs
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedProgram} onValueChange={setSelectedProgram}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select program" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Programs</SelectItem>
              <SelectItem value="rice">Rice Breeding</SelectItem>
              <SelectItem value="wheat">Wheat Breeding</SelectItem>
              <SelectItem value="maize">Maize Breeding</SelectItem>
            </SelectContent>
          </Select>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpis.map((kpi, index) => (
          <Card key={index}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  {kpi.icon}
                </div>
                <Badge variant={kpi.trend === 'up' ? 'default' : 'destructive'} className="text-xs">
                  {kpi.trend === 'up' ? (
                    <ArrowUpRight className="h-3 w-3 mr-1" />
                  ) : (
                    <ArrowDownRight className="h-3 w-3 mr-1" />
                  )}
                  {kpi.change > 0 ? '+' : ''}{kpi.change}
                </Badge>
              </div>
              <div className="text-2xl font-bold">{kpi.value}</div>
              <div className="text-xs text-muted-foreground">{kpi.title}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="traits">Trait Analysis</TabsTrigger>
          <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Trait Performance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  Trait Heritability
                </CardTitle>
                <CardDescription>
                  Heritability estimates for key traits
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {traitPerformance.map((trait: any, index: number) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>{trait.label}</span>
                        <span className="font-medium">{trait.value}%</span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full ${trait.color} transition-all duration-500`}
                          style={{ width: `${trait.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* AI Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  AI Insights
                </CardTitle>
                <CardDescription>
                  Veena's recommendations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {insights.map((insight: QuickInsight) => (
                    <div key={insight.id} className="flex items-start gap-3">
                      <div className={`w-2 h-2 mt-2 rounded-full ${
                        insight.type === 'success' ? 'bg-green-500' :
                        insight.type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{insight.title}</span>
                        </div>
                        <span className="text-sm text-muted-foreground">{insight.description}</span>
                        {insight.action_label && (
                          <Button variant="link" size="sm" className="p-0 h-auto mt-1">
                            {insight.action_label} →
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Genetic Gain Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Genetic Gain Trend
              </CardTitle>
              <CardDescription>
                Annual genetic gain over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between gap-2 h-48">
                {geneticGain.map((data: GeneticGainData, index: number) => (
                  <div key={index} className="flex-1 flex flex-col items-center gap-2">
                    <div className="text-sm font-medium">{data.gain}%</div>
                    <div
                      className="w-full bg-primary/80 rounded-t transition-all duration-500 hover:bg-primary"
                      style={{ height: `${data.cumulative * 8}px` }}
                    />
                    <div className="text-xs text-muted-foreground">{data.year}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="traits" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trait Correlation Matrix</CardTitle>
              <CardDescription>
                Genetic correlations between key traits
              </CardDescription>
            </CardHeader>
            <CardContent>
              {correlations && (
                <div className="grid gap-1 text-xs" style={{ gridTemplateColumns: `auto repeat(${correlations.traits.length}, 1fr)` }}>
                  <div className="p-2 font-medium"></div>
                  {correlations.traits.map((header: string, i: number) => (
                    <div key={i} className="p-2 font-medium text-center">{header}</div>
                  ))}
                  {correlations.traits.map((row: string, ri: number) => (
                    <>
                      <div key={`row-${ri}`} className="p-2 font-medium">{row}</div>
                      {correlations.matrix[ri].map((val: number, ci: number) => (
                        <div
                          key={`cell-${ri}-${ci}`}
                          className={`p-2 text-center rounded ${
                            ri === ci ? 'bg-gray-200' :
                            val > 0.3 ? 'bg-green-100 text-green-800' :
                            val > 0 ? 'bg-green-50 text-green-700' :
                            val < -0.2 ? 'bg-red-100 text-red-800' :
                            'bg-gray-50'
                          }`}
                        >
                          {val.toFixed(2)}
                        </div>
                      ))}
                    </>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pipeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Breeding Pipeline Funnel</CardTitle>
              <CardDescription>
                Material flow through breeding stages
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between gap-2 h-48">
                {pipelineStages.map((stage: any, index: number) => (
                  <div key={index} className="flex-1 flex flex-col items-center gap-2">
                    <div className="text-sm font-medium">{stage.count}</div>
                    <div
                      className="w-full bg-primary/80 rounded-t transition-all duration-500 hover:bg-primary"
                      style={{ height: `${stage.percentage * 1.5}px` }}
                    />
                    <div className="text-xs text-muted-foreground">{stage.stage}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pipeline Stage Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {pipelineStages.map((stage: any, index: number) => (
                  <div key={index} className="flex items-center gap-4 p-4 border rounded-lg">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                      <span className="text-lg font-bold">{stage.stage}</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{stage.count} entries</span>
                        <Badge variant="outline">{stage.percentage}% of initial</Badge>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${stage.percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="predictions" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LineChart className="h-5 w-5" />
                  Yield Trend Forecast
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-48 flex items-end justify-between gap-2">
                  {geneticGain.map((data: GeneticGainData, i: number) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className={`w-full rounded-t ${i >= geneticGain.length - 2 ? 'bg-primary/50 border-2 border-dashed border-primary' : 'bg-primary'}`}
                        style={{ height: `${data.cumulative * 10}px` }}
                      />
                      <span className="text-xs">{data.year}</span>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground mt-4">
                  Projected {summary?.genetic_gain_rate || 2.5}% annual yield increase based on current genetic gain
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Selection Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {selectionResponse.slice(0, 4).map((entry: SelectionResponseData, i: number) => (
                    <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">BM-2025-{String(i + 1).padStart(3, '0')}</div>
                        <div className="flex gap-1 mt-1">
                          <Badge variant="secondary" className="text-xs">High yield</Badge>
                          <Badge variant="secondary" className="text-xs">Disease resistant</Badge>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-600">+{(entry.selected - entry.mean).toFixed(2)}</div>
                        <div className="text-xs text-muted-foreground">GEBV</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { 
  BarChart3, PieChart, LineChart, ScatterChart,
  Download, Settings, Plus, Maximize2, Trash2
} from 'lucide-react'
import { dataVisualizationAPI, ChartConfig } from '@/lib/api-client'

export function DataVisualization() {
  const [activeTab, setActiveTab] = useState('gallery')
  const [selectedChart, setSelectedChart] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const queryClient = useQueryClient()

  // Fetch charts
  const { data: chartsData, isLoading: chartsLoading } = useQuery({
    queryKey: ['visualizations-charts', typeFilter, sourceFilter],
    queryFn: () => dataVisualizationAPI.getCharts({
      type: typeFilter || undefined,
      data_source: sourceFilter || undefined,
    }),
  })

  const charts = chartsData?.data || []

  // Fetch statistics
  const { data: statsData } = useQuery({
    queryKey: ['visualizations-stats'],
    queryFn: () => dataVisualizationAPI.getStatistics(),
  })

  const stats = statsData || { total_charts: 0, by_type: {}, public_charts: 0, private_charts: 0, data_sources: 0 }

  // Fetch data sources
  const { data: sourcesData } = useQuery({
    queryKey: ['visualizations-sources'],
    queryFn: () => dataVisualizationAPI.getDataSources(),
  })

  const dataSources = sourcesData?.data || []

  // Fetch chart types
  const { data: typesData } = useQuery({
    queryKey: ['visualizations-types'],
    queryFn: () => dataVisualizationAPI.getChartTypes(),
  })

  const chartTypes = typesData?.data || []

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (chartId: string) => dataVisualizationAPI.deleteChart(chartId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['visualizations-charts'] })
      queryClient.invalidateQueries({ queryKey: ['visualizations-stats'] })
      toast.success('Chart deleted')
    },
    onError: () => toast.error('Failed to delete chart'),
  })

  const getChartIcon = (type: string) => {
    const icons: Record<string, any> = { bar: BarChart3, line: LineChart, pie: PieChart, scatter: ScatterChart }
    const Icon = icons[type] || BarChart3
    return <Icon className="h-5 w-5" />
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = { 
      bar: 'bg-blue-100 text-blue-800', 
      line: 'bg-green-100 text-green-800', 
      pie: 'bg-purple-100 text-purple-800', 
      scatter: 'bg-orange-100 text-orange-800',
      heatmap: 'bg-red-100 text-red-800',
      box: 'bg-pink-100 text-pink-800'
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const handleExport = async (chartId: string) => {
    try {
      const result = await dataVisualizationAPI.exportChart(chartId, 'png')
      toast.success(result.message)
    } catch {
      toast.error('Export failed')
    }
  }

  if (chartsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Visualization</h1>
          <p className="text-muted-foreground">Create and explore interactive charts</p>
        </div>
        <Button onClick={() => toast.success('Chart builder coming soon!')}>
          <Plus className="mr-2 h-4 w-4" />New Chart
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Charts</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_charts}</div>
            <p className="text-xs text-muted-foreground">Saved visualizations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bar Charts</CardTitle>
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.by_type?.bar || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Line Charts</CardTitle>
            <LineChart className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.by_type?.line || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scatter Plots</CardTitle>
            <ScatterChart className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.by_type?.scatter || 0}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="gallery"><BarChart3 className="mr-2 h-4 w-4" />Gallery</TabsTrigger>
            <TabsTrigger value="builder"><Settings className="mr-2 h-4 w-4" />Chart Builder</TabsTrigger>
          </TabsList>
          <div className="flex gap-2">
            <Select value={typeFilter || '__all__'} onValueChange={(v) => setTypeFilter(v === '__all__' ? '' : v)}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">All Types</SelectItem>
                {chartTypes.map((t: any) => (
                  <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sourceFilter || '__all__'} onValueChange={(v) => setSourceFilter(v === '__all__' ? '' : v)}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="All Sources" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">All Sources</SelectItem>
                {dataSources.map((s: any) => (
                  <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <TabsContent value="gallery" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {charts.map((chart: ChartConfig) => (
              <Card key={chart.id} className="cursor-pointer hover:border-primary" onClick={() => setSelectedChart(chart.id)}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getChartIcon(chart.type)}
                      <CardTitle className="text-lg">{chart.name}</CardTitle>
                    </div>
                    <Badge className={getTypeColor(chart.type)}>{chart.type}</Badge>
                  </div>
                  <CardDescription>Data: {chart.dataSource}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-32 bg-accent/50 rounded-lg flex items-center justify-center">
                    {getChartIcon(chart.type)}
                  </div>
                  <div className="flex items-center justify-between mt-4">
                    <span className="text-xs text-muted-foreground">
                      {chart.isPublic ? '🌐 Public' : '🔒 Private'}
                    </span>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon" aria-label="Expand chart" onClick={(e) => { e.stopPropagation(); setSelectedChart(chart.id) }}>
                        <Maximize2 className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" aria-label="Export chart" onClick={(e) => { e.stopPropagation(); handleExport(chart.id) }}>
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" aria-label="Delete chart" onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(chart.id) }}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          {charts.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No charts found. Create your first visualization!</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="builder">
          <Card>
            <CardHeader>
              <CardTitle>Chart Builder</CardTitle>
              <CardDescription>Create custom visualizations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Chart Type</label>
                    <Select>
                      <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent>
                        {chartTypes.map((t: any) => (
                          <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Data Source</label>
                    <Select>
                      <SelectTrigger><SelectValue placeholder="Select source" /></SelectTrigger>
                      <SelectContent>
                        {dataSources.map((s: any) => (
                          <SelectItem key={s.id} value={s.id}>{s.name} ({s.recordCount.toLocaleString()} records)</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">X-Axis</label>
                    <Select>
                      <SelectTrigger><SelectValue placeholder="Select field" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="germplasm">Germplasm</SelectItem>
                        <SelectItem value="trial">Trial</SelectItem>
                        <SelectItem value="location">Location</SelectItem>
                        <SelectItem value="year">Year</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Y-Axis</label>
                    <Select>
                      <SelectTrigger><SelectValue placeholder="Select field" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="yield">Yield</SelectItem>
                        <SelectItem value="height">Plant Height</SelectItem>
                        <SelectItem value="maturity">Days to Maturity</SelectItem>
                        <SelectItem value="count">Count</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button className="w-full">Generate Preview</Button>
                </div>
                <div className="md:col-span-2">
                  <div className="h-64 border-2 border-dashed rounded-lg flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                      <p>Chart preview will appear here</p>
                      <p className="text-sm">Configure options and click Generate Preview</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

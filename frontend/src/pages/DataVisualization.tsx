import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  BarChart3, PieChart, LineChart, ScatterChart,
  Download, Settings, Plus, Maximize2
} from 'lucide-react'

interface ChartConfig {
  id: string
  name: string
  type: 'bar' | 'line' | 'pie' | 'scatter'
  dataSource: string
  lastUpdated: string
}

export function DataVisualization() {
  const [activeTab, setActiveTab] = useState('gallery')
  const [selectedChart, setSelectedChart] = useState<string | null>(null)

  const charts: ChartConfig[] = [
    { id: '1', name: 'Yield Distribution', type: 'bar', dataSource: 'Trials', lastUpdated: '2 hours ago' },
    { id: '2', name: 'Trait Correlations', type: 'scatter', dataSource: 'Observations', lastUpdated: '1 day ago' },
    { id: '3', name: 'Germplasm by Origin', type: 'pie', dataSource: 'Germplasm', lastUpdated: '3 days ago' },
    { id: '4', name: 'Yield Trends', type: 'line', dataSource: 'Historical', lastUpdated: '1 week ago' },
    { id: '5', name: 'Selection Progress', type: 'bar', dataSource: 'Pipeline', lastUpdated: '2 days ago' },
    { id: '6', name: 'Disease Scores', type: 'scatter', dataSource: 'Phenotyping', lastUpdated: '5 hours ago' },
  ]

  const getChartIcon = (type: string) => {
    const icons: Record<string, any> = { bar: BarChart3, line: LineChart, pie: PieChart, scatter: ScatterChart }
    const Icon = icons[type] || BarChart3
    return <Icon className="h-5 w-5" />
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = { bar: 'bg-blue-100 text-blue-800', line: 'bg-green-100 text-green-800', pie: 'bg-purple-100 text-purple-800', scatter: 'bg-orange-100 text-orange-800' }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Visualization</h1>
          <p className="text-muted-foreground">Create and explore interactive charts</p>
        </div>
        <Button><Plus className="mr-2 h-4 w-4" />New Chart</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Charts</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{charts.length}</div>
            <p className="text-xs text-muted-foreground">Saved visualizations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bar Charts</CardTitle>
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{charts.filter(c => c.type === 'bar').length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Line Charts</CardTitle>
            <LineChart className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{charts.filter(c => c.type === 'line').length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scatter Plots</CardTitle>
            <ScatterChart className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{charts.filter(c => c.type === 'scatter').length}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="gallery"><BarChart3 className="mr-2 h-4 w-4" />Gallery</TabsTrigger>
          <TabsTrigger value="builder"><Settings className="mr-2 h-4 w-4" />Chart Builder</TabsTrigger>
        </TabsList>

        <TabsContent value="gallery" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {charts.map((chart) => (
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
                    <span className="text-xs text-muted-foreground">Updated {chart.lastUpdated}</span>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon"><Maximize2 className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="icon"><Download className="h-4 w-4" /></Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="builder">
          <Card>
            <CardHeader><CardTitle>Chart Builder</CardTitle><CardDescription>Create custom visualizations</CardDescription></CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Chart Type</label>
                    <Select>
                      <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="bar">Bar Chart</SelectItem>
                        <SelectItem value="line">Line Chart</SelectItem>
                        <SelectItem value="pie">Pie Chart</SelectItem>
                        <SelectItem value="scatter">Scatter Plot</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Data Source</label>
                    <Select>
                      <SelectTrigger><SelectValue placeholder="Select source" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="trials">Trials</SelectItem>
                        <SelectItem value="observations">Observations</SelectItem>
                        <SelectItem value="germplasm">Germplasm</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="md:col-span-2">
                  <div className="h-64 border-2 border-dashed rounded-lg flex items-center justify-center text-muted-foreground">
                    Chart preview will appear here
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

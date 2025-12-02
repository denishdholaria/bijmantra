import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
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

interface KPICard {
  title: string
  value: string
  change: number
  trend: 'up' | 'down'
  icon: React.ReactNode
  description: string
}

interface ChartData {
  label: string
  value: number
  color: string
}

export function AnalyticsDashboard() {
  const [timeRange, setTimeRange] = useState('30d')
  const [selectedProgram, setSelectedProgram] = useState('all')

  const kpis: KPICard[] = [
    {
      title: 'Genetic Gain',
      value: '2.4%',
      change: 0.3,
      trend: 'up',
      icon: <TrendingUp className="h-5 w-5" />,
      description: 'Annual genetic gain rate'
    },
    {
      title: 'Selection Accuracy',
      value: '0.78',
      change: 0.05,
      trend: 'up',
      icon: <Target className="h-5 w-5" />,
      description: 'Genomic prediction accuracy'
    },
    {
      title: 'Active Trials',
      value: '47',
      change: 12,
      trend: 'up',
      icon: <FlaskConical className="h-5 w-5" />,
      description: 'Currently running trials'
    },
    {
      title: 'Germplasm Entries',
      value: '12,847',
      change: 523,
      trend: 'up',
      icon: <Leaf className="h-5 w-5" />,
      description: 'Total germplasm in database'
    },
    {
      title: 'Observations',
      value: '284K',
      change: 15.2,
      trend: 'up',
      icon: <Activity className="h-5 w-5" />,
      description: 'Data points collected'
    },
    {
      title: 'Breeding Cycle',
      value: '3.2 yrs',
      change: -0.4,
      trend: 'up',
      icon: <Calendar className="h-5 w-5" />,
      description: 'Average cycle time'
    }
  ]

  const traitPerformance: ChartData[] = [
    { label: 'Yield', value: 85, color: 'bg-green-500' },
    { label: 'Disease Resistance', value: 72, color: 'bg-blue-500' },
    { label: 'Drought Tolerance', value: 68, color: 'bg-yellow-500' },
    { label: 'Quality', value: 79, color: 'bg-purple-500' },
    { label: 'Maturity', value: 91, color: 'bg-pink-500' }
  ]

  const pipelineStages = [
    { stage: 'F1', count: 234, percentage: 100 },
    { stage: 'F2', count: 189, percentage: 81 },
    { stage: 'F3', count: 145, percentage: 62 },
    { stage: 'F4', count: 98, percentage: 42 },
    { stage: 'F5', count: 67, percentage: 29 },
    { stage: 'Advanced', count: 34, percentage: 15 },
    { stage: 'Release', count: 8, percentage: 3 }
  ]

  const recentActivity = [
    { action: 'Trial completed', item: 'YT-2025-001', time: '2 hours ago', type: 'success' },
    { action: 'Crosses made', item: '45 new crosses', time: '5 hours ago', type: 'info' },
    { action: 'Data uploaded', item: 'Field observations', time: '1 day ago', type: 'info' },
    { action: 'Variety released', item: 'BM-Gold-2025', time: '3 days ago', type: 'success' },
    { action: 'Alert', item: 'Disease detected in Block A', time: '4 days ago', type: 'warning' }
  ]

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
          <Button variant="outline" size="icon">
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
                  Trait Performance Index
                </CardTitle>
                <CardDescription>
                  Progress towards breeding objectives
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {traitPerformance.map((trait, index) => (
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

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Recent Activity
                </CardTitle>
                <CardDescription>
                  Latest updates across programs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className={`w-2 h-2 mt-2 rounded-full ${
                        activity.type === 'success' ? 'bg-green-500' :
                        activity.type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{activity.action}</span>
                          <span className="text-xs text-muted-foreground">{activity.time}</span>
                        </div>
                        <span className="text-sm text-muted-foreground">{activity.item}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Breeding Pipeline Funnel */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Breeding Pipeline Funnel
              </CardTitle>
              <CardDescription>
                Material flow through breeding stages
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between gap-2 h-48">
                {pipelineStages.map((stage, index) => (
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
              <div className="grid grid-cols-6 gap-1 text-xs">
                {['', 'Yield', 'Height', 'Maturity', 'Quality', 'Resistance'].map((header, i) => (
                  <div key={i} className="p-2 font-medium text-center">{header}</div>
                ))}
                {['Yield', 'Height', 'Maturity', 'Quality', 'Resistance'].map((row, ri) => (
                  <>
                    <div key={`row-${ri}`} className="p-2 font-medium">{row}</div>
                    {[1.0, 0.3, -0.2, 0.5, 0.1].map((val, ci) => (
                      <div
                        key={`cell-${ri}-${ci}`}
                        className={`p-2 text-center rounded ${
                          val > 0.5 ? 'bg-green-100 text-green-800' :
                          val > 0 ? 'bg-green-50 text-green-700' :
                          val < -0.3 ? 'bg-red-100 text-red-800' :
                          'bg-gray-50'
                        }`}
                      >
                        {ri === ci ? '1.00' : (val * (ri + 1) / 5).toFixed(2)}
                      </div>
                    ))}
                  </>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pipeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Pipeline Stage Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {pipelineStages.map((stage, index) => (
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
                  {[65, 68, 72, 75, 78, 82, 85, 88].map((val, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className={`w-full rounded-t ${i >= 5 ? 'bg-primary/50 border-2 border-dashed border-primary' : 'bg-primary'}`}
                        style={{ height: `${val * 1.8}px` }}
                      />
                      <span className="text-xs">{2018 + i}</span>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground mt-4">
                  Projected 3.2% annual yield increase based on current genetic gain
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Selection Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { id: 'BM-2025-001', gebv: 2.45, traits: ['High yield', 'Disease resistant'] },
                    { id: 'BM-2025-015', gebv: 2.38, traits: ['Drought tolerant', 'Early maturity'] },
                    { id: 'BM-2025-023', gebv: 2.31, traits: ['Quality', 'High yield'] },
                    { id: 'BM-2025-042', gebv: 2.28, traits: ['Disease resistant', 'Quality'] }
                  ].map((entry, i) => (
                    <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">{entry.id}</div>
                        <div className="flex gap-1 mt-1">
                          {entry.traits.map((trait, ti) => (
                            <Badge key={ti} variant="secondary" className="text-xs">{trait}</Badge>
                          ))}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-600">+{entry.gebv}</div>
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

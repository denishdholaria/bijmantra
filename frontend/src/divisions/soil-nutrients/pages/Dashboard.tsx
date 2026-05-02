/**
 * Soil & Nutrients Dashboard
 *
 * Monitor soil health and nutrient levels across fields.
 */

import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { RefreshCw, Sprout, Droplets, Activity, Beaker } from 'lucide-react'
import { EChartsWrapper } from '@/components/charts/EChartsWrapper'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export function Dashboard() {
  const { data: soilTests, isLoading: testsLoading, error: testsError, refetch: refetchTests } = useQuery({
    queryKey: ['soil-tests'],
    queryFn: async () => {
      const response = await apiClient.get<any[]>('/api/v2/future/soil-tests')
      return response
    }
  })

  const { data: healthScores, isLoading: healthLoading, error: healthError, refetch: refetchHealth } = useQuery({
    queryKey: ['soil-health'],
    queryFn: async () => {
      const response = await apiClient.get<any[]>('/api/v2/future/soil-health')
      return response
    }
  })

  // We can also fetch fields to map IDs to names, but let's stick to core requirements first.
  // Assuming soilTests contains field_id.

  const isLoading = testsLoading || healthLoading
  const error = testsError || healthError

  const refetchAll = () => {
    refetchTests()
    refetchHealth()
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-10 w-24" />
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-[300px] w-full" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">Soil & Nutrients Dashboard</h1>
            <p className="text-muted-foreground text-gray-600 dark:text-gray-400">Monitor soil health and nutrient levels across your fields</p>
          </div>
        </div>
        <Alert variant="destructive">
          <AlertDescription className="flex items-center justify-between">
            <span>Failed to load soil data</span>
            <Button
              variant="outline"
              size="sm"
              onClick={refetchAll}
              aria-label="Retry loading data"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // Calculate stats
  const totalTests = soilTests?.length || 0

  const avgPh = totalTests > 0
    ? (soilTests?.reduce((acc: number, t: any) => acc + (t.ph || 0), 0) / totalTests).toFixed(1)
    : 'N/A'

  const avgOrganicMatter = totalTests > 0
    ? (soilTests?.reduce((acc: number, t: any) => acc + (t.organic_matter_percent || 0), 0) / totalTests).toFixed(1)
    : 'N/A'

  const avgHealthScore = healthScores?.length
    ? Math.round(healthScores.reduce((acc: number, s: any) => acc + (s.overall_score || 0), 0) / healthScores.length)
    : 'N/A'

  // Prepare chart data
  // Sort health scores by date
  const sortedHealth = [...(healthScores || [])].sort((a: any, b: any) =>
    new Date(a.assessment_date).getTime() - new Date(b.assessment_date).getTime()
  )

  const chartDates = sortedHealth.map((h: any) => h.assessment_date)
  const chartScores = sortedHealth.map((h: any) => h.overall_score)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">Soil & Nutrients Dashboard</h1>
          <p className="text-muted-foreground text-gray-600 dark:text-gray-400">Monitor soil health and nutrient levels across your fields</p>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={refetchAll}
          aria-label="Refresh data"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Total Soil Tests
            </CardTitle>
            <Beaker className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {totalTests}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Average pH
            </CardTitle>
            <Droplets className="h-4 w-4 text-cyan-600 dark:text-cyan-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {avgPh}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Avg Organic Matter
            </CardTitle>
            <Sprout className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {avgOrganicMatter}%
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Avg Health Score
            </CardTitle>
            <Activity className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {avgHealthScore}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chart and Recent Activity Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">

        {/* Recent Soil Tests Table */}
        <Card className="col-span-4 bg-white dark:bg-slate-800">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-gray-100">Recent Soil Tests</CardTitle>
          </CardHeader>
          <CardContent>
            {soilTests && soilTests.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-gray-500 dark:text-gray-400">Field</TableHead>
                    <TableHead className="text-gray-500 dark:text-gray-400">Date</TableHead>
                    <TableHead className="text-gray-500 dark:text-gray-400">pH</TableHead>
                    <TableHead className="text-gray-500 dark:text-gray-400">OM %</TableHead>
                    <TableHead className="text-gray-500 dark:text-gray-400">N-P-K (ppm)</TableHead>
                    <TableHead className="text-right text-gray-500 dark:text-gray-400">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {soilTests.slice(0, 10).map((test: any) => (
                    <TableRow key={test.id} className="hover:bg-gray-50 dark:hover:bg-slate-700/50">
                      <TableCell className="font-medium text-gray-900 dark:text-gray-100">
                        {test.field_name || `Field #${test.field_id}`}
                      </TableCell>
                      <TableCell className="text-gray-500 dark:text-gray-400">
                        {new Date(test.sample_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-gray-900 dark:text-gray-100">{test.ph}</TableCell>
                      <TableCell className="text-gray-900 dark:text-gray-100">{test.organic_matter_percent}</TableCell>
                      <TableCell className="text-gray-500 dark:text-gray-400">
                        {test.n_ppm}-{test.p_ppm}-{test.k_ppm}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          aria-label={`View details for test ${test.id}`}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No recent soil tests found.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Soil Health Trend Chart */}
        <Card className="col-span-3 bg-white dark:bg-slate-800">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-gray-100">Soil Health Trend</CardTitle>
          </CardHeader>
          <CardContent>
            {chartDates.length > 0 ? (
              <EChartsWrapper
                option={{
                  tooltip: {
                    trigger: 'axis'
                  },
                  grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                  },
                  xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: chartDates,
                    axisLine: { lineStyle: { color: '#9ca3af' } },
                    axisLabel: { color: '#6b7280' }
                  },
                  yAxis: {
                    type: 'value',
                    min: 0,
                    max: 100,
                    axisLine: { show: false },
                    axisTick: { show: false },
                    splitLine: { lineStyle: { color: '#e5e7eb', type: 'dashed' } },
                    axisLabel: { color: '#6b7280' }
                  },
                  series: [{
                    name: 'Health Score',
                    data: chartScores,
                    type: 'line',
                    smooth: true,
                    itemStyle: { color: '#10b981' },
                    areaStyle: {
                      color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0, color: 'rgba(16, 185, 129, 0.2)' // 0% 处的颜色
                        }, {
                            offset: 1, color: 'rgba(16, 185, 129, 0)' // 100% 处的颜色
                        }],
                        global: false // 缺省为 false
                      }
                    }
                  }]
                }}
                style={{ height: '300px', width: '100%' }}
              />
            ) : (
              <div className="flex h-[300px] items-center justify-center text-gray-500 dark:text-gray-400">
                No health data available.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

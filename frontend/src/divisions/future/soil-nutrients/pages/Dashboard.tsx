/**
 * Soil & Nutrients Dashboard
 *
 * Overview of soil test statistics and health metrics.
 * Shows stats cards, recent soil tests table, and health trend chart.
 */
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiClient } from '@/lib/api-client'
import { RefreshCw, Sprout, Droplets, Activity, FlaskConical, Eye } from 'lucide-react'
import { EChartsWrapper } from '@/components/charts/EChartsWrapper'

// Types based on backend schemas
interface SoilTest {
  id: number
  field_id: number | null
  sample_id: string
  sample_date: string
  lab_name: string | null
  ph: number | null
  organic_matter_percent: number | null
  n_ppm: number | null
  p_ppm: number | null
  k_ppm: number | null
  created_at: string
}

interface SoilHealthScore {
  id: number
  field_id: number | null
  assessment_date: string
  overall_score: number | null
  physical_score: number | null
  chemical_score: number | null
  biological_score: number | null
  created_at: string
}

/**
 * Calculate average of numeric values, ignoring nulls
 */
function calculateAverage(values: (number | null | undefined)[]): number {
  const validValues = values.filter((v): v is number => v !== null && v !== undefined)
  if (validValues.length === 0) return 0
  return validValues.reduce((sum, v) => sum + v, 0) / validValues.length
}

/**
 * Format date for display
 */
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function Dashboard() {
  // Fetch soil tests
  const {
    data: soilTests,
    isLoading: testsLoading,
    error: testsError,
    refetch: refetchTests,
  } = useQuery<SoilTest[]>({
    queryKey: ['soil-tests'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v2/future/soil-tests/')
      return response
    },
  })

  // Fetch soil health scores
  const {
    data: healthScores,
    isLoading: healthLoading,
    error: healthError,
    refetch: refetchHealth,
  } = useQuery<SoilHealthScore[]>({
    queryKey: ['soil-health'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v2/future/soil-health/')
      return response
    },
  })

  const isLoading = testsLoading || healthLoading
  const error = testsError || healthError

  const refetch = () => {
    refetchTests()
    refetchHealth()
  }

  // Calculate stats
  const totalTests = soilTests?.length || 0
  const avgPh = calculateAverage(soilTests?.map((t) => t.ph) || [])
  const avgOrganicMatter = calculateAverage(soilTests?.map((t) => t.organic_matter_percent) || [])
  const avgHealthScore = calculateAverage(healthScores?.map((h) => h.overall_score) || [])

  // Get last 10 tests for table
  const recentTests = soilTests?.slice(0, 10) || []

  // Prepare chart data (sort by date ascending)
  const sortedHealthScores = [...(healthScores || [])]
    .sort((a, b) => new Date(a.assessment_date).getTime() - new Date(b.assessment_date).getTime())
  const chartDates = sortedHealthScores.map((h) => formatDate(h.assessment_date))
  const chartScores = sortedHealthScores.map((h) => h.overall_score ?? 0)

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription className="flex items-center justify-between">
          <span>Failed to load soil data</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            aria-label="Retry loading data"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  // Empty state
  if (totalTests === 0 && healthScores?.length === 0) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">
              Soil & Nutrients Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Monitor soil health and nutrient levels across your fields
            </p>
          </div>
          <Button variant="outline" size="icon" onClick={() => refetch()} aria-label="Refresh data">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <Alert>
          <AlertDescription>
            No soil data available. Start by recording soil test results to see statistics and
            trends.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">
            Soil & Nutrients Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor soil health and nutrient levels across your fields
          </p>
        </div>
        <Button variant="outline" size="icon" onClick={() => refetch()} aria-label="Refresh data">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Stats Cards Row */}
      <div className="grid gap-4 md:grid-cols-4">
        {/* Total Soil Tests */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Total Soil Tests
            </CardTitle>
            <Sprout className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalTests}</div>
          </CardContent>
        </Card>

        {/* Average pH */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Average pH
            </CardTitle>
            <Droplets className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {avgPh.toFixed(1)}
            </div>
          </CardContent>
        </Card>

        {/* Average Organic Matter % */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Avg Organic Matter
            </CardTitle>
            <FlaskConical className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {avgOrganicMatter.toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        {/* Average Health Score */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Avg Health Score
            </CardTitle>
            <Activity className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {avgHealthScore.toFixed(0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Soil Tests Table */}
      <Card className="bg-white dark:bg-slate-800">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-gray-100">Recent Soil Tests</CardTitle>
          <CardDescription className="text-gray-600 dark:text-gray-400">
            Last {recentTests.length} soil tests recorded
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recentTests.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No soil tests recorded yet
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-gray-700 dark:text-gray-300">Sample ID</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Test Date</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">pH</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Organic Matter %</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">N-P-K (ppm)</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentTests.map((test) => (
                  <TableRow key={test.id}>
                    <TableCell className="font-medium text-gray-900 dark:text-gray-100">
                      {test.sample_id}
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
                      {formatDate(test.sample_date)}
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
                      {test.ph?.toFixed(1) ?? '—'}
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
                      {test.organic_matter_percent?.toFixed(1) ?? '—'}%
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
                      {test.n_ppm ?? '—'} - {test.p_ppm ?? '—'} - {test.k_ppm ?? '—'}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" aria-label="View details">
                        <Eye className="h-4 w-4 mr-1" />
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Soil Health Trend Chart */}
      {sortedHealthScores.length > 0 && (
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-gray-100">Soil Health Trend</CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400">
              Overall health score over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <EChartsWrapper
              option={{
                tooltip: {
                  trigger: 'axis',
                },
                xAxis: {
                  type: 'category',
                  data: chartDates,
                  axisLabel: {
                    color: '#6b7280',
                  },
                },
                yAxis: {
                  type: 'value',
                  min: 0,
                  max: 100,
                  axisLabel: {
                    color: '#6b7280',
                  },
                },
                series: [
                  {
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
                        colorStops: [
                          { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
                          { offset: 1, color: 'rgba(16, 185, 129, 0.05)' },
                        ],
                      },
                    },
                  },
                ],
                grid: {
                  left: '3%',
                  right: '4%',
                  bottom: '3%',
                  containLabel: true,
                },
              }}
              style={{ height: '300px' }}
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Backward compatibility export
export { Dashboard as SoilNutrientsDashboard }

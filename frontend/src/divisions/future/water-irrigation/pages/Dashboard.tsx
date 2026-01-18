/**
 * Water & Irrigation Dashboard
 *
 * Overview of irrigation schedules, water balance, and moisture monitoring.
 */
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiClient } from '@/lib/api-client'
import { RefreshCw, Droplets, Calendar, Activity, Gauge, Eye } from 'lucide-react'
import { EChartsWrapper } from '@/components/charts/EChartsWrapper'

// Types based on backend schemas
interface IrrigationSchedule {
  id: number
  field_id: number | null
  crop_name: string
  schedule_date: string
  irrigation_method: string | null
  water_requirement_mm: number | null
  duration_minutes: number | null
  status: 'planned' | 'in_progress' | 'completed' | 'canceled'
  created_at: string
}

interface WaterBalance {
  id: number
  field_id: number
  balance_date: string
  precipitation_mm: number
  irrigation_mm: number
  et_actual_mm: number
  deficit_mm: number
  surplus_mm: number
  created_at: string
}

interface SoilMoistureReading {
  id: number
  device_id: number
  reading_timestamp: string
  volumetric_water_content: number
  created_at: string
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

/**
 * Get status badge variant
 */
function getStatusVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'completed':
      return 'default'
    case 'in_progress':
      return 'secondary'
    case 'canceled':
      return 'destructive'
    default:
      return 'outline'
  }
}

export function Dashboard() {
  // Fetch irrigation schedules
  const {
    data: schedules,
    isLoading: schedulesLoading,
    error: schedulesError,
    refetch: refetchSchedules,
  } = useQuery<IrrigationSchedule[]>({
    queryKey: ['irrigation-schedules'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v2/future/irrigation-schedules/')
      return response
    },
  })

  // Fetch water balance records
  const {
    data: waterBalance,
    isLoading: balanceLoading,
    error: balanceError,
    refetch: refetchBalance,
  } = useQuery<WaterBalance[]>({
    queryKey: ['water-balance'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v2/future/water-balance/')
      return response
    },
  })

  // Fetch soil moisture readings
  const {
    data: moistureReadings,
    isLoading: moistureLoading,
    error: moistureError,
    refetch: refetchMoisture,
  } = useQuery<SoilMoistureReading[]>({
    queryKey: ['soil-moisture'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v2/future/soil-moisture/')
      return response
    },
  })

  const isLoading = schedulesLoading || balanceLoading || moistureLoading
  const error = schedulesError || balanceError || moistureError

  const refetch = () => {
    refetchSchedules()
    refetchBalance()
    refetchMoisture()
  }

  // Calculate stats
  const totalSchedules = schedules?.length || 0
  const upcomingSchedules = schedules?.filter((s) => s.status === 'planned').length || 0
  const avgWaterApplied =
    schedules && schedules.length > 0
      ? schedules
          .filter((s) => s.water_requirement_mm)
          .reduce((sum, s) => sum + (s.water_requirement_mm || 0), 0) /
        schedules.filter((s) => s.water_requirement_mm).length
      : 0
  const activeSensors = new Set(moistureReadings?.map((r) => r.device_id) || []).size

  // Get upcoming schedules for table (planned only, next 10)
  const upcomingSchedulesList =
    schedules
      ?.filter((s) => s.status === 'planned')
      .sort((a, b) => new Date(a.schedule_date).getTime() - new Date(b.schedule_date).getTime())
      .slice(0, 10) || []

  // Prepare water balance chart data
  const sortedBalance = [...(waterBalance || [])]
    .sort((a, b) => new Date(a.balance_date).getTime() - new Date(b.balance_date).getTime())
    .slice(-14) // Last 14 days
  const chartDates = sortedBalance.map((w) => formatDate(w.balance_date))
  const precipitationData = sortedBalance.map((w) => w.precipitation_mm)
  const irrigationData = sortedBalance.map((w) => w.irrigation_mm)
  const etData = sortedBalance.map((w) => w.et_actual_mm)

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
          <span>Failed to load water and irrigation data</span>
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
  if (totalSchedules === 0 && waterBalance?.length === 0 && moistureReadings?.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">
              Water & Irrigation Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Monitor irrigation schedules and water management across your fields
            </p>
          </div>
          <Button variant="outline" size="icon" onClick={() => refetch()} aria-label="Refresh data">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <Alert>
          <AlertDescription>
            No water management data available. Start by creating irrigation schedules or recording
            water balance data.
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
            Water & Irrigation Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor irrigation schedules and water management across your fields
          </p>
        </div>
        <Button variant="outline" size="icon" onClick={() => refetch()} aria-label="Refresh data">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Stats Cards Row */}
      <div className="grid gap-4 md:grid-cols-4">
        {/* Total Schedules */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Total Schedules
            </CardTitle>
            <Calendar className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {totalSchedules}
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Schedules */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Upcoming
            </CardTitle>
            <Activity className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {upcomingSchedules}
            </div>
          </CardContent>
        </Card>

        {/* Average Water Applied */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Avg Water (mm)
            </CardTitle>
            <Droplets className="h-4 w-4 text-cyan-600 dark:text-cyan-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {avgWaterApplied.toFixed(1)}
            </div>
          </CardContent>
        </Card>

        {/* Active Sensors */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Active Sensors
            </CardTitle>
            <Gauge className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {activeSensors}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Irrigation Table */}
      <Card className="bg-white dark:bg-slate-800">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-gray-100">Upcoming Irrigation</CardTitle>
          <CardDescription className="text-gray-600 dark:text-gray-400">
            Next {upcomingSchedulesList.length} planned irrigation schedules
          </CardDescription>
        </CardHeader>
        <CardContent>
          {upcomingSchedulesList.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No upcoming irrigation schedules
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-gray-700 dark:text-gray-300">Crop</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Schedule Date</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Method</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Water (mm)</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Status</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {upcomingSchedulesList.map((schedule) => (
                  <TableRow key={schedule.id}>
                    <TableCell className="font-medium text-gray-900 dark:text-gray-100">
                      {schedule.crop_name}
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
                      {formatDate(schedule.schedule_date)}
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
                      {schedule.irrigation_method ?? '—'}
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
                      {schedule.water_requirement_mm?.toFixed(1) ?? '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(schedule.status)}>{schedule.status}</Badge>
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

      {/* Water Balance Chart */}
      {sortedBalance.length > 0 && (
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-gray-100">Water Balance Trend</CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400">
              Precipitation, Irrigation, and Evapotranspiration (mm)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <EChartsWrapper
              option={{
                tooltip: {
                  trigger: 'axis',
                },
                legend: {
                  data: ['Precipitation', 'Irrigation', 'ET'],
                  textStyle: { color: '#6b7280' },
                },
                xAxis: {
                  type: 'category',
                  data: chartDates,
                  axisLabel: { color: '#6b7280' },
                },
                yAxis: {
                  type: 'value',
                  name: 'mm',
                  axisLabel: { color: '#6b7280' },
                },
                series: [
                  {
                    name: 'Precipitation',
                    type: 'bar',
                    data: precipitationData,
                    itemStyle: { color: '#3b82f6' },
                  },
                  {
                    name: 'Irrigation',
                    type: 'bar',
                    data: irrigationData,
                    itemStyle: { color: '#06b6d4' },
                  },
                  {
                    name: 'ET',
                    type: 'line',
                    data: etData,
                    itemStyle: { color: '#ef4444' },
                    smooth: true,
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

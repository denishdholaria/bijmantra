/**
 * Soil Moisture Monitoring Page
 * Display sensor readings with timeseries chart
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, Gauge, RefreshCw, Trash2, Battery, Signal } from 'lucide-react'
import { EChartsWrapper } from '@/components/charts/EChartsWrapper'

interface SoilMoistureReading {
  id: number
  device_id: number
  field_id: number | null
  reading_timestamp: string
  depth_cm: number
  volumetric_water_content: number
  soil_temperature_c: number | null
  electrical_conductivity: number | null
  sensor_type: string
  battery_level: number | null
  signal_strength: number | null
  created_at: string
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getMoistureStatus(vwc: number): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } {
  const pct = vwc * 100
  if (pct >= 40) return { label: 'Saturated', variant: 'secondary' }
  if (pct >= 25) return { label: 'Optimal', variant: 'default' }
  if (pct >= 15) return { label: 'Low', variant: 'outline' }
  return { label: 'Critical', variant: 'destructive' }
}

export function SoilMoisture() {
  const [showCreate, setShowCreate] = useState(false)
  const [newReading, setNewReading] = useState({
    device_id: 1,
    reading_timestamp: new Date().toISOString(),
    depth_cm: 30,
    volumetric_water_content: 0.25,
    soil_temperature_c: 20,
    sensor_type: 'soil_moisture',
  })
  const queryClient = useQueryClient()

  const { data: readings, isLoading, error, refetch } = useQuery<SoilMoistureReading[]>({
    queryKey: ['soil-moisture'],
    queryFn: () => apiClient.get('/api/v2/future/soil-moisture/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newReading) => apiClient.post('/api/v2/future/soil-moisture/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['soil-moisture'] })
      toast.success('Reading recorded')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/soil-moisture/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['soil-moisture'] })
      toast.success('Reading deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  // Group readings by device
  const deviceGroups = readings?.reduce((acc, r) => {
    if (!acc[r.device_id]) acc[r.device_id] = []
    acc[r.device_id].push(r)
    return acc
  }, {} as Record<number, SoilMoistureReading[]>) || {}

  const deviceIds = Object.keys(deviceGroups).map(Number)

  // Get latest reading per device
  const latestByDevice = deviceIds.map((id) => {
    const sorted = [...deviceGroups[id]].sort(
      (a, b) => new Date(b.reading_timestamp).getTime() - new Date(a.reading_timestamp).getTime()
    )
    return sorted[0]
  })

  // Chart data from most recent 24 readings
  const sortedReadings = [...(readings || [])]
    .sort((a, b) => new Date(a.reading_timestamp).getTime() - new Date(b.reading_timestamp).getTime())
    .slice(-24)
  const chartTimes = sortedReadings.map((r) => formatDateTime(r.reading_timestamp))
  const chartVWC = sortedReadings.map((r) => (r.volumetric_water_content * 100).toFixed(1))

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Gauge className="h-8 w-8 text-emerald-500" />
            Soil Moisture
          </h1>
          <p className="text-muted-foreground mt-1">
            Monitor soil moisture sensor readings across your fields
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Manual Reading
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Record Soil Moisture</DialogTitle>
                <DialogDescription>Manually enter a sensor reading</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Device ID</Label>
                    <Input
                      type="number"
                      value={newReading.device_id}
                      onChange={(e) => setNewReading((p) => ({ ...p, device_id: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Depth (cm)</Label>
                    <Input
                      type="number"
                      value={newReading.depth_cm}
                      onChange={(e) => setNewReading((p) => ({ ...p, depth_cm: Number(e.target.value) }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>VWC (0-1)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      value={newReading.volumetric_water_content}
                      onChange={(e) => setNewReading((p) => ({ ...p, volumetric_water_content: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Temp (°C)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newReading.soil_temperature_c || ''}
                      onChange={(e) => setNewReading((p) => ({ ...p, soil_temperature_c: Number(e.target.value) }))}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button onClick={() => createMutation.mutate(newReading)} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Saving...' : 'Record'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load soil moisture data.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32" />)}
          </div>
          <Skeleton className="h-80" />
        </div>
      )}

      {!isLoading && !error && (
        <>
          {/* Device Status Cards */}
          {latestByDevice.length > 0 && (
            <div className="grid gap-4 md:grid-cols-3">
              {latestByDevice.map((latest) => {
                const status = getMoistureStatus(latest.volumetric_water_content)
                return (
                  <Card key={latest.device_id} className="bg-white dark:bg-slate-800">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          Device {latest.device_id}
                        </CardTitle>
                        <Badge variant={status.variant}>{status.label}</Badge>
                      </div>
                      <CardDescription>Depth: {latest.depth_cm} cm</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
                        {(latest.volumetric_water_content * 100).toFixed(1)}%
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                        {latest.battery_level !== null && (
                          <span className="flex items-center gap-1">
                            <Battery className="h-3 w-3" />
                            {latest.battery_level}%
                          </span>
                        )}
                        {latest.signal_strength !== null && (
                          <span className="flex items-center gap-1">
                            <Signal className="h-3 w-3" />
                            {latest.signal_strength}
                          </span>
                        )}
                        <span>{formatDateTime(latest.reading_timestamp)}</span>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}

          {/* Moisture Trend Chart */}
          {sortedReadings.length > 0 && (
            <Card className="bg-white dark:bg-slate-800">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-gray-100">Moisture Trend</CardTitle>
                <CardDescription>
                  Volumetric Water Content (%) — Thresholds: FC=25-35%, WP=10-15%
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EChartsWrapper
                  option={{
                    tooltip: { trigger: 'axis' },
                    xAxis: { type: 'category', data: chartTimes, axisLabel: { color: '#6b7280', rotate: 45 } },
                    yAxis: { type: 'value', name: 'VWC %', min: 0, max: 60, axisLabel: { color: '#6b7280' } },
                    series: [
                      {
                        name: 'VWC',
                        type: 'line',
                        data: chartVWC,
                        smooth: true,
                        itemStyle: { color: '#10b981' },
                        areaStyle: {
                          color: {
                            type: 'linear',
                            x: 0, y: 0, x2: 0, y2: 1,
                            colorStops: [
                              { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
                              { offset: 1, color: 'rgba(16, 185, 129, 0.05)' },
                            ],
                          },
                        },
                        markLine: {
                          silent: true,
                          data: [
                            { yAxis: 35, name: 'Field Capacity', lineStyle: { color: '#3b82f6', type: 'dashed' } },
                            { yAxis: 15, name: 'Wilting Point', lineStyle: { color: '#ef4444', type: 'dashed' } },
                          ],
                        },
                      },
                    ],
                    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
                  }}
                  style={{ height: '300px' }}
                />
              </CardContent>
            </Card>
          )}

          {/* Recent Readings Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-gray-900 dark:text-gray-100">Recent Readings</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Device</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead className="text-center">Depth (cm)</TableHead>
                    <TableHead className="text-center">VWC (%)</TableHead>
                    <TableHead className="text-center">Temp (°C)</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Array.isArray(readings) && readings.length > 0 ? (
                    readings.slice(0, 20).map((reading) => (
                      <TableRow key={reading.id}>
                        <TableCell className="font-medium">Device {reading.device_id}</TableCell>
                        <TableCell>{formatDateTime(reading.reading_timestamp)}</TableCell>
                        <TableCell className="text-center">{reading.depth_cm}</TableCell>
                        <TableCell className="text-center">
                          <Badge variant={getMoistureStatus(reading.volumetric_water_content).variant}>
                            {(reading.volumetric_water_content * 100).toFixed(1)}%
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          {reading.soil_temperature_c?.toFixed(1) ?? '—'}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Delete reading"
                            onClick={() => deleteMutation.mutate(reading.id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-12">
                        <Gauge className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                        <p className="text-muted-foreground">No soil moisture readings yet</p>
                        <Button className="mt-4" onClick={() => setShowCreate(true)}>
                          <Plus className="h-4 w-4 mr-2" />Add Reading
                        </Button>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

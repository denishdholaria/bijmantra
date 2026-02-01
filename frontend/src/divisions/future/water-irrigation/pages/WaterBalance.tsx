/**
 * Water Balance Page
 * Track daily water balance records with inputs/outputs chart
 */
import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
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
import { AlertCircle, Plus, Droplets, RefreshCw, Trash2 } from 'lucide-react'
import { EChartsWrapper } from '@/components/charts/EChartsWrapper'
import { useActiveWorkspace } from '@/store/workspaceStore'

interface WaterBalance {
  id: number
  field_id: number
  balance_date: string
  precipitation_mm: number
  irrigation_mm: number
  et_actual_mm: number
  runoff_mm: number
  deep_percolation_mm: number
  soil_water_content_mm: number
  available_water_mm: number
  deficit_mm: number
  surplus_mm: number
  crop_name: string | null
  growth_stage: string | null
  created_at: string
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function WaterBalance() {
  const { activeWorkspace } = useActiveWorkspace()
  const [showCreate, setShowCreate] = useState(false)
  const [newRecord, setNewRecord] = useState({
    field_id: 1,
    balance_date: new Date().toISOString().split('T')[0],
    precipitation_mm: 0,
    irrigation_mm: 0,
    et_actual_mm: 0,
    runoff_mm: 0,
    deep_percolation_mm: 0,
    soil_water_content_mm: 0,
    available_water_mm: 0,
    deficit_mm: 0,
    surplus_mm: 0,
    crop_name: '',
    growth_stage: '',
  })
  const queryClient = useQueryClient()

  const { data: balanceRecords, isLoading, error, refetch } = useQuery<WaterBalance[]>({
    queryKey: ['water-balance', activeWorkspace?.id],
    queryFn: () => apiClient.get('/api/v2/future/water-balance/'),
    enabled: !!activeWorkspace,
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newRecord) => apiClient.post('/api/v2/future/water-balance/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['water-balance', activeWorkspace?.id] })
      toast.success('Water balance record created')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create record'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/water-balance/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['water-balance', activeWorkspace?.id] })
      toast.success('Record deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  if (!activeWorkspace) {
    return <Navigate to="/gateway" />
  }

  // Calculate summary stats
  const totalPrecipitation = balanceRecords?.reduce((sum, r) => sum + r.precipitation_mm, 0) || 0
  const totalIrrigation = balanceRecords?.reduce((sum, r) => sum + r.irrigation_mm, 0) || 0
  const totalET = balanceRecords?.reduce((sum, r) => sum + r.et_actual_mm, 0) || 0
  const totalRunoff = balanceRecords?.reduce((sum, r) => sum + r.runoff_mm, 0) || 0
  const totalPercolation = balanceRecords?.reduce((sum, r) => sum + r.deep_percolation_mm, 0) || 0
  const netBalance = totalPrecipitation + totalIrrigation - totalET - totalRunoff - totalPercolation

  // Chart data
  const sortedRecords = [...(balanceRecords || [])]
    .sort((a, b) => new Date(a.balance_date).getTime() - new Date(b.balance_date).getTime())
    .slice(-14)
  const chartDates = sortedRecords.map((r) => formatDate(r.balance_date))
  const inputsData = sortedRecords.map((r) => r.precipitation_mm + r.irrigation_mm)
  const outputsData = sortedRecords.map((r) => r.et_actual_mm + r.runoff_mm + r.deep_percolation_mm)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Droplets className="h-8 w-8 text-cyan-500" />
            Water Balance
          </h1>
          <p className="text-muted-foreground mt-1">
            Track daily water inputs and outputs for your fields
          </p>
          <p className="text-xs text-muted-foreground mt-2 font-mono bg-slate-100 dark:bg-slate-800 p-2 rounded inline-block">
            ΔS = P + I - ET - R - D
            <span className="ml-2 opacity-75 font-sans">
              (Where: P=Precipitation, I=Irrigation, ET=Evapotranspiration, R=Runoff, D=Deep Percolation)
            </span>
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
                New Record
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Record Water Balance</DialogTitle>
                <DialogDescription>
                  ΔS = P + I - ET - R - D (Precipitation + Irrigation - ET - Runoff - Deep Percolation)
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4 max-h-96 overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Field ID</Label>
                    <Input
                      type="number"
                      value={newRecord.field_id}
                      onChange={(e) => setNewRecord((p) => ({ ...p, field_id: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Date</Label>
                    <Input
                      type="date"
                      value={newRecord.balance_date}
                      onChange={(e) => setNewRecord((p) => ({ ...p, balance_date: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Precipitation (mm)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newRecord.precipitation_mm}
                      onChange={(e) => setNewRecord((p) => ({ ...p, precipitation_mm: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Irrigation (mm)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newRecord.irrigation_mm}
                      onChange={(e) => setNewRecord((p) => ({ ...p, irrigation_mm: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>ET (mm)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newRecord.et_actual_mm}
                      onChange={(e) => setNewRecord((p) => ({ ...p, et_actual_mm: Number(e.target.value) }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Runoff (mm)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newRecord.runoff_mm}
                      onChange={(e) => setNewRecord((p) => ({ ...p, runoff_mm: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Deep Percolation (mm)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newRecord.deep_percolation_mm}
                      onChange={(e) => setNewRecord((p) => ({ ...p, deep_percolation_mm: Number(e.target.value) }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Deficit (mm)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newRecord.deficit_mm}
                      onChange={(e) => setNewRecord((p) => ({ ...p, deficit_mm: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Surplus (mm)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newRecord.surplus_mm}
                      onChange={(e) => setNewRecord((p) => ({ ...p, surplus_mm: Number(e.target.value) }))}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button onClick={() => createMutation.mutate(newRecord)} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create'}
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
            Failed to load water balance data.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-4">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24" />)}
          </div>
          <Skeleton className="h-80" />
        </div>
      )}

      {!isLoading && !error && (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card className="bg-white dark:bg-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Total Precipitation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {totalPrecipitation.toFixed(1)} mm
                </div>
              </CardContent>
            </Card>
            <Card className="bg-white dark:bg-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Total Irrigation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-cyan-600 dark:text-cyan-400">
                  {totalIrrigation.toFixed(1)} mm
                </div>
              </CardContent>
            </Card>
            <Card className="bg-white dark:bg-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Total ET
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {totalET.toFixed(1)} mm
                </div>
              </CardContent>
            </Card>
            <Card className="bg-white dark:bg-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Net Balance (ΔS)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${netBalance >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                  {netBalance >= 0 ? '+' : ''}{netBalance.toFixed(1)} mm
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Water Balance Chart */}
          {sortedRecords.length > 0 && (
            <Card className="bg-white dark:bg-slate-800">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-gray-100">Water Balance Trend</CardTitle>
                <CardDescription>Inputs (P+I) vs Outputs (ET+R+D)</CardDescription>
              </CardHeader>
              <CardContent>
                <EChartsWrapper
                  option={{
                    tooltip: { trigger: 'axis' },
                    legend: { data: ['Inputs (P+I)', 'Outputs (ET+R+D)'], textStyle: { color: '#6b7280' } },
                    xAxis: { type: 'category', data: chartDates, axisLabel: { color: '#6b7280' } },
                    yAxis: { type: 'value', name: 'mm', axisLabel: { color: '#6b7280' } },
                    series: [
                      { name: 'Inputs (P+I)', type: 'bar', data: inputsData, itemStyle: { color: '#3b82f6' } },
                      { name: 'Outputs (ET+R+D)', type: 'bar', data: outputsData, itemStyle: { color: '#ef4444' } },
                    ],
                    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
                  }}
                  style={{ height: '300px' }}
                />
              </CardContent>
            </Card>
          )}

          {/* Data Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-gray-900 dark:text-gray-100">Records</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-center">Precip (mm)</TableHead>
                    <TableHead className="text-center">Irrigation (mm)</TableHead>
                    <TableHead className="text-center">ET (mm)</TableHead>
                    <TableHead className="text-center">Deficit</TableHead>
                    <TableHead className="text-center">Surplus</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Array.isArray(balanceRecords) && balanceRecords.length > 0 ? (
                    balanceRecords.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell className="font-medium">{formatDate(record.balance_date)}</TableCell>
                        <TableCell className="text-center">{record.precipitation_mm.toFixed(1)}</TableCell>
                        <TableCell className="text-center">{record.irrigation_mm.toFixed(1)}</TableCell>
                        <TableCell className="text-center">{record.et_actual_mm.toFixed(1)}</TableCell>
                        <TableCell className="text-center">{record.deficit_mm.toFixed(1)}</TableCell>
                        <TableCell className="text-center">{record.surplus_mm.toFixed(1)}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Delete record"
                            onClick={() => deleteMutation.mutate(record.id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-12">
                        <Droplets className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                        <p className="text-muted-foreground">No water balance records yet</p>
                        <Button className="mt-4" onClick={() => setShowCreate(true)}>
                          <Plus className="h-4 w-4 mr-2" />Add First Record
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

/**
 * GDD Tracker Page
 * Growing Degree Days monitoring and logging
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
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
import { AlertCircle, Plus, Thermometer, RefreshCw, Trash2, Sun } from 'lucide-react'

interface GDDLog {
  id: number
  field_id: number
  date: string
  tmax: number
  tmin: number
  daily_gdd: number
  cumulative_gdd: number | null
  created_at: string
}

export function GDDTracker() {
  const [showCreate, setShowCreate] = useState(false)
  const [newLog, setNewLog] = useState({
    field_id: 1, // Defaulting to 1 for now, ideally selectable
    date: new Date().toISOString().split('T')[0],
    tmax: 30,
    tmin: 15,
  })
  const queryClient = useQueryClient()

  const { data: logs, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'gdd'],
    queryFn: () => apiClient.get('/api/v2/future/gdd/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newLog) => apiClient.post('/api/v2/future/gdd/', {
        ...data,
        base_temp: 10 // Assumption for corn/general
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'gdd'] })
      toast.success('GDD Log created')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create log'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/gdd/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'gdd'] })
      toast.success('Log deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Thermometer className="h-8 w-8 text-orange-500" />
            GDD Tracker
          </h1>
          <p className="text-muted-foreground mt-1">
            Growing Degree Days monitoring for crop phenology
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="bg-orange-600 hover:bg-orange-700">
                <Plus className="h-4 w-4 mr-2" />Log Temperature
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Log Daily GDD</DialogTitle>
                <DialogDescription>Enter daily min/max temperatures to calculate GDD</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Field ID</Label>
                    <Input
                      type="number"
                      value={newLog.field_id}
                      onChange={(e) => setNewLog((p) => ({ ...p, field_id: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Date</Label>
                    <Input
                      type="date"
                      value={newLog.date}
                      onChange={(e) => setNewLog((p) => ({ ...p, date: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Max Temp (°C)</Label>
                    <Input
                      type="number"
                      value={newLog.tmax}
                      onChange={(e) => setNewLog((p) => ({ ...p, tmax: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Min Temp (°C)</Label>
                    <Input
                      type="number"
                      value={newLog.tmin}
                      onChange={(e) => setNewLog((p) => ({ ...p, tmin: Number(e.target.value) }))}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newLog)}
                  className="bg-orange-600 hover:bg-orange-700"
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? 'Calculating...' : 'Save Log'}
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
            Failed to load GDD logs.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      )}

      {/* Data Table */}
      {!isLoading && !error && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-center">Max Temp</TableHead>
                  <TableHead className="text-center">Min Temp</TableHead>
                  <TableHead className="text-center">Daily GDD</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(logs) && logs.length > 0 ? (
                  logs.map((log: GDDLog) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-medium">{log.field_id}</TableCell>
                      <TableCell>{formatDate(log.date)}</TableCell>
                      <TableCell className="text-center">{log.tmax}°C</TableCell>
                      <TableCell className="text-center">{log.tmin}°C</TableCell>
                      <TableCell className="text-center font-bold text-orange-600">
                        {log.daily_gdd.toFixed(1)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete log"
                          onClick={() => deleteMutation.mutate(log.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12">
                      <Sun className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No GDD logs recorded yet</p>
                      <Button className="mt-4" onClick={() => setShowCreate(true)}>
                        <Plus className="h-4 w-4 mr-2" />Log First GDD
                      </Button>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

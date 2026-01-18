/**
 * Irrigation Schedules Page
 * CRUD interface for managing irrigation schedules
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
import { AlertCircle, Plus, Calendar, RefreshCw, Trash2, Pencil } from 'lucide-react'

interface IrrigationSchedule {
  id: number
  field_id: number | null
  crop_name: string
  schedule_date: string
  irrigation_method: string | null
  water_requirement_mm: number | null
  duration_minutes: number | null
  start_time: string | null
  actual_applied_mm: number | null
  soil_moisture_before: number | null
  soil_moisture_after: number | null
  et_reference: number | null
  crop_coefficient: number | null
  status: 'planned' | 'in_progress' | 'completed' | 'canceled'
  notes: string | null
  created_at: string
}

const statusOptions = ['planned', 'in_progress', 'completed', 'canceled'] as const
const methodOptions = ['drip', 'sprinkler', 'flood', 'furrow', 'center_pivot']

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

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function IrrigationSchedules() {
  const [showCreate, setShowCreate] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<IrrigationSchedule | null>(null)
  const [newSchedule, setNewSchedule] = useState({
    crop_name: '',
    schedule_date: new Date().toISOString().split('T')[0],
    irrigation_method: 'drip',
    water_requirement_mm: 25,
    duration_minutes: 60,
    status: 'planned' as const,
    notes: '',
  })
  const queryClient = useQueryClient()

  const { data: schedules, isLoading, error, refetch } = useQuery<IrrigationSchedule[]>({
    queryKey: ['irrigation-schedules'],
    queryFn: () => apiClient.get('/api/v2/future/irrigation-schedules/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newSchedule) =>
      apiClient.post('/api/v2/future/irrigation-schedules/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['irrigation-schedules'] })
      toast.success('Irrigation schedule created successfully')
      setShowCreate(false)
      resetForm()
    },
    onError: (err) =>
      toast.error(err instanceof Error ? err.message : 'Failed to create schedule'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<typeof newSchedule> }) =>
      apiClient.put(`/api/v2/future/irrigation-schedules/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['irrigation-schedules'] })
      toast.success('Schedule updated successfully')
      setEditingSchedule(null)
    },
    onError: (err) =>
      toast.error(err instanceof Error ? err.message : 'Failed to update schedule'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/irrigation-schedules/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['irrigation-schedules'] })
      toast.success('Schedule deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  const resetForm = () => {
    setNewSchedule({
      crop_name: '',
      schedule_date: new Date().toISOString().split('T')[0],
      irrigation_method: 'drip',
      water_requirement_mm: 25,
      duration_minutes: 60,
      status: 'planned',
      notes: '',
    })
  }

  const handleEdit = (schedule: IrrigationSchedule) => {
    setEditingSchedule(schedule)
    setNewSchedule({
      crop_name: schedule.crop_name,
      schedule_date: schedule.schedule_date,
      irrigation_method: schedule.irrigation_method || 'drip',
      water_requirement_mm: schedule.water_requirement_mm || 25,
      duration_minutes: schedule.duration_minutes || 60,
      status: schedule.status,
      notes: schedule.notes || '',
    })
  }

  const handleSave = () => {
    if (editingSchedule) {
      updateMutation.mutate({ id: editingSchedule.id, data: newSchedule })
    } else {
      createMutation.mutate(newSchedule)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Calendar className="h-8 w-8 text-blue-500" />
            Irrigation Schedules
          </h1>
          <p className="text-muted-foreground mt-1">
            Plan and track irrigation activities for your fields
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate || !!editingSchedule} onOpenChange={(open) => {
            if (!open) {
              setShowCreate(false)
              setEditingSchedule(null)
              resetForm()
            }
          }}>
            <DialogTrigger asChild>
              <Button onClick={() => setShowCreate(true)}>
                <Plus className="h-4 w-4 mr-2" />
                New Schedule
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>
                  {editingSchedule ? 'Edit Schedule' : 'Create Irrigation Schedule'}
                </DialogTitle>
                <DialogDescription>
                  {editingSchedule
                    ? 'Update the irrigation schedule details'
                    : 'Plan a new irrigation event'}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Crop Name *</Label>
                  <Input
                    value={newSchedule.crop_name}
                    onChange={(e) => setNewSchedule((p) => ({ ...p, crop_name: e.target.value }))}
                    placeholder="e.g., Wheat, Rice, Cotton"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Schedule Date</Label>
                    <Input
                      type="date"
                      value={newSchedule.schedule_date}
                      onChange={(e) =>
                        setNewSchedule((p) => ({ ...p, schedule_date: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Method</Label>
                    <Select
                      value={newSchedule.irrigation_method}
                      onValueChange={(v) =>
                        setNewSchedule((p) => ({ ...p, irrigation_method: v }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {methodOptions.map((m) => (
                          <SelectItem key={m} value={m}>
                            {m.charAt(0).toUpperCase() + m.slice(1).replace('_', ' ')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Water (mm)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newSchedule.water_requirement_mm}
                      onChange={(e) =>
                        setNewSchedule((p) => ({
                          ...p,
                          water_requirement_mm: Number(e.target.value),
                        }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Duration (min)</Label>
                    <Input
                      type="number"
                      value={newSchedule.duration_minutes}
                      onChange={(e) =>
                        setNewSchedule((p) => ({
                          ...p,
                          duration_minutes: Number(e.target.value),
                        }))
                      }
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={newSchedule.status}
                    onValueChange={(v) =>
                      setNewSchedule((p) => ({
                        ...p,
                        status: v as typeof newSchedule.status,
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {statusOptions.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s.charAt(0).toUpperCase() + s.slice(1).replace('_', ' ')}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Input
                    value={newSchedule.notes}
                    onChange={(e) => setNewSchedule((p) => ({ ...p, notes: e.target.value }))}
                    placeholder="Optional notes"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowCreate(false)
                    setEditingSchedule(null)
                    resetForm()
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={
                    !newSchedule.crop_name ||
                    createMutation.isPending ||
                    updateMutation.isPending
                  }
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Saving...'
                    : editingSchedule
                    ? 'Update'
                    : 'Create'}
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
            Failed to load irrigation schedules.
            <Button variant="link" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
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
                  <TableHead>Crop</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead className="text-center">Water (mm)</TableHead>
                  <TableHead className="text-center">Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(schedules) && schedules.length > 0 ? (
                  schedules.map((schedule) => (
                    <TableRow key={schedule.id}>
                      <TableCell className="font-medium">{schedule.crop_name}</TableCell>
                      <TableCell>{formatDate(schedule.schedule_date)}</TableCell>
                      <TableCell>
                        {schedule.irrigation_method
                          ? schedule.irrigation_method.charAt(0).toUpperCase() +
                            schedule.irrigation_method.slice(1).replace('_', ' ')
                          : '—'}
                      </TableCell>
                      <TableCell className="text-center">
                        {schedule.water_requirement_mm?.toFixed(1) ?? '—'}
                      </TableCell>
                      <TableCell className="text-center">
                        {schedule.duration_minutes ? `${schedule.duration_minutes} min` : '—'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(schedule.status)}>
                          {schedule.status.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Edit schedule"
                            onClick={() => handleEdit(schedule)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Delete schedule"
                            onClick={() => deleteMutation.mutate(schedule.id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12">
                      <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No irrigation schedules yet</p>
                      <Button className="mt-4" onClick={() => setShowCreate(true)}>
                        <Plus className="h-4 w-4 mr-2" />
                        Create First Schedule
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

/**
 * Crossing Planner Page
 * Plan and schedule crosses between germplasm
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface PlannedCross {
  crossId: string
  femaleParentName: string
  maleParentName: string
  objective: string
  priority: string
  targetDate: string
  status: string
  expectedProgeny: number
  actualProgeny: number
}

interface Germplasm {
  id: string
  name: string
}

export function CrossingPlanner() {
  const [showForm, setShowForm] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [newCross, setNewCross] = useState({
    femaleParentId: '',
    maleParentId: '',
    objective: '',
    priority: 'medium',
    targetDate: '',
    expectedProgeny: 50,
  })
  const queryClient = useQueryClient()

  const { data: crossesData, isLoading } = useQuery({
    queryKey: ['crossing-planner', statusFilter],
    queryFn: () => apiClient.getPlannedCrosses({
      status: statusFilter !== 'all' ? statusFilter : undefined,
      pageSize: 100,
    }),
  })

  const { data: statsData } = useQuery({
    queryKey: ['crossing-planner-stats'],
    queryFn: () => apiClient.getCrossingPlannerStats(),
  })

  const { data: germplasmData } = useQuery({
    queryKey: ['crossing-planner-germplasm'],
    queryFn: () => apiClient.getCrossingPlannerGermplasm(),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newCross) => apiClient.createPlannedCross(data),
    onSuccess: () => {
      toast.success('Cross planned successfully')
      setShowForm(false)
      setNewCross({ femaleParentId: '', maleParentId: '', objective: '', priority: 'medium', targetDate: '', expectedProgeny: 50 })
      queryClient.invalidateQueries({ queryKey: ['crossing-planner'] })
      queryClient.invalidateQueries({ queryKey: ['crossing-planner-stats'] })
    },
    onError: () => toast.error('Failed to create cross'),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ crossId, status }: { crossId: string; status: string }) => apiClient.updatePlannedCrossStatus(crossId, status),
    onSuccess: () => {
      toast.success('Status updated')
      queryClient.invalidateQueries({ queryKey: ['crossing-planner'] })
      queryClient.invalidateQueries({ queryKey: ['crossing-planner-stats'] })
    },
    onError: () => toast.error('Failed to update status'),
  })

  const crosses: PlannedCross[] = crossesData?.result?.data || []
  const stats = statsData?.result || { total: 0, planned: 0, scheduled: 0, completed: 0, totalActualProgeny: 0 }
  const germplasm: Germplasm[] = germplasmData?.result?.data || []

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
      case 'medium': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'low': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planned': return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
      case 'scheduled': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
      case 'in_progress': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
      case 'completed': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      case 'failed': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Crossing Planner</h1>
          <p className="text-muted-foreground mt-1">Plan and schedule crosses</p>
        </div>
        <Dialog open={showForm} onOpenChange={setShowForm}>
          <DialogTrigger asChild><Button>➕ Plan Cross</Button></DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Plan New Cross</DialogTitle><DialogDescription>Select parents and define objectives</DialogDescription></DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Female Parent ♀</Label>
                  <Select value={newCross.femaleParentId} onValueChange={(v) => setNewCross({ ...newCross, femaleParentId: v })}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>{germplasm.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Male Parent ♂</Label>
                  <Select value={newCross.maleParentId} onValueChange={(v) => setNewCross({ ...newCross, maleParentId: v })}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>{germplasm.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <Select value={newCross.priority} onValueChange={(v) => setNewCross({ ...newCross, priority: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>Target Date</Label><Input type="date" value={newCross.targetDate} onChange={(e) => setNewCross({ ...newCross, targetDate: e.target.value })} /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Expected Progeny</Label><Input type="number" value={newCross.expectedProgeny} onChange={(e) => setNewCross({ ...newCross, expectedProgeny: parseInt(e.target.value) || 0 })} /></div>
              </div>
              <div className="space-y-2"><Label>Objective</Label><Input value={newCross.objective} onChange={(e) => setNewCross({ ...newCross, objective: e.target.value })} placeholder="Breeding objective" /></div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button onClick={() => createMutation.mutate(newCross)} disabled={!newCross.femaleParentId || !newCross.maleParentId}>Save</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-gray-600">{stats.planned}</p><p className="text-xs text-muted-foreground">Planned</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-blue-600">{stats.scheduled}</p><p className="text-xs text-muted-foreground">Scheduled</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-600">{stats.completed}</p><p className="text-xs text-muted-foreground">Completed</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-purple-600">{stats.totalActualProgeny}</p><p className="text-xs text-muted-foreground">Progeny</p></CardContent></Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]"><SelectValue placeholder="Filter by status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="planned">Planned</SelectItem>
              <SelectItem value="scheduled">Scheduled</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Planned Crosses</CardTitle><CardDescription>{crosses.length} crosses</CardDescription></CardHeader>
        <CardContent>
          {isLoading ? <p className="text-muted-foreground">Loading...</p> : crosses.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No crosses found</p>
          ) : (
            <div className="space-y-3">
              {crosses.map((cross) => (
                <div key={cross.crossId} className="flex items-center gap-4 p-4 rounded-lg border bg-white dark:bg-slate-800 hover:shadow-sm transition-shadow">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium">{cross.femaleParentName}</span>
                      <span className="text-muted-foreground">×</span>
                      <span className="font-medium">{cross.maleParentName}</span>
                      <Badge className={getPriorityColor(cross.priority)}>{cross.priority}</Badge>
                      <Badge className={getStatusColor(cross.status)}>{cross.status}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{cross.objective || 'No objective specified'}</p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="font-medium">{cross.targetDate || 'No date'}</p>
                    <p className="text-xs text-muted-foreground">{cross.expectedProgeny} expected</p>
                  </div>
                  <Select value={cross.status} onValueChange={(v) => updateStatusMutation.mutate({ crossId: cross.crossId, status: v })}>
                    <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="planned">Planned</SelectItem>
                      <SelectItem value="scheduled">Scheduled</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

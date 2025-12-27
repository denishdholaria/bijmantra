/**
 * Planned Crosses Page - Connected to Backend API
 * Plan and schedule breeding crosses
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface PlannedCross {
  crossId: string
  crossName: string
  femaleParentId: string
  femaleParentName: string
  maleParentId: string
  maleParentName: string
  objective: string
  priority: 'high' | 'medium' | 'low'
  targetDate: string
  status: 'planned' | 'scheduled' | 'in_progress' | 'completed' | 'failed'
  expectedProgeny: number
  actualProgeny: number
  crossType: string
  season: string
  location: string
  breeder: string
  notes: string
  created: string
}

interface CrossStats {
  total: number
  planned: number
  scheduled: number
  inProgress: number
  completed: number
  failed: number
  totalExpectedProgeny: number
  totalActualProgeny: number
  byPriority: { high: number; medium: number; low: number }
}

interface Germplasm {
  id: string
  name: string
  type: string
  traits: string[]
}

export function PlannedCrosses() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')
  const [selectedCrosses, setSelectedCrosses] = useState<string[]>([])
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newCross, setNewCross] = useState({
    femaleParentId: '',
    maleParentId: '',
    objective: '',
    priority: 'medium',
    targetDate: '',
    expectedProgeny: 50,
    crossType: 'single',
    season: '',
    location: '',
    breeder: '',
    notes: '',
  })

  const queryClient = useQueryClient()

  // Fetch crosses from backend
  const { data: crossesData, isLoading } = useQuery({
    queryKey: ['plannedCrosses', statusFilter, priorityFilter],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (statusFilter !== 'all') params.status = statusFilter
      if (priorityFilter !== 'all') params.priority = priorityFilter
      return apiClient.getCrossingPlannerCrosses(params)
    },
  })

  // Fetch statistics
  const { data: statsData } = useQuery({
    queryKey: ['crossingStats'],
    queryFn: () => apiClient.getCrossingPlannerStats(),
  })

  // Fetch germplasm for selection
  const { data: germplasmData } = useQuery({
    queryKey: ['crossingGermplasm', search],
    queryFn: () => apiClient.getCrossingPlannerGermplasm(search),
  })

  // Create cross mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newCross) => apiClient.createCrossingPlannerCross(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plannedCrosses'] })
      queryClient.invalidateQueries({ queryKey: ['crossingStats'] })
      toast.success('Cross planned successfully')
      setIsCreateOpen(false)
      setNewCross({
        femaleParentId: '',
        maleParentId: '',
        objective: '',
        priority: 'medium',
        targetDate: '',
        expectedProgeny: 50,
        crossType: 'single',
        season: '',
        location: '',
        breeder: '',
        notes: '',
      })
    },
    onError: () => toast.error('Failed to create cross'),
  })

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ crossId, status }: { crossId: string; status: string }) =>
      apiClient.updateCrossingPlannerStatus(crossId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plannedCrosses'] })
      queryClient.invalidateQueries({ queryKey: ['crossingStats'] })
      toast.success('Status updated')
    },
    onError: () => toast.error('Failed to update status'),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (crossId: string) => apiClient.deleteCrossingPlannerCross(crossId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plannedCrosses'] })
      queryClient.invalidateQueries({ queryKey: ['crossingStats'] })
      toast.success('Cross deleted')
    },
    onError: () => toast.error('Failed to delete cross'),
  })

  const crosses: PlannedCross[] = crossesData?.result?.data || []
  const stats: CrossStats | null = statsData?.result || null
  const germplasm: Germplasm[] = germplasmData?.result?.data || []

  // Filter by search locally
  const filteredCrosses = search
    ? crosses.filter(
        (c) =>
          c.crossName.toLowerCase().includes(search.toLowerCase()) ||
          c.femaleParentName.toLowerCase().includes(search.toLowerCase()) ||
          c.maleParentName.toLowerCase().includes(search.toLowerCase())
      )
    : crosses

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      planned: 'bg-gray-100 text-gray-800',
      scheduled: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }
    return <Badge className={styles[status] || 'bg-gray-100'}>{status.replace('_', ' ')}</Badge>
  }

  const getPriorityBadge = (priority: string) => {
    const styles: Record<string, string> = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    }
    return <Badge className={styles[priority] || 'bg-gray-100'}>{priority}</Badge>
  }

  const handleBulkSchedule = () => {
    if (selectedCrosses.length === 0) {
      toast.error('Select crosses to schedule')
      return
    }
    selectedCrosses.forEach((crossId) => {
      updateStatusMutation.mutate({ crossId, status: 'scheduled' })
    })
    setSelectedCrosses([])
  }

  const toggleSelect = (id: string) => {
    setSelectedCrosses((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const toggleSelectAll = () => {
    if (selectedCrosses.length === filteredCrosses.length) {
      setSelectedCrosses([])
    } else {
      setSelectedCrosses(filteredCrosses.map((c) => c.crossId))
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Planned Crosses</h1>
          <p className="text-muted-foreground mt-1">Schedule and manage breeding crosses</p>
        </div>
        <div className="flex gap-2">
          {selectedCrosses.length > 0 && (
            <Button variant="outline" onClick={handleBulkSchedule}>
              📅 Schedule ({selectedCrosses.length})
            </Button>
          )}
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>➕ Plan Cross</Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Plan New Cross</DialogTitle>
                <DialogDescription>Define a new planned cross between germplasm</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Female Parent (♀)</Label>
                    <Select
                      value={newCross.femaleParentId}
                      onValueChange={(v) => setNewCross({ ...newCross, femaleParentId: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select female parent" />
                      </SelectTrigger>
                      <SelectContent>
                        {germplasm.map((g) => (
                          <SelectItem key={g.id} value={g.id}>
                            {g.name} ({g.type})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Male Parent (♂)</Label>
                    <Select
                      value={newCross.maleParentId}
                      onValueChange={(v) => setNewCross({ ...newCross, maleParentId: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select male parent" />
                      </SelectTrigger>
                      <SelectContent>
                        {germplasm.map((g) => (
                          <SelectItem key={g.id} value={g.id}>
                            {g.name} ({g.type})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Objective</Label>
                  <Input
                    placeholder="e.g., Combine yield + disease resistance"
                    value={newCross.objective}
                    onChange={(e) => setNewCross({ ...newCross, objective: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <Select
                      value={newCross.priority}
                      onValueChange={(v) => setNewCross({ ...newCross, priority: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Cross Type</Label>
                    <Select
                      value={newCross.crossType}
                      onValueChange={(v) => setNewCross({ ...newCross, crossType: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="single">Single Cross</SelectItem>
                        <SelectItem value="backcross">Backcross</SelectItem>
                        <SelectItem value="wide">Wide Cross</SelectItem>
                        <SelectItem value="topcross">Top Cross</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Expected Progeny</Label>
                    <Input
                      type="number"
                      value={newCross.expectedProgeny}
                      onChange={(e) =>
                        setNewCross({ ...newCross, expectedProgeny: parseInt(e.target.value) || 50 })
                      }
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Target Date</Label>
                    <Input
                      type="date"
                      value={newCross.targetDate}
                      onChange={(e) => setNewCross({ ...newCross, targetDate: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Season</Label>
                    <Input
                      placeholder="e.g., 2024-Kharif"
                      value={newCross.season}
                      onChange={(e) => setNewCross({ ...newCross, season: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Location</Label>
                    <Input
                      placeholder="e.g., Field Station A"
                      value={newCross.location}
                      onChange={(e) => setNewCross({ ...newCross, location: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Breeder</Label>
                    <Input
                      placeholder="e.g., Dr. Smith"
                      value={newCross.breeder}
                      onChange={(e) => setNewCross({ ...newCross, breeder: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea
                    placeholder="Additional notes..."
                    value={newCross.notes}
                    onChange={(e) => setNewCross({ ...newCross, notes: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createMutation.mutate(newCross)}
                  disabled={!newCross.femaleParentId || !newCross.maleParentId || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Plan Cross'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by cross name or parent..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="planned">Planned</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priority</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
            <p className="text-sm text-muted-foreground">Total Crosses</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-gray-600">{stats?.planned || 0}</div>
            <p className="text-sm text-muted-foreground">Planned</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-blue-600">{stats?.scheduled || 0}</div>
            <p className="text-sm text-muted-foreground">Scheduled</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">{stats?.completed || 0}</div>
            <p className="text-sm text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats?.totalActualProgeny || 0}</div>
            <p className="text-sm text-muted-foreground">Total Progeny</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Planned Crosses</CardTitle>
            <CardDescription>{filteredCrosses.length} crosses found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedCrosses.length === filteredCrosses.length && filteredCrosses.length > 0}
                      onCheckedChange={toggleSelectAll}
                    />
                  </TableHead>
                  <TableHead>Cross</TableHead>
                  <TableHead>Female (♀)</TableHead>
                  <TableHead>Male (♂)</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Target Date</TableHead>
                  <TableHead>Progeny</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCrosses.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                      No crosses found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredCrosses.map((cross) => (
                    <TableRow key={cross.crossId}>
                      <TableCell>
                        <Checkbox
                          checked={selectedCrosses.includes(cross.crossId)}
                          onCheckedChange={() => toggleSelect(cross.crossId)}
                        />
                      </TableCell>
                      <TableCell className="font-medium">
                        <div>
                          <p>{cross.crossName}</p>
                          <p className="text-xs text-muted-foreground">{cross.objective}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Link
                          to={`/germplasm/${cross.femaleParentId}`}
                          className="text-pink-600 hover:underline"
                        >
                          {cross.femaleParentName}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Link
                          to={`/germplasm/${cross.maleParentId}`}
                          className="text-blue-600 hover:underline"
                        >
                          {cross.maleParentName}
                        </Link>
                      </TableCell>
                      <TableCell>{getPriorityBadge(cross.priority)}</TableCell>
                      <TableCell>{getStatusBadge(cross.status)}</TableCell>
                      <TableCell>{cross.targetDate || '-'}</TableCell>
                      <TableCell>
                        {cross.actualProgeny}/{cross.expectedProgeny}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {cross.status === 'planned' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() =>
                                updateStatusMutation.mutate({ crossId: cross.crossId, status: 'scheduled' })
                              }
                            >
                              Schedule
                            </Button>
                          )}
                          {cross.status === 'scheduled' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() =>
                                updateStatusMutation.mutate({ crossId: cross.crossId, status: 'in_progress' })
                              }
                            >
                              Start
                            </Button>
                          )}
                          {cross.status === 'in_progress' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() =>
                                updateStatusMutation.mutate({ crossId: cross.crossId, status: 'completed' })
                              }
                            >
                              Complete
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-600"
                            onClick={() => deleteMutation.mutate(cross.crossId)}
                          >
                            Delete
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

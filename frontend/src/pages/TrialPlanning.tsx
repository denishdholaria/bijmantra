/**
 * Trial Planning Page
 * Plan and schedule breeding trials with backend API integration
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Plus, Search, Calendar, MapPin, CheckCircle, Clock, XCircle, Play } from 'lucide-react'
import { apiClient, type PlannedTrial, type TrialType, type TrialDesign } from '@/lib/api-client'
import { toast } from 'sonner'

export function TrialPlanning() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newTrial, setNewTrial] = useState({
    name: '', type: 'AYT', season: '', locations: '', entries: 25, reps: 3, design: 'RCBD', startDate: '', endDate: '', crop: 'Rice', objectives: ''
  })

  // Fetch trials
  const { data: trialsData, isLoading } = useQuery({
    queryKey: ['plannedTrials', statusFilter, typeFilter, searchQuery],
    queryFn: () => apiClient.trialPlanningService.getTrials({
      status: statusFilter !== 'all' ? statusFilter : undefined,
      type: typeFilter !== 'all' ? typeFilter : undefined,
      search: searchQuery || undefined,
    }),
  })

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['trialPlanningStats'],
    queryFn: () => apiClient.trialPlanningService.getStatistics(),
  })

  // Fetch trial types
  const { data: trialTypes } = useQuery({
    queryKey: ['trialTypes'],
    queryFn: () => apiClient.trialPlanningService.getTypes(),
  })

  // Fetch designs
  const { data: designs } = useQuery({
    queryKey: ['trialDesigns'],
    queryFn: () => apiClient.trialDesignService.getDesigns(),
  })

  // Create trial mutation
  const createTrialMutation = useMutation({
    mutationFn: (data: typeof newTrial) => apiClient.trialPlanningService.createTrial({
      name: data.name,
      type: data.type,
      season: data.season,
      locations: data.locations.split(',').map(l => l.trim()).filter(Boolean),
      entries: data.entries,
      reps: data.reps,
      design: data.design,
      startDate: data.startDate,
      endDate: data.endDate || undefined,
      crop: data.crop,
      objectives: data.objectives || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plannedTrials'] })
      queryClient.invalidateQueries({ queryKey: ['trialPlanningStats'] })
      setShowCreateDialog(false)
      setNewTrial({ name: '', type: 'AYT', season: '', locations: '', entries: 25, reps: 3, design: 'RCBD', startDate: '', endDate: '', crop: 'Rice', objectives: '' })
      toast.success('Trial created successfully')
    },
    onError: () => toast.error('Failed to create trial'),
  })

  // Approve trial mutation
  const approveTrialMutation = useMutation({
    mutationFn: (trialId: string) => apiClient.trialPlanningService.approveTrial(trialId, 'Current User'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plannedTrials'] })
      toast.success('Trial approved')
    },
    onError: () => toast.error('Failed to approve trial'),
  })

  // Start trial mutation
  const startTrialMutation = useMutation({
    mutationFn: (trialId: string) => apiClient.trialPlanningService.startTrial(trialId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plannedTrials'] })
      toast.success('Trial started')
    },
    onError: () => toast.error('Failed to start trial'),
  })

  // Complete trial mutation
  const completeTrialMutation = useMutation({
    mutationFn: (trialId: string) => apiClient.trialPlanningService.completeTrial(trialId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plannedTrials'] })
      toast.success('Trial completed')
    },
    onError: () => toast.error('Failed to complete trial'),
  })

  const trials: PlannedTrial[] = trialsData || []
  const types: TrialType[] = trialTypes || []
  const designList: TrialDesign[] = designs || []

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      planning: 'bg-yellow-100 text-yellow-700',
      approved: 'bg-blue-100 text-blue-700',
      active: 'bg-green-100 text-green-700',
      completed: 'bg-purple-100 text-purple-700',
      cancelled: 'bg-red-100 text-red-700',
    }
    return colors[status] || 'bg-gray-100 text-gray-700'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'planning': return <Clock className="h-4 w-4" />
      case 'approved': return <CheckCircle className="h-4 w-4" />
      case 'active': return <Play className="h-4 w-4" />
      case 'completed': return <CheckCircle className="h-4 w-4" />
      case 'cancelled': return <XCircle className="h-4 w-4" />
      default: return null
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Trial Planning</h1>
          <p className="text-muted-foreground mt-1">Plan and schedule breeding trials</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button><Plus className="mr-2 h-4 w-4" />Plan New Trial</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader><DialogTitle>Plan New Trial</DialogTitle></DialogHeader>
            <div className="space-y-4 pt-4 max-h-[70vh] overflow-auto">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Label>Trial Name</Label>
                  <Input value={newTrial.name} onChange={e => setNewTrial({ ...newTrial, name: e.target.value })} placeholder="Advanced Yield Trial 2025" />
                </div>
                <div>
                  <Label>Trial Type</Label>
                  <Select value={newTrial.type} onValueChange={v => setNewTrial({ ...newTrial, type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {types.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Season</Label>
                  <Input value={newTrial.season} onChange={e => setNewTrial({ ...newTrial, season: e.target.value })} placeholder="Rabi 2025" />
                </div>
                <div>
                  <Label>Crop</Label>
                  <Input value={newTrial.crop} onChange={e => setNewTrial({ ...newTrial, crop: e.target.value })} placeholder="Rice" />
                </div>
                <div>
                  <Label>Design</Label>
                  <Select value={newTrial.design} onValueChange={v => setNewTrial({ ...newTrial, design: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {designList.map((d) => <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="col-span-2">
                  <Label>Locations (comma-separated)</Label>
                  <Input value={newTrial.locations} onChange={e => setNewTrial({ ...newTrial, locations: e.target.value })} placeholder="Location A, Location B, Location C" />
                </div>
                <div>
                  <Label>Number of Entries</Label>
                  <Input type="number" value={newTrial.entries} onChange={e => setNewTrial({ ...newTrial, entries: parseInt(e.target.value) || 0 })} />
                </div>
                <div>
                  <Label>Replications</Label>
                  <Input type="number" value={newTrial.reps} onChange={e => setNewTrial({ ...newTrial, reps: parseInt(e.target.value) || 0 })} />
                </div>
                <div>
                  <Label>Start Date</Label>
                  <Input type="date" value={newTrial.startDate} onChange={e => setNewTrial({ ...newTrial, startDate: e.target.value })} />
                </div>
                <div>
                  <Label>End Date (optional)</Label>
                  <Input type="date" value={newTrial.endDate} onChange={e => setNewTrial({ ...newTrial, endDate: e.target.value })} />
                </div>
                <div className="col-span-2">
                  <Label>Objectives</Label>
                  <Textarea value={newTrial.objectives} onChange={e => setNewTrial({ ...newTrial, objectives: e.target.value })} placeholder="Evaluate advanced breeding lines for yield potential..." />
                </div>
              </div>
              <Button className="w-full" onClick={() => createTrialMutation.mutate(newTrial)} disabled={!newTrial.name || !newTrial.season || !newTrial.startDate || createTrialMutation.isPending}>
                {createTrialMutation.isPending ? 'Creating...' : 'Create Trial'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{stats?.totalTrials || trials.length}</p><p className="text-xs text-muted-foreground">Total Trials</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-yellow-600">{stats?.planning || 0}</p><p className="text-xs text-muted-foreground">Planning</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-600">{stats?.active || 0}</p><p className="text-xs text-muted-foreground">Active</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-purple-600">{stats?.completed || 0}</p><p className="text-xs text-muted-foreground">Completed</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-blue-600">{stats?.totalPlots?.toLocaleString() || 0}</p><p className="text-xs text-muted-foreground">Total Plots</p></CardContent></Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input className="pl-10" placeholder="Search trials..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="planning">Planning</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {types.map((t) => <SelectItem key={t.value} value={t.value}>{t.value}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="list">
        <TabsList>
          <TabsTrigger value="list">List View</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="mt-4">
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : (
            <div className="space-y-4">
              {trials.map((trial: PlannedTrial) => (
                <Card key={trial.id}>
                  <CardContent className="pt-4">
                    <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold">{trial.name}</span>
                          <Badge variant="outline">{trial.type}</Badge>
                          <Badge className={getStatusColor(trial.status)}>
                            <span className="flex items-center gap-1">{getStatusIcon(trial.status)}{trial.status}</span>
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          <Calendar className="inline h-3 w-3 mr-1" />{trial.season} • 
                          <MapPin className="inline h-3 w-3 mx-1" />{Array.isArray(trial.locations) ? trial.locations.length : 1} locations
                        </p>
                        
                        <div className="mt-3">
                          <div className="flex justify-between text-xs mb-1">
                            <span>Progress</span>
                            <span>{trial.progress}%</span>
                          </div>
                          <Progress value={trial.progress} className="h-2" />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div className="p-2 bg-muted rounded">
                          <p className="text-lg font-bold">{trial.entries}</p>
                          <p className="text-xs text-muted-foreground">Entries</p>
                        </div>
                        <div className="p-2 bg-muted rounded">
                          <p className="text-lg font-bold">{trial.reps}</p>
                          <p className="text-xs text-muted-foreground">Reps</p>
                        </div>
                        <div className="p-2 bg-muted rounded">
                          <p className="text-lg font-bold">{trial.totalPlots}</p>
                          <p className="text-xs text-muted-foreground">Plots</p>
                        </div>
                      </div>

                      <div className="flex flex-col gap-2">
                        <div className="text-sm text-right">
                          <p className="font-medium">{trial.startDate}</p>
                          <p className="text-xs text-muted-foreground">Start Date</p>
                        </div>
                        {trial.status === 'planning' && (
                          <Button size="sm" onClick={() => approveTrialMutation.mutate(trial.id)} disabled={approveTrialMutation.isPending}>
                            Approve
                          </Button>
                        )}
                        {trial.status === 'approved' && (
                          <Button size="sm" onClick={() => startTrialMutation.mutate(trial.id)} disabled={startTrialMutation.isPending}>
                            Start
                          </Button>
                        )}
                        {trial.status === 'active' && (
                          <Button size="sm" variant="outline" onClick={() => completeTrialMutation.mutate(trial.id)} disabled={completeTrialMutation.isPending}>
                            Complete
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {trials.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                  <Calendar className="h-12 w-12 mx-auto mb-4" />
                  <p>No trials found</p>
                </div>
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="timeline" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trial Timeline</CardTitle>
              <CardDescription>Visual timeline of planned trials</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trials.map((trial: PlannedTrial) => (
                  <div key={trial.id} className="flex items-center gap-4">
                    <div className="w-24 text-sm text-muted-foreground">{trial.startDate}</div>
                    <div className={`w-4 h-4 rounded-full ${
                      trial.status === 'completed' ? 'bg-purple-500' : 
                      trial.status === 'active' ? 'bg-green-500' : 
                      trial.status === 'approved' ? 'bg-blue-500' : 
                      'bg-yellow-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="font-medium">{trial.name}</p>
                      <p className="text-sm text-muted-foreground">{trial.type} • {Array.isArray(trial.locations) ? trial.locations.length : 1} locations</p>
                    </div>
                    <Badge className={getStatusColor(trial.status)}>{trial.status}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

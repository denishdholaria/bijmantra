/**
 * Harvest Planner Page
 * Plan and track harvest activities - Connected to real API
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Checkbox } from '@/components/ui/checkbox'
import { Loader2 } from 'lucide-react'
import { harvestPlannerAPI, HarvestTask } from '@/lib/api-client'
import { toast } from 'sonner'

export function HarvestPlanner() {
  const [filter, setFilter] = useState<'all' | 'pending' | 'ready' | 'completed'>('all')
  const queryClient = useQueryClient()

  // Fetch tasks from API
  const { data: tasksData, isLoading, error } = useQuery({
    queryKey: ['harvest-tasks', filter],
    queryFn: async () => {
      const params: { status?: string } = {}
      if (filter === 'pending') params.status = 'pending'
      else if (filter === 'ready') params.status = 'ready'
      else if (filter === 'completed') params.status = 'harvested'
      const response = await harvestPlannerAPI.getTasks(params)
      return response.data
    },
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['harvest-stats'],
    queryFn: () => harvestPlannerAPI.getStats(),
  })

  // Update task mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<HarvestTask> }) =>
      harvestPlannerAPI.updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['harvest-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['harvest-stats'] })
      toast.success('Task updated')
    },
    onError: () => toast.error('Failed to update task'),
  })

  const tasks: HarvestTask[] = tasksData || []
  const stats = statsData || { total: 0, pending: 0, ready: 0, harvested: 0, processed: 0, progress: 0 }

  const toggleTask = (task: HarvestTask) => {
    const newCompleted = !task.completed
    updateMutation.mutate({
      id: task.id,
      data: {
        completed: newCompleted,
        status: newCompleted ? 'harvested' : 'ready'
      }
    })
  }

  const progress = stats.total > 0 
    ? ((stats.harvested + stats.processed) / stats.total) * 100 
    : 0

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
      case 'pending': return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
      case 'ready': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
      case 'harvested': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      case 'processed': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
    }
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">
        Failed to load harvest tasks. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Harvest Planner</h1>
          <p className="text-muted-foreground mt-1">Plan and track harvest activities</p>
        </div>
        <Button>➕ Add Task</Button>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Harvest Progress</span>
            <span className="text-sm text-muted-foreground">{progress.toFixed(0)}% Complete</span>
          </div>
          <Progress value={progress} className="h-3" />
          <div className="grid grid-cols-4 gap-4 mt-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-600">{stats.pending}</p>
              <p className="text-xs text-muted-foreground">Pending</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{stats.ready}</p>
              <p className="text-xs text-muted-foreground">Ready</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{stats.harvested}</p>
              <p className="text-xs text-muted-foreground">Harvested</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">{stats.processed}</p>
              <p className="text-xs text-muted-foreground">Processed</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {(['all', 'pending', 'ready', 'completed'] as const).map((f) => (
          <Button
            key={f}
            size="sm"
            variant={filter === f ? 'default' : 'outline'}
            onClick={() => setFilter(f)}
            className="capitalize"
          >
            {f}
          </Button>
        ))}
      </div>

      {/* Task List */}
      <Card>
        <CardHeader>
          <CardTitle>Harvest Tasks</CardTitle>
          <CardDescription>{tasks.length} tasks</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No harvest tasks found
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className={`flex items-center gap-4 p-4 rounded-lg border ${task.completed ? 'bg-gray-50 dark:bg-slate-900 opacity-75' : 'bg-white dark:bg-slate-800'}`}
                >
                  <Checkbox
                    checked={task.completed}
                    onCheckedChange={() => toggleTask(task)}
                    disabled={updateMutation.isPending}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-medium ${task.completed ? 'line-through text-muted-foreground' : ''}`}>
                        {task.germplasm}
                      </span>
                      <Badge variant="outline">{task.plot}</Badge>
                      <Badge className={getPriorityColor(task.priority)}>{task.priority}</Badge>
                      <Badge className={getStatusColor(task.status)}>{task.status}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{task.notes}</p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="font-medium">{task.expectedDate}</p>
                    <p className="text-xs text-muted-foreground">{task.id}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Harvest Planner Page
 * Plan and track harvest activities
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Checkbox } from '@/components/ui/checkbox'
import { toast } from 'sonner'

interface HarvestTask {
  id: string
  plot: string
  germplasm: string
  expectedDate: string
  status: 'pending' | 'ready' | 'harvested' | 'processed'
  priority: 'high' | 'medium' | 'low'
  notes: string
  completed: boolean
}

const sampleTasks: HarvestTask[] = [
  { id: 'H001', plot: 'A-01', germplasm: 'Elite Line 001', expectedDate: '2024-12-05', status: 'ready', priority: 'high', notes: 'Ready for harvest', completed: false },
  { id: 'H002', plot: 'A-02', germplasm: 'Elite Line 002', expectedDate: '2024-12-05', status: 'ready', priority: 'high', notes: 'Mature', completed: false },
  { id: 'H003', plot: 'A-03', germplasm: 'Test Line 003', expectedDate: '2024-12-07', status: 'pending', priority: 'medium', notes: 'Check moisture', completed: false },
  { id: 'H004', plot: 'B-01', germplasm: 'Variety X', expectedDate: '2024-12-03', status: 'harvested', priority: 'high', notes: 'Harvested', completed: true },
  { id: 'H005', plot: 'B-02', germplasm: 'Variety Y', expectedDate: '2024-12-02', status: 'processed', priority: 'medium', notes: 'Threshed and weighed', completed: true },
  { id: 'H006', plot: 'C-01', germplasm: 'New Cross 006', expectedDate: '2024-12-10', status: 'pending', priority: 'low', notes: 'Still maturing', completed: false },
]

export function HarvestPlanner() {
  const [tasks, setTasks] = useState<HarvestTask[]>(sampleTasks)
  const [filter, setFilter] = useState<'all' | 'pending' | 'ready' | 'completed'>('all')

  const toggleTask = (id: string) => {
    setTasks(prev => prev.map(t => {
      if (t.id === id) {
        const newCompleted = !t.completed
        return { ...t, completed: newCompleted, status: newCompleted ? 'harvested' : 'ready' }
      }
      return t
    }))
    toast.success('Task updated')
  }

  const filteredTasks = tasks.filter(t => {
    if (filter === 'all') return true
    if (filter === 'pending') return t.status === 'pending'
    if (filter === 'ready') return t.status === 'ready'
    if (filter === 'completed') return t.completed
    return true
  })

  const stats = {
    total: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    ready: tasks.filter(t => t.status === 'ready').length,
    harvested: tasks.filter(t => t.status === 'harvested').length,
    processed: tasks.filter(t => t.status === 'processed').length,
  }

  const progress = ((stats.harvested + stats.processed) / stats.total) * 100

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-700'
      case 'medium': return 'bg-yellow-100 text-yellow-700'
      case 'low': return 'bg-green-100 text-green-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-700'
      case 'ready': return 'bg-blue-100 text-blue-700'
      case 'harvested': return 'bg-green-100 text-green-700'
      case 'processed': return 'bg-purple-100 text-purple-700'
      default: return 'bg-gray-100 text-gray-700'
    }
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
          <CardDescription>{filteredTasks.length} tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredTasks.map((task) => (
              <div
                key={task.id}
                className={`flex items-center gap-4 p-4 rounded-lg border ${task.completed ? 'bg-gray-50 opacity-75' : 'bg-white'}`}
              >
                <Checkbox
                  checked={task.completed}
                  onCheckedChange={() => toggleTask(task.id)}
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
        </CardContent>
      </Card>
    </div>
  )
}

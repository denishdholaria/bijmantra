import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Target, TrendingUp, CheckCircle, Clock, Plus,
  BarChart3, Leaf, Droplets, Bug, Wheat, AlertCircle
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface BreedingGoal {
  id: string
  name: string
  category: string
  description: string
  targetValue: string
  currentValue: string
  progress: number
  priority: 'high' | 'medium' | 'low'
  status: 'on-track' | 'at-risk' | 'achieved'
  deadline: string
}

interface Milestone {
  id: string
  goalId: string
  name: string
  completed: boolean
  date: string
}

export function BreedingGoals() {
  const [activeTab, setActiveTab] = useState('active')

  // Fetch breeding goals from database (endpoint returns empty until goals table is created)
  const { data: goalsData, isLoading } = useQuery({
    queryKey: ['breeding-goals'],
    queryFn: () => apiClient.get<{ data: BreedingGoal[] }>('/api/v2/breeding-pipeline/goals').catch(() => ({ data: [] })),
  })

  const { data: milestonesData } = useQuery({
    queryKey: ['breeding-milestones'],
    queryFn: () => apiClient.get<{ data: Milestone[] }>('/api/v2/breeding-pipeline/milestones').catch(() => ({ data: [] })),
  })

  const goals: BreedingGoal[] = (goalsData?.data || []).map((g: any) => ({
    id: String(g.id),
    name: g.name || g.goal_name || '',
    category: g.category || 'yield',
    description: g.description || '',
    targetValue: g.target_value || '',
    currentValue: g.current_value || '',
    progress: g.progress || 0,
    priority: g.priority || 'medium',
    status: g.status || 'on-track',
    deadline: g.deadline || '',
  }))

  const milestones: Milestone[] = (milestonesData?.data || []).map((m: any) => ({
    id: String(m.id),
    goalId: String(m.goal_id || ''),
    name: m.name || m.milestone_name || '',
    completed: m.completed || false,
    date: m.date || m.target_date || '',
  }))

  const stats = {
    total: goals.length,
    onTrack: goals.filter(g => g.status === 'on-track').length,
    atRisk: goals.filter(g => g.status === 'at-risk').length,
    achieved: goals.filter(g => g.status === 'achieved').length
  }

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, any> = { yield: Wheat, stress: Droplets, disease: Bug, duration: Clock, quality: Target }
    const Icon = icons[category] || Target
    return <Icon className="h-5 w-5" />
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { 'on-track': 'bg-green-100 text-green-800', 'at-risk': 'bg-yellow-100 text-yellow-800', achieved: 'bg-blue-100 text-blue-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = { high: 'bg-red-100 text-red-800', medium: 'bg-orange-100 text-orange-800', low: 'bg-gray-100 text-gray-800' }
    return colors[priority] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Breeding Goals</h1>
          <p className="text-muted-foreground">Track progress towards breeding objectives</p>
        </div>
        <Button><Plus className="mr-2 h-4 w-4" />Add Goal</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Goals</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Active objectives</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">On Track</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.onTrack}</div>
            <p className="text-xs text-muted-foreground">Progressing well</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">At Risk</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.atRisk}</div>
            <p className="text-xs text-muted-foreground">Need attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Achieved</CardTitle>
            <CheckCircle className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.achieved}</div>
            <p className="text-xs text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="active"><Target className="mr-2 h-4 w-4" />Active Goals</TabsTrigger>
          <TabsTrigger value="milestones"><BarChart3 className="mr-2 h-4 w-4" />Milestones</TabsTrigger>
          <TabsTrigger value="achieved"><CheckCircle className="mr-2 h-4 w-4" />Achieved</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {isLoading ? (
            <div className="space-y-4">
              {Array(3).fill(0).map((_, i) => <Skeleton key={i} className="h-40 w-full" />)}
            </div>
          ) : goals.filter(g => g.status !== 'achieved').length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No breeding goals defined</h3>
                  <p className="text-muted-foreground mb-4">
                    Define breeding objectives (yield targets, disease resistance, quality standards) to track your program's progress.
                  </p>
                  <Button><Plus className="mr-2 h-4 w-4" />Create First Goal</Button>
                </div>
              </CardContent>
            </Card>
          ) : (
          goals.filter(g => g.status !== 'achieved').map((goal) => (
            <Card key={goal.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getCategoryIcon(goal.category)}
                    <div>
                      <CardTitle className="text-lg">{goal.name}</CardTitle>
                      <CardDescription>{goal.description}</CardDescription>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Badge className={getPriorityColor(goal.priority)}>{goal.priority}</Badge>
                    <Badge className={getStatusColor(goal.status)}>{goal.status}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between text-sm">
                    <span>Current: {goal.currentValue}</span>
                    <span>Target: {goal.targetValue}</span>
                  </div>
                  <Progress value={goal.progress} />
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{goal.progress}% complete</span>
                    <span>Deadline: {goal.deadline}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
          )}
        </TabsContent>

        <TabsContent value="milestones" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Recent Milestones</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {milestones.map((m) => (
                  <div key={m.id} className="flex items-center gap-4 p-3 border rounded-lg">
                    <div className={`h-8 w-8 rounded-full flex items-center justify-center ${m.completed ? 'bg-green-100' : 'bg-gray-100'}`}>
                      {m.completed ? <CheckCircle className="h-4 w-4 text-green-600" /> : <Clock className="h-4 w-4 text-gray-400" />}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{m.name}</p>
                      <p className="text-sm text-muted-foreground">{m.date}</p>
                    </div>
                    <Badge variant={m.completed ? 'default' : 'secondary'}>{m.completed ? 'Completed' : 'Pending'}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="achieved" className="space-y-4">
          {goals.filter(g => g.status === 'achieved').map((goal) => (
            <Card key={goal.id} className="border-blue-200 bg-blue-50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center"><CheckCircle className="h-6 w-6 text-blue-600" /></div>
                  <div className="flex-1">
                    <p className="font-medium">{goal.name}</p>
                    <p className="text-sm text-muted-foreground">{goal.description}</p>
                    <p className="text-sm mt-1">Achieved: {goal.targetValue}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}

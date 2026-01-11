import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Target, TrendingUp, CheckCircle, Clock, Plus,
  BarChart3, Leaf, Droplets, Bug, Wheat
} from 'lucide-react'

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

  const goals: BreedingGoal[] = [
    { id: '1', name: 'Increase Yield by 15%', category: 'yield', description: 'Develop varieties with 15% higher yield than current checks', targetValue: '8.5 t/ha', currentValue: '7.8 t/ha', progress: 75, priority: 'high', status: 'on-track', deadline: '2026-12-31' },
    { id: '2', name: 'Drought Tolerance', category: 'stress', description: 'Develop varieties surviving 3 weeks without irrigation', targetValue: '21 days', currentValue: '18 days', progress: 85, priority: 'high', status: 'on-track', deadline: '2025-12-31' },
    { id: '3', name: 'Disease Resistance - Blast', category: 'disease', description: 'Incorporate Pita and Pi9 genes for blast resistance', targetValue: 'Score < 3', currentValue: 'Score 4', progress: 60, priority: 'medium', status: 'at-risk', deadline: '2025-06-30' },
    { id: '4', name: 'Reduce Maturity Duration', category: 'duration', description: 'Develop early maturing varieties (< 110 days)', targetValue: '105 days', currentValue: '112 days', progress: 45, priority: 'medium', status: 'on-track', deadline: '2026-06-30' },
    { id: '5', name: 'Improve Grain Quality', category: 'quality', description: 'Achieve premium grain quality standards', targetValue: 'Grade A', currentValue: 'Grade B+', progress: 90, priority: 'low', status: 'achieved', deadline: '2025-03-31' },
  ]

  const milestones: Milestone[] = [
    { id: '1', goalId: '1', name: 'Identify QTLs for yield', completed: true, date: '2024-06-15' },
    { id: '2', goalId: '1', name: 'Develop mapping population', completed: true, date: '2024-12-01' },
    { id: '3', goalId: '1', name: 'Validate markers in breeding lines', completed: false, date: '2025-06-30' },
    { id: '4', goalId: '2', name: 'Screen germplasm for drought tolerance', completed: true, date: '2024-09-15' },
    { id: '5', goalId: '2', name: 'Introgress drought QTLs', completed: true, date: '2025-03-01' },
  ]

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
          {goals.filter(g => g.status !== 'achieved').map((goal) => (
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
          ))}
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

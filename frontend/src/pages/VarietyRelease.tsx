import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Award, FileCheck, Clock, CheckCircle, AlertCircle,
  FileText, Calendar, Users, ArrowRight, Plus
} from 'lucide-react'

interface VarietyCandidate {
  id: string
  name: string
  crop: string
  stage: 'testing' | 'dut' | 'vcu' | 'registration' | 'released'
  progress: number
  startDate: string
  targetDate: string
  traits: string[]
}

interface ReleaseTask {
  id: string
  task: string
  status: 'completed' | 'in-progress' | 'pending'
  dueDate: string
  assignee: string
}

export function VarietyRelease() {
  const [activeTab, setActiveTab] = useState('pipeline')

  const candidates: VarietyCandidate[] = [
    { id: '1', name: 'BIJ-R-2025-001', crop: 'Rice', stage: 'vcu', progress: 75, startDate: '2023-06-01', targetDate: '2026-03-01', traits: ['High Yield', 'Drought Tolerant', 'Short Duration'] },
    { id: '2', name: 'BIJ-W-2024-003', crop: 'Wheat', stage: 'registration', progress: 90, startDate: '2022-10-01', targetDate: '2025-06-01', traits: ['Disease Resistant', 'High Protein'] },
    { id: '3', name: 'BIJ-R-2024-007', crop: 'Rice', stage: 'dut', progress: 45, startDate: '2024-01-01', targetDate: '2027-01-01', traits: ['Aromatic', 'Premium Quality'] },
    { id: '4', name: 'BIJ-M-2025-002', crop: 'Maize', stage: 'testing', progress: 20, startDate: '2025-03-01', targetDate: '2028-06-01', traits: ['High Yield', 'Heat Tolerant'] },
    { id: '5', name: 'BIJ-R-2023-012', crop: 'Rice', stage: 'released', progress: 100, startDate: '2021-06-01', targetDate: '2024-12-01', traits: ['Submergence Tolerant', 'High Yield'] },
  ]

  const tasks: ReleaseTask[] = [
    { id: '1', task: 'Submit VCU trial data for BIJ-R-2025-001', status: 'in-progress', dueDate: '2025-12-15', assignee: 'Dr. Sarah Chen' },
    { id: '2', task: 'Complete DUS testing documentation', status: 'pending', dueDate: '2025-12-20', assignee: 'Raj Patel' },
    { id: '3', task: 'Prepare registration application', status: 'pending', dueDate: '2026-01-10', assignee: 'Maria Garcia' },
    { id: '4', task: 'Seed multiplication for BIJ-W-2024-003', status: 'completed', dueDate: '2025-11-30', assignee: 'John Smith' },
  ]

  const stages = ['testing', 'dut', 'vcu', 'registration', 'released']
  const stageLabels: Record<string, string> = { testing: 'Initial Testing', dut: 'DUS Testing', vcu: 'VCU Trials', registration: 'Registration', released: 'Released' }

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = { testing: 'bg-blue-100 text-blue-800', dut: 'bg-yellow-100 text-yellow-800', vcu: 'bg-orange-100 text-orange-800', registration: 'bg-purple-100 text-purple-800', released: 'bg-green-100 text-green-800' }
    return colors[stage] || 'bg-gray-100 text-gray-800'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'in-progress': return <Clock className="h-4 w-4 text-yellow-500" />
      default: return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Variety Release</h1>
          <p className="text-muted-foreground">Track variety candidates through the release pipeline</p>
        </div>
        <Button><Plus className="mr-2 h-4 w-4" />Add Candidate</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        {stages.map((stage) => {
          const count = candidates.filter(c => c.stage === stage).length
          return (
            <Card key={stage}>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-2xl font-bold">{count}</p>
                  <p className="text-sm text-muted-foreground">{stageLabels[stage]}</p>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="pipeline"><Award className="mr-2 h-4 w-4" />Pipeline</TabsTrigger>
          <TabsTrigger value="tasks"><FileCheck className="mr-2 h-4 w-4" />Tasks</TabsTrigger>
          <TabsTrigger value="released"><CheckCircle className="mr-2 h-4 w-4" />Released</TabsTrigger>
        </TabsList>

        <TabsContent value="pipeline" className="space-y-4">
          {candidates.filter(c => c.stage !== 'released').map((candidate) => (
            <Card key={candidate.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">{candidate.name}</CardTitle>
                    <CardDescription>{candidate.crop}</CardDescription>
                  </div>
                  <Badge className={getStageColor(candidate.stage)}>{stageLabels[candidate.stage]}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    {stages.map((stage, idx) => (
                      <div key={stage} className="flex items-center">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-medium ${stages.indexOf(candidate.stage) >= idx ? 'bg-primary text-primary-foreground' : 'bg-gray-100 text-gray-400'}`}>{idx + 1}</div>
                        {idx < stages.length - 1 && <ArrowRight className={`h-4 w-4 mx-1 ${stages.indexOf(candidate.stage) > idx ? 'text-primary' : 'text-gray-300'}`} />}
                      </div>
                    ))}
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm"><span>Progress</span><span>{candidate.progress}%</span></div>
                    <Progress value={candidate.progress} />
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>Started: {candidate.startDate}</span>
                    <span>Target: {candidate.targetDate}</span>
                  </div>
                  <div className="flex gap-1 flex-wrap">{candidate.traits.map(t => (<Badge key={t} variant="outline" className="text-xs">{t}</Badge>))}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Release Tasks</CardTitle><CardDescription>Pending and completed tasks</CardDescription></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {tasks.map((task) => (
                  <div key={task.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(task.status)}
                      <div>
                        <p className="font-medium">{task.task}</p>
                        <p className="text-sm text-muted-foreground">{task.assignee} • Due: {task.dueDate}</p>
                      </div>
                    </div>
                    <Badge variant={task.status === 'completed' ? 'default' : 'secondary'}>{task.status}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="released" className="space-y-4">
          {candidates.filter(c => c.stage === 'released').map((candidate) => (
            <Card key={candidate.id} className="border-green-200 bg-green-50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center"><Award className="h-6 w-6 text-green-600" /></div>
                  <div className="flex-1">
                    <p className="font-medium">{candidate.name}</p>
                    <p className="text-sm text-muted-foreground">{candidate.crop} • Released {candidate.targetDate}</p>
                    <div className="flex gap-1 mt-2">{candidate.traits.map(t => (<Badge key={t} variant="outline" className="text-xs">{t}</Badge>))}</div>
                  </div>
                  <Button variant="outline">View Details</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}

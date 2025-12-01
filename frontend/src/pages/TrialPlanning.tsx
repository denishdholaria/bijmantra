/**
 * Trial Planning Page
 * Plan and schedule breeding trials
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface PlannedTrial {
  id: string
  name: string
  type: string
  season: string
  locations: string[]
  entries: number
  reps: number
  status: 'planning' | 'approved' | 'active' | 'completed'
  progress: number
  startDate: string
}

const sampleTrials: PlannedTrial[] = [
  { id: 'T001', name: 'Advanced Yield Trial 2025', type: 'AYT', season: 'Rabi 2025', locations: ['Location A', 'Location B', 'Location C'], entries: 25, reps: 3, status: 'planning', progress: 30, startDate: '2025-01-15' },
  { id: 'T002', name: 'Multi-Location Trial 2025', type: 'MLT', season: 'Rabi 2025', locations: ['Location A', 'Location B', 'Location C', 'Location D', 'Location E'], entries: 15, reps: 3, status: 'approved', progress: 60, startDate: '2025-01-20' },
  { id: 'T003', name: 'Preliminary Yield Trial', type: 'PYT', season: 'Kharif 2024', locations: ['Location A'], entries: 100, reps: 2, status: 'active', progress: 85, startDate: '2024-07-01' },
  { id: 'T004', name: 'Disease Screening Trial', type: 'DST', season: 'Kharif 2024', locations: ['Location B'], entries: 50, reps: 2, status: 'completed', progress: 100, startDate: '2024-06-15' },
]

export function TrialPlanning() {
  const [trials] = useState<PlannedTrial[]>(sampleTrials)

  const stats = {
    total: trials.length,
    planning: trials.filter(t => t.status === 'planning').length,
    active: trials.filter(t => t.status === 'active').length,
    completed: trials.filter(t => t.status === 'completed').length,
    totalPlots: trials.reduce((sum, t) => sum + (t.entries * t.reps * t.locations.length), 0),
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planning': return 'bg-yellow-100 text-yellow-700'
      case 'approved': return 'bg-blue-100 text-blue-700'
      case 'active': return 'bg-green-100 text-green-700'
      case 'completed': return 'bg-purple-100 text-purple-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Trial Planning</h1>
          <p className="text-muted-foreground mt-1">Plan and schedule breeding trials</p>
        </div>
        <Button>➕ Plan New Trial</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total Trials</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-yellow-600">{stats.planning}</p><p className="text-xs text-muted-foreground">Planning</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-600">{stats.active}</p><p className="text-xs text-muted-foreground">Active</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-purple-600">{stats.completed}</p><p className="text-xs text-muted-foreground">Completed</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-blue-600">{stats.totalPlots.toLocaleString()}</p><p className="text-xs text-muted-foreground">Total Plots</p></CardContent></Card>
      </div>

      <Tabs defaultValue="list">
        <TabsList>
          <TabsTrigger value="list">List View</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="mt-4">
          <div className="space-y-4">
            {trials.map((trial) => (
              <Card key={trial.id}>
                <CardContent className="pt-4">
                  <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold">{trial.name}</span>
                        <Badge variant="outline">{trial.type}</Badge>
                        <Badge className={getStatusColor(trial.status)}>{trial.status}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{trial.season} • {trial.locations.length} locations</p>
                      
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
                        <p className="text-lg font-bold">{trial.entries * trial.reps * trial.locations.length}</p>
                        <p className="text-xs text-muted-foreground">Plots</p>
                      </div>
                    </div>

                    <div className="text-sm text-right">
                      <p className="font-medium">{trial.startDate}</p>
                      <p className="text-xs text-muted-foreground">Start Date</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="timeline" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trial Timeline</CardTitle>
              <CardDescription>Visual timeline of planned trials</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trials.map((trial, i) => (
                  <div key={trial.id} className="flex items-center gap-4">
                    <div className="w-24 text-sm text-muted-foreground">{trial.startDate}</div>
                    <div className={`w-4 h-4 rounded-full ${trial.status === 'completed' ? 'bg-green-500' : trial.status === 'active' ? 'bg-blue-500' : 'bg-gray-300'}`}></div>
                    <div className="flex-1">
                      <p className="font-medium">{trial.name}</p>
                      <p className="text-sm text-muted-foreground">{trial.type} • {trial.locations.length} locations</p>
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

/**
 * Crossing Planner Page
 * Plan and schedule crosses between germplasm
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'

interface PlannedCross {
  id: string
  female: string
  male: string
  objective: string
  priority: 'high' | 'medium' | 'low'
  targetDate: string
  status: 'planned' | 'scheduled' | 'completed' | 'failed'
  expectedProgeny: number
}

const sampleCrosses: PlannedCross[] = [
  { id: 'CX001', female: 'Elite Line A', male: 'Disease Resistant B', objective: 'Combine yield + resistance', priority: 'high', targetDate: '2024-12-15', status: 'scheduled', expectedProgeny: 50 },
  { id: 'CX002', female: 'High Yield X', male: 'Drought Tolerant Y', objective: 'Drought tolerance introgression', priority: 'high', targetDate: '2024-12-20', status: 'planned', expectedProgeny: 100 },
  { id: 'CX003', female: 'Variety 2023', male: 'Wild Relative', objective: 'Widen genetic base', priority: 'medium', targetDate: '2025-01-10', status: 'planned', expectedProgeny: 30 },
  { id: 'CX004', female: 'Inbred A', male: 'Inbred B', objective: 'Hybrid development', priority: 'high', targetDate: '2024-12-10', status: 'completed', expectedProgeny: 200 },
  { id: 'CX005', female: 'Test Line 1', male: 'Test Line 2', objective: 'Recombination', priority: 'low', targetDate: '2025-02-01', status: 'planned', expectedProgeny: 40 },
]

const germplasmOptions = [
  'Elite Line A', 'Elite Line B', 'Disease Resistant B', 'High Yield X',
  'Drought Tolerant Y', 'Variety 2023', 'Wild Relative', 'Inbred A', 'Inbred B'
]

export function CrossingPlanner() {
  const [crosses, setCrosses] = useState<PlannedCross[]>(sampleCrosses)
  const [showForm, setShowForm] = useState(false)
  const [newCross, setNewCross] = useState({ female: '', male: '', objective: '', priority: 'medium' as const, targetDate: '', expectedProgeny: 50 })

  const addCross = () => {
    if (!newCross.female || !newCross.male) {
      toast.error('Please select both parents')
      return
    }
    const cross: PlannedCross = {
      id: `CX${String(crosses.length + 1).padStart(3, '0')}`,
      ...newCross,
      status: 'planned',
    }
    setCrosses([...crosses, cross])
    setNewCross({ female: '', male: '', objective: '', priority: 'medium', targetDate: '', expectedProgeny: 50 })
    setShowForm(false)
    toast.success('Cross planned successfully')
  }

  const updateStatus = (id: string, status: PlannedCross['status']) => {
    setCrosses(prev => prev.map(c => c.id === id ? { ...c, status } : c))
    toast.success('Status updated')
  }

  const stats = {
    total: crosses.length,
    planned: crosses.filter(c => c.status === 'planned').length,
    scheduled: crosses.filter(c => c.status === 'scheduled').length,
    completed: crosses.filter(c => c.status === 'completed').length,
    totalProgeny: crosses.filter(c => c.status === 'completed').reduce((sum, c) => sum + c.expectedProgeny, 0),
  }

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
      case 'planned': return 'bg-gray-100 text-gray-700'
      case 'scheduled': return 'bg-blue-100 text-blue-700'
      case 'completed': return 'bg-green-100 text-green-700'
      case 'failed': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Crossing Planner</h1>
          <p className="text-muted-foreground mt-1">Plan and schedule crosses</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Cancel' : '➕ Plan Cross'}
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total Crosses</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-gray-600">{stats.planned}</p><p className="text-xs text-muted-foreground">Planned</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-blue-600">{stats.scheduled}</p><p className="text-xs text-muted-foreground">Scheduled</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-600">{stats.completed}</p><p className="text-xs text-muted-foreground">Completed</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-purple-600">{stats.totalProgeny}</p><p className="text-xs text-muted-foreground">Progeny Made</p></CardContent></Card>
      </div>

      {/* New Cross Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Plan New Cross</CardTitle>
            <CardDescription>Select parents and define objectives</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Female Parent ♀</Label>
                <Select value={newCross.female} onValueChange={(v) => setNewCross({ ...newCross, female: v })}>
                  <SelectTrigger><SelectValue placeholder="Select female" /></SelectTrigger>
                  <SelectContent>
                    {germplasmOptions.map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Male Parent ♂</Label>
                <Select value={newCross.male} onValueChange={(v) => setNewCross({ ...newCross, male: v })}>
                  <SelectTrigger><SelectValue placeholder="Select male" /></SelectTrigger>
                  <SelectContent>
                    {germplasmOptions.map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select value={newCross.priority} onValueChange={(v: 'high' | 'medium' | 'low') => setNewCross({ ...newCross, priority: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Target Date</Label>
                <Input type="date" value={newCross.targetDate} onChange={(e) => setNewCross({ ...newCross, targetDate: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Expected Progeny</Label>
                <Input type="number" value={newCross.expectedProgeny} onChange={(e) => setNewCross({ ...newCross, expectedProgeny: parseInt(e.target.value) || 0 })} />
              </div>
              <div className="space-y-2 md:col-span-2 lg:col-span-1">
                <Label>Objective</Label>
                <Input value={newCross.objective} onChange={(e) => setNewCross({ ...newCross, objective: e.target.value })} placeholder="Breeding objective" />
              </div>
            </div>
            <Button onClick={addCross} className="mt-4">💾 Save Cross</Button>
          </CardContent>
        </Card>
      )}

      {/* Crosses List */}
      <Card>
        <CardHeader>
          <CardTitle>Planned Crosses</CardTitle>
          <CardDescription>{crosses.length} crosses in plan</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {crosses.map((cross) => (
              <div key={cross.id} className="flex items-center gap-4 p-4 rounded-lg border bg-white hover:shadow-sm transition-shadow">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium">{cross.female}</span>
                    <span className="text-muted-foreground">×</span>
                    <span className="font-medium">{cross.male}</span>
                    <Badge className={getPriorityColor(cross.priority)}>{cross.priority}</Badge>
                    <Badge className={getStatusColor(cross.status)}>{cross.status}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">{cross.objective}</p>
                </div>
                <div className="text-right text-sm">
                  <p className="font-medium">{cross.targetDate}</p>
                  <p className="text-xs text-muted-foreground">{cross.expectedProgeny} progeny</p>
                </div>
                <Select value={cross.status} onValueChange={(v: PlannedCross['status']) => updateStatus(cross.id, v)}>
                  <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="planned">Planned</SelectItem>
                    <SelectItem value="scheduled">Scheduled</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

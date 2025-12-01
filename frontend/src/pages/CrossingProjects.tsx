/**
 * Crossing Projects Page - BrAPI Germplasm Module
 * Breeding crossing project management
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'

interface CrossingProject {
  crossingProjectDbId: string
  crossingProjectName: string
  crossingProjectDescription?: string
  programDbId: string
  programName: string
  commonCropName: string
  plannedCrossCount: number
  completedCrossCount: number
  status: 'planning' | 'active' | 'completed' | 'cancelled'
  startDate?: string
  endDate?: string
}

const mockProjects: CrossingProject[] = [
  { crossingProjectDbId: 'cp001', crossingProjectName: 'Rice Yield Improvement 2024', crossingProjectDescription: 'Crossing elite lines for yield improvement', programDbId: 'prog001', programName: 'Rice Breeding Program', commonCropName: 'Rice', plannedCrossCount: 50, completedCrossCount: 35, status: 'active', startDate: '2024-01-01' },
  { crossingProjectDbId: 'cp002', crossingProjectName: 'Disease Resistance Introgression', crossingProjectDescription: 'Introgressing blast resistance genes', programDbId: 'prog001', programName: 'Rice Breeding Program', commonCropName: 'Rice', plannedCrossCount: 30, completedCrossCount: 30, status: 'completed', startDate: '2023-06-01', endDate: '2023-12-15' },
  { crossingProjectDbId: 'cp003', crossingProjectName: 'Wheat Quality Enhancement', crossingProjectDescription: 'Improving grain quality traits', programDbId: 'prog002', programName: 'Wheat Breeding Program', commonCropName: 'Wheat', plannedCrossCount: 40, completedCrossCount: 12, status: 'active', startDate: '2024-02-01' },
  { crossingProjectDbId: 'cp004', crossingProjectName: 'Maize Drought Tolerance', crossingProjectDescription: 'Developing drought tolerant varieties', programDbId: 'prog003', programName: 'Maize Breeding Program', commonCropName: 'Maize', plannedCrossCount: 25, completedCrossCount: 0, status: 'planning', startDate: '2024-04-01' },
]

export function CrossingProjects() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['crossingProjects', search, statusFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockProjects
      if (search) {
        filtered = filtered.filter(p => 
          p.crossingProjectName.toLowerCase().includes(search.toLowerCase()) ||
          p.programName.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (statusFilter !== 'all') {
        filtered = filtered.filter(p => p.status === statusFilter)
      }
      return { result: { data: filtered } }
    },
  })

  const projects = data?.result?.data || []

  const getStatusBadge = (status: CrossingProject['status']) => {
    const styles: Record<string, string> = {
      planning: 'bg-blue-100 text-blue-800',
      active: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800',
    }
    return <Badge className={styles[status]}>{status}</Badge>
  }

  const handleCreate = () => {
    toast.success('Crossing project created (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Crossing Projects</h1>
          <p className="text-muted-foreground mt-1">Breeding crossing project management</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>🧬 New Project</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Crossing Project</DialogTitle>
              <DialogDescription>Start a new breeding crossing project</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Project Name</Label>
                <Input placeholder="Rice Yield Improvement 2024" />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea placeholder="Project objectives and goals..." rows={3} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Program</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select program" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="prog001">Rice Breeding Program</SelectItem>
                      <SelectItem value="prog002">Wheat Breeding Program</SelectItem>
                      <SelectItem value="prog003">Maize Breeding Program</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Start Date</Label>
                  <Input type="date" />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Create Project</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search projects..."
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
                <SelectItem value="planning">Planning</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockProjects.length}</div>
            <p className="text-sm text-muted-foreground">Total Projects</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockProjects.filter(p => p.status === 'active').length}</div>
            <p className="text-sm text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockProjects.reduce((a, p) => a + p.plannedCrossCount, 0)}</div>
            <p className="text-sm text-muted-foreground">Planned Crosses</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockProjects.reduce((a, p) => a + p.completedCrossCount, 0)}</div>
            <p className="text-sm text-muted-foreground">Completed Crosses</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map(i => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      ) : projects.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No crossing projects found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((project) => {
            const progress = project.plannedCrossCount > 0 
              ? (project.completedCrossCount / project.plannedCrossCount) * 100 
              : 0
            return (
              <Card key={project.crossingProjectDbId} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{project.crossingProjectName}</CardTitle>
                      <CardDescription>{project.programName}</CardDescription>
                    </div>
                    {getStatusBadge(project.status)}
                  </div>
                </CardHeader>
                <CardContent>
                  {project.crossingProjectDescription && (
                    <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                      {project.crossingProjectDescription}
                    </p>
                  )}
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span>{project.completedCrossCount} / {project.plannedCrossCount} crosses</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500 transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="flex gap-2 mt-4">
                      <Button size="sm" variant="outline" asChild>
                        <Link to={`/crosses?projectDbId=${project.crossingProjectDbId}`}>View Crosses</Link>
                      </Button>
                      <Button size="sm" variant="outline" asChild>
                        <Link to={`/plannedcrosses?projectDbId=${project.crossingProjectDbId}`}>Plan Crosses</Link>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

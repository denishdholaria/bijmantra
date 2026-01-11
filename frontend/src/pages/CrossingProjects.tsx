/**
 * Crossing Projects Page
 * Manage crossing projects for breeding programs - Connected to BrAPI API
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Loader2, Plus, Search, Pencil, Trash2, FolderKanban, Wheat } from 'lucide-react'
import { crossingProjectsAPI, CrossingProject } from '@/lib/api-client'
import { toast } from 'sonner'

export function CrossingProjects() {
  const [search, setSearch] = useState('')
  const [cropFilter, setCropFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<CrossingProject | null>(null)
  const [newProject, setNewProject] = useState({
    crossingProjectName: '',
    crossingProjectDescription: '',
    commonCropName: '',
  })

  const queryClient = useQueryClient()

  // Fetch crossing projects from BrAPI
  const { data: projectsData, isLoading, error } = useQuery({
    queryKey: ['crossing-projects', cropFilter],
    queryFn: async () => {
      const params: { commonCropName?: string; pageSize?: number } = { pageSize: 100 }
      if (cropFilter !== 'all') params.commonCropName = cropFilter
      const response = await crossingProjectsAPI.getProjects(params)
      return response.result.data
    },
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newProject) => crossingProjectsAPI.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crossing-projects'] })
      setIsCreateOpen(false)
      setNewProject({ crossingProjectName: '', crossingProjectDescription: '', commonCropName: '' })
      toast.success('Crossing project created')
    },
    onError: () => toast.error('Failed to create project'),
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CrossingProject> }) => 
      crossingProjectsAPI.updateProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crossing-projects'] })
      setEditingProject(null)
      toast.success('Project updated')
    },
    onError: () => toast.error('Failed to update project'),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => crossingProjectsAPI.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crossing-projects'] })
      toast.success('Project deleted')
    },
    onError: () => toast.error('Failed to delete project'),
  })

  const projects: CrossingProject[] = projectsData || []
  
  // Filter by search
  const filteredProjects = projects.filter(p => 
    p.crossingProjectName.toLowerCase().includes(search.toLowerCase()) ||
    p.crossingProjectDescription?.toLowerCase().includes(search.toLowerCase()) ||
    p.programName?.toLowerCase().includes(search.toLowerCase())
  )

  // Get unique crops for filter
  const crops = [...new Set(projects.map(p => p.commonCropName).filter(Boolean))]

  // Stats
  const activeCount = projects.filter(p => p.status === 'active').length
  const completedCount = projects.filter(p => p.status === 'completed').length
  const totalPlanned = projects.reduce((sum, p) => sum + (p.plannedCrossCount || 0), 0)
  const totalCompleted = projects.reduce((sum, p) => sum + (p.completedCrossCount || 0), 0)

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-500">Active</Badge>
      case 'completed': return <Badge className="bg-blue-500">Completed</Badge>
      case 'planned': return <Badge variant="outline">Planned</Badge>
      default: return <Badge variant="secondary">{status || 'Unknown'}</Badge>
    }
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">
        Failed to load crossing projects. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Crossing Projects</h1>
          <p className="text-muted-foreground mt-1">Manage breeding crossing projects</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Crossing Project</DialogTitle>
              <DialogDescription>Add a new crossing project to your breeding program</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Project Name</Label>
                <Input
                  value={newProject.crossingProjectName}
                  onChange={(e) => setNewProject({ ...newProject, crossingProjectName: e.target.value })}
                  placeholder="e.g., Rice Yield Improvement 2024"
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={newProject.crossingProjectDescription}
                  onChange={(e) => setNewProject({ ...newProject, crossingProjectDescription: e.target.value })}
                  placeholder="Describe the project objectives..."
                />
              </div>
              <div className="space-y-2">
                <Label>Crop</Label>
                <Select
                  value={newProject.commonCropName}
                  onValueChange={(v) => setNewProject({ ...newProject, commonCropName: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select crop" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Rice">Rice</SelectItem>
                    <SelectItem value="Wheat">Wheat</SelectItem>
                    <SelectItem value="Maize">Maize</SelectItem>
                    <SelectItem value="Soybean">Soybean</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button 
                onClick={() => createMutation.mutate(newProject)}
                disabled={!newProject.crossingProjectName || createMutation.isPending}
              >
                {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <FolderKanban className="w-6 h-6 mx-auto mb-2 text-blue-500" />
            <p className="text-2xl font-bold">{projects.length}</p>
            <p className="text-xs text-muted-foreground">Total Projects</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-green-600">{activeCount}</p>
            <p className="text-xs text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{completedCount}</p>
            <p className="text-xs text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{totalCompleted}/{totalPlanned}</p>
            <p className="text-xs text-muted-foreground">Crosses Done</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search projects..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={cropFilter} onValueChange={setCropFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Crops" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Crops</SelectItem>
                {crops.map(crop => (
                  <SelectItem key={crop} value={crop!}>{crop}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Projects List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : filteredProjects.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <FolderKanban className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No crossing projects found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map((project) => (
            <Card key={project.crossingProjectDbId} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-base">{project.crossingProjectName}</CardTitle>
                    <CardDescription className="line-clamp-2">{project.crossingProjectDescription}</CardDescription>
                  </div>
                  {getStatusBadge(project.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Wheat className="w-4 h-4 text-amber-500" />
                    <span>{project.commonCropName || 'Not specified'}</span>
                  </div>
                  
                  {project.programName && (
                    <p className="text-sm text-muted-foreground">
                      Program: {project.programName}
                    </p>
                  )}
                  
                  {(project.plannedCrossCount || project.completedCrossCount) && (
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-muted rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full transition-all"
                          style={{ width: `${((project.completedCrossCount || 0) / (project.plannedCrossCount || 1)) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {project.completedCrossCount || 0}/{project.plannedCrossCount || 0}
                      </span>
                    </div>
                  )}
                  
                  <div className="flex gap-2 pt-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => setEditingProject(project)}
                    >
                      <Pencil className="w-3 h-3 mr-1" />
                      Edit
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        if (confirm('Delete this project?')) {
                          deleteMutation.mutate(project.crossingProjectDbId)
                        }
                      }}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={!!editingProject} onOpenChange={() => setEditingProject(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Crossing Project</DialogTitle>
          </DialogHeader>
          {editingProject && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Project Name</Label>
                <Input
                  value={editingProject.crossingProjectName}
                  onChange={(e) => setEditingProject({ ...editingProject, crossingProjectName: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={editingProject.crossingProjectDescription || ''}
                  onChange={(e) => setEditingProject({ ...editingProject, crossingProjectDescription: e.target.value })}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingProject(null)}>Cancel</Button>
            <Button 
              onClick={() => editingProject && updateMutation.mutate({
                id: editingProject.crossingProjectDbId,
                data: {
                  crossingProjectName: editingProject.crossingProjectName,
                  crossingProjectDescription: editingProject.crossingProjectDescription,
                }
              })}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

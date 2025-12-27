import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { workflowsAPI } from '@/lib/api-client'
import {
  Workflow,
  Play,
  Pause,
  Plus,
  Settings,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Zap,
  Mail,
  Bell,
  Database,
  FileText,
  GitBranch,
  RefreshCw,
  Trash2
} from 'lucide-react'

export function WorkflowAutomation() {
  const [searchQuery, setSearchQuery] = useState('')
  const queryClient = useQueryClient()

  // Fetch workflows
  const { data: workflowsData, isLoading: workflowsLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowsAPI.listWorkflows(),
  })

  const workflows = workflowsData?.data || []

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['workflow-stats'],
    queryFn: workflowsAPI.getStats,
  })

  const stats = statsData?.data

  // Fetch templates
  const { data: templatesData } = useQuery({
    queryKey: ['workflow-templates'],
    queryFn: workflowsAPI.listTemplates,
  })

  const workflowTemplates = templatesData?.data || []

  // Fetch run history
  const { data: runsData } = useQuery({
    queryKey: ['workflow-runs'],
    queryFn: () => workflowsAPI.getWorkflowRuns({ limit: 10 }),
  })

  const recentRuns = runsData?.data || []

  // Toggle workflow mutation
  const toggleMutation = useMutation({
    mutationFn: (workflowId: string) => workflowsAPI.toggleWorkflow(workflowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      queryClient.invalidateQueries({ queryKey: ['workflow-stats'] })
      toast.success('Workflow status updated')
    },
  })

  // Run workflow mutation
  const runMutation = useMutation({
    mutationFn: (workflowId: string) => workflowsAPI.runWorkflow(workflowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      queryClient.invalidateQueries({ queryKey: ['workflow-runs'] })
      toast.success('Workflow run started')
    },
  })

  // Delete workflow mutation
  const deleteMutation = useMutation({
    mutationFn: (workflowId: string) => workflowsAPI.deleteWorkflow(workflowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      queryClient.invalidateQueries({ queryKey: ['workflow-stats'] })
      toast.success('Workflow deleted')
    },
  })

  // Use template mutation
  const useTemplateMutation = useMutation({
    mutationFn: ({ templateId, name }: { templateId: string; name: string }) =>
      workflowsAPI.useTemplate(templateId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      toast.success('Workflow created from template')
    },
  })

  const getTemplateIcon = (category: string) => {
    switch (category) {
      case 'maintenance': return <Database className="h-5 w-5" />
      case 'notifications': return <Mail className="h-5 w-5" />
      case 'reports': return <FileText className="h-5 w-5" />
      case 'integration': return <RefreshCw className="h-5 w-5" />
      case 'monitoring': return <Bell className="h-5 w-5" />
      case 'breeding': return <GitBranch className="h-5 w-5" />
      default: return <Workflow className="h-5 w-5" />
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'paused': return <Pause className="h-4 w-4 text-yellow-500" />
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const filteredWorkflows = workflows.filter((w: any) =>
    w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    w.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Workflow className="h-8 w-8 text-primary" />
            Workflow Automation
          </h1>
          <p className="text-muted-foreground mt-1">Automate breeding program tasks and notifications</p>
        </div>
        <Button><Plus className="h-4 w-4 mr-2" />Create Workflow</Button>
      </div>

      {/* Stats */}
      {stats ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg"><Zap className="h-5 w-5 text-green-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.active_workflows}</div>
                  <div className="text-sm text-muted-foreground">Active Workflows</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg"><Play className="h-5 w-5 text-blue-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.total_runs}</div>
                  <div className="text-sm text-muted-foreground">Total Runs</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg"><CheckCircle2 className="h-5 w-5 text-purple-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.average_success_rate}%</div>
                  <div className="text-sm text-muted-foreground">Success Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg"><Clock className="h-5 w-5 text-orange-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.time_saved_hours}h</div>
                  <div className="text-sm text-muted-foreground">Time Saved</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      )}

      <Tabs defaultValue="workflows" className="space-y-4">
        <TabsList>
          <TabsTrigger value="workflows">My Workflows</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="history">Run History</TabsTrigger>
        </TabsList>

        <TabsContent value="workflows" className="space-y-4">
          <div className="flex items-center gap-4">
            <Input placeholder="Search workflows..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="max-w-sm" />
          </div>

          {workflowsLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-32" />)}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredWorkflows.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center text-muted-foreground">
                    No workflows found
                  </CardContent>
                </Card>
              ) : (
                filteredWorkflows.map((workflow: any) => (
                  <Card key={workflow.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="p-3 bg-primary/10 rounded-lg"><Workflow className="h-6 w-6 text-primary" /></div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="font-semibold">{workflow.name}</h3>
                              <Badge variant={workflow.status === 'active' ? 'default' : workflow.status === 'paused' ? 'secondary' : 'destructive'}>
                                {getStatusIcon(workflow.status)}
                                <span className="ml-1 capitalize">{workflow.status}</span>
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">{workflow.description}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{workflow.trigger}</span>
                              <span>Last: {workflow.last_run}</span>
                              <span>Next: {workflow.next_run}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="text-sm font-medium">{workflow.runs} runs</div>
                            <div className="text-xs text-muted-foreground">{workflow.success_rate}% success</div>
                          </div>
                          <Switch 
                            checked={workflow.status === 'active'} 
                            onCheckedChange={() => toggleMutation.mutate(workflow.id)}
                            disabled={toggleMutation.isPending}
                          />
                          <Button variant="ghost" size="icon"><Settings className="h-4 w-4" /></Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => runMutation.mutate(workflow.id)}
                            disabled={runMutation.isPending || !workflow.enabled}
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => deleteMutation.mutate(workflow.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workflowTemplates.map((template: any) => (
              <Card key={template.id} className="cursor-pointer hover:border-primary transition-colors">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-primary/10 rounded-lg">{getTemplateIcon(template.category)}</div>
                    <h3 className="font-semibold">{template.name}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-4">{template.description}</p>
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => {
                      const name = prompt('Enter workflow name:')
                      if (name) {
                        useTemplateMutation.mutate({ templateId: template.id, name })
                      }
                    }}
                    disabled={useTemplateMutation.isPending}
                  >
                    <Plus className="h-4 w-4 mr-2" />Use Template
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Recent Workflow Runs</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentRuns.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground">
                    No workflow runs yet
                  </div>
                ) : (
                  recentRuns.map((run: any) => (
                    <div key={run.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        {run.status === 'success' ? <CheckCircle2 className="h-5 w-5 text-green-500" /> : <XCircle className="h-5 w-5 text-red-500" />}
                        <div>
                          <div className="font-medium">{run.workflow_name}</div>
                          {run.error && <div className="text-sm text-red-500">{run.error}</div>}
                        </div>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        <div>{run.started_at}</div>
                        <div>Duration: {run.duration}</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

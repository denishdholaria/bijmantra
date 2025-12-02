import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
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
  ArrowRight,
  Zap,
  Calendar,
  Mail,
  Bell,
  Database,
  FileText,
  GitBranch,
  RefreshCw
} from 'lucide-react'

interface WorkflowItem {
  id: string
  name: string
  description: string
  trigger: string
  status: 'active' | 'paused' | 'error'
  lastRun: string
  nextRun: string
  runs: number
  successRate: number
}

interface WorkflowStep {
  id: string
  type: 'trigger' | 'action' | 'condition'
  name: string
  config: Record<string, string>
}

export function WorkflowAutomation() {
  const [searchQuery, setSearchQuery] = useState('')

  const workflows: WorkflowItem[] = [
    { id: '1', name: 'Daily Data Backup', description: 'Automated backup of all breeding data', trigger: 'Schedule: Daily 2:00 AM', status: 'active', lastRun: '2 hours ago', nextRun: 'Tomorrow 2:00 AM', runs: 365, successRate: 99.7 },
    { id: '2', name: 'Trial Completion Alert', description: 'Notify team when trial reaches completion', trigger: 'Event: Trial status change', status: 'active', lastRun: '1 day ago', nextRun: 'On trigger', runs: 47, successRate: 100 },
    { id: '3', name: 'Weekly Report Generation', description: 'Generate and email weekly progress reports', trigger: 'Schedule: Every Monday 8:00 AM', status: 'active', lastRun: '5 days ago', nextRun: 'Monday 8:00 AM', runs: 52, successRate: 98.1 },
    { id: '4', name: 'Low Seed Inventory Alert', description: 'Alert when seed lot falls below threshold', trigger: 'Event: Inventory change', status: 'active', lastRun: '3 hours ago', nextRun: 'On trigger', runs: 23, successRate: 100 },
    { id: '5', name: 'Cross Verification', description: 'Verify crosses and update pedigree records', trigger: 'Event: New cross recorded', status: 'paused', lastRun: '2 weeks ago', nextRun: 'Paused', runs: 156, successRate: 95.5 },
    { id: '6', name: 'Weather Alert Integration', description: 'Send alerts for adverse weather conditions', trigger: 'Event: Weather API update', status: 'error', lastRun: '1 hour ago', nextRun: 'Retry in 30 min', runs: 89, successRate: 87.6 }
  ]

  const workflowTemplates = [
    { name: 'Data Backup', icon: <Database className="h-5 w-5" />, description: 'Scheduled database backups' },
    { name: 'Email Notifications', icon: <Mail className="h-5 w-5" />, description: 'Send automated emails' },
    { name: 'Report Generation', icon: <FileText className="h-5 w-5" />, description: 'Create periodic reports' },
    { name: 'Data Sync', icon: <RefreshCw className="h-5 w-5" />, description: 'Sync data between systems' },
    { name: 'Alert System', icon: <Bell className="h-5 w-5" />, description: 'Threshold-based alerts' },
    { name: 'Pipeline Automation', icon: <GitBranch className="h-5 w-5" />, description: 'Breeding pipeline tasks' }
  ]

  const recentRuns = [
    { workflow: 'Daily Data Backup', status: 'success', time: '2 hours ago', duration: '3m 24s' },
    { workflow: 'Low Seed Inventory Alert', status: 'success', time: '3 hours ago', duration: '0.5s' },
    { workflow: 'Weather Alert Integration', status: 'error', time: '1 hour ago', duration: '12s', error: 'API timeout' },
    { workflow: 'Trial Completion Alert', status: 'success', time: '1 day ago', duration: '1.2s' }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'paused': return <Pause className="h-4 w-4 text-yellow-500" />
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const filteredWorkflows = workflows.filter(w =>
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><Zap className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{workflows.filter(w => w.status === 'active').length}</div>
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
                <div className="text-2xl font-bold">{workflows.reduce((sum, w) => sum + w.runs, 0)}</div>
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
                <div className="text-2xl font-bold">97.2%</div>
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
                <div className="text-2xl font-bold">142h</div>
                <div className="text-sm text-muted-foreground">Time Saved</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

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

          <div className="space-y-4">
            {filteredWorkflows.map((workflow) => (
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
                          <span>Last: {workflow.lastRun}</span>
                          <span>Next: {workflow.nextRun}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-medium">{workflow.runs} runs</div>
                        <div className="text-xs text-muted-foreground">{workflow.successRate}% success</div>
                      </div>
                      <Switch checked={workflow.status === 'active'} />
                      <Button variant="ghost" size="icon"><Settings className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="icon"><Play className="h-4 w-4" /></Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workflowTemplates.map((template, index) => (
              <Card key={index} className="cursor-pointer hover:border-primary transition-colors">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-primary/10 rounded-lg">{template.icon}</div>
                    <h3 className="font-semibold">{template.name}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-4">{template.description}</p>
                  <Button variant="outline" className="w-full"><Plus className="h-4 w-4 mr-2" />Use Template</Button>
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
                {recentRuns.map((run, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {run.status === 'success' ? <CheckCircle2 className="h-5 w-5 text-green-500" /> : <XCircle className="h-5 w-5 text-red-500" />}
                      <div>
                        <div className="font-medium">{run.workflow}</div>
                        {run.error && <div className="text-sm text-red-500">{run.error}</div>}
                      </div>
                    </div>
                    <div className="text-right text-sm text-muted-foreground">
                      <div>{run.time}</div>
                      <div>Duration: {run.duration}</div>
                    </div>
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

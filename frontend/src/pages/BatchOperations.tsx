import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Layers, CheckCircle, Clock, AlertCircle,
  RefreshCw
} from 'lucide-react'

interface BatchJob {
  id: string
  name: string
  type: string
  status: 'running' | 'completed' | 'failed' | 'queued'
  progress: number
  items: number
  startedAt: string
}

export function BatchOperations() {
  const [_activeTab, _setActiveTab] = useState('jobs')

  const jobs: BatchJob[] = [
    { id: '1', name: 'Import Germplasm Data', type: 'import', status: 'running', progress: 65, items: 500, startedAt: '10 min ago' },
    { id: '2', name: 'Export Trial Results', type: 'export', status: 'completed', progress: 100, items: 1200, startedAt: '1 hour ago' },
    { id: '3', name: 'Update Observations', type: 'update', status: 'queued', progress: 0, items: 350, startedAt: 'Pending' },
    { id: '4', name: 'Delete Old Records', type: 'delete', status: 'failed', progress: 45, items: 200, startedAt: '2 hours ago' },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed': return <AlertCircle className="h-4 w-4 text-red-500" />
      default: return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { running: 'bg-blue-100 text-blue-800', completed: 'bg-green-100 text-green-800', failed: 'bg-red-100 text-red-800', queued: 'bg-gray-100 text-gray-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Batch Operations</h1>
          <p className="text-muted-foreground">Manage bulk data operations</p>
        </div>
        <Button><Layers className="mr-2 h-4 w-4" />New Batch Job</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <RefreshCw className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobs.filter(j => j.status === 'running').length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobs.filter(j => j.status === 'completed').length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Queued</CardTitle>
            <Clock className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobs.filter(j => j.status === 'queued').length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobs.filter(j => j.status === 'failed').length}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Batch Jobs</CardTitle><CardDescription>Monitor and manage batch operations</CardDescription></CardHeader>
        <CardContent>
          <div className="space-y-4">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  {getStatusIcon(job.status)}
                  <div>
                    <p className="font-medium">{job.name}</p>
                    <p className="text-sm text-muted-foreground">{job.items} items • Started {job.startedAt}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {job.status === 'running' && (
                    <div className="w-32">
                      <Progress value={job.progress} />
                      <p className="text-xs text-center mt-1">{job.progress}%</p>
                    </div>
                  )}
                  <Badge className={getStatusColor(job.status)}>{job.status}</Badge>
                  <Button variant="outline" size="sm">{job.status === 'running' ? 'Cancel' : 'Details'}</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

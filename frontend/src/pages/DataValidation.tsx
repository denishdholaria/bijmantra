import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { toast } from 'sonner'
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Download,
  Eye,
  Trash2,
  Edit
} from 'lucide-react'
import { dataValidationAPI } from '@/lib/api-client'

export function DataValidation() {
  const queryClient = useQueryClient()
  const [isValidating, setIsValidating] = useState(false)
  const [progress, setProgress] = useState(0)

  // Fetch validation stats
  const { data: statsData } = useQuery({
    queryKey: ['validation-stats'],
    queryFn: () => dataValidationAPI.getStats(),
  })

  // Fetch validation issues
  const { data: issuesData, isLoading: issuesLoading } = useQuery({
    queryKey: ['validation-issues'],
    queryFn: () => dataValidationAPI.getIssues({ status: 'open', limit: 50 }),
  })

  // Fetch validation rules
  const { data: rulesData } = useQuery({
    queryKey: ['validation-rules'],
    queryFn: () => dataValidationAPI.getRules(),
  })

  // Run validation mutation
  const runValidationMutation = useMutation({
    mutationFn: () => dataValidationAPI.runValidation(),
    onSuccess: (data) => {
      toast.success(data.message || 'Validation completed')
      queryClient.invalidateQueries({ queryKey: ['validation-stats'] })
      queryClient.invalidateQueries({ queryKey: ['validation-issues'] })
    },
    onError: () => toast.error('Validation failed'),
  })

  // Update issue status mutation
  const updateIssueMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => 
      dataValidationAPI.updateIssueStatus(id, { status }),
    onSuccess: () => {
      toast.success('Issue updated')
      queryClient.invalidateQueries({ queryKey: ['validation-issues'] })
      queryClient.invalidateQueries({ queryKey: ['validation-stats'] })
    },
  })

  // Toggle rule mutation
  const toggleRuleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      dataValidationAPI.updateRule(id, { enabled }),
    onSuccess: () => {
      toast.success('Rule updated')
      queryClient.invalidateQueries({ queryKey: ['validation-rules'] })
    },
  })

  // Delete issue mutation
  const deleteIssueMutation = useMutation({
    mutationFn: (id: string) => dataValidationAPI.deleteIssue(id),
    onSuccess: () => {
      toast.success('Issue deleted')
      queryClient.invalidateQueries({ queryKey: ['validation-issues'] })
      queryClient.invalidateQueries({ queryKey: ['validation-stats'] })
    },
  })

  const handleValidate = () => {
    setIsValidating(true)
    setProgress(0)
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsValidating(false)
          runValidationMutation.mutate()
          return 100
        }
        return prev + 10
      })
    }, 300)
  }

  const handleExport = async () => {
    try {
      const data = await dataValidationAPI.exportReport('json')
      const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `validation-report-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      toast.success('Report exported')
    } catch {
      toast.error('Export failed')
    }
  }

  const stats = statsData?.data || { total_issues: 0, errors: 0, warnings: 0, info: 0, data_quality_score: 100 }
  const issues = issuesData?.data || []
  const rules = rulesData?.data || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <ShieldCheck className="h-8 w-8 text-primary" />
            Data Validation
          </h1>
          <p className="text-muted-foreground mt-1">Validate data quality and integrity</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}><Download className="h-4 w-4 mr-2" />Export Report</Button>
          <Button onClick={handleValidate} disabled={isValidating}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isValidating ? 'animate-spin' : ''}`} />
            {isValidating ? 'Validating...' : 'Run Validation'}
          </Button>
        </div>
      </div>

      {/* Progress */}
      {isValidating && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <RefreshCw className="h-5 w-5 animate-spin text-primary" />
              <div className="flex-1">
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Validating data...</span>
                  <span className="text-sm text-muted-foreground">{progress}%</span>
                </div>
                <Progress value={progress} />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><ShieldCheck className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.total_issues}</div>
                <div className="text-sm text-muted-foreground">Total Issues</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg"><XCircle className="h-5 w-5 text-red-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.errors}</div>
                <div className="text-sm text-muted-foreground">Errors</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><AlertTriangle className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.warnings}</div>
                <div className="text-sm text-muted-foreground">Warnings</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><CheckCircle2 className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.data_quality_score}%</div>
                <div className="text-sm text-muted-foreground">Data Quality</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="issues" className="space-y-4">
        <TabsList>
          <TabsTrigger value="issues">Issues ({issues.length})</TabsTrigger>
          <TabsTrigger value="rules">Validation Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="issues">
          <Card>
            <CardHeader>
              <CardTitle>Validation Issues</CardTitle>
              <CardDescription>Review and resolve data quality issues</CardDescription>
            </CardHeader>
            <CardContent>
              {issuesLoading ? (
                <div className="text-center py-8 text-muted-foreground">Loading issues...</div>
              ) : issues.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No open issues found</div>
              ) : (
                <div className="space-y-3">
                  {issues.map((issue: any) => (
                    <div key={issue.id} className={`p-4 border rounded-lg ${issue.type === 'error' ? 'border-red-200 bg-red-50' : issue.type === 'warning' ? 'border-yellow-200 bg-yellow-50' : 'border-blue-200 bg-blue-50'}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          {issue.type === 'error' ? <XCircle className="h-5 w-5 text-red-500 mt-0.5" /> :
                           issue.type === 'warning' ? <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" /> :
                           <CheckCircle2 className="h-5 w-5 text-blue-500 mt-0.5" />}
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline">{issue.record_id}</Badge>
                              <span className="text-sm text-muted-foreground">Field: {issue.field}</span>
                            </div>
                            <p className="font-medium">{issue.message}</p>
                            {issue.suggestion && <p className="text-sm text-muted-foreground mt-1">💡 {issue.suggestion}</p>}
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="icon" title="View"><Eye className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" title="Resolve" onClick={() => updateIssueMutation.mutate({ id: issue.id, status: 'resolved' })}><CheckCircle2 className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" title="Delete" onClick={() => deleteIssueMutation.mutate(issue.id)}><Trash2 className="h-4 w-4" /></Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rules">
          <Card>
            <CardHeader>
              <CardTitle>Validation Rules</CardTitle>
              <CardDescription>Configure data validation rules</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {rules.map((rule: any) => (
                  <div key={rule.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <div className="font-medium">{rule.name}</div>
                      <div className="text-sm text-muted-foreground">{rule.description}</div>
                    </div>
                    <div className="flex items-center gap-4">
                      {rule.issues_found > 0 && <Badge variant="destructive">{rule.issues_found} issues</Badge>}
                      <Switch 
                        checked={rule.enabled} 
                        onCheckedChange={(checked) => toggleRuleMutation.mutate({ id: rule.id, enabled: checked })}
                      />
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

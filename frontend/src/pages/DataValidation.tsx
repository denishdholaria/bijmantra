import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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

interface ValidationIssue {
  id: string
  type: 'error' | 'warning' | 'info'
  field: string
  record: string
  message: string
  suggestion?: string
}

interface ValidationRule {
  name: string
  description: string
  enabled: boolean
  issuesFound: number
}

export function DataValidation() {
  const [isValidating, setIsValidating] = useState(false)
  const [progress, setProgress] = useState(0)

  const issues: ValidationIssue[] = [
    { id: '1', type: 'error', field: 'yield', record: 'OBS-2025-001', message: 'Value 150 t/ha exceeds maximum threshold (15)', suggestion: 'Check decimal placement' },
    { id: '2', type: 'error', field: 'germplasmDbId', record: 'OBS-2025-045', message: 'Referenced germplasm does not exist', suggestion: 'Verify germplasm ID' },
    { id: '3', type: 'warning', field: 'plantHeight', record: 'OBS-2025-089', message: 'Value 250cm is an outlier (>3 SD from mean)', suggestion: 'Verify measurement' },
    { id: '4', type: 'warning', field: 'observationDate', record: 'OBS-2025-102', message: 'Date is in the future', suggestion: 'Check date entry' },
    { id: '5', type: 'info', field: 'notes', record: 'OBS-2025-156', message: 'Field contains special characters', suggestion: 'Review for data quality' }
  ]

  const rules: ValidationRule[] = [
    { name: 'Range Check', description: 'Values within expected ranges', enabled: true, issuesFound: 2 },
    { name: 'Referential Integrity', description: 'Foreign keys exist', enabled: true, issuesFound: 1 },
    { name: 'Outlier Detection', description: 'Statistical outliers', enabled: true, issuesFound: 1 },
    { name: 'Date Validation', description: 'Valid date formats and ranges', enabled: true, issuesFound: 1 },
    { name: 'Duplicate Check', description: 'Duplicate records', enabled: true, issuesFound: 0 },
    { name: 'Required Fields', description: 'Mandatory fields populated', enabled: true, issuesFound: 0 }
  ]

  const handleValidate = () => {
    setIsValidating(true)
    setProgress(0)
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsValidating(false)
          return 100
        }
        return prev + 10
      })
    }, 300)
  }

  const stats = {
    total: issues.length,
    errors: issues.filter(i => i.type === 'error').length,
    warnings: issues.filter(i => i.type === 'warning').length,
    info: issues.filter(i => i.type === 'info').length
  }

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
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Report</Button>
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
                <div className="text-2xl font-bold">{stats.total}</div>
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
                <div className="text-2xl font-bold">98.5%</div>
                <div className="text-sm text-muted-foreground">Data Quality</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="issues" className="space-y-4">
        <TabsList>
          <TabsTrigger value="issues">Issues ({stats.total})</TabsTrigger>
          <TabsTrigger value="rules">Validation Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="issues">
          <Card>
            <CardHeader>
              <CardTitle>Validation Issues</CardTitle>
              <CardDescription>Review and resolve data quality issues</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {issues.map(issue => (
                  <div key={issue.id} className={`p-4 border rounded-lg ${issue.type === 'error' ? 'border-red-200 bg-red-50' : issue.type === 'warning' ? 'border-yellow-200 bg-yellow-50' : 'border-blue-200 bg-blue-50'}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        {issue.type === 'error' ? <XCircle className="h-5 w-5 text-red-500 mt-0.5" /> :
                         issue.type === 'warning' ? <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" /> :
                         <CheckCircle2 className="h-5 w-5 text-blue-500 mt-0.5" />}
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline">{issue.record}</Badge>
                            <span className="text-sm text-muted-foreground">Field: {issue.field}</span>
                          </div>
                          <p className="font-medium">{issue.message}</p>
                          {issue.suggestion && <p className="text-sm text-muted-foreground mt-1">💡 {issue.suggestion}</p>}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon"><Eye className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon"><Edit className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
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
                {rules.map((rule, i) => (
                  <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <div className="font-medium">{rule.name}</div>
                      <div className="text-sm text-muted-foreground">{rule.description}</div>
                    </div>
                    <div className="flex items-center gap-4">
                      {rule.issuesFound > 0 && <Badge variant="destructive">{rule.issuesFound} issues</Badge>}
                      <Badge variant={rule.enabled ? 'default' : 'secondary'}>{rule.enabled ? 'Enabled' : 'Disabled'}</Badge>
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

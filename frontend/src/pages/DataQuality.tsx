/**
 * Data Quality Page
 * Data quality monitoring and validation
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'

interface QualityIssue {
  id: string
  entity: string
  entityId: string
  entityName: string
  issueType: 'missing' | 'outlier' | 'duplicate' | 'invalid' | 'inconsistent'
  field: string
  description: string
  severity: 'low' | 'medium' | 'high'
  status: 'open' | 'resolved' | 'ignored'
  detectedAt: string
}

interface QualityMetric {
  entity: string
  totalRecords: number
  completeRecords: number
  issueCount: number
  completeness: number
}

const mockIssues: QualityIssue[] = [
  { id: 'q001', entity: 'Germplasm', entityId: 'g001', entityName: 'IR64-2024', issueType: 'missing', field: 'pedigree', description: 'Missing pedigree information', severity: 'medium', status: 'open', detectedAt: '2024-02-20T10:00:00' },
  { id: 'q002', entity: 'Observation', entityId: 'obs001', entityName: 'Plant Height', issueType: 'outlier', field: 'value', description: 'Value 250cm exceeds expected range (50-150cm)', severity: 'high', status: 'open', detectedAt: '2024-02-20T09:30:00' },
  { id: 'q003', entity: 'Germplasm', entityId: 'g002', entityName: 'Nipponbare', issueType: 'duplicate', field: 'accessionNumber', description: 'Duplicate accession number found', severity: 'high', status: 'open', detectedAt: '2024-02-19T15:00:00' },
  { id: 'q004', entity: 'Location', entityId: 'loc001', entityName: 'Field Station A', issueType: 'invalid', field: 'coordinates', description: 'Invalid GPS coordinates', severity: 'medium', status: 'resolved', detectedAt: '2024-02-18T11:00:00' },
  { id: 'q005', entity: 'Sample', entityId: 's001', entityName: 'SAMPLE-001', issueType: 'inconsistent', field: 'germplasmDbId', description: 'Referenced germplasm does not exist', severity: 'high', status: 'open', detectedAt: '2024-02-17T14:00:00' },
]

const mockMetrics: QualityMetric[] = [
  { entity: 'Germplasm', totalRecords: 1250, completeRecords: 1180, issueCount: 15, completeness: 94.4 },
  { entity: 'Observations', totalRecords: 45000, completeRecords: 44500, issueCount: 23, completeness: 98.9 },
  { entity: 'Samples', totalRecords: 500, completeRecords: 485, issueCount: 8, completeness: 97.0 },
  { entity: 'Locations', totalRecords: 25, completeRecords: 24, issueCount: 2, completeness: 96.0 },
  { entity: 'Trials', totalRecords: 15, completeRecords: 15, issueCount: 0, completeness: 100 },
]

export function DataQuality() {
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data: issuesData, isLoading: issuesLoading } = useQuery({
    queryKey: ['qualityIssues', statusFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockIssues
      if (statusFilter !== 'all') {
        filtered = filtered.filter(i => i.status === statusFilter)
      }
      return filtered
    },
  })

  const issues = issuesData || []
  const overallCompleteness = mockMetrics.reduce((sum, m) => sum + m.completeness, 0) / mockMetrics.length

  const getSeverityBadge = (severity: QualityIssue['severity']) => {
    const styles: Record<string, string> = {
      low: 'bg-blue-100 text-blue-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800',
    }
    return styles[severity]
  }

  const getIssueTypeBadge = (type: QualityIssue['issueType']) => {
    const styles: Record<string, string> = {
      missing: 'bg-gray-100 text-gray-800',
      outlier: 'bg-orange-100 text-orange-800',
      duplicate: 'bg-purple-100 text-purple-800',
      invalid: 'bg-red-100 text-red-800',
      inconsistent: 'bg-yellow-100 text-yellow-800',
    }
    return styles[type]
  }

  const runValidation = () => {
    toast.success('Data validation started (demo)')
  }

  const resolveIssue = (id: string) => {
    toast.success('Issue marked as resolved')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Data Quality</h1>
          <p className="text-muted-foreground mt-1">Monitor and improve data quality</p>
        </div>
        <Button onClick={runValidation}>🔍 Run Validation</Button>
      </div>

      {/* Overall Score */}
      <Card className="bg-gradient-to-br from-green-500 to-emerald-600 text-white">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Overall Data Quality Score</h2>
              <p className="text-green-100">Based on completeness and validation</p>
            </div>
            <div className="text-right">
              <div className="text-5xl font-bold">{overallCompleteness.toFixed(1)}%</div>
              <Badge className="bg-white/20 text-white mt-2">Excellent</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics by Entity */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {mockMetrics.map((metric) => (
          <Card key={metric.entity}>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-sm text-muted-foreground">{metric.entity}</p>
                <p className="text-2xl font-bold mt-1">{metric.completeness}%</p>
                <Progress value={metric.completeness} className="mt-2 h-2" />
                <p className="text-xs text-muted-foreground mt-2">
                  {metric.issueCount} issues
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="issues">
        <TabsList>
          <TabsTrigger value="issues">Issues ({mockIssues.filter(i => i.status === 'open').length})</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="issues" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Quality Issues</CardTitle>
                  <CardDescription>Data quality issues requiring attention</CardDescription>
                </div>
                <div className="flex gap-2">
                  {['all', 'open', 'resolved', 'ignored'].map(status => (
                    <Button
                      key={status}
                      size="sm"
                      variant={statusFilter === status ? 'default' : 'outline'}
                      onClick={() => setStatusFilter(status)}
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {issuesLoading ? (
                <Skeleton className="h-48 w-full" />
              ) : issues.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p className="text-4xl mb-2">✅</p>
                  <p>No issues found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Entity</TableHead>
                      <TableHead>Issue Type</TableHead>
                      <TableHead>Field</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {issues.map((issue) => (
                      <TableRow key={issue.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{issue.entity}</p>
                            <p className="text-xs text-muted-foreground">{issue.entityName}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getIssueTypeBadge(issue.issueType)}>{issue.issueType}</Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{issue.field}</TableCell>
                        <TableCell className="max-w-xs truncate">{issue.description}</TableCell>
                        <TableCell>
                          <Badge className={getSeverityBadge(issue.severity)}>{issue.severity}</Badge>
                        </TableCell>
                        <TableCell>
                          {issue.status === 'open' && (
                            <Button size="sm" variant="ghost" onClick={() => resolveIssue(issue.id)}>
                              Resolve
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Metrics</CardTitle>
              <CardDescription>Data completeness by entity type</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Entity</TableHead>
                    <TableHead>Total Records</TableHead>
                    <TableHead>Complete Records</TableHead>
                    <TableHead>Issues</TableHead>
                    <TableHead>Completeness</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockMetrics.map((metric) => (
                    <TableRow key={metric.entity}>
                      <TableCell className="font-medium">{metric.entity}</TableCell>
                      <TableCell>{metric.totalRecords.toLocaleString()}</TableCell>
                      <TableCell>{metric.completeRecords.toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge variant={metric.issueCount > 0 ? 'destructive' : 'secondary'}>
                          {metric.issueCount}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={metric.completeness} className="w-24 h-2" />
                          <span className="text-sm font-medium">{metric.completeness}%</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

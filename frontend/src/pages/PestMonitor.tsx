import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Bug, AlertTriangle, CheckCircle, MapPin, Shield } from 'lucide-react'

interface PestReport {
  id: string
  pest: string
  severity: 'low' | 'medium' | 'high'
  location: string
  reportedAt: string
  status: 'active' | 'treated' | 'resolved'
  affectedArea: number
}

export function PestMonitor() {
  const [activeTab, setActiveTab] = useState('active')

  const reports: PestReport[] = [
    { id: '1', pest: 'Rice Stem Borer', severity: 'high', location: 'Block A - Zone 3', reportedAt: '2 hours ago', status: 'active', affectedArea: 0.5 },
    { id: '2', pest: 'Brown Planthopper', severity: 'medium', location: 'Block B - Zone 1', reportedAt: '1 day ago', status: 'treated', affectedArea: 0.3 },
    { id: '3', pest: 'Leaf Folder', severity: 'low', location: 'Block A - Zone 1', reportedAt: '3 days ago', status: 'resolved', affectedArea: 0.2 },
    { id: '4', pest: 'Rice Bug', severity: 'medium', location: 'Block C - Zone 2', reportedAt: '5 hours ago', status: 'active', affectedArea: 0.4 },
  ]

  const stats = {
    active: reports.filter(r => r.status === 'active').length,
    treated: reports.filter(r => r.status === 'treated').length,
    resolved: reports.filter(r => r.status === 'resolved').length,
    totalArea: reports.filter(r => r.status !== 'resolved').reduce((s, r) => s + r.affectedArea, 0)
  }

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = { low: 'bg-yellow-100 text-yellow-800', medium: 'bg-orange-100 text-orange-800', high: 'bg-red-100 text-red-800' }
    return colors[severity] || 'bg-gray-100 text-gray-800'
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { active: 'bg-red-100 text-red-800', treated: 'bg-blue-100 text-blue-800', resolved: 'bg-green-100 text-green-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const filteredReports = reports.filter(r => activeTab === 'all' || r.status === activeTab)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Pest Monitor</h1>
          <p className="text-muted-foreground">Track and manage pest infestations</p>
        </div>
        <Button><Bug className="mr-2 h-4 w-4" />Report Pest</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><AlertTriangle className="h-8 w-8 text-red-500" /><div><p className="text-2xl font-bold">{stats.active}</p><p className="text-xs text-muted-foreground">Active</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Shield className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{stats.treated}</p><p className="text-xs text-muted-foreground">Treated</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><CheckCircle className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{stats.resolved}</p><p className="text-xs text-muted-foreground">Resolved</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><MapPin className="h-8 w-8 text-orange-500" /><div><p className="text-2xl font-bold">{stats.totalArea} ha</p><p className="text-xs text-muted-foreground">Affected</p></div></div></CardContent></Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="active">Active ({stats.active})</TabsTrigger>
          <TabsTrigger value="treated">Treated ({stats.treated})</TabsTrigger>
          <TabsTrigger value="resolved">Resolved ({stats.resolved})</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          <Card>
            <CardContent className="p-0">
              <div className="divide-y">
                {filteredReports.map((report) => (
                  <div key={report.id} className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4">
                      <Bug className={`h-8 w-8 ${report.severity === 'high' ? 'text-red-500' : report.severity === 'medium' ? 'text-orange-500' : 'text-yellow-500'}`} />
                      <div>
                        <p className="font-medium">{report.pest}</p>
                        <p className="text-sm text-muted-foreground flex items-center gap-1"><MapPin className="h-3 w-3" />{report.location}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right text-sm">
                        <p>{report.affectedArea} ha affected</p>
                        <p className="text-muted-foreground">{report.reportedAt}</p>
                      </div>
                      <Badge className={getSeverityColor(report.severity)}>{report.severity}</Badge>
                      <Badge className={getStatusColor(report.status)}>{report.status}</Badge>
                      <Button variant="outline" size="sm">Details</Button>
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

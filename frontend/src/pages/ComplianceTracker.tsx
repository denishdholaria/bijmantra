import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Shield, FileCheck, AlertTriangle, CheckCircle, Clock,
  FileText, Calendar, Download, Upload, Eye
} from 'lucide-react'

interface ComplianceItem {
  id: string
  name: string
  category: string
  status: 'compliant' | 'pending' | 'non-compliant' | 'expired'
  dueDate: string
  lastReview: string
  documents: number
}

interface Regulation {
  id: string
  name: string
  authority: string
  requirements: string[]
  status: 'active' | 'upcoming'
}

export function ComplianceTracker() {
  const [activeTab, setActiveTab] = useState('overview')

  const complianceItems: ComplianceItem[] = [
    { id: '1', name: 'Biosafety Protocol', category: 'Safety', status: 'compliant', dueDate: '2026-06-01', lastReview: '2025-06-01', documents: 5 },
    { id: '2', name: 'GMO Handling Permit', category: 'Regulatory', status: 'compliant', dueDate: '2025-12-31', lastReview: '2025-01-15', documents: 3 },
    { id: '3', name: 'Seed Certification', category: 'Quality', status: 'pending', dueDate: '2025-12-15', lastReview: '2024-12-15', documents: 8 },
    { id: '4', name: 'Environmental Impact Assessment', category: 'Environmental', status: 'compliant', dueDate: '2026-03-01', lastReview: '2025-03-01', documents: 12 },
    { id: '5', name: 'Data Privacy Compliance', category: 'Data', status: 'pending', dueDate: '2025-12-10', lastReview: '2024-12-10', documents: 4 },
    { id: '6', name: 'Phytosanitary Certificate', category: 'Regulatory', status: 'expired', dueDate: '2025-11-30', lastReview: '2024-11-30', documents: 2 },
  ]

  const regulations: Regulation[] = [
    { id: '1', name: 'Plant Variety Protection Act', authority: 'National Authority', requirements: ['DUS Testing', 'Novelty Declaration', 'Denomination'], status: 'active' },
    { id: '2', name: 'Seed Act Regulations', authority: 'Seed Certification Agency', requirements: ['Quality Standards', 'Labeling', 'Traceability'], status: 'active' },
    { id: '3', name: 'Biosafety Guidelines', authority: 'Biosafety Committee', requirements: ['Risk Assessment', 'Containment', 'Monitoring'], status: 'active' },
    { id: '4', name: 'New Gene Editing Regulations', authority: 'Regulatory Authority', requirements: ['Notification', 'Risk Assessment', 'Traceability'], status: 'upcoming' },
  ]

  const stats = {
    compliant: complianceItems.filter(i => i.status === 'compliant').length,
    pending: complianceItems.filter(i => i.status === 'pending').length,
    expired: complianceItems.filter(i => i.status === 'expired' || i.status === 'non-compliant').length,
    total: complianceItems.length
  }

  const complianceRate = Math.round((stats.compliant / stats.total) * 100)

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { compliant: 'bg-green-100 text-green-800', pending: 'bg-yellow-100 text-yellow-800', 'non-compliant': 'bg-red-100 text-red-800', expired: 'bg-red-100 text-red-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />
      default: return <AlertTriangle className="h-4 w-4 text-red-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Compliance Tracker</h1>
          <p className="text-muted-foreground">Monitor regulatory compliance and certifications</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export Report</Button>
          <Button><Upload className="mr-2 h-4 w-4" />Upload Document</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Rate</CardTitle>
            <Shield className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{complianceRate}%</div>
            <Progress value={complianceRate} className="mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliant</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.compliant}</div>
            <p className="text-xs text-muted-foreground">Up to date</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pending}</div>
            <p className="text-xs text-muted-foreground">Action required</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expired</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.expired}</div>
            <p className="text-xs text-muted-foreground">Needs renewal</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview"><Shield className="mr-2 h-4 w-4" />Overview</TabsTrigger>
          <TabsTrigger value="regulations"><FileText className="mr-2 h-4 w-4" />Regulations</TabsTrigger>
          <TabsTrigger value="calendar"><Calendar className="mr-2 h-4 w-4" />Calendar</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Compliance Items</CardTitle><CardDescription>Track all compliance requirements</CardDescription></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {complianceItems.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      {getStatusIcon(item.status)}
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <p className="text-sm text-muted-foreground">{item.category} • Due: {item.dueDate}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right text-sm">
                        <p className="text-muted-foreground">{item.documents} documents</p>
                        <p className="text-xs text-muted-foreground">Last review: {item.lastReview}</p>
                      </div>
                      <Badge className={getStatusColor(item.status)}>{item.status}</Badge>
                      <Button variant="outline" size="sm"><Eye className="mr-1 h-3 w-3" />View</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="regulations" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {regulations.map((reg) => (
              <Card key={reg.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{reg.name}</CardTitle>
                    <Badge variant={reg.status === 'active' ? 'default' : 'secondary'}>{reg.status}</Badge>
                  </div>
                  <CardDescription>{reg.authority}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Requirements:</p>
                    <div className="flex gap-1 flex-wrap">{reg.requirements.map(r => (<Badge key={r} variant="outline" className="text-xs">{r}</Badge>))}</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="calendar"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Compliance calendar and deadlines</p></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  )
}

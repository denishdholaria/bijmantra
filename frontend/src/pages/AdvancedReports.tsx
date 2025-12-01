import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  FileText, Download, Calendar, Filter, BarChart3, 
  PieChart, TrendingUp, Table, FileSpreadsheet, Printer,
  Share2, Clock, CheckCircle, AlertCircle, RefreshCw
} from 'lucide-react'

interface ReportTemplate {
  id: string
  name: string
  description: string
  category: string
  lastGenerated?: string
  format: string[]
}

interface ScheduledReport {
  id: string
  name: string
  schedule: string
  nextRun: string
  recipients: number
  status: 'active' | 'paused'
}

export function AdvancedReports() {
  const [activeTab, setActiveTab] = useState('templates')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const reportTemplates: ReportTemplate[] = [
    { id: '1', name: 'Trial Summary Report', description: 'Comprehensive overview of trial performance', category: 'trials', lastGenerated: '2 hours ago', format: ['PDF', 'Excel', 'CSV'] },
    { id: '2', name: 'Germplasm Inventory', description: 'Current stock levels and locations', category: 'germplasm', lastGenerated: '1 day ago', format: ['PDF', 'Excel'] },
    { id: '3', name: 'Breeding Progress', description: 'Pipeline advancement and selection rates', category: 'breeding', lastGenerated: '3 days ago', format: ['PDF', 'PowerPoint'] },
    { id: '4', name: 'Phenotypic Analysis', description: 'Statistical analysis of trait data', category: 'phenotyping', format: ['PDF', 'Excel', 'R'] },
    { id: '5', name: 'Genomic Selection Results', description: 'GEBV rankings and predictions', category: 'genomics', format: ['PDF', 'Excel', 'CSV'] },
    { id: '6', name: 'Cross Performance', description: 'Crossing success rates and progeny analysis', category: 'breeding', format: ['PDF', 'Excel'] },
    { id: '7', name: 'Location Comparison', description: 'Multi-environment trial analysis', category: 'trials', format: ['PDF', 'Excel'] },
    { id: '8', name: 'Seed Lot Tracking', description: 'Seed inventory movements and transactions', category: 'germplasm', format: ['PDF', 'Excel', 'CSV'] },
  ]

  const scheduledReports: ScheduledReport[] = [
    { id: '1', name: 'Weekly Trial Update', schedule: 'Every Monday 8:00 AM', nextRun: 'Dec 2, 2025', recipients: 5, status: 'active' },
    { id: '2', name: 'Monthly Breeding Summary', schedule: '1st of each month', nextRun: 'Jan 1, 2026', recipients: 12, status: 'active' },
    { id: '3', name: 'Daily Data Quality Check', schedule: 'Every day 6:00 AM', nextRun: 'Dec 2, 2025', recipients: 3, status: 'active' },
    { id: '4', name: 'Quarterly Progress Report', schedule: 'Every 3 months', nextRun: 'Jan 1, 2026', recipients: 8, status: 'paused' },
  ]

  const recentReports = [
    { id: '1', name: 'Rice Yield Trial 2025 Summary', generatedAt: '2 hours ago', size: '2.4 MB', format: 'PDF' },
    { id: '2', name: 'Germplasm Collection Export', generatedAt: '1 day ago', size: '15.2 MB', format: 'Excel' },
    { id: '3', name: 'QTL Mapping Results', generatedAt: '2 days ago', size: '1.8 MB', format: 'PDF' },
    { id: '4', name: 'Crossing Block Plan', generatedAt: '3 days ago', size: '856 KB', format: 'PDF' },
  ]

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'trials', label: 'Trials' },
    { value: 'germplasm', label: 'Germplasm' },
    { value: 'breeding', label: 'Breeding' },
    { value: 'phenotyping', label: 'Phenotyping' },
    { value: 'genomics', label: 'Genomics' },
  ]

  const filteredTemplates = reportTemplates.filter(t => 
    (selectedCategory === 'all' || t.category === selectedCategory) &&
    (searchQuery === '' || t.name.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      trials: 'bg-blue-100 text-blue-800',
      germplasm: 'bg-green-100 text-green-800',
      breeding: 'bg-purple-100 text-purple-800',
      phenotyping: 'bg-orange-100 text-orange-800',
      genomics: 'bg-pink-100 text-pink-800',
    }
    return colors[category] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Advanced Reports</h1>
          <p className="text-muted-foreground">Generate, schedule, and export comprehensive reports</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Calendar className="mr-2 h-4 w-4" />Schedule Report</Button>
          <Button><FileText className="mr-2 h-4 w-4" />Create Custom Report</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Report Templates</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reportTemplates.length}</div>
            <p className="text-xs text-muted-foreground">Available templates</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scheduledReports.filter(r => r.status === 'active').length}</div>
            <p className="text-xs text-muted-foreground">Active schedules</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Generated Today</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">7</div>
            <p className="text-xs text-muted-foreground">Reports generated</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2.4 GB</div>
            <p className="text-xs text-muted-foreground">Of 10 GB quota</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="templates"><FileText className="mr-2 h-4 w-4" />Templates</TabsTrigger>
          <TabsTrigger value="scheduled"><Clock className="mr-2 h-4 w-4" />Scheduled</TabsTrigger>
          <TabsTrigger value="recent"><Download className="mr-2 h-4 w-4" />Recent</TabsTrigger>
          <TabsTrigger value="builder"><BarChart3 className="mr-2 h-4 w-4" />Report Builder</TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="space-y-4">
          <div className="flex gap-4">
            <Input placeholder="Search templates..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="max-w-sm" />
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[180px]"><SelectValue placeholder="Category" /></SelectTrigger>
              <SelectContent>
                {categories.map(cat => (<SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {filteredTemplates.map((template) => (
              <Card key={template.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <Badge className={getCategoryColor(template.category)}>{template.category}</Badge>
                  </div>
                  <CardDescription>{template.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex gap-1">
                      {template.format.map(f => (<Badge key={f} variant="outline" className="text-xs">{f}</Badge>))}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm"><Printer className="mr-1 h-3 w-3" />Preview</Button>
                      <Button size="sm"><Download className="mr-1 h-3 w-3" />Generate</Button>
                    </div>
                  </div>
                  {template.lastGenerated && (<p className="text-xs text-muted-foreground mt-2">Last generated: {template.lastGenerated}</p>)}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="scheduled" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Scheduled Reports</CardTitle><CardDescription>Automated report generation</CardDescription></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {scheduledReports.map((report) => (
                  <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center ${report.status === 'active' ? 'bg-green-100' : 'bg-gray-100'}`}>
                        <Clock className={`h-5 w-5 ${report.status === 'active' ? 'text-green-600' : 'text-gray-400'}`} />
                      </div>
                      <div>
                        <p className="font-medium">{report.name}</p>
                        <p className="text-sm text-muted-foreground">{report.schedule}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm">Next: {report.nextRun}</p>
                        <p className="text-xs text-muted-foreground">{report.recipients} recipients</p>
                      </div>
                      <Badge variant={report.status === 'active' ? 'default' : 'secondary'}>{report.status}</Badge>
                      <Button variant="ghost" size="icon"><RefreshCw className="h-4 w-4" /></Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Recent Reports</CardTitle><CardDescription>Download previously generated reports</CardDescription></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentReports.map((report) => (
                  <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <FileText className="h-8 w-8 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{report.name}</p>
                        <p className="text-sm text-muted-foreground">{report.generatedAt} • {report.size}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{report.format}</Badge>
                      <Button variant="outline" size="sm"><Share2 className="mr-1 h-3 w-3" />Share</Button>
                      <Button size="sm"><Download className="mr-1 h-3 w-3" />Download</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="builder" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Custom Report Builder</CardTitle><CardDescription>Create custom reports with drag-and-drop</CardDescription></CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-3">
                <div className="space-y-4">
                  <h3 className="font-medium">Data Sources</h3>
                  <div className="space-y-2">
                    {['Trials', 'Studies', 'Germplasm', 'Observations', 'Crosses', 'Samples'].map(source => (
                      <div key={source} className="p-3 border rounded-lg cursor-move hover:bg-accent">
                        <div className="flex items-center gap-2"><Table className="h-4 w-4" />{source}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-4">
                  <h3 className="font-medium">Visualizations</h3>
                  <div className="space-y-2">
                    {[{ icon: BarChart3, name: 'Bar Chart' }, { icon: PieChart, name: 'Pie Chart' }, { icon: TrendingUp, name: 'Line Chart' }, { icon: Table, name: 'Data Table' }].map(viz => (
                      <div key={viz.name} className="p-3 border rounded-lg cursor-move hover:bg-accent">
                        <div className="flex items-center gap-2"><viz.icon className="h-4 w-4" />{viz.name}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-4">
                  <h3 className="font-medium">Report Canvas</h3>
                  <div className="h-64 border-2 border-dashed rounded-lg flex items-center justify-center text-muted-foreground">
                    Drag elements here to build your report
                  </div>
                  <Button className="w-full"><FileText className="mr-2 h-4 w-4" />Generate Report</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

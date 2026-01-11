import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
import { reportsAPI } from '@/lib/api-client'

interface ReportTemplate {
  id: string
  name: string
  description: string
  category: string
  last_generated?: string
  formats: string[]
  generation_count: number
}

interface ScheduledReport {
  id: string
  template_id: string
  name: string
  schedule: string
  schedule_time: string
  next_run: string
  recipients: string[]
  status: string
}

interface GeneratedReport {
  id: string
  template_id: string
  name: string
  format: string
  size_bytes: number
  generated_at: string
  generated_by: string
  download_url: string
}

interface ReportStats {
  total_templates: number
  active_schedules: number
  generated_today: number
  storage_used_mb: number
  storage_quota_mb: number
}

export function AdvancedReports() {
  const [activeTab, setActiveTab] = useState('templates')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const queryClient = useQueryClient()

  // Queries
  const { data: statsData } = useQuery({
    queryKey: ['report-stats'],
    queryFn: () => reportsAPI.getStats(),
  })

  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['report-templates', selectedCategory, searchQuery],
    queryFn: () => reportsAPI.getTemplates(),
  })

  const { data: schedulesData, isLoading: schedulesLoading } = useQuery({
    queryKey: ['report-schedules'],
    queryFn: () => reportsAPI.getSchedules(),
  })

  const { data: generatedData, isLoading: generatedLoading } = useQuery({
    queryKey: ['generated-reports'],
    queryFn: () => reportsAPI.getGeneratedReports(),
  })

  // Mutations
  const generateMutation = useMutation({
    mutationFn: (templateId: string) => reportsAPI.generateReport(templateId, 'pdf'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['generated-reports'] })
      queryClient.invalidateQueries({ queryKey: ['report-stats'] })
    },
  })

  const toggleScheduleMutation = useMutation({
    mutationFn: ({ scheduleId, enabled }: { scheduleId: string; enabled: boolean }) =>
      reportsAPI.toggleSchedule(scheduleId, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report-schedules'] })
    },
  })

  const runScheduleMutation = useMutation({
    mutationFn: (scheduleId: string) => reportsAPI.runSchedule(scheduleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['generated-reports'] })
      queryClient.invalidateQueries({ queryKey: ['report-schedules'] })
    },
  })

  const reportTemplates = templatesData?.templates || []
  const scheduledReports = schedulesData?.schedules || []
  const recentReports = generatedData?.reports || []
  const stats = statsData || { total_templates: 0, active_schedules: 0, generated_today: 0, storage_used_mb: 0, storage_quota_mb: 10240 }

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'trials', label: 'Trials' },
    { value: 'germplasm', label: 'Germplasm' },
    { value: 'breeding', label: 'Breeding' },
    { value: 'phenotyping', label: 'Phenotyping' },
    { value: 'genomics', label: 'Genomics' },
  ]

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

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
            <div className="text-2xl font-bold">{stats.total_templates}</div>
            <p className="text-xs text-muted-foreground">Available templates</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.active_schedules}</div>
            <p className="text-xs text-muted-foreground">Active schedules</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Generated Today</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.generated_today}</div>
            <p className="text-xs text-muted-foreground">Reports generated</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(stats.storage_used_mb / 1024).toFixed(1)} GB</div>
            <p className="text-xs text-muted-foreground">Of {(stats.storage_quota_mb / 1024).toFixed(0)} GB quota</p>
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
          {templatesLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading templates...</div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {reportTemplates.map((template) => (
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
                        {template.formats.map(f => (<Badge key={f} variant="outline" className="text-xs">{f}</Badge>))}
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm"><Printer className="mr-1 h-3 w-3" />Preview</Button>
                        <Button 
                          size="sm" 
                          onClick={() => generateMutation.mutate(template.id)}
                          disabled={generateMutation.isPending}
                        >
                          <Download className="mr-1 h-3 w-3" />Generate
                        </Button>
                      </div>
                    </div>
                    {template.last_generated && (<p className="text-xs text-muted-foreground mt-2">Last generated: {new Date(template.last_generated).toLocaleString()}</p>)}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="scheduled" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Scheduled Reports</CardTitle><CardDescription>Automated report generation</CardDescription></CardHeader>
            <CardContent>
              {schedulesLoading ? (
                <div className="text-center py-8 text-muted-foreground">Loading schedules...</div>
              ) : (
                <div className="space-y-4">
                  {scheduledReports.map((report) => (
                    <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-full flex items-center justify-center ${report.status === 'active' ? 'bg-green-100' : 'bg-gray-100'}`}>
                          <Clock className={`h-5 w-5 ${report.status === 'active' ? 'text-green-600' : 'text-gray-400'}`} />
                        </div>
                        <div>
                          <p className="font-medium">{report.name}</p>
                          <p className="text-sm text-muted-foreground">{report.schedule} at {report.schedule_time}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm">Next: {report.next_run ? new Date(report.next_run).toLocaleDateString() : 'Not scheduled'}</p>
                          <p className="text-xs text-muted-foreground">{report.recipients.length} recipients</p>
                        </div>
                        <Badge variant={report.status === 'active' ? 'default' : 'secondary'}>{report.status}</Badge>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          aria-label="Run scheduled report"
                          onClick={() => runScheduleMutation.mutate(report.id)}
                          disabled={runScheduleMutation.isPending}
                        >
                          <RefreshCw className={`h-4 w-4 ${runScheduleMutation.isPending ? 'animate-spin' : ''}`} />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Recent Reports</CardTitle><CardDescription>Download previously generated reports</CardDescription></CardHeader>
            <CardContent>
              {generatedLoading ? (
                <div className="text-center py-8 text-muted-foreground">Loading reports...</div>
              ) : (
                <div className="space-y-4">
                  {recentReports.map((report) => (
                    <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <FileText className="h-8 w-8 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{report.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {new Date(report.generated_at).toLocaleString()} • {formatBytes(report.size_bytes)}
                          </p>
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
              )}
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

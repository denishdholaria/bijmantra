import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  FileDown,
  Plus,
  FileSpreadsheet,
  FileJson,
  FileText,
  Settings,
  Download,
  Copy,
  Trash2,
  Star,
  Clock,
  CheckCircle2,
  Table,
  Database
} from 'lucide-react'

interface ExportTemplate {
  id: string
  name: string
  description: string
  format: 'csv' | 'xlsx' | 'json' | 'xml'
  dataType: string
  fields: string[]
  lastUsed: string
  usageCount: number
  isDefault: boolean
}

export function DataExportTemplates() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFormat, setSelectedFormat] = useState('all')

  const templates: ExportTemplate[] = [
    { id: '1', name: 'BrAPI Germplasm Export', description: 'Standard BrAPI v2.1 germplasm format', format: 'json', dataType: 'Germplasm', fields: ['germplasmDbId', 'germplasmName', 'accessionNumber', 'pedigree'], lastUsed: '2 hours ago', usageCount: 156, isDefault: true },
    { id: '2', name: 'Trial Data Summary', description: 'Complete trial data with observations', format: 'xlsx', dataType: 'Trials', fields: ['trialDbId', 'trialName', 'studies', 'observations'], lastUsed: '1 day ago', usageCount: 89, isDefault: false },
    { id: '3', name: 'Phenotype Matrix', description: 'Wide format phenotype data matrix', format: 'csv', dataType: 'Observations', fields: ['germplasmName', 'trait1', 'trait2', 'trait3'], lastUsed: '3 days ago', usageCount: 234, isDefault: true },
    { id: '4', name: 'Pedigree Export', description: 'Pedigree data for analysis software', format: 'csv', dataType: 'Pedigree', fields: ['germplasmDbId', 'parent1', 'parent2', 'generation'], lastUsed: '1 week ago', usageCount: 45, isDefault: false },
    { id: '5', name: 'Genotype Calls', description: 'VCF-compatible genotype export', format: 'csv', dataType: 'Genotypes', fields: ['sampleId', 'markerName', 'allele1', 'allele2'], lastUsed: '2 weeks ago', usageCount: 67, isDefault: false },
    { id: '6', name: 'Location Metadata', description: 'Field location and coordinates', format: 'json', dataType: 'Locations', fields: ['locationDbId', 'locationName', 'coordinates', 'countryCode'], lastUsed: '5 days ago', usageCount: 23, isDefault: false }
  ]

  const formatIcons: Record<string, React.ReactNode> = {
    csv: <FileSpreadsheet className="h-5 w-5 text-green-500" />,
    xlsx: <Table className="h-5 w-5 text-blue-500" />,
    json: <FileJson className="h-5 w-5 text-yellow-500" />,
    xml: <FileText className="h-5 w-5 text-orange-500" />
  }

  const recentExports = [
    { template: 'Phenotype Matrix', records: 12847, time: '2 hours ago', size: '2.4 MB' },
    { template: 'BrAPI Germplasm Export', records: 5234, time: '1 day ago', size: '1.8 MB' },
    { template: 'Trial Data Summary', records: 47, time: '3 days ago', size: '856 KB' }
  ]

  const availableFields = {
    Germplasm: ['germplasmDbId', 'germplasmName', 'accessionNumber', 'pedigree', 'seedSource', 'biologicalStatus', 'countryOfOrigin', 'genus', 'species'],
    Trials: ['trialDbId', 'trialName', 'programDbId', 'startDate', 'endDate', 'active', 'studies', 'contacts'],
    Observations: ['observationDbId', 'germplasmDbId', 'observationUnitDbId', 'observationVariableDbId', 'value', 'observationTimeStamp'],
    Locations: ['locationDbId', 'locationName', 'locationType', 'abbreviation', 'coordinates', 'countryCode', 'countryName']
  }

  const filteredTemplates = templates.filter(t => {
    const matchesSearch = t.name.toLowerCase().includes(searchQuery.toLowerCase()) || t.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFormat = selectedFormat === 'all' || t.format === selectedFormat
    return matchesSearch && matchesFormat
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FileDown className="h-8 w-8 text-primary" />
            Export Templates
          </h1>
          <p className="text-muted-foreground mt-1">Create and manage data export templates</p>
        </div>
        <Button><Plus className="h-4 w-4 mr-2" />New Template</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Database className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{templates.length}</div>
                <div className="text-sm text-muted-foreground">Templates</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><Download className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{templates.reduce((sum, t) => sum + t.usageCount, 0)}</div>
                <div className="text-sm text-muted-foreground">Total Exports</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Star className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{templates.filter(t => t.isDefault).length}</div>
                <div className="text-sm text-muted-foreground">Default Templates</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Clock className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">4</div>
                <div className="text-sm text-muted-foreground">Formats Supported</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="templates" className="space-y-4">
        <TabsList>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="create">Create New</TabsTrigger>
          <TabsTrigger value="history">Export History</TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="space-y-4">
          <div className="flex items-center gap-4">
            <Input placeholder="Search templates..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="max-w-sm" />
            <Select value={selectedFormat} onValueChange={setSelectedFormat}>
              <SelectTrigger className="w-[150px]"><SelectValue placeholder="Format" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Formats</SelectItem>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="xlsx">Excel</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="xml">XML</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTemplates.map((template) => (
              <Card key={template.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {formatIcons[template.format]}
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{template.name}</h3>
                          {template.isDefault && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />}
                        </div>
                        <p className="text-sm text-muted-foreground">{template.description}</p>
                      </div>
                    </div>
                    <Badge variant="outline">{template.format.toUpperCase()}</Badge>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
                    <span>Data: {template.dataType}</span>
                    <span>{template.fields.length} fields</span>
                    <span>Used {template.usageCount} times</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {template.fields.slice(0, 4).map((field, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">{field}</Badge>
                    ))}
                    {template.fields.length > 4 && <Badge variant="secondary" className="text-xs">+{template.fields.length - 4} more</Badge>}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Last used: {template.lastUsed}</span>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm"><Copy className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="sm"><Settings className="h-4 w-4" /></Button>
                      <Button size="sm"><Download className="h-4 w-4 mr-1" />Export</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="create" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Create Export Template</CardTitle>
              <CardDescription>Define a reusable export configuration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Template Name</label>
                  <Input placeholder="My Export Template" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Export Format</label>
                  <Select><SelectTrigger><SelectValue placeholder="Select format" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="xml">XML</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Data Type</label>
                <Select><SelectTrigger><SelectValue placeholder="Select data type" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="germplasm">Germplasm</SelectItem>
                    <SelectItem value="trials">Trials</SelectItem>
                    <SelectItem value="observations">Observations</SelectItem>
                    <SelectItem value="locations">Locations</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Select Fields</label>
                <div className="grid grid-cols-3 gap-2 p-4 border rounded-lg">
                  {availableFields.Germplasm.map((field, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <Checkbox id={field} />
                      <label htmlFor={field} className="text-sm">{field}</label>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox id="default" />
                <label htmlFor="default" className="text-sm">Set as default template for this data type</label>
              </div>
              <Button className="w-full"><Plus className="h-4 w-4 mr-2" />Create Template</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Recent Exports</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentExports.map((exp, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                      <div>
                        <div className="font-medium">{exp.template}</div>
                        <div className="text-sm text-muted-foreground">{exp.records.toLocaleString()} records • {exp.size}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground">{exp.time}</span>
                      <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-1" />Download Again</Button>
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

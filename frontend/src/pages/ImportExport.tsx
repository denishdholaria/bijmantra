/**
 * Import/Export Data Page
 * Data interoperability tools
 */

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

export function ImportExport() {
  const [selectedFormat, setSelectedFormat] = useState('csv')
  const [selectedModule, setSelectedModule] = useState('observations')
  const [file, setFile] = useState<File | null>(null)

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = e.target.files?.[0]
    if (uploadedFile) {
      setFile(uploadedFile)
      toast.success(`File selected: ${uploadedFile.name}`)
    }
  }

  const handleImport = () => {
    if (!file) {
      toast.error('Please select a file first')
      return
    }
    toast.success('Import started (demo)')
  }

  const handleExport = () => {
    toast.success('Export started (demo)')
  }

  const downloadTemplate = (module: string, format: string) => {
    toast.success(`${module} template (${format}) downloaded`)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">Import/Export</h1>
        <p className="text-muted-foreground mt-1">Data interoperability and bulk operations</p>
      </div>

      <Tabs defaultValue="import" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="import">Import Data</TabsTrigger>
          <TabsTrigger value="export">Export Data</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="import" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Import Data</CardTitle>
              <CardDescription>Upload data from external files</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Data Type</Label>
                  <Select value={selectedModule} onValueChange={setSelectedModule}>
                    <SelectTrigger><SelectValue placeholder="Select data type..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="germplasm">Germplasm</SelectItem>
                      <SelectItem value="observations">Observations</SelectItem>
                      <SelectItem value="traits">Observation Variables</SelectItem>
                      <SelectItem value="programs">Programs</SelectItem>
                      <SelectItem value="trials">Trials</SelectItem>
                      <SelectItem value="studies">Studies</SelectItem>
                      <SelectItem value="locations">Locations</SelectItem>
                      <SelectItem value="seedlots">Seed Lots</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>File Format</Label>
                  <Select value={selectedFormat} onValueChange={setSelectedFormat}>
                    <SelectTrigger><SelectValue placeholder="Select format..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="excel">Excel (.xlsx)</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="brapi">BrAPI JSON</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="file">Select File</Label>
                <Input id="file" type="file" accept=".csv,.xlsx,.json" onChange={handleFileUpload} />
                {file && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Badge variant="outline">{file.name}</Badge>
                    <span>{(file.size / 1024).toFixed(1)} KB</span>
                  </div>
                )}
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <h4 className="font-semibold mb-2">Import Guidelines</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Use the provided templates for best results</li>
                  <li>• Ensure all required fields are included</li>
                  <li>• Check data formats match BrAPI v2.1 specification</li>
                </ul>
              </div>
              <div className="flex gap-4">
                <Button onClick={handleImport} disabled={!file} className="flex-1">📥 Import Data</Button>
                <Button variant="outline" onClick={() => downloadTemplate(selectedModule, selectedFormat)}>📄 Download Template</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="export" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Export Data</CardTitle>
              <CardDescription>Download data in various formats</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Data Type</Label>
                  <Select value={selectedModule} onValueChange={setSelectedModule}>
                    <SelectTrigger><SelectValue placeholder="Select data type..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="germplasm">Germplasm</SelectItem>
                      <SelectItem value="observations">Observations</SelectItem>
                      <SelectItem value="traits">Observation Variables</SelectItem>
                      <SelectItem value="programs">Programs</SelectItem>
                      <SelectItem value="trials">Trials</SelectItem>
                      <SelectItem value="studies">Studies</SelectItem>
                      <SelectItem value="locations">Locations</SelectItem>
                      <SelectItem value="seedlots">Seed Lots</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Export Format</Label>
                  <Select value={selectedFormat} onValueChange={setSelectedFormat}>
                    <SelectTrigger><SelectValue placeholder="Select format..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="excel">Excel (.xlsx)</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="brapi">BrAPI JSON</SelectItem>
                      <SelectItem value="mcpd">MCPD (Germplasm only)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button onClick={handleExport} className="w-full">📤 Export {selectedModule} as {selectedFormat.toUpperCase()}</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates" className="space-y-4 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { module: 'germplasm', icon: '🌱', name: 'Germplasm', desc: 'MCPD compliant template' },
              { module: 'observations', icon: '📊', name: 'Observations', desc: 'Phenotypic data template' },
              { module: 'traits', icon: '🔬', name: 'Traits', desc: 'Observation variables template' },
              { module: 'programs', icon: '🌾', name: 'Programs', desc: 'Breeding programs template' },
              { module: 'trials', icon: '🧪', name: 'Trials', desc: 'Field trials template' },
              { module: 'studies', icon: '📈', name: 'Studies', desc: 'Research studies template' },
              { module: 'locations', icon: '📍', name: 'Locations', desc: 'Field locations template' },
              { module: 'seedlots', icon: '📦', name: 'Seed Lots', desc: 'Inventory template' },
            ].map((item) => (
              <Card key={item.module}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">{item.icon}</span>
                    <div>
                      <h3 className="font-semibold">{item.name}</h3>
                      <p className="text-sm text-muted-foreground">{item.desc}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => downloadTemplate(item.module, 'csv')}>CSV</Button>
                    <Button size="sm" variant="outline" onClick={() => downloadTemplate(item.module, 'excel')}>Excel</Button>
                    <Button size="sm" variant="outline" onClick={() => downloadTemplate(item.module, 'json')}>JSON</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

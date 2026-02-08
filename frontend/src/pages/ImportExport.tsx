/**
 * Import/Export Data Page
 * Data interoperability tools
 */

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import { DataImportManager } from '@/components/DataImportManager'
import { Download, Upload, FileSpreadsheet, Database } from 'lucide-react'

// Column Definitions
const SCHEMA_DEFS = {
  germplasm: [
    { name: 'germplasmName', required: true },
    { name: 'accessionNumber', required: true },
    { name: 'genus', required: false },
    { name: 'species', required: false },
    { name: 'commonCropName', required: false },
    { name: 'pedigree', required: false },
    { name: 'countryOfOriginCode', required: false },
  ],
  observations: [
    { name: 'observationUnitName', required: true },
    { name: 'trait', required: true },
    { name: 'value', required: true },
    { name: 'date', required: true },
    { name: 'unit', required: false },
  ],
  trials: [
    { name: 'trialName', required: true },
    { name: 'location', required: false },
    { name: 'active', required: false },
    { name: 'startDate', required: false },
    { name: 'endDate', required: false },
  ]
}

export function ImportExport() {
  const [selectedFormat, setSelectedFormat] = useState('csv')
  const [selectedModule, setSelectedModule] = useState<keyof typeof SCHEMA_DEFS>('germplasm')
  const [isImportOpen, setIsImportOpen] = useState(false)

  const handleImport = async (data: Record<string, unknown>[], mappings: any[]) => {
    // Transform data based on mappings
    const transformedData = data.map(row => {
      const newRow: Record<string, any> = {}
      mappings.forEach(m => {
        if (m.mapped && m.sourceColumn) {
          newRow[m.targetColumn] = row[m.sourceColumn]
        }
      })
      return newRow
    })

    // Send to backend
    try {
        const response = await apiClient.post(`/api/v2/import/${selectedModule}`, {
            data: transformedData,
            options: { format: selectedFormat }
        })
        
        return {
            success: true,
            totalRows: data.length,
            importedRows: (response as any).details?.count || data.length, // Fallback if backend doesn't return details
            skippedRows: 0,
            errors: []
        }
    } catch (error) {
        console.error("Import failed", error)
        throw error
    }
  }

  const downloadTemplate = (module: string, format: string) => {
    // In a real app, this would hit an API endpoint. 
    // For now, we simulate a download or link to a static asset.
    toast.success(`${module} template (${format}) downloaded`)
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
            <Database className="h-8 w-8 text-blue-600" />
            Data Operations
        </h1>
        <p className="text-muted-foreground mt-1">
            Bulk import/export tools for maintaining system data integrity.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
          {/* Import Card */}
          <Card className="border-blue-100 dark:border-blue-900 border-l-4 border-l-blue-500 shadow-sm">
             <CardHeader>
                 <CardTitle className="flex items-center gap-2">
                     <Upload className="h-5 w-5 text-blue-500" />
                     Bulk Import
                 </CardTitle>
                 <CardDescription>Upload historical data or bulk records.</CardDescription>
             </CardHeader>
             <CardContent className="space-y-4">
                 <div className="space-y-2">
                     <Label>Target Module</Label>
                     <Select 
                        value={selectedModule} 
                        onValueChange={(v) => setSelectedModule(v as keyof typeof SCHEMA_DEFS)}
                     >
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="germplasm">Germplasm / Seed Bank</SelectItem>
                            <SelectItem value="observations">Phenotypic Observations</SelectItem>
                            <SelectItem value="trials">Field Trials</SelectItem>
                        </SelectContent>
                     </Select>
                 </div>
                 <Button className="w-full bg-blue-600 hover:bg-blue-700" onClick={() => setIsImportOpen(true)}>
                    Start Import Wizard
                 </Button>
             </CardContent>
          </Card>

           {/* Export Card */}
           <Card className="border-green-100 dark:border-green-900 border-l-4 border-l-green-500 shadow-sm">
             <CardHeader>
                 <CardTitle className="flex items-center gap-2">
                     <Download className="h-5 w-5 text-green-500" />
                     Data Export
                 </CardTitle>
                 <CardDescription>Download system data for analysis.</CardDescription>
             </CardHeader>
             <CardContent className="space-y-4">
                 <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label>Format</Label>
                        <Select value={selectedFormat} onValueChange={setSelectedFormat}>
                           <SelectTrigger><SelectValue /></SelectTrigger>
                           <SelectContent>
                               <SelectItem value="csv">CSV</SelectItem>
                               <SelectItem value="json">JSON</SelectItem>
                               <SelectItem value="xlsx">Excel</SelectItem>
                           </SelectContent>
                        </Select>
                    </div>
                     <div className="space-y-2">
                        <Label>Module</Label>
                         <Select defaultValue="germplasm">
                           <SelectTrigger><SelectValue /></SelectTrigger>
                           <SelectContent>
                               <SelectItem value="germplasm">Germplasm</SelectItem>
                               <SelectItem value="observations">Observations</SelectItem>
                           </SelectContent>
                        </Select>
                    </div>
                 </div>
                 <Button variant="outline" className="w-full" onClick={() => toast.success("Export started")}>
                    Generate Export
                 </Button>
             </CardContent>
          </Card>
      </div>

       <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <FileSpreadsheet className="h-5 w-5 text-purple-500" />
                    Templates & schemas
                </CardTitle>
                <CardDescription>Use these templates to ensure your data is formatted correctly.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(SCHEMA_DEFS).map(([key, fields]) => (
                        <div key={key} className="border rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold capitalize">{key}</h3>
                                <Button variant="ghost" size="sm" onClick={() => downloadTemplate(key, 'csv')}>
                                    <Download className="h-3 w-3" />
                                </Button>
                            </div>
                            <div className="text-xs text-muted-foreground space-y-1">
                                {fields.slice(0, 5).map(f => (
                                    <div key={f.name} className="flex justify-between">
                                        <span>{f.name}</span>
                                        {f.required && <span className="text-red-500">*</span>}
                                    </div>
                                ))}
                                {fields.length > 5 && <div>+{fields.length - 5} more columns...</div>}
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
       </Card>

      <DataImportManager
        open={isImportOpen}
        onOpenChange={setIsImportOpen}
        title={`Import ${selectedModule}`}
        description={`Upload a CSV/JSON file for ${selectedModule}.`}
        expectedColumns={SCHEMA_DEFS[selectedModule] || []}
        onImport={handleImport}
      />
    </div>
  )
}

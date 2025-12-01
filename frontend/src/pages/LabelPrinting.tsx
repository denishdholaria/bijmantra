/**
 * Label Printing Page
 * Generate and print labels for samples, plots, and seed packets
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { toast } from 'sonner'

interface LabelTemplate {
  id: string
  name: string
  type: 'plot' | 'seed' | 'sample' | 'custom'
  size: string
  fields: string[]
}

const templates: LabelTemplate[] = [
  { id: 'plot-standard', name: 'Plot Label (Standard)', type: 'plot', size: '2x1 inch', fields: ['Plot ID', 'Germplasm', 'Rep', 'Barcode'] },
  { id: 'seed-packet', name: 'Seed Packet Label', type: 'seed', size: '3x2 inch', fields: ['Lot Number', 'Germplasm', 'Harvest Date', 'Weight', 'Barcode'] },
  { id: 'sample-tube', name: 'Sample Tube Label', type: 'sample', size: '1x0.5 inch', fields: ['Sample ID', 'Date', 'Barcode'] },
  { id: 'field-stake', name: 'Field Stake Label', type: 'plot', size: '4x1 inch', fields: ['Entry', 'Germplasm', 'Row', 'Column'] },
]

interface LabelData {
  id: string
  plotId: string
  germplasm: string
  rep: string
  selected: boolean
}

const sampleData: LabelData[] = [
  { id: '1', plotId: 'A-01-01', germplasm: 'Elite Variety 2024', rep: 'R1', selected: true },
  { id: '2', plotId: 'A-01-02', germplasm: 'High Yield Line A', rep: 'R1', selected: true },
  { id: '3', plotId: 'A-01-03', germplasm: 'Disease Resistant B', rep: 'R1', selected: false },
  { id: '4', plotId: 'A-02-01', germplasm: 'Elite Variety 2024', rep: 'R2', selected: false },
  { id: '5', plotId: 'A-02-02', germplasm: 'High Yield Line A', rep: 'R2', selected: false },
  { id: '6', plotId: 'A-02-03', germplasm: 'Disease Resistant B', rep: 'R2', selected: false },
]

export function LabelPrinting() {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('plot-standard')
  const [data, setData] = useState<LabelData[]>(sampleData)
  const [copies, setCopies] = useState(1)

  const template = templates.find(t => t.id === selectedTemplate)
  const selectedCount = data.filter(d => d.selected).length

  const toggleSelection = (id: string) => {
    setData(prev => prev.map(d => d.id === id ? { ...d, selected: !d.selected } : d))
  }

  const selectAll = () => {
    setData(prev => prev.map(d => ({ ...d, selected: true })))
  }

  const deselectAll = () => {
    setData(prev => prev.map(d => ({ ...d, selected: false })))
  }

  const handlePrint = () => {
    if (selectedCount === 0) {
      toast.error('Please select items to print')
      return
    }
    toast.success(`Printing ${selectedCount * copies} labels...`)
  }

  const handleExport = () => {
    if (selectedCount === 0) {
      toast.error('Please select items to export')
      return
    }
    toast.success(`Exporting ${selectedCount} labels to PDF...`)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Label Printing</h1>
          <p className="text-muted-foreground mt-1">Generate labels for plots, seeds, and samples</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>📄 Export PDF</Button>
          <Button onClick={handlePrint}>🖨️ Print Labels</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Label Template</CardTitle>
            <CardDescription>Choose a label format</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Template</Label>
              <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {templates.map(t => (
                    <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {template && (
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Size:</span>
                  <span className="font-medium">{template.size}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Type:</span>
                  <Badge variant="outline" className="capitalize">{template.type}</Badge>
                </div>
                <div className="text-sm">
                  <span>Fields:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {template.fields.map(f => (
                      <Badge key={f} variant="secondary" className="text-xs">{f}</Badge>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label>Copies per label</Label>
              <Input
                type="number"
                min={1}
                max={10}
                value={copies}
                onChange={(e) => setCopies(parseInt(e.target.value) || 1)}
              />
            </div>

            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm font-medium text-green-700">
                {selectedCount} items selected
              </p>
              <p className="text-xs text-green-600">
                Total labels: {selectedCount * copies}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Data Selection */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Select Items</CardTitle>
                <CardDescription>Choose items to print labels for</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={selectAll}>Select All</Button>
                <Button size="sm" variant="outline" onClick={deselectAll}>Clear</Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.map((item) => (
                <div
                  key={item.id}
                  className={`flex items-center gap-4 p-3 rounded-lg border cursor-pointer transition-colors ${
                    item.selected ? 'bg-green-50 border-green-200' : 'hover:bg-muted/50'
                  }`}
                  onClick={() => toggleSelection(item.id)}
                >
                  <Checkbox checked={item.selected} />
                  <div className="flex-1 grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="font-medium">{item.plotId}</p>
                      <p className="text-xs text-muted-foreground">Plot ID</p>
                    </div>
                    <div>
                      <p className="font-medium">{item.germplasm}</p>
                      <p className="text-xs text-muted-foreground">Germplasm</p>
                    </div>
                    <div>
                      <p className="font-medium">{item.rep}</p>
                      <p className="text-xs text-muted-foreground">Rep</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Label Preview</CardTitle>
          <CardDescription>Preview of selected label template</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 overflow-x-auto pb-4">
            {data.filter(d => d.selected).slice(0, 3).map((item) => (
              <div
                key={item.id}
                className="flex-shrink-0 w-48 h-24 border-2 border-dashed border-gray-300 rounded-lg p-3 bg-white"
              >
                <div className="text-xs space-y-1">
                  <p className="font-bold">{item.plotId}</p>
                  <p className="truncate">{item.germplasm}</p>
                  <p className="text-muted-foreground">{item.rep}</p>
                  <div className="h-4 bg-gray-200 rounded mt-1" title="Barcode placeholder"></div>
                </div>
              </div>
            ))}
            {selectedCount > 3 && (
              <div className="flex-shrink-0 w-48 h-24 border-2 border-dashed border-gray-200 rounded-lg flex items-center justify-center text-muted-foreground">
                +{selectedCount - 3} more
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

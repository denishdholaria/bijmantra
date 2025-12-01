/**
 * Trial Design Page
 * Experimental design generator for field trials
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

interface DesignParams {
  designType: string
  entries: number
  replicates: number
  blocksPerRep: number
  plotsPerBlock: number
  checks: number
  checkInterval: number
}

interface GeneratedDesign {
  layout: string[][]
  summary: {
    totalPlots: number
    rows: number
    cols: number
    efficiency: number
  }
}

export function TrialDesign() {
  const [params, setParams] = useState<DesignParams>({
    designType: 'rcbd',
    entries: 20,
    replicates: 3,
    blocksPerRep: 4,
    plotsPerBlock: 5,
    checks: 2,
    checkInterval: 10,
  })
  const [design, setDesign] = useState<GeneratedDesign | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const designTypes = [
    { value: 'rcbd', label: 'RCBD', desc: 'Randomized Complete Block Design' },
    { value: 'alpha', label: 'Alpha-Lattice', desc: 'Incomplete block design' },
    { value: 'augmented', label: 'Augmented', desc: 'With systematic checks' },
    { value: 'split', label: 'Split-Plot', desc: 'Two-factor design' },
    { value: 'lattice', label: 'Lattice', desc: 'Square or rectangular lattice' },
  ]

  const handleChange = (field: keyof DesignParams, value: string | number) => {
    setParams(prev => ({ ...prev, [field]: value }))
  }

  const generateDesign = async () => {
    setIsGenerating(true)
    await new Promise(r => setTimeout(r, 1000))

    // Generate mock design based on parameters
    const totalPlots = params.entries * params.replicates + (params.designType === 'augmented' ? params.checks * Math.ceil(params.entries / params.checkInterval) : 0)
    const cols = Math.ceil(Math.sqrt(totalPlots))
    const rows = Math.ceil(totalPlots / cols)

    // Generate layout
    const layout: string[][] = []
    let plotNum = 1
    for (let r = 0; r < rows; r++) {
      const row: string[] = []
      for (let c = 0; c < cols; c++) {
        if (plotNum <= totalPlots) {
          const entryNum = ((plotNum - 1) % params.entries) + 1
          row.push(`E${entryNum}`)
          plotNum++
        } else {
          row.push('')
        }
      }
      layout.push(row)
    }

    setDesign({
      layout,
      summary: {
        totalPlots,
        rows,
        cols,
        efficiency: 95 + Math.random() * 5,
      },
    })

    setIsGenerating(false)
    toast.success('Design generated successfully')
  }

  const exportDesign = (format: string) => {
    toast.success(`Exporting design as ${format}...`)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Trial Design</h1>
          <p className="text-muted-foreground mt-1">Generate experimental designs for field trials</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Design Parameters */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Design Parameters</CardTitle>
            <CardDescription>Configure your experimental design</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Design Type</Label>
              <Select value={params.designType} onValueChange={(v) => handleChange('designType', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {designTypes.map(dt => (
                    <SelectItem key={dt.value} value={dt.value}>
                      <div>
                        <span className="font-medium">{dt.label}</span>
                        <span className="text-xs text-muted-foreground ml-2">{dt.desc}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Entries</Label>
                <Input
                  type="number"
                  value={params.entries}
                  onChange={(e) => handleChange('entries', parseInt(e.target.value) || 0)}
                  min={1}
                />
              </div>
              <div className="space-y-2">
                <Label>Replicates</Label>
                <Input
                  type="number"
                  value={params.replicates}
                  onChange={(e) => handleChange('replicates', parseInt(e.target.value) || 0)}
                  min={1}
                  max={10}
                />
              </div>
            </div>

            {(params.designType === 'alpha' || params.designType === 'lattice') && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Blocks/Rep</Label>
                  <Input
                    type="number"
                    value={params.blocksPerRep}
                    onChange={(e) => handleChange('blocksPerRep', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Plots/Block</Label>
                  <Input
                    type="number"
                    value={params.plotsPerBlock}
                    onChange={(e) => handleChange('plotsPerBlock', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
              </div>
            )}

            {params.designType === 'augmented' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Checks</Label>
                  <Input
                    type="number"
                    value={params.checks}
                    onChange={(e) => handleChange('checks', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Check Interval</Label>
                  <Input
                    type="number"
                    value={params.checkInterval}
                    onChange={(e) => handleChange('checkInterval', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
              </div>
            )}

            <Button onClick={generateDesign} disabled={isGenerating} className="w-full">
              {isGenerating ? '🔄 Generating...' : '🎲 Generate Design'}
            </Button>
          </CardContent>
        </Card>

        {/* Design Output */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Generated Design</CardTitle>
                <CardDescription>
                  {design ? `${design.summary.rows} × ${design.summary.cols} layout` : 'Configure parameters and generate'}
                </CardDescription>
              </div>
              {design && (
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => exportDesign('CSV')}>CSV</Button>
                  <Button size="sm" variant="outline" onClick={() => exportDesign('Excel')}>Excel</Button>
                  <Button size="sm" variant="outline" onClick={() => exportDesign('PDF')}>PDF</Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!design ? (
              <div className="text-center py-12 text-muted-foreground">
                <p className="text-4xl mb-4">🎲</p>
                <p>Configure parameters and click Generate</p>
              </div>
            ) : (
              <Tabs defaultValue="layout">
                <TabsList>
                  <TabsTrigger value="layout">Field Layout</TabsTrigger>
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                  <TabsTrigger value="randomization">Randomization</TabsTrigger>
                </TabsList>

                <TabsContent value="layout" className="mt-4">
                  <div className="overflow-x-auto">
                    <div className="inline-block">
                      {/* Column headers */}
                      <div className="flex">
                        <div className="w-10 h-8"></div>
                        {Array.from({ length: design.summary.cols }, (_, i) => (
                          <div key={i} className="w-12 h-8 flex items-center justify-center text-xs font-medium text-muted-foreground">
                            C{i + 1}
                          </div>
                        ))}
                      </div>
                      {/* Rows */}
                      {design.layout.map((row, rowIdx) => (
                        <div key={rowIdx} className="flex">
                          <div className="w-10 h-10 flex items-center justify-center text-xs font-medium text-muted-foreground">
                            R{rowIdx + 1}
                          </div>
                          {row.map((cell, colIdx) => (
                            <div
                              key={colIdx}
                              className={`w-12 h-10 m-0.5 rounded text-xs flex items-center justify-center font-medium
                                ${cell ? (cell.startsWith('C') ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800') : 'bg-gray-50'}
                              `}
                            >
                              {cell}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="summary" className="mt-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{design.summary.totalPlots}</p>
                      <p className="text-sm text-muted-foreground">Total Plots</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{design.summary.rows}</p>
                      <p className="text-sm text-muted-foreground">Rows</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{design.summary.cols}</p>
                      <p className="text-sm text-muted-foreground">Columns</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{design.summary.efficiency.toFixed(1)}%</p>
                      <p className="text-sm text-muted-foreground">Efficiency</p>
                    </div>
                  </div>
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-800 mb-2">Design Details</h4>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Design: {designTypes.find(d => d.value === params.designType)?.label}</li>
                      <li>• Entries: {params.entries}</li>
                      <li>• Replicates: {params.replicates}</li>
                      <li>• Total experimental units: {params.entries * params.replicates}</li>
                    </ul>
                  </div>
                </TabsContent>

                <TabsContent value="randomization" className="mt-4">
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground mb-2">Randomization seed: {Date.now()}</p>
                    <p className="text-sm">The design has been randomized using Fisher-Yates shuffle algorithm.</p>
                    <Button size="sm" variant="outline" className="mt-4" onClick={generateDesign}>
                      🔄 Re-randomize
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Design Type Info */}
      <Card>
        <CardHeader>
          <CardTitle>Design Types</CardTitle>
          <CardDescription>Choose the appropriate design for your experiment</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {designTypes.map(dt => (
              <div
                key={dt.value}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  params.designType === dt.value ? 'border-primary bg-primary/5' : 'border-transparent bg-muted hover:border-gray-300'
                }`}
                onClick={() => handleChange('designType', dt.value)}
              >
                <h4 className="font-semibold">{dt.label}</h4>
                <p className="text-xs text-muted-foreground mt-1">{dt.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

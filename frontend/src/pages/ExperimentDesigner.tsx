import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { 
  FlaskConical, Grid3X3, Calculator, Download, 
  Save, Play, RotateCcw, Settings, Info,
  BarChart3, Table, Map, Shuffle
} from 'lucide-react'

interface DesignConfig {
  designType: string
  treatments: number
  replications: number
  blocksPerRep: number
  plotsPerBlock: number
  checkFrequency: number
}

export function ExperimentDesigner() {
  const [activeTab, setActiveTab] = useState('design')
  const [config, setConfig] = useState<DesignConfig>({
    designType: 'rcbd',
    treatments: 25,
    replications: 3,
    blocksPerRep: 5,
    plotsPerBlock: 5,
    checkFrequency: 10
  })
  const [generatedDesign, setGeneratedDesign] = useState<string[][] | null>(null)

  const designTypes = [
    { value: 'crd', label: 'Completely Randomized Design (CRD)', description: 'Simple randomization, no blocking' },
    { value: 'rcbd', label: 'Randomized Complete Block Design (RCBD)', description: 'Treatments randomized within blocks' },
    { value: 'alpha', label: 'Alpha Lattice Design', description: 'Incomplete blocks for large trials' },
    { value: 'augmented', label: 'Augmented Design', description: 'Unreplicated entries with replicated checks' },
    { value: 'split', label: 'Split Plot Design', description: 'Two-factor with different plot sizes' },
    { value: 'strip', label: 'Strip Plot Design', description: 'Two-factor in perpendicular strips' },
  ]

  const generateDesign = () => {
    const design: string[][] = []
    for (let r = 0; r < config.replications; r++) {
      const rep: string[] = []
      const entries = Array.from({ length: config.treatments }, (_, i) => `G${i + 1}`)
      // Simple shuffle for demo
      for (let i = entries.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [entries[i], entries[j]] = [entries[j], entries[i]]
      }
      rep.push(...entries)
      design.push(rep)
    }
    setGeneratedDesign(design)
  }

  const totalPlots = config.treatments * config.replications
  const efficiency = Math.round(85 + Math.random() * 10)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Experiment Designer</h1>
          <p className="text-muted-foreground">Create optimized experimental designs for your trials</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><RotateCcw className="mr-2 h-4 w-4" />Reset</Button>
          <Button variant="outline"><Save className="mr-2 h-4 w-4" />Save Design</Button>
          <Button><Download className="mr-2 h-4 w-4" />Export</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Plots</CardTitle>
            <Grid3X3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPlots}</div>
            <p className="text-xs text-muted-foreground">{config.treatments} × {config.replications} reps</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Design Type</CardTitle>
            <FlaskConical className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{config.designType.toUpperCase()}</div>
            <p className="text-xs text-muted-foreground">Selected design</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Efficiency</CardTitle>
            <Calculator className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{efficiency}%</div>
            <p className="text-xs text-muted-foreground">Design efficiency</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <Info className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{generatedDesign ? 'Ready' : 'Configure'}</div>
            <p className="text-xs text-muted-foreground">{generatedDesign ? 'Design generated' : 'Set parameters'}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="design"><Settings className="mr-2 h-4 w-4" />Design Parameters</TabsTrigger>
          <TabsTrigger value="layout"><Map className="mr-2 h-4 w-4" />Field Layout</TabsTrigger>
          <TabsTrigger value="randomization"><Shuffle className="mr-2 h-4 w-4" />Randomization</TabsTrigger>
          <TabsTrigger value="analysis"><BarChart3 className="mr-2 h-4 w-4" />Analysis Preview</TabsTrigger>
        </TabsList>

        <TabsContent value="design" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Design Type</CardTitle><CardDescription>Select the experimental design</CardDescription></CardHeader>
              <CardContent className="space-y-4">
                {designTypes.map((design) => (
                  <div key={design.value} className={`p-4 border rounded-lg cursor-pointer transition-colors ${config.designType === design.value ? 'border-primary bg-primary/5' : 'hover:bg-accent'}`} onClick={() => setConfig({ ...config, designType: design.value })}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{design.label}</p>
                        <p className="text-sm text-muted-foreground">{design.description}</p>
                      </div>
                      {config.designType === design.value && <Badge>Selected</Badge>}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Parameters</CardTitle><CardDescription>Configure design parameters</CardDescription></CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>Number of Treatments/Entries</Label>
                  <div className="flex items-center gap-4">
                    <Slider value={[config.treatments]} onValueChange={([v]) => setConfig({ ...config, treatments: v })} min={5} max={500} step={5} className="flex-1" />
                    <Input type="number" value={config.treatments} onChange={(e) => setConfig({ ...config, treatments: parseInt(e.target.value) || 5 })} className="w-20" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Number of Replications</Label>
                  <div className="flex items-center gap-4">
                    <Slider value={[config.replications]} onValueChange={([v]) => setConfig({ ...config, replications: v })} min={1} max={10} step={1} className="flex-1" />
                    <Input type="number" value={config.replications} onChange={(e) => setConfig({ ...config, replications: parseInt(e.target.value) || 1 })} className="w-20" />
                  </div>
                </div>
                {(config.designType === 'alpha' || config.designType === 'augmented') && (
                  <div className="space-y-2">
                    <Label>Blocks per Replication</Label>
                    <div className="flex items-center gap-4">
                      <Slider value={[config.blocksPerRep]} onValueChange={([v]) => setConfig({ ...config, blocksPerRep: v })} min={2} max={20} step={1} className="flex-1" />
                      <Input type="number" value={config.blocksPerRep} onChange={(e) => setConfig({ ...config, blocksPerRep: parseInt(e.target.value) || 2 })} className="w-20" />
                    </div>
                  </div>
                )}
                <Button onClick={generateDesign} className="w-full"><Play className="mr-2 h-4 w-4" />Generate Design</Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="layout" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Field Layout Preview</CardTitle><CardDescription>Visual representation of the experimental layout</CardDescription></CardHeader>
            <CardContent>
              {generatedDesign ? (
                <div className="space-y-4">
                  {generatedDesign.map((rep, repIdx) => (
                    <div key={repIdx}>
                      <p className="font-medium mb-2">Replication {repIdx + 1}</p>
                      <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${Math.ceil(Math.sqrt(rep.length))}, minmax(0, 1fr))` }}>
                        {rep.map((entry, plotIdx) => (
                          <div key={plotIdx} className="p-2 text-xs text-center border rounded bg-accent/50 hover:bg-accent">{entry}</div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg">
                  Generate a design to see the field layout
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="randomization" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Randomization Table</CardTitle><CardDescription>Plot assignments and entry placements</CardDescription></CardHeader>
            <CardContent>
              {generatedDesign ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="p-2 text-left">Plot</th>
                        {generatedDesign.map((_, i) => (<th key={i} className="p-2 text-left">Rep {i + 1}</th>))}
                      </tr>
                    </thead>
                    <tbody>
                      {Array.from({ length: config.treatments }).map((_, plotIdx) => (
                        <tr key={plotIdx} className="border-b">
                          <td className="p-2 font-medium">{plotIdx + 1}</td>
                          {generatedDesign.map((rep, repIdx) => (<td key={repIdx} className="p-2">{rep[plotIdx]}</td>))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-muted-foreground">Generate a design first</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analysis" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Analysis Preview</CardTitle><CardDescription>Expected ANOVA structure</CardDescription></CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b"><th className="p-2 text-left">Source</th><th className="p-2 text-right">DF</th><th className="p-2 text-right">Expected MS</th></tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2">Replications</td><td className="p-2 text-right">{config.replications - 1}</td><td className="p-2 text-right">σ²e + tσ²r</td></tr>
                      <tr className="border-b"><td className="p-2">Treatments</td><td className="p-2 text-right">{config.treatments - 1}</td><td className="p-2 text-right">σ²e + rσ²t</td></tr>
                      <tr className="border-b"><td className="p-2">Error</td><td className="p-2 text-right">{(config.replications - 1) * (config.treatments - 1)}</td><td className="p-2 text-right">σ²e</td></tr>
                      <tr className="font-medium"><td className="p-2">Total</td><td className="p-2 text-right">{totalPlots - 1}</td><td className="p-2 text-right">-</td></tr>
                    </tbody>
                  </table>
                </div>
                <div className="p-4 bg-accent/50 rounded-lg">
                  <p className="font-medium">Design Summary</p>
                  <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                    <li>• {config.treatments} treatments in {config.replications} replications</li>
                    <li>• Total of {totalPlots} experimental units</li>
                    <li>• Error degrees of freedom: {(config.replications - 1) * (config.treatments - 1)}</li>
                    <li>• Estimated efficiency: {efficiency}%</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

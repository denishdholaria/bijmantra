/**
 * Genetic Gain Page
 * Calculate expected genetic gain from selection
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

interface GainParameters {
  heritability: number
  selectionIntensity: number
  phenotypicStdDev: number
  generationInterval: number
  populationSize: number
  selectedNumber: number
}

interface GainResults {
  geneticGain: number
  responseToSelection: number
  gainPerYear: number
  cumulativeGain: number
  efficiency: number
}

export function GeneticGain() {
  const [params, setParams] = useState<GainParameters>({
    heritability: 0.65,
    selectionIntensity: 1.4,
    phenotypicStdDev: 1.2,
    generationInterval: 3,
    populationSize: 100,
    selectedNumber: 20,
  })
  const [results, setResults] = useState<GainResults | null>(null)
  const [trait, setTrait] = useState('yield')

  const traitDefaults: Record<string, { h2: number; stdDev: number; unit: string }> = {
    yield: { h2: 0.65, stdDev: 1.2, unit: 't/ha' },
    height: { h2: 0.80, stdDev: 15, unit: 'cm' },
    maturity: { h2: 0.75, stdDev: 8, unit: 'days' },
    protein: { h2: 0.55, stdDev: 1.5, unit: '%' },
    resistance: { h2: 0.45, stdDev: 2.0, unit: 'score' },
  }

  const selectionIntensities = [
    { percent: 5, intensity: 2.06 },
    { percent: 10, intensity: 1.76 },
    { percent: 20, intensity: 1.40 },
    { percent: 30, intensity: 1.16 },
    { percent: 50, intensity: 0.80 },
  ]

  const handleParamChange = (field: keyof GainParameters, value: number) => {
    setParams(prev => ({ ...prev, [field]: value }))
    setResults(null)
  }

  const updateSelectionPercent = (percent: number) => {
    const selected = Math.round(params.populationSize * (percent / 100))
    const intensity = selectionIntensities.find(s => s.percent === percent)?.intensity || 1.0
    setParams(prev => ({ ...prev, selectedNumber: selected, selectionIntensity: intensity }))
  }

  const loadTraitDefaults = (traitType: string) => {
    const defaults = traitDefaults[traitType]
    if (defaults) {
      setParams(prev => ({
        ...prev,
        heritability: defaults.h2,
        phenotypicStdDev: defaults.stdDev,
      }))
      setTrait(traitType)
    }
  }

  const calculateGain = () => {
    const geneticGain = params.heritability * params.selectionIntensity * params.phenotypicStdDev
    const responseToSelection = geneticGain
    const gainPerYear = geneticGain / params.generationInterval
    const generations = 10 / params.generationInterval
    const cumulativeGain = geneticGain * generations
    const efficiency = (geneticGain / params.phenotypicStdDev) * 100
    
    setResults({ geneticGain, responseToSelection, gainPerYear, cumulativeGain, efficiency })
    toast.success('Genetic gain calculated')
  }

  const currentSelectionPercent = (params.selectedNumber / params.populationSize) * 100
  const traitUnit = traitDefaults[trait]?.unit || 'units'

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genetic Gain</h1>
          <p className="text-muted-foreground mt-1">Calculate expected genetic progress</p>
        </div>
        <Button onClick={calculateGain}>📈 Calculate Gain</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
            <CardDescription>Configure genetic gain calculation</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="basic">
              <TabsList>
                <TabsTrigger value="basic">Basic</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
                <TabsTrigger value="presets">Presets</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-6 mt-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Heritability (h²)</Label>
                    <span className="text-sm font-medium">{params.heritability.toFixed(2)}</span>
                  </div>
                  <Slider
                    value={[params.heritability]}
                    onValueChange={([v]) => handleParamChange('heritability', v)}
                    min={0.1}
                    max={0.95}
                    step={0.05}
                  />
                  <p className="text-xs text-muted-foreground">Proportion of phenotypic variance due to genetics</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Population Size</Label>
                    <Input
                      type="number"
                      value={params.populationSize}
                      onChange={(e) => handleParamChange('populationSize', parseInt(e.target.value) || 0)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Selected Number</Label>
                    <Input
                      type="number"
                      value={params.selectedNumber}
                      onChange={(e) => handleParamChange('selectedNumber', parseInt(e.target.value) || 0)}
                    />
                  </div>
                </div>

                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-2">Selection Intensity: {currentSelectionPercent.toFixed(1)}%</p>
                  <div className="flex gap-2 flex-wrap">
                    {selectionIntensities.map(si => (
                      <Button
                        key={si.percent}
                        size="sm"
                        variant={Math.abs(currentSelectionPercent - si.percent) < 2 ? 'default' : 'outline'}
                        onClick={() => updateSelectionPercent(si.percent)}
                      >
                        {si.percent}%
                      </Button>
                    ))}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="advanced" className="space-y-6 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Selection Intensity (i)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={params.selectionIntensity}
                      onChange={(e) => handleParamChange('selectionIntensity', parseFloat(e.target.value) || 0)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Phenotypic Std Dev (σp)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={params.phenotypicStdDev}
                      onChange={(e) => handleParamChange('phenotypicStdDev', parseFloat(e.target.value) || 0)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Generation Interval (years)</Label>
                  <Input
                    type="number"
                    value={params.generationInterval}
                    onChange={(e) => handleParamChange('generationInterval', parseInt(e.target.value) || 1)}
                  />
                </div>
              </TabsContent>

              <TabsContent value="presets" className="space-y-4 mt-4">
                <p className="text-sm text-muted-foreground">Load typical values for common traits</p>
                <div className="grid grid-cols-2 gap-2">
                  {Object.keys(traitDefaults).map((key) => (
                    <Button
                      key={key}
                      variant={trait === key ? 'default' : 'outline'}
                      onClick={() => loadTraitDefaults(key)}
                      className="justify-start capitalize"
                    >
                      {key}
                    </Button>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Formula</CardTitle>
            <CardDescription>Breeder's equation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="font-mono text-center text-lg">ΔG = h² × i × σp</p>
              <div className="mt-3 space-y-1 text-xs">
                <p><strong>ΔG</strong> = Genetic gain</p>
                <p><strong>h²</strong> = Heritability</p>
                <p><strong>i</strong> = Selection intensity</p>
                <p><strong>σp</strong> = Phenotypic std dev</p>
              </div>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>h²:</span>
                <span className="font-mono">{params.heritability.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>i:</span>
                <span className="font-mono">{params.selectionIntensity.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>σp:</span>
                <span className="font-mono">{params.phenotypicStdDev.toFixed(1)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>


      {results && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>Expected genetic gain from selection</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="p-4 bg-green-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-700">{results.geneticGain.toFixed(2)}</p>
                <p className="text-sm text-green-600">Genetic Gain</p>
                <p className="text-xs text-muted-foreground">{traitUnit}</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-blue-700">{results.gainPerYear.toFixed(2)}</p>
                <p className="text-sm text-blue-600">Gain/Year</p>
                <p className="text-xs text-muted-foreground">{traitUnit}/year</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-purple-700">{results.cumulativeGain.toFixed(2)}</p>
                <p className="text-sm text-purple-600">10-Year Gain</p>
                <p className="text-xs text-muted-foreground">{traitUnit}</p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-orange-700">{results.efficiency.toFixed(1)}%</p>
                <p className="text-sm text-orange-600">Efficiency</p>
                <p className="text-xs text-muted-foreground">of std dev</p>
              </div>
              <div className="p-4 bg-red-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-700">{currentSelectionPercent.toFixed(1)}%</p>
                <p className="text-sm text-red-600">Selection</p>
                <p className="text-xs text-muted-foreground">{params.selectedNumber}/{params.populationSize}</p>
              </div>
            </div>

            <div className="mt-6 p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">Interpretation</h4>
              <ul className="text-sm space-y-1">
                <li>• Expected gain per generation: <strong>{results.geneticGain.toFixed(2)} {traitUnit}</strong></li>
                <li>• Annual genetic progress: <strong>{results.gainPerYear.toFixed(2)} {traitUnit}/year</strong></li>
                <li>• Cumulative improvement over 10 years: <strong>{results.cumulativeGain.toFixed(2)} {traitUnit}</strong></li>
                <li>• Selection efficiency: <strong>{results.efficiency.toFixed(1)}%</strong> of phenotypic variation</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

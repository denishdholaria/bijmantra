import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import {
  Calculator,
  TrendingUp,
  Target,
  Clock,
  Dna,
  BarChart3,
  Info,
  Download,
  RefreshCw,
  Lightbulb,
  ArrowRight
} from 'lucide-react'

interface BreederEquationParams {
  selectionIntensity: number
  heritability: number
  phenotypicSD: number
  generationInterval: number
  accuracy: number
}

export function GeneticGainCalculator() {
  const [params, setParams] = useState<BreederEquationParams>({
    selectionIntensity: 1.76,
    heritability: 0.35,
    phenotypicSD: 12.5,
    generationInterval: 4,
    accuracy: 0.7
  })

  const [method, setMethod] = useState('phenotypic')

  // Calculate genetic gain using breeder's equation: ΔG = (i × h² × σp) / L
  const calculateGeneticGain = () => {
    if (method === 'phenotypic') {
      return (params.selectionIntensity * params.heritability * params.phenotypicSD) / params.generationInterval
    } else {
      // Genomic selection: ΔG = (i × r × σa) / L where r is accuracy
      const additiveSD = Math.sqrt(params.heritability) * params.phenotypicSD
      return (params.selectionIntensity * params.accuracy * additiveSD) / params.generationInterval
    }
  }

  const geneticGain = calculateGeneticGain()
  const annualGain = geneticGain
  const fiveYearGain = geneticGain * 5
  const tenYearGain = geneticGain * 10

  const selectionIntensityTable = [
    { selected: '1%', intensity: 2.67 },
    { selected: '5%', intensity: 2.06 },
    { selected: '10%', intensity: 1.76 },
    { selected: '20%', intensity: 1.40 },
    { selected: '30%', intensity: 1.16 },
    { selected: '50%', intensity: 0.80 }
  ]

  const scenarios = [
    { name: 'Current (Phenotypic)', gain: geneticGain, method: 'Phenotypic Selection', cycle: params.generationInterval },
    { name: 'Genomic Selection', gain: (params.selectionIntensity * params.accuracy * Math.sqrt(params.heritability) * params.phenotypicSD) / 2, method: 'GS with 2-year cycle', cycle: 2 },
    { name: 'Speed Breeding + GS', gain: (params.selectionIntensity * params.accuracy * Math.sqrt(params.heritability) * params.phenotypicSD) / 1, method: 'Accelerated cycle', cycle: 1 }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Calculator className="h-8 w-8 text-primary" />
            Genetic Gain Calculator
          </h1>
          <p className="text-muted-foreground mt-1">Predict and optimize breeding program genetic progress</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><RefreshCw className="h-4 w-4 mr-2" />Reset</Button>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
        </div>
      </div>

      {/* Results Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-primary text-primary-foreground">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8" />
              <div>
                <div className="text-3xl font-bold">{geneticGain.toFixed(2)}</div>
                <div className="text-sm opacity-90">Annual Genetic Gain</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Target className="h-5 w-5 text-green-600" />
              <div>
                <div className="text-2xl font-bold">{fiveYearGain.toFixed(1)}</div>
                <div className="text-sm text-muted-foreground">5-Year Gain</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-blue-600" />
              <div>
                <div className="text-2xl font-bold">{params.generationInterval} yrs</div>
                <div className="text-sm text-muted-foreground">Cycle Length</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Dna className="h-5 w-5 text-purple-600" />
              <div>
                <div className="text-2xl font-bold">{(params.heritability * 100).toFixed(0)}%</div>
                <div className="text-sm text-muted-foreground">Heritability</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Parameter Input */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Breeder's Equation Parameters</CardTitle>
            <CardDescription>ΔG = (i × h² × σp) / L</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex gap-4 mb-4">
              <Button variant={method === 'phenotypic' ? 'default' : 'outline'} onClick={() => setMethod('phenotypic')}>Phenotypic Selection</Button>
              <Button variant={method === 'genomic' ? 'default' : 'outline'} onClick={() => setMethod('genomic')}>Genomic Selection</Button>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Selection Intensity (i)</Label>
                  <span className="font-mono text-sm">{params.selectionIntensity.toFixed(2)}</span>
                </div>
                <Slider value={[params.selectionIntensity]} onValueChange={([v]) => setParams({ ...params, selectionIntensity: v })} min={0.5} max={3} step={0.01} />
                <p className="text-xs text-muted-foreground">Higher values = more stringent selection (fewer selected)</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Heritability (h²)</Label>
                  <span className="font-mono text-sm">{params.heritability.toFixed(2)}</span>
                </div>
                <Slider value={[params.heritability]} onValueChange={([v]) => setParams({ ...params, heritability: v })} min={0.05} max={0.95} step={0.01} />
                <p className="text-xs text-muted-foreground">Proportion of phenotypic variance due to genetics</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Phenotypic Standard Deviation (σp)</Label>
                  <span className="font-mono text-sm">{params.phenotypicSD.toFixed(1)}</span>
                </div>
                <Slider value={[params.phenotypicSD]} onValueChange={([v]) => setParams({ ...params, phenotypicSD: v })} min={1} max={50} step={0.5} />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Generation Interval (L) - Years</Label>
                  <span className="font-mono text-sm">{params.generationInterval}</span>
                </div>
                <Slider value={[params.generationInterval]} onValueChange={([v]) => setParams({ ...params, generationInterval: v })} min={1} max={10} step={0.5} />
              </div>

              {method === 'genomic' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Prediction Accuracy (r)</Label>
                    <span className="font-mono text-sm">{params.accuracy.toFixed(2)}</span>
                  </div>
                  <Slider value={[params.accuracy]} onValueChange={([v]) => setParams({ ...params, accuracy: v })} min={0.1} max={0.95} step={0.01} />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Selection Intensity Reference */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Info className="h-5 w-5" />Selection Intensity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {selectionIntensityTable.map((row, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded hover:bg-muted cursor-pointer" onClick={() => setParams({ ...params, selectionIntensity: row.intensity })}>
                  <span>Top {row.selected} selected</span>
                  <Badge variant="outline">{row.intensity.toFixed(2)}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Scenario Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5" />Scenario Comparison</CardTitle>
          <CardDescription>Compare different breeding strategies</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scenarios.map((scenario, i) => (
              <div key={i} className={`p-4 rounded-lg border ${i === 0 ? 'border-primary bg-primary/5' : ''}`}>
                <h4 className="font-semibold mb-2">{scenario.name}</h4>
                <div className="text-3xl font-bold text-primary mb-2">{scenario.gain.toFixed(2)}</div>
                <p className="text-sm text-muted-foreground">{scenario.method}</p>
                <p className="text-sm text-muted-foreground">Cycle: {scenario.cycle} year(s)</p>
                <div className="mt-3 pt-3 border-t">
                  <div className="text-sm">10-year gain: <span className="font-bold">{(scenario.gain * 10).toFixed(1)}</span></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Lightbulb className="h-5 w-5 text-yellow-500" />Optimization Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { title: 'Increase Selection Intensity', desc: 'Select top 5% instead of 10% to increase i from 1.76 to 2.06', impact: '+17% gain' },
              { title: 'Implement Genomic Selection', desc: 'Use GS to reduce generation interval from 4 to 2 years', impact: '+100% gain' },
              { title: 'Improve Phenotyping', desc: 'Better phenotyping can increase heritability estimates', impact: '+15% gain' },
              { title: 'Speed Breeding', desc: 'Accelerate generation turnover with controlled environments', impact: '+50% gain' }
            ].map((rec, i) => (
              <div key={i} className="flex items-start gap-3 p-4 border rounded-lg">
                <ArrowRight className="h-5 w-5 text-primary mt-0.5" />
                <div>
                  <div className="font-medium">{rec.title}</div>
                  <p className="text-sm text-muted-foreground">{rec.desc}</p>
                  <Badge variant="secondary" className="mt-2">{rec.impact}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

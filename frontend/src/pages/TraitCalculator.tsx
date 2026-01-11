/**
 * Trait Calculator Page
 * Calculate derived traits from raw measurements
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

interface Formula {
  id: string
  name: string
  category: string
  formula: string
  inputs: { name: string; unit: string }[]
  output: { name: string; unit: string }
  calculate: (inputs: number[]) => number
}

const formulas: Formula[] = [
  {
    id: 'harvest-index',
    name: 'Harvest Index',
    category: 'Yield',
    formula: 'HI = (Grain Yield / Total Biomass) × 100',
    inputs: [{ name: 'Grain Yield', unit: 'g' }, { name: 'Total Biomass', unit: 'g' }],
    output: { name: 'Harvest Index', unit: '%' },
    calculate: ([gy, tb]) => tb > 0 ? (gy / tb) * 100 : 0,
  },
  {
    id: 'yield-per-ha',
    name: 'Yield per Hectare',
    category: 'Yield',
    formula: 'Yield (t/ha) = (Plot Yield × 10000) / Plot Area',
    inputs: [{ name: 'Plot Yield', unit: 'kg' }, { name: 'Plot Area', unit: 'm²' }],
    output: { name: 'Yield', unit: 't/ha' },
    calculate: ([py, pa]) => pa > 0 ? (py * 10000) / (pa * 1000) : 0,
  },
  {
    id: 'thousand-grain-weight',
    name: '1000 Grain Weight',
    category: 'Grain',
    formula: 'TGW = (Sample Weight / Grain Count) × 1000',
    inputs: [{ name: 'Sample Weight', unit: 'g' }, { name: 'Grain Count', unit: 'count' }],
    output: { name: '1000 Grain Weight', unit: 'g' },
    calculate: ([sw, gc]) => gc > 0 ? (sw / gc) * 1000 : 0,
  },
  {
    id: 'grain-moisture',
    name: 'Grain Moisture',
    category: 'Grain',
    formula: 'Moisture = ((Wet - Dry) / Wet) × 100',
    inputs: [{ name: 'Wet Weight', unit: 'g' }, { name: 'Dry Weight', unit: 'g' }],
    output: { name: 'Moisture Content', unit: '%' },
    calculate: ([wet, dry]) => wet > 0 ? ((wet - dry) / wet) * 100 : 0,
  },
  {
    id: 'plant-density',
    name: 'Plant Density',
    category: 'Agronomy',
    formula: 'Density = (Plant Count / Plot Area) × 10000',
    inputs: [{ name: 'Plant Count', unit: 'count' }, { name: 'Plot Area', unit: 'm²' }],
    output: { name: 'Plant Density', unit: 'plants/ha' },
    calculate: ([pc, pa]) => pa > 0 ? (pc / pa) * 10000 : 0,
  },
  {
    id: 'lodging-score',
    name: 'Lodging Score',
    category: 'Agronomy',
    formula: 'Score = (Lodged Area / Total Area) × Severity',
    inputs: [{ name: 'Lodged Area', unit: '%' }, { name: 'Severity', unit: '1-5' }],
    output: { name: 'Lodging Score', unit: 'score' },
    calculate: ([la, sev]) => (la / 100) * sev,
  },
  {
    id: 'relative-yield',
    name: 'Relative Yield',
    category: 'Yield',
    formula: 'RY = (Entry Yield / Check Yield) × 100',
    inputs: [{ name: 'Entry Yield', unit: 't/ha' }, { name: 'Check Yield', unit: 't/ha' }],
    output: { name: 'Relative Yield', unit: '%' },
    calculate: ([ey, cy]) => cy > 0 ? (ey / cy) * 100 : 0,
  },
  {
    id: 'protein-yield',
    name: 'Protein Yield',
    category: 'Quality',
    formula: 'Protein Yield = Grain Yield × (Protein % / 100)',
    inputs: [{ name: 'Grain Yield', unit: 't/ha' }, { name: 'Protein Content', unit: '%' }],
    output: { name: 'Protein Yield', unit: 't/ha' },
    calculate: ([gy, pc]) => gy * (pc / 100),
  },
]

export function TraitCalculator() {
  const [selectedFormula, setSelectedFormula] = useState<string>('harvest-index')
  const [inputs, setInputs] = useState<number[]>([0, 0])
  const [result, setResult] = useState<number | null>(null)
  const [history, setHistory] = useState<{ formula: string; inputs: number[]; result: number }[]>([])

  const formula = formulas.find(f => f.id === selectedFormula)
  const categories = [...new Set(formulas.map(f => f.category))]

  const handleFormulaChange = (id: string) => {
    setSelectedFormula(id)
    const f = formulas.find(f => f.id === id)
    if (f) {
      setInputs(new Array(f.inputs.length).fill(0))
      setResult(null)
    }
  }

  const handleInputChange = (index: number, value: string) => {
    const newInputs = [...inputs]
    newInputs[index] = parseFloat(value) || 0
    setInputs(newInputs)
  }

  const calculate = () => {
    if (!formula) return
    const res = formula.calculate(inputs)
    setResult(res)
    setHistory(prev => [{ formula: formula.name, inputs: [...inputs], result: res }, ...prev.slice(0, 9)])
    toast.success('Calculated!')
  }

  const clearHistory = () => {
    setHistory([])
    toast.success('History cleared')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Trait Calculator</h1>
          <p className="text-muted-foreground mt-1">Calculate derived traits from measurements</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Formula Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Formulas</CardTitle>
            <CardDescription>Select a calculation</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue={categories[0]}>
              <TabsList className="w-full flex-wrap h-auto">
                {categories.map(cat => (
                  <TabsTrigger key={cat} value={cat} className="text-xs">{cat}</TabsTrigger>
                ))}
              </TabsList>
              {categories.map(cat => (
                <TabsContent key={cat} value={cat} className="space-y-2 mt-4">
                  {formulas.filter(f => f.category === cat).map(f => (
                    <Button
                      key={f.id}
                      variant={selectedFormula === f.id ? 'default' : 'outline'}
                      className="w-full justify-start text-left h-auto py-2"
                      onClick={() => handleFormulaChange(f.id)}
                    >
                      <span className="truncate">{f.name}</span>
                    </Button>
                  ))}
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>

        {/* Calculator */}
        <Card>
          <CardHeader>
            <CardTitle>{formula?.name || 'Calculator'}</CardTitle>
            <CardDescription>{formula?.formula}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {formula?.inputs.map((input, i) => (
              <div key={i} className="space-y-2">
                <Label>{input.name} ({input.unit})</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={inputs[i] || ''}
                  onChange={(e) => handleInputChange(i, e.target.value)}
                  placeholder={`Enter ${input.name.toLowerCase()}`}
                />
              </div>
            ))}

            <Button onClick={calculate} className="w-full">
              🧮 Calculate
            </Button>

            {result !== null && formula && (
              <div className="p-4 bg-green-50 rounded-lg text-center">
                <p className="text-sm text-green-600">{formula.output.name}</p>
                <p className="text-3xl font-bold text-green-700">
                  {result.toFixed(2)} <span className="text-lg">{formula.output.unit}</span>
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* History */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>History</CardTitle>
                <CardDescription>Recent calculations</CardDescription>
              </div>
              {history.length > 0 && (
                <Button size="sm" variant="ghost" onClick={clearHistory}>Clear</Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {history.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">No calculations yet</p>
            ) : (
              <div className="space-y-2">
                {history.map((h, i) => (
                  <div key={i} className="p-3 bg-muted rounded-lg text-sm">
                    <p className="font-medium">{h.formula}</p>
                    <p className="text-muted-foreground text-xs">
                      Inputs: {h.inputs.join(', ')}
                    </p>
                    <p className="text-green-600 font-bold">= {h.result.toFixed(2)}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

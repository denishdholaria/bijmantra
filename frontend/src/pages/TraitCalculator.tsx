/**
 * Trait Calculator Page
 * Calculate derived traits from raw measurements
 */
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import type { OntologyFormula, OntologyFormulaInput, OntologyFormulaOutput } from '@/lib/api/brapi/phenotyping/ontologies'

type FormulaInput = OntologyFormulaInput
type FormulaOutput = OntologyFormulaOutput
type Formula = OntologyFormula

export function TraitCalculator() {
  const [formulas, setFormulas] = useState<Formula[]>([])
  const [selectedFormulaId, setSelectedFormulaId] = useState<string>('')
  const [inputs, setInputs] = useState<number[]>([])
  const [result, setResult] = useState<number | null>(null)
  const [history, setHistory] = useState<{ formula: string; inputs: number[]; result: number }[]>([])
  const [loading, setLoading] = useState(false)
  const [calculating, setCalculating] = useState(false)

  useEffect(() => {
    const fetchFormulas = async () => {
      setLoading(true)
      try {
        const response = await apiClient.ontologiesService.getFormulas()
        setFormulas(response.formulas)
        if (response.formulas.length > 0) {
           // Don't auto-select, or do? Let's default to first if noneselected
           if (!selectedFormulaId) {
             handleFormulaChangeInternal(response.formulas[0].id, response.formulas)
           }
        }
      } catch (error) {
        console.error('Failed to fetch formulas:', error)
        toast.error('Failed to load formulas')
      } finally {
        setLoading(false)
      }
    }
    fetchFormulas()
  }, [])

  const handleFormulaChangeInternal = (id: string, currentFormulas: Formula[]) => {
    setSelectedFormulaId(id)
    const f = currentFormulas.find(f => f.id === id)
    if (f) {
      setInputs(new Array(f.inputs.length).fill(0))
      setResult(null)
    }
  }

  const handleFormulaChange = (id: string) => {
    handleFormulaChangeInternal(id, formulas)
  }

  const handleInputChange = (index: number, value: string) => {
    const newInputs = [...inputs]
    newInputs[index] = parseFloat(value) || 0
    setInputs(newInputs)
  }

  const selectedFormula = formulas.find(f => f.id === selectedFormulaId)
  const categories = [...new Set(formulas.map(f => f.category))]

  const calculate = async () => {
    if (!selectedFormula) return
    setCalculating(true)
    try {
      // Map inputs to name: value
      const inputMap: Record<string, number> = {}
      selectedFormula.inputs.forEach((inp, idx) => {
        inputMap[inp.name] = inputs[idx] || 0
      })

      const response = await apiClient.ontologiesService.calculateFormula(selectedFormula.id, inputMap)
      setResult(response.result)
      setHistory(prev => [{ formula: selectedFormula.name, inputs: [...inputs], result: response.result }, ...prev.slice(0, 9)])
      toast.success('Calculated!')
    } catch (error) {
       console.error('Calculation failed', error)
       toast.error('Calculation failed')
    } finally {
       setCalculating(false)
    }
  }

  const clearHistory = () => {
    setHistory([])
    toast.success('History cleared')
  }

  if (loading && formulas.length === 0) {
    return <div className="p-8 text-center">Loading formulas...</div>
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Trait Calculator</h1>
          <p className="text-muted-foreground mt-1">Calculate derived traits from measurements (Dynamic Ontology)</p>
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
            {categories.length > 0 ? (
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
                      variant={selectedFormulaId === f.id ? 'default' : 'outline'}
                      className="w-full justify-start text-left h-auto py-2"
                      onClick={() => handleFormulaChange(f.id)}
                    >
                      <span className="truncate">{f.name}</span>
                    </Button>
                  ))}
                </TabsContent>
              ))}
            </Tabs>
            ) : (
              <p className="text-muted-foreground">No formulas available.</p>
            )}
          </CardContent>
        </Card>

        {/* Calculator */}
        <Card>
          <CardHeader>
            <CardTitle>{selectedFormula?.name || 'Calculator'}</CardTitle>
            <CardDescription>{selectedFormula?.formula}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedFormula?.inputs.map((input, i) => (
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

            <Button onClick={calculate} className="w-full" disabled={calculating || !selectedFormula}>
              {calculating ? 'Calculating...' : '🧮 Calculate'}
            </Button>

            {result !== null && selectedFormula && (
              <div className="p-4 bg-green-50 rounded-lg text-center">
                <p className="text-sm text-green-600">{selectedFormula.output.name}</p>
                <p className="text-3xl font-bold text-green-700">
                  {result.toFixed(2)} <span className="text-lg">{selectedFormula.output.unit}</span>
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

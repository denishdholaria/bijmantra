/**
 * Selection Index Page - Connected to Backend API
 * Calculate breeding selection indices using Smith-Hazel and other methods
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface Trait {
  id: string
  name: string
  weight: number
  heritability: number
  economicValue: number
  direction: 'higher' | 'lower'
}

interface GermplasmScore {
  id: string
  name: string
  traitValues: Record<string, number>
  indexScore?: number
  rank?: number
}

interface SelectionMethod {
  code: string
  name: string
  description: string
  requires: string[]
}

const defaultTraits: Trait[] = [
  { id: 'yield', name: 'Yield', weight: 40, heritability: 0.65, economicValue: 100, direction: 'higher' },
  { id: 'plant_height', name: 'Plant Height', weight: 15, heritability: 0.80, economicValue: 20, direction: 'lower' },
  { id: 'days_to_maturity', name: 'Days to Maturity', weight: 20, heritability: 0.75, economicValue: 30, direction: 'lower' },
  { id: 'disease_resistance', name: 'Disease Resistance', weight: 25, heritability: 0.50, economicValue: 50, direction: 'higher' },
]

const defaultGermplasm: GermplasmScore[] = [
  { id: 'g1', name: 'IR64', traitValues: { yield: 6.5, plant_height: 95, days_to_maturity: 115, disease_resistance: 7 } },
  { id: 'g2', name: 'Nipponbare', traitValues: { yield: 5.8, plant_height: 110, days_to_maturity: 125, disease_resistance: 5 } },
  { id: 'g3', name: 'Kasalath', traitValues: { yield: 4.2, plant_height: 130, days_to_maturity: 140, disease_resistance: 8 } },
  { id: 'g4', name: 'Azucena', traitValues: { yield: 5.5, plant_height: 145, days_to_maturity: 135, disease_resistance: 6 } },
  { id: 'g5', name: 'Moroberekan', traitValues: { yield: 4.8, plant_height: 140, days_to_maturity: 130, disease_resistance: 9 } },
  { id: 'g6', name: 'CO39', traitValues: { yield: 6.2, plant_height: 85, days_to_maturity: 110, disease_resistance: 4 } },
  { id: 'g7', name: 'IRBB21', traitValues: { yield: 5.9, plant_height: 100, days_to_maturity: 118, disease_resistance: 8 } },
  { id: 'g8', name: 'Swarna', traitValues: { yield: 7.0, plant_height: 90, days_to_maturity: 145, disease_resistance: 6 } },
]

export function SelectionIndex() {
  const [traits, setTraits] = useState<Trait[]>(defaultTraits)
  const [germplasm, setGermplasm] = useState<GermplasmScore[]>(defaultGermplasm)
  const [selectionIntensity, setSelectionIntensity] = useState(20)
  const [selectedMethod, setSelectedMethod] = useState('smith_hazel')
  const [calculated, setCalculated] = useState(false)

  // Fetch available selection methods
  const { data: methodsData } = useQuery({
    queryKey: ['selectionMethods'],
    queryFn: () => apiClient.getSelectionMethods(),
  })

  // Fetch default weights
  const { data: defaultWeightsData } = useQuery({
    queryKey: ['defaultWeights'],
    queryFn: () => apiClient.getDefaultWeights(),
  })

  // Calculate index mutation
  const calculateMutation = useMutation({
    mutationFn: async () => {
      const phenotypicValues = germplasm.map((g) => ({
        id: g.id,
        ...g.traitValues,
      }))
      const traitNames = traits.map((t) => t.id)
      const economicWeights = traits.map((t) => (t.direction === 'lower' ? -t.economicValue : t.economicValue))
      const heritabilities = traits.map((t) => t.heritability)

      if (selectedMethod === 'smith_hazel') {
        return apiClient.calculateSmithHazel({
          phenotypic_values: phenotypicValues,
          trait_names: traitNames,
          economic_weights: economicWeights,
          heritabilities: heritabilities,
        })
      } else if (selectedMethod === 'base_index') {
        const weights = traits.map((t) => (t.direction === 'lower' ? -t.weight / 100 : t.weight / 100))
        return apiClient.calculateBaseIndex({
          phenotypic_values: phenotypicValues,
          trait_names: traitNames,
          weights: weights,
        })
      } else {
        // Default to smith_hazel
        return apiClient.calculateSmithHazel({
          phenotypic_values: phenotypicValues,
          trait_names: traitNames,
          economic_weights: economicWeights,
          heritabilities: heritabilities,
        })
      }
    },
    onSuccess: (data) => {
      if (data?.status === 'success' && data?.data?.results) {
        // Update germplasm with results
        const results = data.data.results
        const updatedGermplasm = germplasm.map((g) => {
          const result = results.find((r: any) => r.individual_id === g.id)
          if (result) {
            return {
              ...g,
              indexScore: result.index_value,
              rank: result.rank,
            }
          }
          return g
        })
        // Sort by rank
        updatedGermplasm.sort((a, b) => (a.rank || 999) - (b.rank || 999))
        setGermplasm(updatedGermplasm)
        setCalculated(true)
        toast.success(`Selection index calculated using ${selectedMethod.replace('_', ' ')}`)
      } else {
        // Fallback to local calculation
        calculateLocally()
      }
    },
    onError: () => {
      // Fallback to local calculation
      calculateLocally()
    },
  })

  const methods: SelectionMethod[] = methodsData?.data || [
    { code: 'smith_hazel', name: 'Smith-Hazel Index', description: 'Optimal index using genetic parameters', requires: [] },
    { code: 'base_index', name: 'Base Index', description: 'Simple weighted sum', requires: [] },
  ]

  const updateTraitWeight = (traitId: string, weight: number) => {
    setTraits((prev) => prev.map((t) => (t.id === traitId ? { ...t, weight } : t)))
    setCalculated(false)
  }

  const normalizeWeights = () => {
    const total = traits.reduce((sum, t) => sum + t.weight, 0)
    if (total === 0) return
    setTraits((prev) => prev.map((t) => ({ ...t, weight: Math.round((t.weight / total) * 100) })))
  }

  const calculateLocally = () => {
    // Local fallback calculation
    const traitStats: Record<string, { min: number; max: number; mean: number; std: number }> = {}

    traits.forEach((trait) => {
      const values = germplasm.map((g) => g.traitValues[trait.id])
      const min = Math.min(...values)
      const max = Math.max(...values)
      const mean = values.reduce((a, b) => a + b, 0) / values.length
      const std = Math.sqrt(values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length)
      traitStats[trait.id] = { min, max, mean, std }
    })

    const scored = germplasm.map((g) => {
      let indexScore = 0
      traits.forEach((trait) => {
        const stats = traitStats[trait.id]
        const rawValue = g.traitValues[trait.id]
        let standardized = stats.std > 0 ? (rawValue - stats.mean) / stats.std : 0
        if (trait.direction === 'lower') standardized = -standardized
        indexScore += standardized * (trait.weight / 100) * trait.heritability
      })
      return { ...g, indexScore }
    })

    scored.sort((a, b) => (b.indexScore || 0) - (a.indexScore || 0))
    scored.forEach((g, i) => {
      g.rank = i + 1
    })

    setGermplasm(scored)
    setCalculated(true)
    toast.success('Selection index calculated (local)')
  }

  const handleCalculate = () => {
    calculateMutation.mutate()
  }

  const selectedCount = Math.ceil(germplasm.length * (selectionIntensity / 100))
  const totalWeight = traits.reduce((sum, t) => sum + t.weight, 0)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Selection Index</h1>
          <p className="text-muted-foreground mt-1">Multi-trait selection for breeding</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedMethod} onValueChange={setSelectedMethod}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select method" />
            </SelectTrigger>
            <SelectContent>
              {methods.map((m) => (
                <SelectItem key={m.code} value={m.code}>
                  {m.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={handleCalculate} disabled={calculateMutation.isPending}>
            {calculateMutation.isPending ? '⏳ Calculating...' : '📊 Calculate Index'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trait Weights */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Trait Weights</CardTitle>
                <CardDescription>Adjust importance of each trait</CardDescription>
              </div>
              <Badge variant={totalWeight === 100 ? 'default' : 'destructive'}>{totalWeight}%</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {traits.map((trait) => (
              <div key={trait.id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="flex items-center gap-2">
                    {trait.name}
                    <Badge variant="outline" className="text-xs">
                      {trait.direction === 'higher' ? '↑' : '↓'}
                    </Badge>
                  </Label>
                  <span className="text-sm font-medium">{trait.weight}%</span>
                </div>
                <Slider
                  value={[trait.weight]}
                  onValueChange={([v]) => updateTraitWeight(trait.id, v)}
                  max={100}
                  step={5}
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>h² = {trait.heritability}</span>
                  <span>EV = ${trait.economicValue}</span>
                </div>
              </div>
            ))}
            <Button variant="outline" size="sm" onClick={normalizeWeights} className="w-full">
              Normalize to 100%
            </Button>
          </CardContent>
        </Card>

        {/* Selection Parameters */}
        <Card>
          <CardHeader>
            <CardTitle>Selection Parameters</CardTitle>
            <CardDescription>Configure selection intensity</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Selection Intensity</Label>
                <span className="text-sm font-medium">{selectionIntensity}%</span>
              </div>
              <Slider
                value={[selectionIntensity]}
                onValueChange={([v]) => setSelectionIntensity(v)}
                min={5}
                max={50}
                step={5}
              />
              <p className="text-xs text-muted-foreground">
                Select top {selectedCount} of {germplasm.length} entries
              </p>
            </div>

            <div className="p-4 bg-muted rounded-lg space-y-2">
              <h4 className="font-medium">
                {methods.find((m) => m.code === selectedMethod)?.name || 'Selection Index'}
              </h4>
              <p className="text-xs text-muted-foreground">
                {methods.find((m) => m.code === selectedMethod)?.description}
              </p>
              {selectedMethod === 'smith_hazel' && (
                <p className="text-xs font-mono">I = Σ(h²ᵢ × aᵢ × Pᵢ)</p>
              )}
              {selectedMethod === 'base_index' && <p className="text-xs font-mono">I = Σ(wᵢ × Pᵢ)</p>}
            </div>

            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-700">{selectedCount}</p>
                <p className="text-xs text-green-600">To Select</p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg">
                <p className="text-2xl font-bold text-red-700">{germplasm.length - selectedCount}</p>
                <p className="text-xs text-red-600">To Discard</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
            <CardDescription>Selection overview</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-muted rounded-lg text-center">
                <p className="text-xl font-bold">{germplasm.length}</p>
                <p className="text-xs text-muted-foreground">Candidates</p>
              </div>
              <div className="p-3 bg-muted rounded-lg text-center">
                <p className="text-xl font-bold">{traits.length}</p>
                <p className="text-xs text-muted-foreground">Traits</p>
              </div>
            </div>
            {calculated && germplasm[0] && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm font-medium text-green-800">Top Selection</p>
                <p className="text-lg font-bold text-green-700">{germplasm[0].name}</p>
                <p className="text-xs text-green-600">Index: {germplasm[0].indexScore?.toFixed(3)}</p>
              </div>
            )}
            {calculated && germplasm.length > 1 && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-800">Selection Differential</p>
                <p className="text-xs text-blue-600">
                  Top {selectedCount}: avg index{' '}
                  {(
                    germplasm.slice(0, selectedCount).reduce((s, g) => s + (g.indexScore || 0), 0) / selectedCount
                  ).toFixed(3)}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>Ranking Results</CardTitle>
          <CardDescription>
            {calculated ? 'Germplasm ranked by selection index' : 'Calculate index to see rankings'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rank</TableHead>
                <TableHead>Germplasm</TableHead>
                {traits.map((t) => (
                  <TableHead key={t.id} className="text-right">
                    {t.name}
                  </TableHead>
                ))}
                <TableHead className="text-right">Index Score</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {germplasm.map((g, idx) => (
                <TableRow key={g.id} className={idx < selectedCount && calculated ? 'bg-green-50' : ''}>
                  <TableCell className="font-medium">{calculated ? g.rank : '-'}</TableCell>
                  <TableCell className="font-medium">{g.name}</TableCell>
                  {traits.map((t) => (
                    <TableCell key={t.id} className="text-right font-mono text-sm">
                      {g.traitValues[t.id]}
                    </TableCell>
                  ))}
                  <TableCell className="text-right font-mono font-bold">
                    {calculated ? g.indexScore?.toFixed(3) : '-'}
                  </TableCell>
                  <TableCell>
                    {calculated && (
                      <Badge variant={idx < selectedCount ? 'default' : 'secondary'}>
                        {idx < selectedCount ? '✓ Select' : '✗ Discard'}
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

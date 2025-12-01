/**
 * Phenotype Comparison Page
 * Compare phenotypic data across germplasm entries
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'

interface GermplasmData {
  id: string
  name: string
  traits: Record<string, number>
}

const sampleData: GermplasmData[] = [
  { id: 'G001', name: 'Elite Variety 2024', traits: { yield: 5.2, height: 95, maturity: 120, protein: 12.5, disease: 8 } },
  { id: 'G002', name: 'High Yield Line A', traits: { yield: 5.8, height: 105, maturity: 125, protein: 11.2, disease: 6 } },
  { id: 'G003', name: 'Disease Resistant B', traits: { yield: 4.5, height: 90, maturity: 115, protein: 13.1, disease: 9 } },
  { id: 'G004', name: 'Drought Tolerant C', traits: { yield: 4.2, height: 85, maturity: 110, protein: 12.8, disease: 7 } },
  { id: 'G005', name: 'Check Variety', traits: { yield: 4.8, height: 100, maturity: 118, protein: 11.8, disease: 5 } },
]

const traitInfo: Record<string, { unit: string; higher: boolean }> = {
  yield: { unit: 't/ha', higher: true },
  height: { unit: 'cm', higher: false },
  maturity: { unit: 'days', higher: false },
  protein: { unit: '%', higher: true },
  disease: { unit: 'score', higher: true },
}

export function PhenotypeComparison() {
  const [selected, setSelected] = useState<string[]>(['G001', 'G002', 'G005'])
  const [traits] = useState(Object.keys(traitInfo))

  const toggleSelection = (id: string) => {
    setSelected(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id])
  }

  const selectedData = sampleData.filter(g => selected.includes(g.id))
  const checkVariety = sampleData.find(g => g.id === 'G005')

  const getTraitColor = (value: number, trait: string, allValues: number[]) => {
    const info = traitInfo[trait]
    const max = Math.max(...allValues)
    const min = Math.min(...allValues)
    const isTop = info.higher ? value === max : value === min
    const isBottom = info.higher ? value === min : value === max
    if (isTop) return 'bg-green-100 text-green-700 font-bold'
    if (isBottom) return 'bg-red-100 text-red-700'
    return ''
  }

  const calculateDiff = (value: number, checkValue: number, higher: boolean) => {
    const diff = ((value - checkValue) / checkValue) * 100
    const isPositive = higher ? diff > 0 : diff < 0
    return { diff, isPositive }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Phenotype Comparison</h1>
          <p className="text-muted-foreground mt-1">Compare traits across germplasm</p>
        </div>
        <Badge variant="outline">{selected.length} selected</Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Selection Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Select Germplasm</CardTitle>
            <CardDescription>Choose entries to compare</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {sampleData.map((g) => (
              <div key={g.id} className="flex items-center gap-2">
                <Checkbox
                  id={g.id}
                  checked={selected.includes(g.id)}
                  onCheckedChange={() => toggleSelection(g.id)}
                />
                <Label htmlFor={g.id} className="text-sm cursor-pointer">
                  {g.name}
                  {g.id === 'G005' && <Badge variant="secondary" className="ml-2 text-xs">Check</Badge>}
                </Label>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Comparison Table */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Trait Comparison</CardTitle>
            <CardDescription>
              {selectedData.length > 0 ? `Comparing ${selectedData.length} entries` : 'Select germplasm to compare'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedData.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <span className="text-4xl">📊</span>
                <p className="mt-2">Select germplasm entries to compare</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Trait</th>
                      {selectedData.map((g) => (
                        <th key={g.id} className="text-center p-2">
                          {g.name}
                          {g.id === 'G005' && <span className="text-xs text-muted-foreground block">Check</span>}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {traits.map((trait) => {
                      const allValues = selectedData.map(g => g.traits[trait])
                      return (
                        <tr key={trait} className="border-b">
                          <td className="p-2 font-medium capitalize">
                            {trait}
                            <span className="text-xs text-muted-foreground ml-1">({traitInfo[trait].unit})</span>
                          </td>
                          {selectedData.map((g) => {
                            const value = g.traits[trait]
                            const colorClass = getTraitColor(value, trait, allValues)
                            const checkValue = checkVariety?.traits[trait]
                            const diffInfo = checkValue ? calculateDiff(value, checkValue, traitInfo[trait].higher) : null
                            
                            return (
                              <td key={g.id} className={`p-2 text-center ${colorClass}`}>
                                <span className="block">{value}</span>
                                {diffInfo && g.id !== 'G005' && (
                                  <span className={`text-xs ${diffInfo.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                                    {diffInfo.diff > 0 ? '+' : ''}{diffInfo.diff.toFixed(1)}%
                                  </span>
                                )}
                              </td>
                            )
                          })}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Legend */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
              <span>Best value</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-100 border border-red-300 rounded"></div>
              <span>Lowest value</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-600">+%</span>
              <span>Better than check</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-red-600">-%</span>
              <span>Worse than check</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

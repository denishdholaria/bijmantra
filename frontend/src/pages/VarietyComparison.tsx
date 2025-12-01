/**
 * Variety Comparison Page
 * Compare varieties across multiple trials and locations
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'

interface VarietyData {
  id: string
  name: string
  type: 'check' | 'test' | 'elite'
  trials: number
  locations: number
  years: number[]
  avgYield: number
  stability: number
  traits: Record<string, number>
}

const sampleVarieties: VarietyData[] = [
  { id: 'V001', name: 'Check Variety (Control)', type: 'check', trials: 15, locations: 5, years: [2022, 2023, 2024], avgYield: 4.5, stability: 85, traits: { height: 100, maturity: 120, protein: 11.5, disease: 6 } },
  { id: 'V002', name: 'Elite Variety 2024', type: 'elite', trials: 12, locations: 4, years: [2023, 2024], avgYield: 5.2, stability: 78, traits: { height: 95, maturity: 118, protein: 12.2, disease: 8 } },
  { id: 'V003', name: 'High Yield Line A', type: 'test', trials: 8, locations: 3, years: [2024], avgYield: 5.5, stability: 72, traits: { height: 105, maturity: 125, protein: 10.8, disease: 7 } },
  { id: 'V004', name: 'Disease Resistant B', type: 'test', trials: 10, locations: 4, years: [2023, 2024], avgYield: 4.8, stability: 88, traits: { height: 90, maturity: 115, protein: 13.0, disease: 9 } },
  { id: 'V005', name: 'Early Maturing C', type: 'test', trials: 6, locations: 2, years: [2024], avgYield: 4.2, stability: 82, traits: { height: 85, maturity: 105, protein: 11.8, disease: 5 } },
]

export function VarietyComparison() {
  const [selected, setSelected] = useState<string[]>(['V001', 'V002', 'V003'])
  const checkVariety = sampleVarieties.find(v => v.type === 'check')

  const toggleSelection = (id: string) => {
    setSelected(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id])
  }

  const selectedVarieties = sampleVarieties.filter(v => selected.includes(v.id))

  const getYieldComparison = (yield_: number) => {
    if (!checkVariety) return { diff: 0, color: 'text-gray-600' }
    const diff = ((yield_ - checkVariety.avgYield) / checkVariety.avgYield) * 100
    return {
      diff,
      color: diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-gray-600'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'check': return 'bg-purple-100 text-purple-700'
      case 'elite': return 'bg-green-100 text-green-700'
      case 'test': return 'bg-blue-100 text-blue-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Variety Comparison</h1>
          <p className="text-muted-foreground mt-1">Compare varieties across trials</p>
        </div>
        <Badge variant="outline">{selected.length} selected</Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Selection Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Select Varieties</CardTitle>
            <CardDescription>Choose varieties to compare</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {sampleVarieties.map((v) => (
              <div key={v.id} className="flex items-center gap-2">
                <Checkbox
                  id={v.id}
                  checked={selected.includes(v.id)}
                  onCheckedChange={() => toggleSelection(v.id)}
                />
                <Label htmlFor={v.id} className="text-sm cursor-pointer flex-1">
                  {v.name}
                </Label>
                <Badge className={getTypeColor(v.type)} variant="secondary">{v.type}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Comparison Table */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Performance Comparison</CardTitle>
            <CardDescription>Relative to check variety</CardDescription>
          </CardHeader>
          <CardContent>
            {selectedVarieties.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <span className="text-4xl">📊</span>
                <p className="mt-2">Select varieties to compare</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Variety</th>
                      <th className="text-center p-2">Trials</th>
                      <th className="text-center p-2">Locations</th>
                      <th className="text-right p-2">Avg Yield</th>
                      <th className="text-right p-2">vs Check</th>
                      <th className="text-center p-2">Stability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedVarieties.map((v) => {
                      const comparison = getYieldComparison(v.avgYield)
                      return (
                        <tr key={v.id} className="border-b hover:bg-muted/50">
                          <td className="p-2">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{v.name}</span>
                              <Badge className={getTypeColor(v.type)} variant="secondary">{v.type}</Badge>
                            </div>
                          </td>
                          <td className="p-2 text-center">{v.trials}</td>
                          <td className="p-2 text-center">{v.locations}</td>
                          <td className="p-2 text-right font-mono">{v.avgYield.toFixed(1)} t/ha</td>
                          <td className={`p-2 text-right font-mono ${comparison.color}`}>
                            {v.type === 'check' ? '-' : `${comparison.diff > 0 ? '+' : ''}${comparison.diff.toFixed(1)}%`}
                          </td>
                          <td className="p-2 text-center">
                            <Badge variant={v.stability >= 80 ? 'default' : 'secondary'}>
                              {v.stability}%
                            </Badge>
                          </td>
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

      {/* Trait Comparison */}
      {selectedVarieties.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Trait Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {['height', 'maturity', 'protein', 'disease'].map(trait => (
                <div key={trait} className="space-y-2">
                  <p className="font-medium capitalize">{trait}</p>
                  {selectedVarieties.map(v => (
                    <div key={v.id} className="flex justify-between text-sm p-2 bg-muted rounded">
                      <span className="truncate">{v.name.split(' ')[0]}</span>
                      <span className="font-mono">{v.traits[trait]}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

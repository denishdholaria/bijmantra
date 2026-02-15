/**
 * Phenotype Comparison Page
 * Compare phenotypic data across germplasm entries - Connected to real API
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Loader2, Download, BarChart3 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface GermplasmData {
  id: string
  name: string
  traits: Record<string, number>
}

const traitInfo: Record<string, { unit: string; higher: boolean }> = {
  yield: { unit: 't/ha', higher: true },
  height: { unit: 'cm', higher: false },
  maturity: { unit: 'days', higher: false },
  protein: { unit: '%', higher: true },
  disease: { unit: 'score', higher: true },
}

export function PhenotypeComparison() {
  const [selected, setSelected] = useState<string[]>([])

  // Fetch germplasm list from API
  const { data: germplasmData, isLoading: loadingGermplasm } = useQuery({
    queryKey: ['phenotype-comparison-germplasm'],
    queryFn: async () => {
      const response = await apiClient.phenotypeComparisonService.getGermplasm({ limit: 20 })
      return response.result.data.map(g => ({
        id: g.germplasmDbId,
        name: g.germplasmName || g.defaultDisplayName || g.germplasmDbId,
        isCheck: g.isCheck || false,
      }))
    },
  })

  // Fetch observations for selected germplasm from API
  const { data: observationsData, isLoading: loadingObservations } = useQuery({
    queryKey: ['phenotype-comparison-observations', selected],
    queryFn: async () => {
      if (selected.length === 0) return {}
      
      const response = await apiClient.phenotypeComparisonService.getObservations(selected)
      // Transform observations into trait values per germplasm
      const traitsByGermplasm: Record<string, Record<string, number>> = {}
      
      response.result.data.forEach(obs => {
        if (!traitsByGermplasm[obs.germplasmDbId]) {
          traitsByGermplasm[obs.germplasmDbId] = {}
        }
        const traitKey = obs.observationVariableName.toLowerCase().replace(/\s+/g, '_').replace('grain_', '').replace('plant_', '').replace('days_to_', '').replace('_content', '').replace('_resistance', '')
        traitsByGermplasm[obs.germplasmDbId][traitKey] = parseFloat(obs.value) || 0
      })
      
      return traitsByGermplasm
    },
    enabled: selected.length > 0,
  })

  const germplasmList = germplasmData || []
  const traitsData: Record<string, Record<string, number>> = observationsData || {}

  // Build comparison data
  const comparisonData: GermplasmData[] = selected.map(id => {
    const germplasm = germplasmList.find(g => g.id === id)
    return {
      id,
      name: germplasm?.name || id,
      traits: traitsData[id] || { yield: 0, height: 0, maturity: 0, protein: 0, disease: 0 },
    }
  })

  const traits = Object.keys(traitInfo)
  const checkVariety = comparisonData.find(g => g.id === 'G005' || g.name.toLowerCase().includes('check'))

  const toggleSelection = (id: string) => {
    setSelected(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id])
  }

  const getTraitColor = (value: number, trait: string, allValues: number[]) => {
    if (allValues.length === 0 || allValues.every(v => v === 0)) return ''
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
    if (checkValue === 0) return { diff: 0, isPositive: true }
    const diff = ((value - checkValue) / checkValue) * 100
    const isPositive = higher ? diff > 0 : diff < 0
    return { diff, isPositive }
  }

  const exportCSV = () => {
    const headers = ['Germplasm', ...traits.map(t => `${t} (${traitInfo[t].unit})`)]
    const rows = comparisonData.map(g => [g.name, ...traits.map(t => g.traits[t]?.toFixed(2) || '-')])
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'phenotype_comparison.csv'
    a.click()
  }

  const isLoading = loadingGermplasm || loadingObservations

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Phenotype Comparison</h1>
          <p className="text-muted-foreground mt-1">Compare traits across germplasm</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline">{selected.length} selected</Badge>
          {comparisonData.length > 0 && (
            <Button variant="outline" size="sm" onClick={exportCSV}>
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Selection Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Select Germplasm</CardTitle>
            <CardDescription>Choose entries to compare</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading && germplasmList.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              germplasmList.map((g) => (
                <div key={g.id} className="flex items-center gap-2">
                  <Checkbox
                    id={g.id}
                    checked={selected.includes(g.id)}
                    onCheckedChange={() => toggleSelection(g.id)}
                  />
                  <Label htmlFor={g.id} className="text-sm cursor-pointer">
                    {g.name}
                    {(g.id === 'G005' || g.name.toLowerCase().includes('check') || g.isCheck) && (
                      <Badge variant="secondary" className="ml-2 text-xs">Check</Badge>
                    )}
                  </Label>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Comparison Table */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Trait Comparison</CardTitle>
            <CardDescription>
              {comparisonData.length > 0 ? `Comparing ${comparisonData.length} entries` : 'Select germplasm to compare'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {comparisonData.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="mt-2">Select germplasm entries to compare</p>
              </div>
            ) : loadingObservations ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Trait</th>
                      {comparisonData.map((g) => (
                        <th key={g.id} className="text-center p-2">
                          {g.name}
                          {(g.id === 'G005' || g.name.toLowerCase().includes('check')) && (
                            <span className="text-xs text-muted-foreground block">Check</span>
                          )}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {traits.map((trait) => {
                      const allValues = comparisonData.map(g => g.traits[trait] || 0)
                      return (
                        <tr key={trait} className="border-b">
                          <td className="p-2 font-medium capitalize">
                            {trait}
                            <span className="text-xs text-muted-foreground ml-1">({traitInfo[trait].unit})</span>
                          </td>
                          {comparisonData.map((g) => {
                            const value = g.traits[trait] || 0
                            const colorClass = getTraitColor(value, trait, allValues)
                            const checkValue = checkVariety?.traits[trait]
                            const diffInfo = checkValue ? calculateDiff(value, checkValue, traitInfo[trait].higher) : null
                            const isCheck = g.id === 'G005' || g.name.toLowerCase().includes('check')
                            
                            return (
                              <td key={g.id} className={`p-2 text-center ${colorClass}`}>
                                <span className="block">{value.toFixed(1)}</span>
                                {diffInfo && !isCheck && (
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

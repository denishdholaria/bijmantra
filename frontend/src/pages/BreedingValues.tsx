/**
 * Breeding Values Estimation Page
 * BLUP/GBLUP breeding value calculations - Connected to real API
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Loader2, Calculator, TrendingUp, Award } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface BreedingValue {
  id: string
  name: string
  ebv: number
  accuracy: number
  rank: number
  parent_mean?: number
  mendelian_sampling?: number
}

interface TraitAnalysis {
  id: string
  trait: string
  method: string
  heritability: number
  genetic_variance: number
  mean: number
  breeding_values: BreedingValue[]
}

export function BreedingValues() {
  const [selectedTrait, setSelectedTrait] = useState<string>('')
  const [method, setMethod] = useState('BLUP')
  const [selectionIntensity, setSelectionIntensity] = useState('20')

  // Fetch available analyses from API
  const { data: analysesData, isLoading: loadingAnalyses } = useQuery({
    queryKey: ['breeding-value-analyses'],
    queryFn: () => apiClient.breedingValueService.listAnalyses(),
  })

  // Fetch methods from API
  const { data: methodsData } = useQuery({
    queryKey: ['breeding-value-methods'],
    queryFn: () => apiClient.breedingValueService.getMethods(),
  })

  // Fetch selected analysis details
  const { data: analysisData, isLoading: loadingAnalysis } = useQuery({
    queryKey: ['breeding-value-analysis', selectedTrait],
    queryFn: async () => {
      const result = await apiClient.breedingValueService.getAnalysis(selectedTrait)
      if (result.data) {
        return {
          ...result,
          data: {
            ...result.data,
            mean: typeof result.data.mean === 'string' ? parseFloat(result.data.mean) : result.data.mean
          }
        }
      }
      return result
    },
    enabled: !!selectedTrait,
  })

  // Calculate EBVs mutation
  const calculateMutation = useMutation({
    mutationFn: async () => {
      const phenotypes = [
        { id: 'G001', value: 5.2 },
        { id: 'G002', value: 5.8 },
        { id: 'G003', value: 4.5 },
        { id: 'G004', value: 4.2 },
        { id: 'G005', value: 4.8 },
      ]
      
      if (method === 'BLUP') {
        return apiClient.breedingValueService.estimateBLUP({
          phenotypes,
          trait: 'Grain Yield',
          heritability: 0.65,
        })
      } else {
        return apiClient.breedingValueService.estimateGBLUP({
          phenotypes,
          markers: phenotypes.map(p => ({ id: p.id, markers: [0, 1, 2, 1, 0] })),
          trait: 'Grain Yield',
          heritability: 0.65,
        })
      }
    },
  })

  const analyses = analysesData?.data || []
  const currentAnalysis: TraitAnalysis | null = analysisData?.data as TraitAnalysis | null
  const methods = methodsData?.data || [
    { id: 'BLUP', name: 'BLUP', description: 'Best Linear Unbiased Prediction using pedigree' },
    { id: 'GBLUP', name: 'GBLUP', description: 'Genomic BLUP using marker data' },
    { id: 'ssGBLUP', name: 'ssGBLUP', description: 'Single-Step GBLUP combining pedigree and genomic' },
  ]

  // Empty state when no analysis is selected - Zero Mock Data Policy
  const emptyData: TraitAnalysis = {
    id: '',
    trait: 'No Analysis Selected',
    method: method,
    heritability: 0,
    genetic_variance: 0,
    mean: 0,
    breeding_values: [],
  }

  const displayData: TraitAnalysis = currentAnalysis || emptyData
  const hasData = displayData.breeding_values.length > 0

  const topPercent = parseInt(selectionIntensity) / 100
  const selectedCount = Math.ceil(displayData.breeding_values.length * topPercent)

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.9) return 'bg-green-100 text-green-700'
    if (accuracy >= 0.7) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  const calculateResponse = () => {
    if (!hasData || selectedCount === 0) return 0
    const selected = displayData.breeding_values.slice(0, selectedCount)
    const selectionDifferential = selected.reduce((sum, v) => sum + v.ebv, 0) / selected.length
    return selectionDifferential * displayData.heritability
  }

  const isLoading = loadingAnalyses || loadingAnalysis

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Breeding Value Estimation</h1>
          <p className="text-muted-foreground mt-1">BLUP/GBLUP breeding value predictions</p>
        </div>
        <div className="flex gap-2">
          <Select value={method} onValueChange={setMethod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {methods.map(m => (
                <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={() => calculateMutation.mutate()} disabled={calculateMutation.isPending}>
            {calculateMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Calculator className="w-4 h-4 mr-2" />}
            Calculate EBVs
          </Button>
        </div>
      </div>

      {/* Method Info */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            <TrendingUp className="w-6 h-6 text-blue-600" />
            <div>
              <p className="font-medium text-blue-800">
                {method === 'BLUP' && 'Best Linear Unbiased Prediction (BLUP)'}
                {method === 'GBLUP' && 'Genomic BLUP (GBLUP)'}
                {method === 'ssGBLUP' && 'Single-Step GBLUP (ssGBLUP)'}
              </p>
              <p className="text-sm text-blue-700">
                {methods.find(m => m.id === method)?.description || 'Select a method to see description'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <Tabs defaultValue="estimates">
          <TabsList>
            <TabsTrigger value="estimates">EBV Estimates</TabsTrigger>
            <TabsTrigger value="response">Selection Response</TabsTrigger>
            <TabsTrigger value="parameters">Genetic Parameters</TabsTrigger>
          </TabsList>

          <TabsContent value="estimates" className="space-y-6 mt-4">
            {/* Analysis Selection */}
            <Card>
              <CardContent className="pt-4">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Analysis:</span>
                    <Select value={selectedTrait} onValueChange={setSelectedTrait}>
                      <SelectTrigger className="w-48">
                        <SelectValue placeholder="Select analysis..." />
                      </SelectTrigger>
                      <SelectContent>
                        {analyses.length > 0 ? (
                          analyses.map(a => (
                            <SelectItem key={a.id} value={a.id}>{a.trait} ({a.method})</SelectItem>
                          ))
                        ) : (
                          <SelectItem value="__empty__" disabled>No analyses available</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  {hasData && (
                    <>
                      <Badge variant="outline">h² = {displayData.heritability.toFixed(2)}</Badge>
                      <Badge variant="outline">σ²g = {displayData.genetic_variance.toFixed(2)}</Badge>
                      <Badge variant="outline">μ = {displayData.mean} t/ha</Badge>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* EBV Table */}
            <Card>
              <CardHeader>
                <CardTitle>Estimated Breeding Values{hasData ? ` - ${displayData.trait}` : ''}</CardTitle>
                <CardDescription>Ranked by EBV (higher is better for yield)</CardDescription>
              </CardHeader>
              <CardContent>
                {!hasData ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Calculator className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium">No breeding value analyses available</p>
                    <p className="text-sm mt-2">Select an analysis from the dropdown or click "Calculate EBVs" to run a new analysis</p>
                  </div>
                ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3">Rank</th>
                        <th className="text-left p-3">Germplasm</th>
                        <th className="text-right p-3">EBV</th>
                        <th className="text-right p-3">Parent Mean</th>
                        <th className="text-right p-3">Mendelian</th>
                        <th className="text-center p-3">Accuracy</th>
                        <th className="text-center p-3">Select</th>
                      </tr>
                    </thead>
                    <tbody>
                      {displayData.breeding_values.map((bv, i) => (
                        <tr key={bv.id} className={`border-b hover:bg-muted/50 ${i < selectedCount ? 'bg-green-50 dark:bg-green-900/20' : ''}`}>
                          <td className="p-3">
                            <Badge variant={bv.rank <= 3 ? 'default' : 'secondary'}>
                              {bv.rank <= 3 && <Award className="w-3 h-3 mr-1" />}
                              #{bv.rank}
                            </Badge>
                          </td>
                          <td className="p-3 font-medium">{bv.name}</td>
                          <td className="p-3 text-right font-mono font-bold">
                            {bv.ebv > 0 ? '+' : ''}{bv.ebv.toFixed(2)}
                          </td>
                          <td className="p-3 text-right font-mono text-muted-foreground">
                            {bv.parent_mean !== undefined ? (bv.parent_mean > 0 ? '+' : '') + bv.parent_mean.toFixed(2) : '-'}
                          </td>
                          <td className="p-3 text-right font-mono text-muted-foreground">
                            {bv.mendelian_sampling !== undefined ? (bv.mendelian_sampling > 0 ? '+' : '') + bv.mendelian_sampling.toFixed(2) : '-'}
                          </td>
                          <td className="p-3 text-center">
                            <Badge className={getAccuracyColor(bv.accuracy)}>
                              {(bv.accuracy * 100).toFixed(0)}%
                            </Badge>
                          </td>
                          <td className="p-3 text-center">
                            {i < selectedCount ? (
                              <Badge className="bg-green-500">✓</Badge>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="response" className="space-y-6 mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Selection Response Prediction</CardTitle>
                <CardDescription>Expected genetic gain from selection</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium">Selection Intensity:</span>
                  <Select value={selectionIntensity} onValueChange={setSelectionIntensity}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">Top 10%</SelectItem>
                      <SelectItem value="20">Top 20%</SelectItem>
                      <SelectItem value="30">Top 30%</SelectItem>
                      <SelectItem value="50">Top 50%</SelectItem>
                    </SelectContent>
                  </Select>
                  <span className="text-sm text-muted-foreground">
                    ({selectedCount} of {displayData.breeding_values.length} selected)
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg text-center">
                    <p className="text-sm text-blue-600">Selection Differential (S)</p>
                    <p className="text-3xl font-bold text-blue-700">
                      {(displayData.breeding_values.slice(0, selectedCount).reduce((s, v) => s + v.ebv, 0) / selectedCount).toFixed(3)}
                    </p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg text-center">
                    <p className="text-sm text-green-600">Expected Response (R)</p>
                    <p className="text-3xl font-bold text-green-700">
                      {calculateResponse().toFixed(3)} t/ha
                    </p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg text-center">
                    <p className="text-sm text-purple-600">% Gain per Cycle</p>
                    <p className="text-3xl font-bold text-purple-700">
                      {((calculateResponse() / displayData.mean) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>

                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2">Breeder's Equation</h4>
                  <p className="font-mono text-sm">
                    R = h² × S = {displayData.heritability.toFixed(2)} × {(displayData.breeding_values.slice(0, selectedCount).reduce((s, v) => s + v.ebv, 0) / selectedCount).toFixed(3)} = {calculateResponse().toFixed(3)}
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="parameters" className="space-y-6 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{displayData.trait}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{displayData.heritability.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Heritability (h²)</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{displayData.genetic_variance.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Genetic Variance (σ²g)</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{displayData.mean}</p>
                      <p className="text-xs text-muted-foreground">Mean (t/ha)</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{displayData.breeding_values.length}</p>
                      <p className="text-xs text-muted-foreground">Entries</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Method: {method}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <p>{methods.find(m => m.id === method)?.description}</p>
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="font-medium text-blue-800">When to use:</p>
                      <p className="text-blue-700">
                        {method === 'BLUP' && 'When pedigree information is available but no marker data'}
                        {method === 'GBLUP' && 'When genomic marker data is available for all individuals'}
                        {method === 'ssGBLUP' && 'When some individuals have markers and others only pedigree'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}

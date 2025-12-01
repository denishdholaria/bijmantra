/**
 * Breeding Values Estimation Page
 * BLUP/GBLUP breeding value calculations
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface BreedingValue {
  germplasmId: string
  germplasmName: string
  ebv: number
  accuracy: number
  rank: number
  parentMean: number
  mendelianSampling: number
}

interface TraitBV {
  trait: string
  unit: string
  mean: number
  heritability: number
  geneticVariance: number
  values: BreedingValue[]
}

const sampleData: TraitBV[] = [
  {
    trait: 'Grain Yield',
    unit: 't/ha',
    mean: 4.5,
    heritability: 0.65,
    geneticVariance: 0.42,
    values: [
      { germplasmId: 'G001', germplasmName: 'Elite-2024-001', ebv: 0.85, accuracy: 0.92, rank: 1, parentMean: 0.62, mendelianSampling: 0.23 },
      { germplasmId: 'G002', germplasmName: 'Elite-2024-002', ebv: 0.72, accuracy: 0.88, rank: 2, parentMean: 0.55, mendelianSampling: 0.17 },
      { germplasmId: 'G003', germplasmName: 'Elite-2024-003', ebv: 0.68, accuracy: 0.85, rank: 3, parentMean: 0.48, mendelianSampling: 0.20 },
      { germplasmId: 'G004', germplasmName: 'Elite-2024-004', ebv: 0.55, accuracy: 0.90, rank: 4, parentMean: 0.42, mendelianSampling: 0.13 },
      { germplasmId: 'G005', germplasmName: 'Elite-2024-005', ebv: 0.48, accuracy: 0.82, rank: 5, parentMean: 0.38, mendelianSampling: 0.10 },
      { germplasmId: 'G006', germplasmName: 'Elite-2024-006', ebv: 0.35, accuracy: 0.78, rank: 6, parentMean: 0.30, mendelianSampling: 0.05 },
      { germplasmId: 'G007', germplasmName: 'Elite-2024-007', ebv: 0.22, accuracy: 0.75, rank: 7, parentMean: 0.25, mendelianSampling: -0.03 },
      { germplasmId: 'G008', germplasmName: 'Elite-2024-008', ebv: -0.15, accuracy: 0.80, rank: 8, parentMean: -0.10, mendelianSampling: -0.05 },
    ],
  },
  {
    trait: 'Plant Height',
    unit: 'cm',
    mean: 95,
    heritability: 0.82,
    geneticVariance: 125,
    values: [
      { germplasmId: 'G001', germplasmName: 'Elite-2024-001', ebv: -8.5, accuracy: 0.95, rank: 1, parentMean: -6.2, mendelianSampling: -2.3 },
      { germplasmId: 'G003', germplasmName: 'Elite-2024-003', ebv: -5.2, accuracy: 0.88, rank: 2, parentMean: -4.0, mendelianSampling: -1.2 },
      { germplasmId: 'G002', germplasmName: 'Elite-2024-002', ebv: -3.8, accuracy: 0.90, rank: 3, parentMean: -2.5, mendelianSampling: -1.3 },
    ],
  },
]

export function BreedingValues() {
  const [selectedTrait, setSelectedTrait] = useState('Grain Yield')
  const [method, setMethod] = useState('BLUP')
  const [selectionIntensity, setSelectionIntensity] = useState('20')

  const currentTrait = sampleData.find(t => t.trait === selectedTrait)
  const topPercent = parseInt(selectionIntensity) / 100
  const selectedCount = currentTrait ? Math.ceil(currentTrait.values.length * topPercent) : 0

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.9) return 'bg-green-100 text-green-700'
    if (accuracy >= 0.7) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  const calculateResponse = () => {
    if (!currentTrait) return 0
    const selected = currentTrait.values.slice(0, selectedCount)
    const selectionDifferential = selected.reduce((sum, v) => sum + v.ebv, 0) / selected.length
    return selectionDifferential * currentTrait.heritability
  }

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
              <SelectItem value="BLUP">BLUP</SelectItem>
              <SelectItem value="GBLUP">GBLUP</SelectItem>
              <SelectItem value="ssGBLUP">ssGBLUP</SelectItem>
            </SelectContent>
          </Select>
          <Button>🧮 Calculate EBVs</Button>
        </div>
      </div>

      {/* Method Info */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">📊</span>
            <div>
              <p className="font-medium text-blue-800">
                {method === 'BLUP' && 'Best Linear Unbiased Prediction (BLUP)'}
                {method === 'GBLUP' && 'Genomic BLUP (GBLUP)'}
                {method === 'ssGBLUP' && 'Single-Step GBLUP (ssGBLUP)'}
              </p>
              <p className="text-sm text-blue-700">
                {method === 'BLUP' && 'Uses pedigree relationships to predict breeding values'}
                {method === 'GBLUP' && 'Uses genomic relationships from marker data'}
                {method === 'ssGBLUP' && 'Combines pedigree and genomic information'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="estimates">
        <TabsList>
          <TabsTrigger value="estimates">EBV Estimates</TabsTrigger>
          <TabsTrigger value="response">Selection Response</TabsTrigger>
          <TabsTrigger value="parameters">Genetic Parameters</TabsTrigger>
        </TabsList>

        <TabsContent value="estimates" className="space-y-6 mt-4">
          {/* Trait Selection */}
          <Card>
            <CardContent className="pt-4">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Trait:</span>
                  <Select value={selectedTrait} onValueChange={setSelectedTrait}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {sampleData.map(t => (
                        <SelectItem key={t.trait} value={t.trait}>{t.trait}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {currentTrait && (
                  <>
                    <Badge variant="outline">h² = {currentTrait.heritability.toFixed(2)}</Badge>
                    <Badge variant="outline">σ²g = {currentTrait.geneticVariance.toFixed(2)}</Badge>
                    <Badge variant="outline">μ = {currentTrait.mean} {currentTrait.unit}</Badge>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* EBV Table */}
          {currentTrait && (
            <Card>
              <CardHeader>
                <CardTitle>Estimated Breeding Values - {currentTrait.trait}</CardTitle>
                <CardDescription>Ranked by EBV (higher is better for yield, lower for height)</CardDescription>
              </CardHeader>
              <CardContent>
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
                      {currentTrait.values.map((bv, i) => (
                        <tr key={bv.germplasmId} className={`border-b hover:bg-muted/50 ${i < selectedCount ? 'bg-green-50' : ''}`}>
                          <td className="p-3">
                            <Badge variant={bv.rank <= 3 ? 'default' : 'secondary'}>#{bv.rank}</Badge>
                          </td>
                          <td className="p-3 font-medium">{bv.germplasmName}</td>
                          <td className="p-3 text-right font-mono font-bold">
                            {bv.ebv > 0 ? '+' : ''}{bv.ebv.toFixed(2)}
                          </td>
                          <td className="p-3 text-right font-mono text-muted-foreground">
                            {bv.parentMean > 0 ? '+' : ''}{bv.parentMean.toFixed(2)}
                          </td>
                          <td className="p-3 text-right font-mono text-muted-foreground">
                            {bv.mendelianSampling > 0 ? '+' : ''}{bv.mendelianSampling.toFixed(2)}
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
              </CardContent>
            </Card>
          )}
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
                  ({selectedCount} of {currentTrait?.values.length || 0} selected)
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg text-center">
                  <p className="text-sm text-blue-600">Selection Differential (S)</p>
                  <p className="text-3xl font-bold text-blue-700">
                    {currentTrait ? (currentTrait.values.slice(0, selectedCount).reduce((s, v) => s + v.ebv, 0) / selectedCount).toFixed(3) : '-'}
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg text-center">
                  <p className="text-sm text-green-600">Expected Response (R)</p>
                  <p className="text-3xl font-bold text-green-700">
                    {calculateResponse().toFixed(3)} {currentTrait?.unit}
                  </p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg text-center">
                  <p className="text-sm text-purple-600">% Gain per Cycle</p>
                  <p className="text-3xl font-bold text-purple-700">
                    {currentTrait ? ((calculateResponse() / currentTrait.mean) * 100).toFixed(1) : '-'}%
                  </p>
                </div>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">Breeder's Equation</h4>
                <p className="font-mono text-sm">R = h² × S = {currentTrait?.heritability.toFixed(2)} × {currentTrait ? (currentTrait.values.slice(0, selectedCount).reduce((s, v) => s + v.ebv, 0) / selectedCount).toFixed(3) : '-'} = {calculateResponse().toFixed(3)}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="parameters" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {sampleData.map(trait => (
              <Card key={trait.trait}>
                <CardHeader>
                  <CardTitle className="text-base">{trait.trait}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{trait.heritability.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Heritability (h²)</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{trait.geneticVariance.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Genetic Variance (σ²g)</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{trait.mean}</p>
                      <p className="text-xs text-muted-foreground">Mean ({trait.unit})</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{trait.values.length}</p>
                      <p className="text-xs text-muted-foreground">Entries</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

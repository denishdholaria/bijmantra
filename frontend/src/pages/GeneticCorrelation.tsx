/**
 * Genetic Correlation Page
 * Analyze genetic correlations between traits for breeding decisions
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'

interface TraitCorrelation {
  trait1: string
  trait2: string
  geneticCorr: number
  phenotypicCorr: number
  environmentalCorr: number
  se: number
}

interface Trait {
  name: string
  heritability: number
  geneticVariance: number
  phenotypicVariance: number
}

const traits: Trait[] = [
  { name: 'Grain Yield', heritability: 0.45, geneticVariance: 125.5, phenotypicVariance: 278.9 },
  { name: 'Plant Height', heritability: 0.72, geneticVariance: 85.2, phenotypicVariance: 118.3 },
  { name: 'Days to Flowering', heritability: 0.68, geneticVariance: 12.4, phenotypicVariance: 18.2 },
  { name: 'Grain Weight', heritability: 0.58, geneticVariance: 2.8, phenotypicVariance: 4.8 },
  { name: 'Protein Content', heritability: 0.52, geneticVariance: 1.2, phenotypicVariance: 2.3 },
  { name: 'Drought Tolerance', heritability: 0.35, geneticVariance: 0.8, phenotypicVariance: 2.3 },
]

const correlations: TraitCorrelation[] = [
  { trait1: 'Grain Yield', trait2: 'Plant Height', geneticCorr: 0.45, phenotypicCorr: 0.38, environmentalCorr: 0.25, se: 0.08 },
  { trait1: 'Grain Yield', trait2: 'Days to Flowering', geneticCorr: -0.32, phenotypicCorr: -0.28, environmentalCorr: -0.18, se: 0.09 },
  { trait1: 'Grain Yield', trait2: 'Grain Weight', geneticCorr: 0.68, phenotypicCorr: 0.55, environmentalCorr: 0.35, se: 0.06 },
  { trait1: 'Grain Yield', trait2: 'Protein Content', geneticCorr: -0.42, phenotypicCorr: -0.35, environmentalCorr: -0.22, se: 0.08 },
  { trait1: 'Grain Yield', trait2: 'Drought Tolerance', geneticCorr: 0.28, phenotypicCorr: 0.22, environmentalCorr: 0.12, se: 0.10 },
  { trait1: 'Plant Height', trait2: 'Days to Flowering', geneticCorr: 0.55, phenotypicCorr: 0.48, environmentalCorr: 0.35, se: 0.07 },
  { trait1: 'Plant Height', trait2: 'Grain Weight', geneticCorr: 0.22, phenotypicCorr: 0.18, environmentalCorr: 0.12, se: 0.09 },
  { trait1: 'Days to Flowering', trait2: 'Grain Weight', geneticCorr: -0.15, phenotypicCorr: -0.12, environmentalCorr: -0.08, se: 0.10 },
  { trait1: 'Grain Weight', trait2: 'Protein Content', geneticCorr: -0.25, phenotypicCorr: -0.20, environmentalCorr: -0.12, se: 0.09 },
  { trait1: 'Protein Content', trait2: 'Drought Tolerance', geneticCorr: 0.18, phenotypicCorr: 0.15, environmentalCorr: 0.10, se: 0.11 },
]

export function GeneticCorrelation() {
  const [activeTab, setActiveTab] = useState('matrix')
  const [selectedTrait1, setSelectedTrait1] = useState('Grain Yield')
  const [selectedTrait2, setSelectedTrait2] = useState('Plant Height')
  const [correlationType, setCorrelationType] = useState('genetic')

  const getCorrelationColor = (corr: number) => {
    const absCorr = Math.abs(corr)
    if (absCorr >= 0.7) return corr > 0 ? 'bg-green-500' : 'bg-red-500'
    if (absCorr >= 0.4) return corr > 0 ? 'bg-green-300' : 'bg-red-300'
    if (absCorr >= 0.2) return corr > 0 ? 'bg-green-100' : 'bg-red-100'
    return 'bg-gray-100'
  }

  const getCorrelationBadge = (corr: number) => {
    const absCorr = Math.abs(corr)
    if (absCorr >= 0.7) return corr > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
    if (absCorr >= 0.4) return corr > 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
    return 'bg-gray-100 text-gray-600'
  }

  const selectedCorr = correlations.find(
    c => (c.trait1 === selectedTrait1 && c.trait2 === selectedTrait2) ||
         (c.trait1 === selectedTrait2 && c.trait2 === selectedTrait1)
  )

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genetic Correlations</h1>
          <p className="text-muted-foreground mt-1">Analyze trait relationships for breeding decisions</p>
        </div>
        <div className="flex gap-2">
          <Select value={correlationType} onValueChange={setCorrelationType}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="genetic">Genetic (rG)</SelectItem>
              <SelectItem value="phenotypic">Phenotypic (rP)</SelectItem>
              <SelectItem value="environmental">Environmental (rE)</SelectItem>
            </SelectContent>
          </Select>
          <Button>📊 Calculate</Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="matrix">Correlation Matrix</TabsTrigger>
          <TabsTrigger value="pairwise">Pairwise Analysis</TabsTrigger>
          <TabsTrigger value="heritability">Heritability</TabsTrigger>
          <TabsTrigger value="implications">Breeding Implications</TabsTrigger>
        </TabsList>

        <TabsContent value="matrix" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>
                {correlationType === 'genetic' ? 'Genetic' : correlationType === 'phenotypic' ? 'Phenotypic' : 'Environmental'} Correlation Matrix
              </CardTitle>
              <CardDescription>Pairwise correlations between traits</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className="p-2"></th>
                      {traits.map(t => (
                        <th key={t.name} className="p-2 text-center text-xs font-medium" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', height: '100px' }}>
                          {t.name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {traits.map((t1, i) => (
                      <tr key={t1.name}>
                        <td className="p-2 font-medium text-sm">{t1.name}</td>
                        {traits.map((t2, j) => {
                          if (i === j) {
                            return <td key={t2.name} className="p-1"><div className="w-10 h-10 bg-gray-300 rounded flex items-center justify-center text-xs">1.00</div></td>
                          }
                          const corr = correlations.find(
                            c => (c.trait1 === t1.name && c.trait2 === t2.name) ||
                                 (c.trait1 === t2.name && c.trait2 === t1.name)
                          )
                          const value = corr ? (
                            correlationType === 'genetic' ? corr.geneticCorr :
                            correlationType === 'phenotypic' ? corr.phenotypicCorr :
                            corr.environmentalCorr
                          ) : 0
                          return (
                            <td key={t2.name} className="p-1">
                              <div 
                                className={`w-10 h-10 ${getCorrelationColor(value)} rounded flex items-center justify-center text-xs cursor-pointer hover:opacity-80`}
                                title={`${t1.name} × ${t2.name}: ${value.toFixed(2)}`}
                              >
                                {value.toFixed(2)}
                              </div>
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-center gap-4 mt-4 text-sm">
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-red-500 rounded" />
                  <span>Strong negative</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-red-100 rounded" />
                  <span>Weak negative</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-gray-100 rounded" />
                  <span>Near zero</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-green-100 rounded" />
                  <span>Weak positive</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-green-500 rounded" />
                  <span>Strong positive</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pairwise" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Pairwise Correlation Analysis</CardTitle>
              <CardDescription>Detailed analysis of trait pair correlations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Trait 1</Label>
                  <Select value={selectedTrait1} onValueChange={setSelectedTrait1}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {traits.map(t => (
                        <SelectItem key={t.name} value={t.name}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Trait 2</Label>
                  <Select value={selectedTrait2} onValueChange={setSelectedTrait2}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {traits.map(t => (
                        <SelectItem key={t.name} value={t.name}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {selectedCorr && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="pt-4 text-center">
                      <p className="text-3xl font-bold text-blue-700">{selectedCorr.geneticCorr.toFixed(2)}</p>
                      <p className="text-sm text-blue-600">Genetic Correlation (rG)</p>
                      <p className="text-xs text-blue-500 mt-1">SE: ±{selectedCorr.se.toFixed(2)}</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-green-50 border-green-200">
                    <CardContent className="pt-4 text-center">
                      <p className="text-3xl font-bold text-green-700">{selectedCorr.phenotypicCorr.toFixed(2)}</p>
                      <p className="text-sm text-green-600">Phenotypic Correlation (rP)</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-purple-50 border-purple-200">
                    <CardContent className="pt-4 text-center">
                      <p className="text-3xl font-bold text-purple-700">{selectedCorr.environmentalCorr.toFixed(2)}</p>
                      <p className="text-sm text-purple-600">Environmental Correlation (rE)</p>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Scatter Plot Placeholder */}
              <div className="h-48 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">📈</span>
                  <p className="mt-2 text-muted-foreground">{selectedTrait1} vs {selectedTrait2}</p>
                  <p className="text-xs text-muted-foreground">Scatter plot with regression line</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* All Correlations Table */}
          <Card>
            <CardHeader>
              <CardTitle>All Pairwise Correlations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Trait 1</th>
                      <th className="text-left p-3">Trait 2</th>
                      <th className="text-right p-3">rG</th>
                      <th className="text-right p-3">rP</th>
                      <th className="text-right p-3">rE</th>
                      <th className="text-right p-3">SE</th>
                      <th className="text-center p-3">Significance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {correlations.map((corr, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{corr.trait1}</td>
                        <td className="p-3">{corr.trait2}</td>
                        <td className="p-3 text-right">
                          <Badge className={getCorrelationBadge(corr.geneticCorr)}>
                            {corr.geneticCorr.toFixed(2)}
                          </Badge>
                        </td>
                        <td className="p-3 text-right font-mono">{corr.phenotypicCorr.toFixed(2)}</td>
                        <td className="p-3 text-right font-mono">{corr.environmentalCorr.toFixed(2)}</td>
                        <td className="p-3 text-right font-mono">±{corr.se.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          {Math.abs(corr.geneticCorr) > 2 * corr.se ? (
                            <Badge className="bg-green-100 text-green-700">***</Badge>
                          ) : Math.abs(corr.geneticCorr) > 1.5 * corr.se ? (
                            <Badge className="bg-yellow-100 text-yellow-700">**</Badge>
                          ) : (
                            <Badge variant="secondary">ns</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="heritability" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trait Heritability & Variance Components</CardTitle>
              <CardDescription>Genetic parameters for each trait</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {traits.map((trait) => (
                  <div key={trait.name} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-bold">{trait.name}</h4>
                      <Badge className={trait.heritability >= 0.6 ? 'bg-green-100 text-green-700' : trait.heritability >= 0.4 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}>
                        h² = {trait.heritability.toFixed(2)}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Genetic Variance (σ²G)</p>
                        <p className="font-bold">{trait.geneticVariance.toFixed(1)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Phenotypic Variance (σ²P)</p>
                        <p className="font-bold">{trait.phenotypicVariance.toFixed(1)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Environmental Variance (σ²E)</p>
                        <p className="font-bold">{(trait.phenotypicVariance - trait.geneticVariance).toFixed(1)}</p>
                      </div>
                    </div>
                    <div className="mt-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-4 bg-muted rounded overflow-hidden">
                          <div 
                            className="h-full bg-primary"
                            style={{ width: `${trait.heritability * 100}%` }}
                          />
                        </div>
                        <span className="text-sm w-16">{(trait.heritability * 100).toFixed(0)}% genetic</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="implications" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Breeding Implications</CardTitle>
              <CardDescription>How genetic correlations affect selection decisions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Favorable Correlations */}
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-bold text-green-800 mb-2">✓ Favorable Correlations</h4>
                <div className="space-y-2 text-sm text-green-700">
                  <p>• <strong>Grain Yield × Grain Weight (rG = 0.68):</strong> Selection for larger grains will indirectly improve yield</p>
                  <p>• <strong>Plant Height × Days to Flowering (rG = 0.55):</strong> Taller plants tend to flower later</p>
                  <p>• <strong>Grain Yield × Drought Tolerance (rG = 0.28):</strong> Moderate positive correlation allows simultaneous improvement</p>
                </div>
              </div>

              {/* Unfavorable Correlations */}
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 className="font-bold text-red-800 mb-2">✗ Unfavorable Correlations</h4>
                <div className="space-y-2 text-sm text-red-700">
                  <p>• <strong>Grain Yield × Protein Content (rG = -0.42):</strong> Increasing yield may reduce protein - use index selection</p>
                  <p>• <strong>Grain Yield × Days to Flowering (rG = -0.32):</strong> Early maturity may reduce yield potential</p>
                  <p>• <strong>Grain Weight × Protein Content (rG = -0.25):</strong> Trade-off between grain size and quality</p>
                </div>
              </div>

              {/* Recommendations */}
              <Card className="border-blue-200 bg-blue-50">
                <CardHeader>
                  <CardTitle className="text-blue-800">💡 Selection Recommendations</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-blue-700 space-y-2">
                  <p>• Use <strong>selection index</strong> to balance negatively correlated traits</p>
                  <p>• Consider <strong>tandem selection</strong> for traits with low genetic correlation</p>
                  <p>• Exploit <strong>favorable correlations</strong> for indirect selection</p>
                  <p>• Monitor <strong>correlated response</strong> in non-target traits</p>
                  <p>• Use <strong>restricted selection index</strong> to maintain protein while improving yield</p>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

const Label = ({ children }: { children: React.ReactNode }) => (
  <label className="text-sm font-medium">{children}</label>
)

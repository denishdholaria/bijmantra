/**
 * QTL Mapping Interface
 * Quantitative Trait Loci mapping and marker-trait association analysis
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'

interface QTL {
  id: string
  name: string
  chromosome: string
  position: number
  lod: number
  pve: number
  addEffect: number
  domEffect: number
  flanking: [string, string]
  confidence: [number, number]
  trait: string
}

interface MarkerAssociation {
  marker: string
  chromosome: string
  position: number
  pValue: number
  logP: number
  effect: number
  maf: number
  trait: string
}

const sampleQTLs: QTL[] = [
  {
    id: 'qtl1',
    name: 'qYLD1.1',
    chromosome: '1',
    position: 45.2,
    lod: 8.5,
    pve: 15.2,
    addEffect: 0.85,
    domEffect: 0.12,
    flanking: ['SNP_1_42', 'SNP_1_48'],
    confidence: [42.1, 48.3],
    trait: 'Grain Yield',
  },
  {
    id: 'qtl2',
    name: 'qPH3.1',
    chromosome: '3',
    position: 78.6,
    lod: 12.3,
    pve: 22.8,
    addEffect: -2.45,
    domEffect: 0.35,
    flanking: ['SNP_3_75', 'SNP_3_82'],
    confidence: [75.2, 82.1],
    trait: 'Plant Height',
  },
  {
    id: 'qtl3',
    name: 'qDTF5.1',
    chromosome: '5',
    position: 112.4,
    lod: 6.8,
    pve: 11.5,
    addEffect: 1.2,
    domEffect: -0.08,
    flanking: ['SNP_5_108', 'SNP_5_116'],
    confidence: [108.5, 116.2],
    trait: 'Days to Flowering',
  },
  {
    id: 'qtl4',
    name: 'qGW7.1',
    chromosome: '7',
    position: 34.8,
    lod: 9.2,
    pve: 18.4,
    addEffect: 0.42,
    domEffect: 0.15,
    flanking: ['SNP_7_31', 'SNP_7_38'],
    confidence: [31.2, 38.5],
    trait: 'Grain Weight',
  },
]

const gwasResults: MarkerAssociation[] = [
  { marker: 'SNP_1_45', chromosome: '1', position: 45.2, pValue: 2.5e-8, logP: 7.6, effect: 0.82, maf: 0.35, trait: 'Grain Yield' },
  { marker: 'SNP_3_79', chromosome: '3', position: 79.1, pValue: 1.2e-12, logP: 11.9, effect: -2.38, maf: 0.42, trait: 'Plant Height' },
  { marker: 'SNP_5_112', chromosome: '5', position: 112.8, pValue: 8.5e-7, logP: 6.1, effect: 1.15, maf: 0.28, trait: 'Days to Flowering' },
  { marker: 'SNP_7_35', chromosome: '7', position: 35.2, pValue: 5.8e-9, logP: 8.2, effect: 0.45, maf: 0.38, trait: 'Grain Weight' },
  { marker: 'SNP_2_88', chromosome: '2', position: 88.5, pValue: 3.2e-6, logP: 5.5, effect: 0.28, maf: 0.31, trait: 'Grain Yield' },
  { marker: 'SNP_4_56', chromosome: '4', position: 56.3, pValue: 7.1e-5, logP: 4.1, effect: -0.95, maf: 0.22, trait: 'Plant Height' },
]

const chromosomes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

export function QTLMapping() {
  const [analysisType, setAnalysisType] = useState('linkage')
  const [selectedTrait, setSelectedTrait] = useState('all')
  const [lodThreshold, setLodThreshold] = useState([3.0])
  const [pThreshold, setPThreshold] = useState([5])

  const filteredQTLs = selectedTrait === 'all' 
    ? sampleQTLs 
    : sampleQTLs.filter(q => q.trait === selectedTrait)

  const filteredGWAS = selectedTrait === 'all'
    ? gwasResults
    : gwasResults.filter(g => g.trait === selectedTrait)

  const traits = [...new Set([...sampleQTLs.map(q => q.trait), ...gwasResults.map(g => g.trait)])]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">QTL Mapping</h1>
          <p className="text-muted-foreground mt-1">Marker-trait association and QTL analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedTrait} onValueChange={setSelectedTrait}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Select trait" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Traits</SelectItem>
              {traits.map(t => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button>🧬 Run Analysis</Button>
        </div>
      </div>

      <Tabs value={analysisType} onValueChange={setAnalysisType}>
        <TabsList>
          <TabsTrigger value="linkage">Linkage Mapping</TabsTrigger>
          <TabsTrigger value="gwas">GWAS</TabsTrigger>
          <TabsTrigger value="manhattan">Manhattan Plot</TabsTrigger>
          <TabsTrigger value="candidates">Candidate Genes</TabsTrigger>
        </TabsList>

        <TabsContent value="linkage" className="space-y-6 mt-4">
          {/* LOD Threshold */}
          <Card>
            <CardHeader>
              <CardTitle>Analysis Parameters</CardTitle>
              <CardDescription>Configure QTL detection thresholds</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label>LOD Threshold: {lodThreshold[0].toFixed(1)}</Label>
                  <Slider
                    value={lodThreshold}
                    onValueChange={setLodThreshold}
                    min={2}
                    max={10}
                    step={0.5}
                  />
                  <p className="text-xs text-muted-foreground">Minimum LOD score for QTL detection</p>
                </div>
                <div className="space-y-2">
                  <Label>Mapping Method</Label>
                  <Select defaultValue="cim">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sim">Simple Interval Mapping</SelectItem>
                      <SelectItem value="cim">Composite Interval Mapping</SelectItem>
                      <SelectItem value="mqm">Multiple QTL Mapping</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Population Type</Label>
                  <Select defaultValue="ril">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="f2">F2</SelectItem>
                      <SelectItem value="bc">Backcross</SelectItem>
                      <SelectItem value="ril">RIL</SelectItem>
                      <SelectItem value="dh">Doubled Haploid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* QTL Results Table */}
          <Card>
            <CardHeader>
              <CardTitle>Detected QTLs</CardTitle>
              <CardDescription>{filteredQTLs.length} QTLs above LOD threshold</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">QTL Name</th>
                      <th className="text-left p-3">Trait</th>
                      <th className="text-center p-3">Chr</th>
                      <th className="text-right p-3">Position (cM)</th>
                      <th className="text-right p-3">LOD</th>
                      <th className="text-right p-3">PVE (%)</th>
                      <th className="text-right p-3">Add. Effect</th>
                      <th className="text-left p-3">Flanking Markers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredQTLs.filter(q => q.lod >= lodThreshold[0]).map((qtl) => (
                      <tr key={qtl.id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{qtl.name}</td>
                        <td className="p-3">
                          <Badge variant="outline">{qtl.trait}</Badge>
                        </td>
                        <td className="p-3 text-center">{qtl.chromosome}</td>
                        <td className="p-3 text-right font-mono">{qtl.position.toFixed(1)}</td>
                        <td className="p-3 text-right">
                          <span className={`font-bold ${qtl.lod >= 8 ? 'text-green-600' : qtl.lod >= 5 ? 'text-yellow-600' : 'text-muted-foreground'}`}>
                            {qtl.lod.toFixed(1)}
                          </span>
                        </td>
                        <td className="p-3 text-right font-mono">{qtl.pve.toFixed(1)}%</td>
                        <td className="p-3 text-right font-mono">
                          <span className={qtl.addEffect > 0 ? 'text-green-600' : 'text-red-600'}>
                            {qtl.addEffect > 0 ? '+' : ''}{qtl.addEffect.toFixed(2)}
                          </span>
                        </td>
                        <td className="p-3 text-xs">{qtl.flanking.join(' - ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* LOD Profile Visualization */}
          <Card>
            <CardHeader>
              <CardTitle>LOD Profile</CardTitle>
              <CardDescription>Genome-wide LOD score distribution</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {chromosomes.slice(0, 7).map((chr) => {
                  const chrQTLs = filteredQTLs.filter(q => q.chromosome === chr)
                  return (
                    <div key={chr} className="flex items-center gap-4">
                      <span className="w-8 text-sm font-medium">Chr {chr}</span>
                      <div className="flex-1 h-8 bg-muted rounded relative">
                        {chrQTLs.map((qtl) => (
                          <div
                            key={qtl.id}
                            className="absolute top-0 h-full w-2 bg-primary rounded cursor-pointer hover:bg-primary/80"
                            style={{ left: `${(qtl.position / 150) * 100}%` }}
                            title={`${qtl.name}: LOD ${qtl.lod.toFixed(1)}`}
                          />
                        ))}
                        <div 
                          className="absolute top-0 h-full border-l-2 border-dashed border-red-500"
                          style={{ left: '0%' }}
                        />
                      </div>
                      <span className="w-16 text-xs text-muted-foreground">150 cM</span>
                    </div>
                  )
                })}
                <div className="flex items-center gap-2 mt-2 text-sm">
                  <div className="w-4 h-4 bg-primary rounded" />
                  <span>QTL Peak</span>
                  <div className="w-4 h-0.5 border-t-2 border-dashed border-red-500 ml-4" />
                  <span>LOD Threshold ({lodThreshold[0].toFixed(1)})</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="gwas" className="space-y-6 mt-4">
          {/* GWAS Parameters */}
          <Card>
            <CardHeader>
              <CardTitle>GWAS Parameters</CardTitle>
              <CardDescription>Genome-wide association study settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>-log10(P) Threshold: {pThreshold[0]}</Label>
                  <Slider
                    value={pThreshold}
                    onValueChange={setPThreshold}
                    min={3}
                    max={10}
                    step={0.5}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Model</Label>
                  <Select defaultValue="mlm">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="glm">GLM</SelectItem>
                      <SelectItem value="mlm">MLM</SelectItem>
                      <SelectItem value="cmlm">CMLM</SelectItem>
                      <SelectItem value="farmcpu">FarmCPU</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>MAF Filter</Label>
                  <Input type="number" defaultValue="0.05" step="0.01" />
                </div>
                <div className="space-y-2">
                  <Label>Missing Rate</Label>
                  <Input type="number" defaultValue="0.2" step="0.05" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* GWAS Results */}
          <Card>
            <CardHeader>
              <CardTitle>Significant Associations</CardTitle>
              <CardDescription>{filteredGWAS.filter(g => g.logP >= pThreshold[0]).length} markers above threshold</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Marker</th>
                      <th className="text-left p-3">Trait</th>
                      <th className="text-center p-3">Chr</th>
                      <th className="text-right p-3">Position</th>
                      <th className="text-right p-3">P-value</th>
                      <th className="text-right p-3">-log10(P)</th>
                      <th className="text-right p-3">Effect</th>
                      <th className="text-right p-3">MAF</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredGWAS
                      .filter(g => g.logP >= pThreshold[0])
                      .sort((a, b) => b.logP - a.logP)
                      .map((assoc) => (
                        <tr key={assoc.marker} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-mono font-medium">{assoc.marker}</td>
                          <td className="p-3">
                            <Badge variant="outline">{assoc.trait}</Badge>
                          </td>
                          <td className="p-3 text-center">{assoc.chromosome}</td>
                          <td className="p-3 text-right font-mono">{assoc.position.toFixed(1)}</td>
                          <td className="p-3 text-right font-mono text-xs">{assoc.pValue.toExponential(1)}</td>
                          <td className="p-3 text-right">
                            <span className={`font-bold ${assoc.logP >= 8 ? 'text-red-600' : assoc.logP >= 5 ? 'text-orange-600' : 'text-yellow-600'}`}>
                              {assoc.logP.toFixed(1)}
                            </span>
                          </td>
                          <td className="p-3 text-right font-mono">
                            <span className={assoc.effect > 0 ? 'text-green-600' : 'text-red-600'}>
                              {assoc.effect > 0 ? '+' : ''}{assoc.effect.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-3 text-right font-mono">{assoc.maf.toFixed(2)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manhattan" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Manhattan Plot</CardTitle>
              <CardDescription>Genome-wide association visualization</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Simulated Manhattan Plot */}
              <div className="h-64 bg-muted rounded-lg p-4">
                <div className="h-full flex items-end gap-1">
                  {chromosomes.map((chr, i) => (
                    <div key={chr} className="flex-1 flex flex-col justify-end gap-0.5">
                      {/* Simulated dots */}
                      {Array.from({ length: 15 }).map((_, j) => {
                        const height = Math.random() * 60 + 10
                        const isSignificant = gwasResults.some(g => g.chromosome === chr && g.logP >= pThreshold[0])
                        const isPeak = j === 7 && isSignificant
                        return (
                          <div
                            key={j}
                            className={`w-1.5 h-1.5 rounded-full mx-auto ${
                              isPeak ? 'bg-red-500' : i % 2 === 0 ? 'bg-blue-400' : 'bg-blue-600'
                            }`}
                            style={{ 
                              marginBottom: `${isPeak ? height + 40 : height}%`,
                              opacity: isPeak ? 1 : 0.6
                            }}
                          />
                        )
                      })}
                      <span className="text-xs text-center mt-2">{chr}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between mt-4 text-sm">
                <span className="text-muted-foreground">Chromosome</span>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-0.5 bg-red-500" />
                    <span>Significance threshold (-log10(P) = {pThreshold[0]})</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* QQ Plot */}
          <Card>
            <CardHeader>
              <CardTitle>Q-Q Plot</CardTitle>
              <CardDescription>Quantile-quantile plot for model validation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-48 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">📈</span>
                  <p className="mt-2 text-muted-foreground">Q-Q Plot</p>
                  <p className="text-xs text-muted-foreground">Genomic inflation factor (λ) = 1.02</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="candidates" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Candidate Genes</CardTitle>
              <CardDescription>Genes within QTL confidence intervals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredQTLs.map((qtl) => (
                  <div key={qtl.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-bold">{qtl.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          Chr {qtl.chromosome}: {qtl.confidence[0].toFixed(1)} - {qtl.confidence[1].toFixed(1)} cM
                        </p>
                      </div>
                      <Badge>{qtl.trait}</Badge>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {['Gene_A', 'Gene_B', 'Gene_C'].map((gene, i) => (
                        <div key={gene} className="p-2 bg-muted rounded text-sm">
                          <p className="font-mono font-medium">{gene}_{qtl.chromosome}_{i + 1}</p>
                          <p className="text-xs text-muted-foreground">
                            {['Transcription factor', 'Kinase', 'Transporter'][i]}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Gene Ontology */}
          <Card>
            <CardHeader>
              <CardTitle>GO Enrichment</CardTitle>
              <CardDescription>Gene Ontology enrichment analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { term: 'Response to abiotic stress', pValue: 0.001, genes: 8 },
                  { term: 'Carbohydrate metabolic process', pValue: 0.005, genes: 5 },
                  { term: 'Regulation of growth', pValue: 0.012, genes: 4 },
                  { term: 'Photosynthesis', pValue: 0.023, genes: 3 },
                ].map((go, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-muted rounded">
                    <div>
                      <p className="font-medium">{go.term}</p>
                      <p className="text-xs text-muted-foreground">{go.genes} genes</p>
                    </div>
                    <Badge variant={go.pValue < 0.01 ? 'default' : 'secondary'}>
                      P = {go.pValue.toFixed(3)}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

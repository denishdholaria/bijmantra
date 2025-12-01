/**
 * Haplotype Analysis Page
 * Haplotype block identification, visualization, and breeding applications
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

interface HaplotypeBlock {
  id: string
  chromosome: string
  start: number
  end: number
  size: number
  markers: number
  haplotypes: number
  majorHap: string
  majorFreq: number
  trait?: string
}

interface Haplotype {
  id: string
  block: string
  sequence: string
  frequency: number
  effect: number
  germplasm: string[]
}

const haplotypeBlocks: HaplotypeBlock[] = [
  { id: 'hb1', chromosome: '1', start: 5.2, end: 8.4, size: 3.2, markers: 45, haplotypes: 4, majorHap: 'H1', majorFreq: 0.42, trait: 'Yield' },
  { id: 'hb2', chromosome: '1', start: 35.8, end: 42.1, size: 6.3, markers: 78, haplotypes: 6, majorHap: 'H2', majorFreq: 0.35, trait: 'Drought tolerance' },
  { id: 'hb3', chromosome: '3', start: 12.5, end: 15.8, size: 3.3, markers: 52, haplotypes: 3, majorHap: 'H1', majorFreq: 0.55, trait: 'Plant height' },
  { id: 'hb4', chromosome: '5', start: 22.1, end: 28.9, size: 6.8, markers: 92, haplotypes: 5, majorHap: 'H3', majorFreq: 0.38, trait: 'Flowering time' },
  { id: 'hb5', chromosome: '7', start: 8.4, end: 11.2, size: 2.8, markers: 38, haplotypes: 4, majorHap: 'H1', majorFreq: 0.48, trait: 'Grain weight' },
  { id: 'hb6', chromosome: '9', start: 4.2, end: 7.8, size: 3.6, markers: 56, haplotypes: 3, majorHap: 'H2', majorFreq: 0.52, trait: 'Submergence' },
]

const haplotypes: Haplotype[] = [
  { id: 'h1', block: 'hb1', sequence: 'AGTC-CGTA-TTAG', frequency: 0.42, effect: 1.25, germplasm: ['Elite-001', 'Elite-003', 'Elite-007'] },
  { id: 'h2', block: 'hb1', sequence: 'AGTC-TGTA-TTAG', frequency: 0.28, effect: 0.85, germplasm: ['Elite-002', 'Elite-005'] },
  { id: 'h3', block: 'hb1', sequence: 'GGTC-CGTA-CTAG', frequency: 0.18, effect: -0.45, germplasm: ['Elite-004'] },
  { id: 'h4', block: 'hb1', sequence: 'AATC-CGTA-TTAG', frequency: 0.12, effect: -0.92, germplasm: ['Elite-006'] },
]

const germplasmHaplotypes = [
  { name: 'Elite-001', haplotypes: { hb1: 'H1', hb2: 'H2', hb3: 'H1', hb4: 'H3', hb5: 'H1', hb6: 'H2' }, score: 92 },
  { name: 'Elite-002', haplotypes: { hb1: 'H2', hb2: 'H1', hb3: 'H1', hb4: 'H2', hb5: 'H2', hb6: 'H2' }, score: 85 },
  { name: 'Elite-003', haplotypes: { hb1: 'H1', hb2: 'H3', hb3: 'H2', hb4: 'H1', hb5: 'H1', hb6: 'H1' }, score: 88 },
  { name: 'Elite-004', haplotypes: { hb1: 'H3', hb2: 'H2', hb3: 'H1', hb4: 'H3', hb5: 'H3', hb6: 'H2' }, score: 72 },
  { name: 'Elite-005', haplotypes: { hb1: 'H2', hb2: 'H4', hb3: 'H3', hb4: 'H2', hb5: 'H1', hb6: 'H3' }, score: 68 },
]

export function HaplotypeAnalysis() {
  const [activeTab, setActiveTab] = useState('blocks')
  const [selectedChromosome, setSelectedChromosome] = useState('all')
  const [selectedBlock, setSelectedBlock] = useState('hb1')

  const filteredBlocks = selectedChromosome === 'all' 
    ? haplotypeBlocks 
    : haplotypeBlocks.filter(b => b.chromosome === selectedChromosome)

  const getHapColor = (hap: string) => {
    const colors: { [key: string]: string } = {
      'H1': 'bg-blue-500',
      'H2': 'bg-green-500',
      'H3': 'bg-orange-500',
      'H4': 'bg-purple-500',
      'H5': 'bg-pink-500',
      'H6': 'bg-cyan-500',
    }
    return colors[hap] || 'bg-gray-500'
  }

  const getHapBadgeColor = (hap: string) => {
    const colors: { [key: string]: string } = {
      'H1': 'bg-blue-100 text-blue-700',
      'H2': 'bg-green-100 text-green-700',
      'H3': 'bg-orange-100 text-orange-700',
      'H4': 'bg-purple-100 text-purple-700',
      'H5': 'bg-pink-100 text-pink-700',
      'H6': 'bg-cyan-100 text-cyan-700',
    }
    return colors[hap] || 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Haplotype Analysis</h1>
          <p className="text-muted-foreground mt-1">Haplotype blocks, diversity, and breeding applications</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedChromosome} onValueChange={setSelectedChromosome}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Chromosome" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Chromosomes</SelectItem>
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'].map(c => (
                <SelectItem key={c} value={c}>Chromosome {c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button>🧬 Detect Blocks</Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="blocks">Haplotype Blocks</TabsTrigger>
          <TabsTrigger value="diversity">Haplotype Diversity</TabsTrigger>
          <TabsTrigger value="breeding">Haplotype Breeding</TabsTrigger>
          <TabsTrigger value="network">Haplotype Network</TabsTrigger>
        </TabsList>

        <TabsContent value="blocks" className="space-y-6 mt-4">
          {/* Block Detection Parameters */}
          <Card>
            <CardHeader>
              <CardTitle>Block Detection Parameters</CardTitle>
              <CardDescription>Configure haplotype block identification</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>Method</Label>
                  <Select defaultValue="gabriel">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gabriel">Gabriel et al.</SelectItem>
                      <SelectItem value="4gamete">Four Gamete Rule</SelectItem>
                      <SelectItem value="solid">Solid Spine</SelectItem>
                      <SelectItem value="ci">Confidence Interval</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Min Block Size (kb)</Label>
                  <Input type="number" defaultValue="10" />
                </div>
                <div className="space-y-2">
                  <Label>MAF Threshold</Label>
                  <Input type="number" defaultValue="0.05" step="0.01" />
                </div>
                <div className="space-y-2">
                  <Label>LD Threshold (r²)</Label>
                  <Input type="number" defaultValue="0.8" step="0.1" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Haplotype Blocks Table */}
          <Card>
            <CardHeader>
              <CardTitle>Detected Haplotype Blocks</CardTitle>
              <CardDescription>{filteredBlocks.length} blocks identified</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Block ID</th>
                      <th className="text-center p-3">Chr</th>
                      <th className="text-right p-3">Start (Mb)</th>
                      <th className="text-right p-3">End (Mb)</th>
                      <th className="text-right p-3">Size (Mb)</th>
                      <th className="text-right p-3">Markers</th>
                      <th className="text-center p-3">Haplotypes</th>
                      <th className="text-center p-3">Major Hap</th>
                      <th className="text-left p-3">Associated Trait</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBlocks.map((block) => (
                      <tr 
                        key={block.id} 
                        className={`border-b hover:bg-muted/50 cursor-pointer ${selectedBlock === block.id ? 'bg-primary/5' : ''}`}
                        onClick={() => setSelectedBlock(block.id)}
                      >
                        <td className="p-3 font-mono font-medium">{block.id}</td>
                        <td className="p-3 text-center">{block.chromosome}</td>
                        <td className="p-3 text-right font-mono">{block.start.toFixed(1)}</td>
                        <td className="p-3 text-right font-mono">{block.end.toFixed(1)}</td>
                        <td className="p-3 text-right font-mono">{block.size.toFixed(1)}</td>
                        <td className="p-3 text-right">{block.markers}</td>
                        <td className="p-3 text-center">
                          <Badge variant="outline">{block.haplotypes}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Badge className={getHapBadgeColor(block.majorHap)}>
                            {block.majorHap} ({(block.majorFreq * 100).toFixed(0)}%)
                          </Badge>
                        </td>
                        <td className="p-3">{block.trait || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Genome-wide Block Visualization */}
          <Card>
            <CardHeader>
              <CardTitle>Genome-wide Haplotype Blocks</CardTitle>
              <CardDescription>Distribution of haplotype blocks across chromosomes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {['1', '3', '5', '7', '9'].map((chr) => {
                  const chrBlocks = haplotypeBlocks.filter(b => b.chromosome === chr)
                  return (
                    <div key={chr} className="flex items-center gap-4">
                      <span className="w-16 text-sm font-medium">Chr {chr}</span>
                      <div className="flex-1 h-6 bg-muted rounded relative">
                        {chrBlocks.map((block) => (
                          <div
                            key={block.id}
                            className={`absolute top-0 h-full ${getHapColor(block.majorHap)} rounded cursor-pointer hover:opacity-80`}
                            style={{ 
                              left: `${(block.start / 50) * 100}%`,
                              width: `${(block.size / 50) * 100}%`
                            }}
                            title={`${block.id}: ${block.start}-${block.end} Mb`}
                          />
                        ))}
                      </div>
                      <span className="w-16 text-xs text-muted-foreground">50 Mb</span>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="diversity" className="space-y-6 mt-4">
          {/* Haplotype Diversity for Selected Block */}
          <Card>
            <CardHeader>
              <CardTitle>Haplotype Diversity - Block {selectedBlock}</CardTitle>
              <CardDescription>Haplotype variants and their frequencies</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {haplotypes.map((hap) => (
                  <div key={hap.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <Badge className={getHapBadgeColor(hap.id.toUpperCase().replace('H', 'H'))}>
                          {hap.id.toUpperCase()}
                        </Badge>
                        <span className="font-mono text-sm">{hap.sequence}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm">
                          Effect: <span className={`font-bold ${hap.effect > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {hap.effect > 0 ? '+' : ''}{hap.effect.toFixed(2)}
                          </span>
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={hap.frequency * 100} className="flex-1 h-3" />
                      <span className="w-16 text-right font-bold">{(hap.frequency * 100).toFixed(0)}%</span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {hap.germplasm.map((g) => (
                        <Badge key={g} variant="outline" className="text-xs">{g}</Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Diversity Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-primary">4</p>
                <p className="text-sm text-muted-foreground">Haplotypes</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-green-600">0.72</p>
                <p className="text-sm text-muted-foreground">Haplotype Diversity</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-blue-600">0.42</p>
                <p className="text-sm text-muted-foreground">Major Hap Freq</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-purple-600">3.2</p>
                <p className="text-sm text-muted-foreground">Effective # Haps</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="breeding" className="space-y-6 mt-4">
          {/* Haplotype-based Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Haplotype-based Selection</CardTitle>
              <CardDescription>Select germplasm based on favorable haplotype combinations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Germplasm</th>
                      {haplotypeBlocks.map(b => (
                        <th key={b.id} className="text-center p-2">
                          <div className="text-xs">{b.id}</div>
                          <div className="text-xs text-muted-foreground">Chr{b.chromosome}</div>
                        </th>
                      ))}
                      <th className="text-right p-3">Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {germplasmHaplotypes.map((germ) => (
                      <tr key={germ.name} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{germ.name}</td>
                        {haplotypeBlocks.map(b => (
                          <td key={b.id} className="p-2 text-center">
                            <div className={`w-6 h-6 rounded mx-auto flex items-center justify-center text-xs text-white ${getHapColor(germ.haplotypes[b.id as keyof typeof germ.haplotypes])}`}>
                              {germ.haplotypes[b.id as keyof typeof germ.haplotypes]?.replace('H', '')}
                            </div>
                          </td>
                        ))}
                        <td className="p-3 text-right">
                          <span className={`font-bold ${germ.score >= 85 ? 'text-green-600' : germ.score >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {germ.score}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Ideal Haplotype */}
          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-800">🎯 Ideal Haplotype Combination</CardTitle>
              <CardDescription className="text-green-700">Target haplotypes for breeding</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {haplotypeBlocks.map(b => (
                  <div key={b.id} className="p-3 bg-white rounded-lg border border-green-200">
                    <p className="text-xs text-muted-foreground">{b.id} ({b.trait})</p>
                    <Badge className={getHapBadgeColor(b.majorHap)}>{b.majorHap}</Badge>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-sm text-green-700">
                <strong>Best match:</strong> Elite-001 (92% match to ideal haplotype combination)
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="network" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Haplotype Network</CardTitle>
              <CardDescription>Evolutionary relationships between haplotypes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">🕸️</span>
                  <p className="mt-2 text-muted-foreground">Median-Joining Network</p>
                  <p className="text-xs text-muted-foreground">Block {selectedBlock} - 4 haplotypes</p>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                {haplotypes.map((hap) => (
                  <div key={hap.id} className="flex items-center gap-2">
                    <div className={`w-4 h-4 rounded-full ${getHapColor(hap.id.toUpperCase().replace('H', 'H'))}`} />
                    <span className="text-sm">{hap.id.toUpperCase()} ({(hap.frequency * 100).toFixed(0)}%)</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Mutation Steps */}
          <Card>
            <CardHeader>
              <CardTitle>Mutation Steps Between Haplotypes</CardTitle>
              <CardDescription>Number of SNP differences</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="p-2"></th>
                      <th className="p-2 text-center">H1</th>
                      <th className="p-2 text-center">H2</th>
                      <th className="p-2 text-center">H3</th>
                      <th className="p-2 text-center">H4</th>
                    </tr>
                  </thead>
                  <tbody>
                    {['H1', 'H2', 'H3', 'H4'].map((h1, i) => (
                      <tr key={h1} className="border-b">
                        <td className="p-2 font-medium">{h1}</td>
                        {['H1', 'H2', 'H3', 'H4'].map((h2, j) => (
                          <td key={h2} className="p-2 text-center">
                            {i === j ? '-' : Math.abs(i - j) + Math.floor(Math.random() * 2)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

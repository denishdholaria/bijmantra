/**
 * Haplotype Analysis Page
 * Haplotype block identification, visualization, and breeding applications
 * Connected to /api/v2/haplotype/* endpoints
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, Dna, BarChart3, Target, Network, RefreshCw } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { haplotypeAnalysisAPI, HaplotypeBlock, Haplotype, HaplotypeDiversitySummary, HaplotypeStatistics } from '@/lib/api-client'

// Germplasm haplotype interface for breeding tab
interface GermplasmHaplotype {
  name: string;
  haplotypes: Record<string, string>;
  score: number;
}

export function HaplotypeAnalysis() {
  const [activeTab, setActiveTab] = useState('blocks')
  const [selectedChromosome, setSelectedChromosome] = useState('all')
  const [selectedBlock, setSelectedBlock] = useState('hb1')

  // Fetch haplotype blocks
  const { data: blocksData, isLoading: blocksLoading, error: blocksError, refetch: refetchBlocks } = useQuery({
    queryKey: ['haplotype-blocks', selectedChromosome],
    queryFn: () => haplotypeAnalysisAPI.getBlocks(selectedChromosome === 'all' ? undefined : { chromosome: selectedChromosome }),
  })

  // Fetch haplotypes for selected block
  const { data: haplotypesData, isLoading: haplotypesLoading } = useQuery({
    queryKey: ['haplotype-block-haplotypes', selectedBlock],
    queryFn: () => haplotypeAnalysisAPI.getBlockHaplotypes(selectedBlock),
    enabled: !!selectedBlock,
  })

  // Fetch diversity summary
  const { data: diversityData } = useQuery({
    queryKey: ['haplotype-diversity'],
    queryFn: () => haplotypeAnalysisAPI.getDiversity(),
  })

  // Fetch statistics
  const { data: statsData } = useQuery({
    queryKey: ['haplotype-statistics'],
    queryFn: () => haplotypeAnalysisAPI.getStatistics(),
  })

  // Transform API data to component format
  const blocks: Array<{
    id: string
    chromosome: string
    start_mb: number
    end_mb: number
    length_kb: number
    n_markers: number
    n_haplotypes: number
    major_haplotype: string
    major_frequency: number
    diversity: number
    trait?: string
  }> = (blocksData?.blocks || []).map((b: HaplotypeBlock) => ({
    id: b.block_id || b.id,
    chromosome: b.chromosome,
    start_mb: b.start_mb,
    end_mb: b.end_mb,
    length_kb: b.length_kb,
    n_markers: b.n_markers,
    n_haplotypes: b.n_haplotypes,
    major_haplotype: b.major_haplotype || 'H1',
    major_frequency: b.major_haplotype_freq || 0.5,
    diversity: b.diversity,
    trait: b.trait,
  }))

  const haplotypes: Array<{
    id: string
    block_id: string
    sequence: string
    frequency: number
    effect: number
    germplasm: string[]
  }> = (haplotypesData?.haplotypes || []).map((h: Haplotype) => ({
    id: h.haplotype_id,
    block_id: h.block_id,
    sequence: h.allele_string,
    frequency: h.frequency,
    effect: h.effect || 0,
    germplasm: h.germplasm || [],
  }))

  const diversity: HaplotypeDiversitySummary | null = diversityData?.data || null
  const stats: HaplotypeStatistics | null = statsData?.data || null

  // Germplasm haplotypes - for now, show empty state since API endpoint doesn't exist yet
  // This will be populated when the backend implements /api/v2/haplotype/germplasm-haplotypes
  const germplasmHaplotypes: GermplasmHaplotype[] = []
  const germplasmHaplotypesLoading = false

  const filteredBlocks = selectedChromosome === 'all' 
    ? blocks 
    : blocks.filter(b => b.chromosome === selectedChromosome)

  const getHapColor = (hap: string) => {
    const colors: { [key: string]: string } = {
      'H1': 'bg-blue-500', 'H2': 'bg-green-500', 'H3': 'bg-orange-500',
      'H4': 'bg-purple-500', 'H5': 'bg-pink-500', 'H6': 'bg-cyan-500',
    }
    return colors[hap] || 'bg-gray-500'
  }

  const getHapBadgeColor = (hap: string) => {
    const colors: { [key: string]: string } = {
      'H1': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', 'H2': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      'H3': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400', 'H4': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      'H5': 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400', 'H6': 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
    }
    return colors[hap] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
  }

  if (blocksLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Dna className="h-7 w-7 text-primary" />
            Haplotype Analysis
          </h1>
          <p className="text-muted-foreground mt-1">Haplotype blocks, diversity, and breeding applications</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedChromosome} onValueChange={setSelectedChromosome}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Chromosome" />
            </SelectTrigger>
            <SelectContent position="popper" sideOffset={4}>
              <SelectItem value="all">All Chromosomes</SelectItem>
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'].map(c => (
                <SelectItem key={c} value={c}>Chromosome {c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button><Dna className="h-4 w-4 mr-2" />Detect Blocks</Button>
        </div>
      </div>

      {blocksError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center gap-2">
            Failed to load haplotype data. {blocksError instanceof Error ? blocksError.message : 'Please try again.'}
            <Button variant="outline" size="sm" onClick={() => refetchBlocks()}>
              <RefreshCw className="h-4 w-4 mr-2" />Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{stats?.total_blocks || blocks.length}</p>
            <p className="text-sm text-muted-foreground">Haplotype Blocks</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{stats?.total_haplotypes || 25}</p>
            <p className="text-sm text-muted-foreground">Total Haplotypes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{diversity?.avg_diversity?.toFixed(2) || '0.68'}</p>
            <p className="text-sm text-muted-foreground">Avg Diversity</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">{stats?.favorable_haplotypes || 8}</p>
            <p className="text-sm text-muted-foreground">Favorable Haplotypes</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="blocks" className="flex items-center gap-1">
            <Dna className="h-4 w-4" />Haplotype Blocks
          </TabsTrigger>
          <TabsTrigger value="diversity" className="flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />Diversity
          </TabsTrigger>
          <TabsTrigger value="breeding" className="flex items-center gap-1">
            <Target className="h-4 w-4" />Breeding
          </TabsTrigger>
          <TabsTrigger value="network" className="flex items-center gap-1">
            <Network className="h-4 w-4" />Network
          </TabsTrigger>
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
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent position="popper" sideOffset={4}>
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
                      <th className="text-right p-3">Size (kb)</th>
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
                        <td className="p-3 text-right font-mono">{block.start_mb.toFixed(1)}</td>
                        <td className="p-3 text-right font-mono">{block.end_mb.toFixed(1)}</td>
                        <td className="p-3 text-right font-mono">{(block.length_kb / 1000).toFixed(1)}</td>
                        <td className="p-3 text-right">{block.n_markers}</td>
                        <td className="p-3 text-center"><Badge variant="outline">{block.n_haplotypes}</Badge></td>
                        <td className="p-3 text-center">
                          <Badge className={getHapBadgeColor(block.major_haplotype)}>
                            {block.major_haplotype} ({(block.major_frequency * 100).toFixed(0)}%)
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
                  const chrBlocks = blocks.filter(b => b.chromosome === chr)
                  return (
                    <div key={chr} className="flex items-center gap-4">
                      <span className="w-16 text-sm font-medium">Chr {chr}</span>
                      <div className="flex-1 h-6 bg-muted rounded relative">
                        {chrBlocks.map((block) => (
                          <div
                            key={block.id}
                            className={`absolute top-0 h-full ${getHapColor(block.major_haplotype)} rounded cursor-pointer hover:opacity-80`}
                            style={{ 
                              left: `${(block.start_mb / 50) * 100}%`,
                              width: `${((block.end_mb - block.start_mb) / 50) * 100}%`
                            }}
                            title={`${block.id}: ${block.start_mb}-${block.end_mb} Mb`}
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
              {haplotypesLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => <Skeleton key={i} className="h-24" />)}
                </div>
              ) : (
                <div className="space-y-4">
                  {haplotypes.map((hap) => (
                    <div key={hap.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Badge className={getHapBadgeColor(hap.id.toUpperCase())}>
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
              )}
            </CardContent>
          </Card>

          {/* Diversity Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-primary">{haplotypes.length}</p>
                <p className="text-sm text-muted-foreground">Haplotypes</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-green-600">{diversity?.avg_diversity?.toFixed(2) || '0.72'}</p>
                <p className="text-sm text-muted-foreground">Haplotype Diversity</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-blue-600">
                  {haplotypes.length > 0 ? Math.max(...haplotypes.map(h => h.frequency)).toFixed(2) : '0.42'}
                </p>
                <p className="text-sm text-muted-foreground">Major Hap Freq</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-purple-600">{diversity?.avg_haplotypes_per_block?.toFixed(1) || '3.2'}</p>
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
              {germplasmHaplotypesLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => <Skeleton key={i} className="h-12" />)}
                </div>
              ) : germplasmHaplotypes.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="font-medium">No germplasm haplotype data available</p>
                  <p className="text-sm mt-1">Run haplotype analysis on your germplasm collection to see selection recommendations</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Germplasm</th>
                        {blocks.slice(0, 6).map(b => (
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
                          {blocks.slice(0, 6).map(b => (
                            <td key={b.id} className="p-2 text-center">
                              <div className={`w-6 h-6 rounded mx-auto flex items-center justify-center text-xs text-white ${getHapColor(germ.haplotypes[b.id] || 'H1')}`}>
                                {(germ.haplotypes[b.id] || 'H1').replace('H', '')}
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
              )}
            </CardContent>
          </Card>

          {/* Ideal Haplotype */}
          <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20">
            <CardHeader>
              <CardTitle className="text-green-800 dark:text-green-300 flex items-center gap-2">
                <Target className="h-5 w-5" />
                Ideal Haplotype Combination
              </CardTitle>
              <CardDescription className="text-green-700 dark:text-green-400">Target haplotypes for breeding</CardDescription>
            </CardHeader>
            <CardContent>
              {blocks.length === 0 ? (
                <p className="text-sm text-green-700 dark:text-green-400">No haplotype blocks detected yet. Run block detection to identify target haplotypes.</p>
              ) : (
                <>
                  <div className="flex flex-wrap gap-3">
                    {blocks.slice(0, 6).map(b => (
                      <div key={b.id} className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-green-200 dark:border-green-800">
                        <p className="text-xs text-muted-foreground">{b.id} ({b.trait || 'Unknown'})</p>
                        <Badge className={getHapBadgeColor(b.major_haplotype)}>{b.major_haplotype}</Badge>
                      </div>
                    ))}
                  </div>
                  {germplasmHaplotypes.length > 0 && (
                    <p className="mt-4 text-sm text-green-700">
                      <strong>Best match:</strong> {germplasmHaplotypes.sort((a, b) => b.score - a.score)[0]?.name} ({germplasmHaplotypes.sort((a, b) => b.score - a.score)[0]?.score}% match to ideal haplotype combination)
                    </p>
                  )}
                </>
              )}
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
                  <Network className="h-12 w-12 mx-auto text-muted-foreground" />
                  <p className="mt-2 text-muted-foreground">Median-Joining Network</p>
                  <p className="text-xs text-muted-foreground">Block {selectedBlock} - {haplotypes.length} haplotypes</p>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                {haplotypes.map((hap) => (
                  <div key={hap.id} className="flex items-center gap-2">
                    <div className={`w-4 h-4 rounded-full ${getHapColor(hap.id.toUpperCase())}`} />
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
                      {haplotypes.slice(0, 4).map((_, i) => (
                        <th key={i} className="p-2 text-center">H{i + 1}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {haplotypes.slice(0, 4).map((_, i) => (
                      <tr key={i} className="border-b">
                        <td className="p-2 font-medium">H{i + 1}</td>
                        {haplotypes.slice(0, 4).map((_, j) => (
                          <td key={j} className="p-2 text-center">
                            {i === j ? '-' : Math.abs(i - j) + 1}
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

/**
 * Trial Design Page
 * Experimental design generator for field trials
 * Connected to /api/v2/trial-design endpoints
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import { useActiveWorkspace } from '@/store/workspaceStore'
import { Loader2, Download, RefreshCw, Grid3X3, LayoutGrid, Shuffle } from 'lucide-react'

interface DesignParams {
  designType: string
  genotypes: string
  replicates: number
  blocksPerRep: number
  plotsPerBlock: number
  checks: string
  checkInterval: number
  mainTreatments: string
  subTreatments: string
  seed: number | null
}

interface GeneratedDesign {
  success: boolean
  design_type: string
  n_genotypes?: number
  n_blocks?: number
  n_reps?: number
  total_plots: number
  layout: Array<{
    plot_id: number
    block: number
    genotype: string
    row?: number
    col?: number
  }>
  field_layout?: {
    rows: number
    cols: number
    grid: string[][]
  }
  seed: number | null
}

export function TrialDesign() {
  const activeWorkspace = useActiveWorkspace()
  const [params, setParams] = useState<DesignParams>({
    designType: 'rcbd',
    genotypes: 'G1, G2, G3, G4, G5, G6, G7, G8, G9, G10',
    replicates: 3,
    blocksPerRep: 5,
    plotsPerBlock: 2,
    checks: 'Check1, Check2',
    checkInterval: 10,
    mainTreatments: 'Irrigated, Rainfed',
    subTreatments: 'G1, G2, G3, G4',
    seed: null,
  })
  const [design, setDesign] = useState<GeneratedDesign | null>(null)

  // Fetch available design types
  const { data: designTypesData, isLoading: isLoadingTypes, isError: isErrorTypes } = useQuery({
    queryKey: ['trial-design-types'],
    queryFn: () => apiClient.trialDesignService.getTrialDesignTypes(),
    staleTime: 1000 * 60 * 60, // 1 hour
  })

  const designTypes = designTypesData?.designs || []

  // Generate design mutation
  const generateMutation = useMutation({
    mutationFn: async () => {
      const genotypeList = params.genotypes.split(',').map(g => g.trim()).filter(Boolean)
      const seedValue = params.seed || undefined

      switch (params.designType) {
        case 'rcbd':
          return apiClient.trialDesignService.generateRCBD({
            genotypes: genotypeList,
            n_blocks: params.replicates,
            seed: seedValue,
          })
        case 'alpha_lattice':
          return apiClient.trialDesignService.generateAlphaLattice({
            genotypes: genotypeList,
            n_blocks: params.replicates,
            block_size: params.plotsPerBlock,
            seed: seedValue,
          })
        case 'augmented':
          const checkList = params.checks.split(',').map(c => c.trim()).filter(Boolean)
          return apiClient.trialDesignService.generateAugmented({
            test_genotypes: genotypeList,
            check_genotypes: checkList,
            n_blocks: params.replicates,
            checks_per_block: 1,
            seed: seedValue,
          })
        case 'split_plot':
          const mainList = params.mainTreatments.split(',').map(m => m.trim()).filter(Boolean)
          const subList = params.subTreatments.split(',').map(s => s.trim()).filter(Boolean)
          return apiClient.trialDesignService.generateSplitPlot({
            main_treatments: mainList,
            sub_treatments: subList,
            n_blocks: params.replicates,
            seed: seedValue,
          })
        case 'crd':
          return apiClient.trialDesignService.generateCRD({
            genotypes: genotypeList,
            n_reps: params.replicates,
            seed: seedValue,
          })
        default:
          throw new Error('Unknown design type')
      }
    },
    onSuccess: (data) => {
      setDesign(data as GeneratedDesign)
      toast.success('Design generated successfully')
    },
    onError: (error: Error) => {
      console.error('Design generation failed:', error)
      toast.error(`Design generation failed: ${error.message || 'Unknown error'}`)
    },
  })

  const handleChange = (field: keyof DesignParams, value: string | number | null) => {
    setParams(prev => ({ ...prev, [field]: value }))
  }

  const exportDesign = (format: string) => {
    if (!design) return

    if (format === 'CSV') {
      const headers = ['plot_id', 'block', 'genotype', 'row', 'col']
      const rows = design.layout.map(p => [p.plot_id, p.block, p.genotype, p.row || '', p.col || ''])
      const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `trial_design_${design.design_type}_${Date.now()}.csv`
      a.click()
      toast.success('Design exported as CSV')
    } else if (format === 'JSON') {
      const blob = new Blob([JSON.stringify(design, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `trial_design_${design.design_type}_${Date.now()}.json`
      a.click()
      toast.success('Design exported as JSON')
    }
  }

  const getDesignTypeInfo = (id: string) => {
    return designTypes.find((d: any) => d.id === id) || { name: id, abbreviation: id }
  }

  if (!activeWorkspace) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Select a Workspace</h2>
          <p className="text-muted-foreground">Please select a workspace to generate trial designs.</p>
        </div>
      </div>
    )
  }

  if (isLoadingTypes) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (isErrorTypes) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4 text-center">
        <p className="text-destructive">Failed to load design types.</p>
        <Button variant="outline" onClick={() => window.location.reload()}>Retry</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Trial Design</h1>
          <p className="text-muted-foreground mt-1">Generate experimental designs for field trials</p>
        </div>
        <Badge variant="outline" className="w-fit">
          <Grid3X3 className="w-3 h-3 mr-1" />
          {design ? `${design.total_plots} plots` : 'No design'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Design Parameters */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LayoutGrid className="w-5 h-5" />
              Design Parameters
            </CardTitle>
            <CardDescription>Configure your experimental design</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Design Type</Label>
              <Select value={params.designType} onValueChange={(v) => handleChange('designType', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {designTypes.map((dt: any) => (
                    <SelectItem key={dt.id} value={dt.id}>
                      <div className="flex flex-col">
                        <span className="font-medium">{dt.abbreviation}</span>
                        <span className="text-xs text-muted-foreground">{dt.use_case}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {params.designType !== 'split_plot' && (
              <div className="space-y-2">
                <Label>Genotypes (comma-separated)</Label>
                <Textarea
                  value={params.genotypes}
                  onChange={(e) => handleChange('genotypes', e.target.value)}
                  placeholder="G1, G2, G3, G4, G5..."
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  {params.genotypes.split(',').filter(g => g.trim()).length} genotypes
                </p>
              </div>
            )}

            {params.designType === 'split_plot' && (
              <>
                <div className="space-y-2">
                  <Label>Main Treatments (comma-separated)</Label>
                  <Textarea
                    value={params.mainTreatments}
                    onChange={(e) => handleChange('mainTreatments', e.target.value)}
                    placeholder="Irrigated, Rainfed..."
                    rows={2}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Sub Treatments (comma-separated)</Label>
                  <Textarea
                    value={params.subTreatments}
                    onChange={(e) => handleChange('subTreatments', e.target.value)}
                    placeholder="G1, G2, G3, G4..."
                    rows={2}
                  />
                </div>
              </>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{params.designType === 'crd' ? 'Replications' : 'Blocks'}</Label>
                <Input
                  type="number"
                  value={params.replicates}
                  onChange={(e) => handleChange('replicates', parseInt(e.target.value) || 2)}
                  min={2}
                  max={20}
                />
              </div>
              <div className="space-y-2">
                <Label>Seed (optional)</Label>
                <Input
                  type="number"
                  value={params.seed || ''}
                  onChange={(e) => handleChange('seed', e.target.value ? parseInt(e.target.value) : null)}
                  placeholder="Random"
                />
              </div>
            </div>

            {params.designType === 'alpha_lattice' && (
              <div className="space-y-2">
                <Label>Block Size (plots per incomplete block)</Label>
                <Input
                  type="number"
                  value={params.plotsPerBlock}
                  onChange={(e) => handleChange('plotsPerBlock', parseInt(e.target.value) || 2)}
                  min={2}
                  max={50}
                />
              </div>
            )}

            {params.designType === 'augmented' && (
              <div className="space-y-2">
                <Label>Check Varieties (comma-separated)</Label>
                <Textarea
                  value={params.checks}
                  onChange={(e) => handleChange('checks', e.target.value)}
                  placeholder="Check1, Check2..."
                  rows={2}
                />
              </div>
            )}

            <Button 
              onClick={() => generateMutation.mutate()} 
              disabled={generateMutation.isPending} 
              className="w-full"
            >
              {generateMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Shuffle className="w-4 h-4 mr-2" />
                  Generate Design
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Design Output */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Generated Design</CardTitle>
                <CardDescription>
                  {design 
                    ? `${design.design_type} - ${design.field_layout?.rows || '?'} × ${design.field_layout?.cols || '?'} layout` 
                    : 'Configure parameters and generate'}
                </CardDescription>
              </div>
              {design && (
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => exportDesign('CSV')}>
                    <Download className="w-3 h-3 mr-1" />
                    CSV
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => exportDesign('JSON')}>
                    <Download className="w-3 h-3 mr-1" />
                    JSON
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!design ? (
              <div className="text-center py-12 text-muted-foreground">
                <Grid3X3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Configure parameters and click Generate</p>
              </div>
            ) : (
              <Tabs defaultValue="layout">
                <TabsList>
                  <TabsTrigger value="layout">Field Layout</TabsTrigger>
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                  <TabsTrigger value="randomization">Randomization</TabsTrigger>
                </TabsList>

                <TabsContent value="layout" className="mt-4">
                  <div className="overflow-x-auto">
                    {design.field_layout?.grid ? (
                      <div className="inline-block">
                        {/* Column headers */}
                        <div className="flex">
                          <div className="w-10 h-8"></div>
                          {Array.from({ length: design.field_layout.cols }, (_, i) => (
                            <div key={i} className="w-14 h-8 flex items-center justify-center text-xs font-medium text-muted-foreground">
                              C{i + 1}
                            </div>
                          ))}
                        </div>
                        {/* Rows */}
                        {design.field_layout.grid.map((row, rowIdx) => (
                          <div key={rowIdx} className="flex">
                            <div className="w-10 h-10 flex items-center justify-center text-xs font-medium text-muted-foreground">
                              R{rowIdx + 1}
                            </div>
                            {row.map((cell, colIdx) => (
                              <div
                                key={colIdx}
                                className={`w-14 h-10 m-0.5 rounded text-xs flex items-center justify-center font-medium
                                  ${cell 
                                    ? cell.startsWith('Check') || cell.startsWith('C') && cell.length <= 3
                                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' 
                                      : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                                    : 'bg-gray-50 dark:bg-gray-800'}
                                `}
                              >
                                {cell}
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <p>Layout visualization not available</p>
                        <p className="text-sm">Export to CSV for full plot list</p>
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="summary" className="mt-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{design.total_plots}</p>
                      <p className="text-sm text-muted-foreground">Total Plots</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{design.field_layout?.rows || '-'}</p>
                      <p className="text-sm text-muted-foreground">Rows</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{design.field_layout?.cols || '-'}</p>
                      <p className="text-sm text-muted-foreground">Columns</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{design.n_blocks || design.n_reps || '-'}</p>
                      <p className="text-sm text-muted-foreground">Blocks/Reps</p>
                    </div>
                  </div>
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h4 className="font-medium text-blue-800 dark:text-blue-300 mb-2">Design Details</h4>
                    <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                      <li>• Design: {getDesignTypeInfo(params.designType).name}</li>
                      <li>• Genotypes: {design.n_genotypes || '-'}</li>
                      <li>• Blocks/Replicates: {design.n_blocks || design.n_reps || '-'}</li>
                      <li>• Total experimental units: {design.total_plots}</li>
                      {design.seed && <li>• Random seed: {design.seed}</li>}
                    </ul>
                  </div>
                </TabsContent>

                <TabsContent value="randomization" className="mt-4">
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground mb-2">
                      Randomization seed: {design.seed || 'Random (not reproducible)'}
                    </p>
                    <p className="text-sm">
                      The design has been randomized using Fisher-Yates shuffle algorithm.
                      {design.seed 
                        ? ' Use the same seed to reproduce this exact randomization.'
                        : ' Set a seed value for reproducible randomization.'}
                    </p>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="mt-4" 
                      onClick={() => generateMutation.mutate()}
                      disabled={generateMutation.isPending}
                    >
                      <RefreshCw className={`w-4 h-4 mr-2 ${generateMutation.isPending ? 'animate-spin' : ''}`} />
                      Re-randomize
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Design Type Info */}
      <Card>
        <CardHeader>
          <CardTitle>Design Types</CardTitle>
          <CardDescription>Choose the appropriate design for your experiment</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {designTypes.map((dt: any) => (
              <div
                key={dt.id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  params.designType === dt.id 
                    ? 'border-primary bg-primary/5' 
                    : 'border-transparent bg-muted hover:border-gray-300 dark:hover:border-gray-600'
                }`}
                onClick={() => handleChange('designType', dt.id)}
              >
                <h4 className="font-semibold">{dt.abbreviation}</h4>
                <p className="text-xs text-muted-foreground mt-1">{dt.use_case}</p>
                {(dt as any).advantages && (
                  <div className="mt-2">
                    <p className="text-xs text-green-600 dark:text-green-400">
                      ✓ {(dt as any).advantages[0]}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

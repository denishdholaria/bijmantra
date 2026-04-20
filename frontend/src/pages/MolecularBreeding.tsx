/**
 * Molecular Breeding Page
 * Integrated molecular breeding tools and workflows
 * Connected to /api/v2/molecular-breeding/* endpoints
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Dna, Target, Layers, Workflow, AlertCircle, FileText, Plus, RefreshCw, Search, ArrowRight, CheckCircle2, Loader2, Microscope } from 'lucide-react'
import { apiClient, BreedingScheme, IntrogressionLine, MolecularBreedingStatistics } from '@/lib/api-client'
import type { MABCSelectionCandidate } from '@/lib/api/breeding/marker-assisted'
import { toast } from 'sonner'

interface MASConfig {
  targetMarkers: string[];
  backgroundMarkers: string[];
  population: string;
  genotypes: string[];
}

interface MASAnalysisParams {
  individual_ids: string[];
  target_markers: string[];
  background_markers: string[];
  recurrent_parent_id: string;
  fg_weight: number;
  bg_weight: number;
  n_select: number;
}

interface MASMarkerResponse {
  markers: Array<{
    marker_id?: string;
    id?: string;
    name: string;
    chromosome: string;
    position: number;
    linked_trait?: string;
    target_allele: string;
    distance_to_qtl: number;
    validated?: boolean;
  }>;
  count: number;
}

export function MolecularBreeding() {
  const [activeTab, setActiveTab] = useState('schemes')
  const [selectedScheme, setSelectedScheme] = useState('bs1')

  // MAS State
  const [markerQuery, setMarkerQuery] = useState('')
  const [masStep, setMasStep] = useState(1)
  const [masConfig, setMasConfig] = useState<MASConfig>({
    targetMarkers: [] as string[],
    backgroundMarkers: [] as string[],
    population: 'all-lines',
    genotypes: [] as string[]
  })

  // Fetch breeding schemes
  const { data: schemesData, isLoading: schemesLoading, error: schemesError, refetch: refetchSchemes } = useQuery({
    queryKey: ['molecular-breeding-schemes'],
    queryFn: () => apiClient.molecularBreedingService.getSchemes(),
  })

  // Fetch Markers
  const { data: markersData, isLoading: markersLoading } = useQuery<MASMarkerResponse>({
    queryKey: ['mas-markers', markerQuery],
    queryFn: () => apiClient.markerAssistedService.listMarkers({ trait: markerQuery }),
  })

  // MAS Analysis Mutation
  const masMutation = useMutation({
    mutationFn: (data: MASAnalysisParams) => apiClient.markerAssistedService.mabcSelection(data),
    onSuccess: () => {
      toast.success('MAS analysis completed successfully')
      setMasStep(5) // Move to results
    },
    onError: (err) => {
      toast.error('Failed to run MAS analysis')
      console.error(err)
    }
  })

  // Fetch introgression lines
  const { data: linesData } = useQuery({
    queryKey: ['molecular-breeding-lines'],
    queryFn: () => apiClient.molecularBreedingService.getLines(),
  })

  // Fetch statistics
  const { data: statsData } = useQuery({
    queryKey: ['molecular-breeding-stats'],
    queryFn: () => apiClient.molecularBreedingService.getStatistics(),
  })

  const schemes: BreedingScheme[] = schemesData?.data || []
  const lines: IntrogressionLine[] = linesData?.data || []
  const stats: MolecularBreedingStatistics = statsData?.data || { 
    total_schemes: schemes.length, 
    active_schemes: schemes.filter(s => s.status === 'active').length, 
    total_lines: lines.length, 
    fixed_lines: lines.filter(l => l.foreground_status === 'fixed').length, 
    target_genes: 0, 
    avg_progress: 0 
  }

  const liveMarkers = markersData?.markers || []
  const availableBackgroundMarkers = liveMarkers.filter(marker => !masConfig.targetMarkers.includes(marker.marker_id || marker.id || marker.name))
  const populationOptions = [
    { value: 'all-lines', label: `All introgression lines (${lines.length})`, count: lines.length },
    ...schemes.map((scheme) => ({
      value: scheme.id,
      label: `${scheme.name} (${lines.filter(line => line.scheme_id === scheme.id).length})`,
      count: lines.filter(line => line.scheme_id === scheme.id).length,
    })),
  ]
  const selectedPopulationLines = masConfig.population === 'all-lines'
    ? lines
    : lines.filter(line => line.scheme_id === masConfig.population)
  const candidateIndividuals = selectedPopulationLines.map(line => line.name).filter(Boolean)
  const recurrentParentId = selectedPopulationLines[0]?.recurrent || lines[0]?.recurrent || ''
  const selectedCandidates: MABCSelectionCandidate[] = Array.isArray(masMutation.data?.selected)
    ? masMutation.data.selected
    : []

  const runAnalysis = () => {
    if (!candidateIndividuals.length || !recurrentParentId) {
      toast.error('No live breeding population is available for MAS analysis')
      return
    }
    if (!masConfig.targetMarkers.length || !masConfig.backgroundMarkers.length) {
      toast.error('Select both target and background marker sets before running analysis')
      return
    }

    masMutation.mutate({
      individual_ids: candidateIndividuals,
      target_markers: masConfig.targetMarkers,
      background_markers: masConfig.backgroundMarkers,
      recurrent_parent_id: recurrentParentId,
      fg_weight: 0.7,
      bg_weight: 0.3,
      n_select: 5
    })
  }

  const toggleMarkerSelection = (markerId: string, type: 'target' | 'background') => {
    setMasConfig(prev => {
      const list = type === 'target' ? prev.targetMarkers : prev.backgroundMarkers
      const newList = list.includes(markerId)
        ? list.filter(id => id !== markerId)
        : [...list, markerId]

      return {
        ...prev,
        [type === 'target' ? 'targetMarkers' : 'backgroundMarkers']: newList
      }
    })
  }

  const toggleChromosomeSelection = (chromosome: string) => {
    const chromosomeMarkerIds = availableBackgroundMarkers
      .filter(marker => marker.chromosome === chromosome)
      .map(marker => marker.marker_id || marker.id || marker.name)

    setMasConfig(prev => {
      const allSelected = chromosomeMarkerIds.every(markerId => prev.backgroundMarkers.includes(markerId))
      return {
        ...prev,
        backgroundMarkers: allSelected
          ? prev.backgroundMarkers.filter(markerId => !chromosomeMarkerIds.includes(markerId))
          : Array.from(new Set([...prev.backgroundMarkers, ...chromosomeMarkerIds])),
      }
    })
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-700">Active</Badge>
      case 'completed': return <Badge className="bg-blue-100 text-blue-700">Completed</Badge>
      default: return <Badge variant="secondary">Planned</Badge>
    }
  }

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'MABC': return <Badge className="bg-purple-100 text-purple-700">MABC</Badge>
      case 'MARS': return <Badge className="bg-orange-100 text-orange-700">MARS</Badge>
      case 'GS': return <Badge className="bg-blue-100 text-blue-700">GS</Badge>
      case 'Speed': return <Badge className="bg-green-100 text-green-700">Speed</Badge>
      default: return <Badge variant="secondary">{type}</Badge>
    }
  }

  const getForegroundBadge = (status: string) => {
    switch (status) {
      case 'fixed': return <Badge className="bg-green-100 text-green-700">Fixed</Badge>
      case 'segregating': return <Badge className="bg-yellow-100 text-yellow-700">Segregating</Badge>
      default: return <Badge className="bg-red-100 text-red-700">Absent</Badge>
    }
  }

  if (schemesLoading) {
    return (
      <div className="space-y-6">
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
            Molecular Breeding
          </h1>
          <p className="text-muted-foreground mt-1">Integrated molecular breeding workflows</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><FileText className="h-4 w-4 mr-2" />Reports</Button>
          <Button><Plus className="h-4 w-4 mr-2" />New Scheme</Button>
        </div>
      </div>

      {schemesError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center gap-2">
            Failed to load molecular breeding data. {schemesError instanceof Error ? schemesError.message : 'Please try again.'}
            <Button variant="outline" size="sm" onClick={() => refetchSchemes()}>
              <RefreshCw className="h-4 w-4 mr-2" />Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{stats.total_schemes}</p>
            <p className="text-sm text-muted-foreground">Active Schemes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{stats.total_lines}</p>
            <p className="text-sm text-muted-foreground">Introgression Lines</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{stats.target_genes}</p>
            <p className="text-sm text-muted-foreground">Target Genes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">{stats.avg_progress}%</p>
            <p className="text-sm text-muted-foreground">Avg Progress</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="schemes" className="flex items-center gap-1"><Target className="h-4 w-4" />Schemes</TabsTrigger>
          <TabsTrigger value="markers" className="flex items-center gap-1"><Microscope className="h-4 w-4" />Markers</TabsTrigger>
          <TabsTrigger value="mas" className="flex items-center gap-1"><Workflow className="h-4 w-4" />MAS Workflow</TabsTrigger>
          <TabsTrigger value="mabc" className="flex items-center gap-1"><Dna className="h-4 w-4" />MABC Lines</TabsTrigger>
          <TabsTrigger value="pyramiding" className="flex items-center gap-1"><Layers className="h-4 w-4" />Pyramiding</TabsTrigger>
        </TabsList>

        <TabsContent value="schemes" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Breeding Schemes</CardTitle>
              <CardDescription>Molecular breeding projects and progress</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {schemes.map((scheme) => (
                  <div key={scheme.id} className={`p-4 border rounded-lg cursor-pointer transition-all ${selectedScheme === scheme.id ? 'border-primary bg-primary/5' : 'hover:border-muted-foreground'}`} onClick={() => setSelectedScheme(scheme.id)}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <h4 className="font-bold">{scheme.name}</h4>
                        {getTypeBadge(scheme.type)}
                      </div>
                      {getStatusBadge(scheme.status)}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                      <span>Generation: <strong>{scheme.generation}</strong></span>
                      <span>Targets: {scheme.target_traits.join(', ')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={scheme.progress} className="flex-1 h-2" />
                      <span className="text-sm font-bold">{scheme.progress}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="mabc" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Marker-Assisted Backcrossing</CardTitle>
              <CardDescription>Introgression line development and tracking</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Line</th>
                      <th className="text-left p-3">Target Gene</th>
                      <th className="text-left p-3">Donor</th>
                      <th className="text-left p-3">Recurrent</th>
                      <th className="text-center p-3">BC Gen</th>
                      <th className="text-right p-3">RP Recovery</th>
                      <th className="text-center p-3">Foreground</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lines.map((line) => (
                      <tr key={line.id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{line.name}</td>
                        <td className="p-3"><Badge variant="outline">{line.target_gene}</Badge></td>
                        <td className="p-3">{line.donor}</td>
                        <td className="p-3">{line.recurrent}</td>
                        <td className="p-3 text-center">BC{line.bc_generation}</td>
                        <td className="p-3 text-right">
                          <span className={line.rp_recovery >= 90 ? 'text-green-600 font-bold' : line.rp_recovery >= 80 ? 'text-yellow-600' : 'text-red-600'}>
                            {line.rp_recovery}%
                          </span>
                        </td>
                        <td className="p-3 text-center">{getForegroundBadge(line.foreground_status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* MABC Workflow */}
          <Card>
            <CardHeader>
              <CardTitle>MABC Workflow</CardTitle>
              <CardDescription>Standard backcross breeding pipeline</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                {['F1', 'BC1F1', 'BC2F1', 'BC3F1', 'BC3F2', 'BC3F3'].map((gen, i) => (
                  <div key={gen} className="flex items-center">
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center text-sm font-bold ${i <= 3 ? 'bg-green-100 text-green-700' : 'bg-muted text-muted-foreground'}`}>{gen}</div>
                    {i < 5 && <div className="w-8 h-0.5 bg-muted-foreground/30" />}
                  </div>
                ))}
              </div>
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span>Foreground</span><span>Background</span><span>Background</span><span>Background</span><span>Selfing</span><span>Fixation</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pyramiding" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Gene Pyramiding</CardTitle>
              <CardDescription>Stack multiple genes in elite background</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-muted rounded-lg mb-4">
                <h4 className="font-bold mb-2">Disease Resistance Pyramid</h4>
                <div className="flex flex-wrap gap-2 mb-3">
                  <Badge className="bg-blue-100 text-blue-700">Xa21 (BB)</Badge>
                  <Badge className="bg-green-100 text-green-700">Pi54 (Blast)</Badge>
                  <Badge className="bg-purple-100 text-purple-700">Sub1A (Submergence)</Badge>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Line</th>
                      <th className="text-center p-3">Xa21</th>
                      <th className="text-center p-3">Pi54</th>
                      <th className="text-center p-3">Sub1A</th>
                      <th className="text-center p-3">Stack</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { line: 'Pyramid-001', xa21: true, pi54: true, sub1a: true },
                      { line: 'Pyramid-002', xa21: true, pi54: true, sub1a: false },
                      { line: 'Pyramid-003', xa21: true, pi54: false, sub1a: true },
                    ].map((row, i) => {
                      const stack = [row.xa21, row.pi54, row.sub1a].filter(Boolean).length
                      return (
                        <tr key={i} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{row.line}</td>
                          <td className="p-3 text-center">{row.xa21 ? '✓' : '✗'}</td>
                          <td className="p-3 text-center">{row.pi54 ? '✓' : '✗'}</td>
                          <td className="p-3 text-center">{row.sub1a ? '✓' : '✗'}</td>
                          <td className="p-3 text-center">
                            <Badge className={stack === 3 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>{stack}/3</Badge>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="markers" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Marker Database</CardTitle>
              <CardDescription>Search and explore molecular markers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-6">
                <div className="relative flex-1">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by trait (e.g., rust, yield)..."
                    value={markerQuery}
                    onChange={(e) => setMarkerQuery(e.target.value)}
                    className="pl-8"
                  />
                </div>
                <Button variant="outline">Advanced Filters</Button>
              </div>

              {markersLoading ? (
                <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
              ) : (
                <div className="border rounded-md overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Marker ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Chr</TableHead>
                        <TableHead>Pos (cM)</TableHead>
                        <TableHead>Trait</TableHead>
                        <TableHead>Target Allele</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {markersData?.markers && markersData.markers.length > 0 ? (
                        markersData.markers.map((marker) => (
                          <TableRow key={marker.marker_id}>
                            <TableCell className="font-medium">{marker.marker_id}</TableCell>
                            <TableCell>{marker.name}</TableCell>
                            <TableCell>{marker.chromosome}</TableCell>
                            <TableCell>{marker.position}</TableCell>
                            <TableCell><Badge variant="outline">{marker.linked_trait}</Badge></TableCell>
                            <TableCell>{marker.target_allele}</TableCell>
                            <TableCell className="text-right">
                              <Button size="sm" variant="ghost">Details</Button>
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center h-24 text-muted-foreground">
                            No markers found. Try searching for a trait.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Marker Profile Visualizer</CardTitle>
              <CardDescription>Allele heatmap for selected markers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center border-2 border-dashed rounded-lg bg-muted/20">
                <p className="text-muted-foreground">Select markers and genotypes to generate heatmap</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="mas" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Stepper */}
            <Card className="md:col-span-1 h-fit">
              <CardHeader>
                <CardTitle>Analysis Steps</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6 relative">
                  <div className="absolute left-3.5 top-2 bottom-2 w-0.5 bg-muted" />
                  {[
                    { step: 1, label: 'Select Target Markers' },
                    { step: 2, label: 'Select Background' },
                    { step: 3, label: 'Select Population' },
                    { step: 4, label: 'Run Analysis' },
                    { step: 5, label: 'Results' }
                  ].map((s) => (
                    <div key={s.step} className="relative flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center z-10 border-2 transition-colors ${masStep >= s.step ? 'bg-primary text-primary-foreground border-primary' : 'bg-background border-muted text-muted-foreground'}`}>
                        {masStep > s.step ? <CheckCircle2 className="h-4 w-4" /> : s.step}
                      </div>
                      <span className={`text-sm font-medium ${masStep === s.step ? 'text-foreground' : 'text-muted-foreground'}`}>{s.label}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Step Content */}
            <Card className="md:col-span-3">
              <CardHeader>
                <CardTitle>
                  {masStep === 1 && 'Step 1: Select Target Markers (Foreground)'}
                  {masStep === 2 && 'Step 2: Select Background Markers'}
                  {masStep === 3 && 'Step 3: Select Population'}
                  {masStep === 4 && 'Step 4: Run Analysis'}
                  {masStep === 5 && 'Analysis Results'}
                </CardTitle>
                <CardDescription>
                  {masStep === 1 && 'Identify markers linked to your target traits.'}
                  {masStep === 2 && 'Select genome-wide markers for background recovery.'}
                  {masStep === 3 && 'Choose the breeding population to screen.'}
                  {masStep === 4 && 'Configure analysis parameters and execute.'}
                  {masStep === 5 && 'Review candidates and Make selections.'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {masStep === 1 && (
                  <div className="space-y-4">
                    <Input placeholder="Search markers..." value={markerQuery} onChange={(e) => setMarkerQuery(e.target.value)} className="mb-4" />
                    <div className="border rounded-md">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-12"></TableHead>
                            <TableHead>Marker</TableHead>
                            <TableHead>Trait</TableHead>
                            <TableHead>Chr</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {liveMarkers.length > 0 ? liveMarkers.map((marker) => {
                            const markerId = marker.marker_id || marker.id || marker.name
                            return (
                              <TableRow key={markerId}>
                                <TableCell>
                                  <Checkbox
                                    checked={masConfig.targetMarkers.includes(markerId)}
                                    onCheckedChange={() => toggleMarkerSelection(markerId, 'target')}
                                  />
                                </TableCell>
                                <TableCell>{marker.name}</TableCell>
                                <TableCell>{marker.linked_trait || 'Unannotated'}</TableCell>
                                <TableCell>{marker.chromosome}</TableCell>
                              </TableRow>
                            )
                          }) : (
                            <TableRow>
                              <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                                No live marker records are available for MAS target selection.
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                )}

                {masStep === 2 && (
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2 pb-4">
                      <Checkbox
                        id="all-bg"
                        checked={availableBackgroundMarkers.length > 0 && masConfig.backgroundMarkers.length === availableBackgroundMarkers.length}
                        onCheckedChange={(checked) => setMasConfig(prev => ({
                          ...prev,
                          backgroundMarkers: checked ? availableBackgroundMarkers.map(marker => marker.marker_id || marker.id || marker.name) : [],
                        }))}
                      />
                      <Label htmlFor="all-bg">Select all available background markers (SNP Chip)</Label>
                    </div>
                    <p className="text-sm text-muted-foreground">Or select specific chromosomes:</p>
                    <div className="grid grid-cols-4 gap-2">
                      {Array.from(new Set(availableBackgroundMarkers.map(marker => marker.chromosome))).map((chromosome) => (
                        <div key={chromosome} className="flex items-center space-x-2">
                          <Checkbox
                            id={`chr-${chromosome}`}
                            checked={availableBackgroundMarkers.filter(marker => marker.chromosome === chromosome).every(marker => masConfig.backgroundMarkers.includes(marker.marker_id || marker.id || marker.name))}
                            onCheckedChange={() => toggleChromosomeSelection(chromosome)}
                          />
                          <Label htmlFor={`chr-${chromosome}`}>Chr {chromosome}</Label>
                        </div>
                      ))}
                    </div>
                    {availableBackgroundMarkers.length === 0 && (
                      <Alert>
                        <AlertDescription>Select one or more target markers first to populate the remaining markers for background recovery.</AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}

                {masStep === 3 && (
                  <div className="space-y-4">
                    <Label>Population Source</Label>
                    <RadioGroup value={masConfig.population} onValueChange={(v) => setMasConfig(c => ({ ...c, population: v }))}>
                      {populationOptions.map((option) => (
                        <div key={option.value} className="flex items-center space-x-2">
                          <RadioGroupItem value={option.value} id={option.value} />
                          <Label htmlFor={option.value}>{option.label}</Label>
                        </div>
                      ))}
                    </RadioGroup>
                    <div className="mt-4 p-4 bg-muted rounded-md text-sm">
                      <p><strong>Selected:</strong> {populationOptions.find(option => option.value === masConfig.population)?.label || 'No population selected'}</p>
                      <p><strong>Size:</strong> {candidateIndividuals.length} individuals</p>
                      <p><strong>Recurrent Parent:</strong> {recurrentParentId || 'Not available'}</p>
                    </div>
                  </div>
                )}

                {masStep === 4 && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Foreground Weight</Label>
                        <Input type="number" defaultValue={0.7} />
                      </div>
                      <div className="space-y-2">
                        <Label>Background Weight</Label>
                        <Input type="number" defaultValue={0.3} />
                      </div>
                    </div>
                    <div className="p-4 bg-yellow-50 text-yellow-800 rounded-md border border-yellow-200">
                      <h4 className="font-semibold mb-1 flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Ready to Analyze</h4>
                      <p className="text-sm">Analysis will process {candidateIndividuals.length} individuals against {masConfig.targetMarkers.length} target markers and {masConfig.backgroundMarkers.length} background markers.</p>
                    </div>
                  </div>
                )}

                {masStep === 5 && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-semibold">Top Candidates</h3>
                      <Button size="sm" variant="outline">Export CSV</Button>
                    </div>
                    {selectedCandidates.length > 0 ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Rank</TableHead>
                            <TableHead>ID</TableHead>
                            <TableHead>Total Score</TableHead>
                            <TableHead>FG Score</TableHead>
                            <TableHead>BG Score</TableHead>
                            <TableHead>Action</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {selectedCandidates.map((candidate, index) => (
                            <TableRow key={candidate.individual_id}>
                              <TableCell className="font-bold">#{index + 1}</TableCell>
                              <TableCell>{candidate.individual_id}</TableCell>
                              <TableCell className="font-bold text-primary">{candidate.overall_score}</TableCell>
                              <TableCell>{candidate.foreground_score_percent}%</TableCell>
                              <TableCell>{candidate.background_score_percent}%</TableCell>
                              <TableCell>
                                <Button size="sm">Select</Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <Alert>
                        <AlertDescription>
                          No live candidates passed the current MAS thresholds. Review marker coverage, genotyping state, or breeding population selection and rerun the analysis.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}

                <div className="flex justify-between mt-8 pt-4 border-t">
                  <Button variant="outline" onClick={() => setMasStep(s => Math.max(1, s - 1))} disabled={masStep === 1}>Previous</Button>
                  {masStep < 4 ? (
                     <Button onClick={() => setMasStep(s => s + 1)}>Next <ArrowRight className="ml-2 h-4 w-4" /></Button>
                  ) : masStep === 4 ? (
                     <Button onClick={runAnalysis} disabled={masMutation.isPending}>
                       {masMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                       Run Analysis
                     </Button>
                  ) : (
                     <Button variant="outline" onClick={() => setMasStep(1)}>Start New Analysis</Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

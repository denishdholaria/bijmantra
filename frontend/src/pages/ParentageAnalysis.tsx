/**
 * Parentage Analysis Page
 * DNA-based parentage verification and parent identification
 * Connected to /api/v2/parentage endpoints
 */
import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, CheckCircle2, XCircle, HelpCircle, RefreshCw, Dna, Users, FlaskConical } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface Individual {
  individual_id: string
  type: string
  species: string
  markers_genotyped: number
  claimed_female?: string
  claimed_male?: string
}

interface Marker {
  marker_id: string
  name: string
  chromosome: string
  type: string
  alleles: string[]
}

interface MarkerResult {
  marker_id: string
  marker_name: string
  offspring_genotype: string
  female_genotype: string
  male_genotype: string
  female_compatible: boolean
  male_compatible: boolean | null
  status: string
}

interface VerificationResult {
  analysis_id: string
  offspring_id: string
  claimed_female_id: string
  claimed_male_id: string | null
  analysis_date: string
  summary: {
    total_markers: number
    matches: number
    female_exclusions: number
    male_exclusions: number
    match_rate: number
    likelihood_ratio: number
    conclusion: string
    confidence: number
  }
  marker_results: MarkerResult[]
  interpretation: string
}

interface CandidateResult {
  candidate_id: string
  type: string
  matches: number
  exclusions: number
  total_markers: number
  compatibility_score: number
  likely_parent: boolean
}

const API_BASE = ''

export function ParentageAnalysis() {
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState('verification')
  const [selectedOffspring, setSelectedOffspring] = useState('')
  const [selectedFemale, setSelectedFemale] = useState('')
  const [selectedMale, setSelectedMale] = useState('')
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null)
  const [findParentsResult, setFindParentsResult] = useState<{ likely_parents: CandidateResult[], all_candidates: CandidateResult[] } | null>(null)

  // Fetch individuals
  const { data: individualsData, isLoading: loadingIndividuals } = useQuery({
    queryKey: ['parentage-individuals'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/parentage/individuals`)
      if (!res.ok) throw new Error('Failed to fetch individuals')
      return res.json()
    },
  })

  // Fetch markers
  const { data: markersData, isLoading: loadingMarkers } = useQuery({
    queryKey: ['parentage-markers'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/parentage/markers`)
      if (!res.ok) throw new Error('Failed to fetch markers')
      return res.json()
    },
  })

  // Fetch statistics
  const { data: statsData, refetch: refetchStats } = useQuery({
    queryKey: ['parentage-statistics'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/parentage/statistics`)
      if (!res.ok) throw new Error('Failed to fetch statistics')
      return res.json()
    },
  })

  // Fetch analysis history
  const { data: historyData, refetch: refetchHistory } = useQuery({
    queryKey: ['parentage-history'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/parentage/history`)
      if (!res.ok) throw new Error('Failed to fetch history')
      return res.json()
    },
  })

  const individuals: Individual[] = individualsData?.individuals || []
  const markers: Marker[] = markersData?.markers || []
  const stats = statsData?.data || { total_analyses: 0, confirmed: 0, excluded: 0, inconclusive: 0, confirmation_rate: 0 }
  const history = historyData?.analyses || []

  // Verify parentage mutation
  const verifyMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/parentage/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          offspring_id: selectedOffspring,
          claimed_female_id: selectedFemale,
          claimed_male_id: selectedMale || null,
        }),
      })
      if (!res.ok) throw new Error('Verification failed')
      return res.json()
    },
    onSuccess: (data) => {
      setVerificationResult(data.data)
      refetchStats()
      refetchHistory()
      toast({
        title: 'Analysis Complete',
        description: `Conclusion: ${data.data.summary.conclusion}`,
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to run parentage verification',
        variant: 'destructive',
      })
    },
  })

  // Find parents mutation
  const findParentsMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/parentage/find-parents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          offspring_id: selectedOffspring,
        }),
      })
      if (!res.ok) throw new Error('Find parents failed')
      return res.json()
    },
    onSuccess: (data) => {
      setFindParentsResult(data.data)
      toast({
        title: 'Search Complete',
        description: `Found ${data.data.likely_parents.length} likely parent(s)`,
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to find parents',
        variant: 'destructive',
      })
    },
  })

  const getConclusionBadge = (conclusion: string) => {
    switch (conclusion) {
      case 'CONFIRMED':
        return <Badge className="bg-green-100 text-green-700"><CheckCircle2 className="h-3 w-3 mr-1" />Confirmed</Badge>
      case 'EXCLUDED':
        return <Badge className="bg-red-100 text-red-700"><XCircle className="h-3 w-3 mr-1" />Excluded</Badge>
      case 'INCONCLUSIVE':
        return <Badge className="bg-yellow-100 text-yellow-700"><HelpCircle className="h-3 w-3 mr-1" />Inconclusive</Badge>
      default:
        return <Badge variant="secondary">{conclusion}</Badge>
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'match':
        return <Badge className="bg-green-100 text-green-700">Match</Badge>
      case 'female_exclusion':
        return <Badge className="bg-red-100 text-red-700">♀ Exclusion</Badge>
      case 'male_exclusion':
        return <Badge className="bg-orange-100 text-orange-700">♂ Exclusion</Badge>
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Dna className="h-7 w-7" />
            Parentage Analysis
          </h1>
          <p className="text-muted-foreground mt-1">DNA-based pedigree verification and parent identification</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{individuals.length}</p>
            <p className="text-sm text-muted-foreground">Individuals</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{markers.length}</p>
            <p className="text-sm text-muted-foreground">Markers</p>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-700">{stats.confirmed}</p>
            <p className="text-sm text-green-600">Confirmed</p>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-red-700">{stats.excluded}</p>
            <p className="text-sm text-red-600">Excluded</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">{stats.confirmation_rate}%</p>
            <p className="text-sm text-muted-foreground">Confirm Rate</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="verification">Verify Parentage</TabsTrigger>
          <TabsTrigger value="find-parents">Find Parents</TabsTrigger>
          <TabsTrigger value="history">Analysis History</TabsTrigger>
          <TabsTrigger value="markers">Marker Panel</TabsTrigger>
        </TabsList>

        <TabsContent value="verification" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FlaskConical className="h-5 w-5" />
                Parentage Verification
              </CardTitle>
              <CardDescription>Verify if an offspring matches claimed parents</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Offspring *</Label>
                  <Select value={selectedOffspring} onValueChange={setSelectedOffspring}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select offspring" />
                    </SelectTrigger>
                    <SelectContent position="popper" sideOffset={4}>
                      {individuals.filter(i => i.type === 'progeny' || i.type === 'F1' || i.type === 'unknown').map(ind => (
                        <SelectItem key={ind.individual_id} value={ind.individual_id}>
                          {ind.individual_id} ({ind.type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Claimed Female Parent *</Label>
                  <Select value={selectedFemale} onValueChange={setSelectedFemale}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select female parent" />
                    </SelectTrigger>
                    <SelectContent position="popper" sideOffset={4}>
                      {individuals.filter(i => i.type === 'variety').map(ind => (
                        <SelectItem key={ind.individual_id} value={ind.individual_id}>
                          {ind.individual_id}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Claimed Male Parent (optional)</Label>
                  <Select value={selectedMale || "none"} onValueChange={(v) => setSelectedMale(v === "none" ? "" : v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select male parent" />
                    </SelectTrigger>
                    <SelectContent position="popper" sideOffset={4}>
                      <SelectItem value="none">None</SelectItem>
                      {individuals.filter(i => i.type === 'variety').map(ind => (
                        <SelectItem key={ind.individual_id} value={ind.individual_id}>
                          {ind.individual_id}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button 
                onClick={() => verifyMutation.mutate()} 
                disabled={!selectedOffspring || !selectedFemale || verifyMutation.isPending}
              >
                {verifyMutation.isPending ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Dna className="h-4 w-4 mr-2" />}
                Run Verification
              </Button>

              {/* Results */}
              {verificationResult && (
                <div className="mt-6 space-y-4">
                  <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div>
                      <h4 className="font-semibold">Analysis Result</h4>
                      <p className="text-sm text-muted-foreground">{verificationResult.analysis_id}</p>
                    </div>
                    <div className="text-right">
                      {getConclusionBadge(verificationResult.summary.conclusion)}
                      <p className="text-sm mt-1">Confidence: {verificationResult.summary.confidence}%</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-blue-50 rounded text-center">
                      <p className="text-2xl font-bold text-blue-700">{verificationResult.summary.total_markers}</p>
                      <p className="text-xs text-blue-600">Markers Tested</p>
                    </div>
                    <div className="p-3 bg-green-50 rounded text-center">
                      <p className="text-2xl font-bold text-green-700">{verificationResult.summary.matches}</p>
                      <p className="text-xs text-green-600">Matches</p>
                    </div>
                    <div className="p-3 bg-red-50 rounded text-center">
                      <p className="text-2xl font-bold text-red-700">{verificationResult.summary.female_exclusions}</p>
                      <p className="text-xs text-red-600">♀ Exclusions</p>
                    </div>
                    <div className="p-3 bg-orange-50 rounded text-center">
                      <p className="text-2xl font-bold text-orange-700">{verificationResult.summary.male_exclusions}</p>
                      <p className="text-xs text-orange-600">♂ Exclusions</p>
                    </div>
                  </div>

                  <div className="p-4 bg-muted/50 rounded-lg">
                    <h5 className="font-medium mb-2">Interpretation</h5>
                    <p className="text-sm">{verificationResult.interpretation}</p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-muted/50">
                          <th className="text-left p-2">Marker</th>
                          <th className="text-center p-2">Offspring</th>
                          <th className="text-center p-2">Female</th>
                          <th className="text-center p-2">Male</th>
                          <th className="text-center p-2">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {verificationResult.marker_results.map((mr) => (
                          <tr key={mr.marker_id} className={`border-b ${mr.status !== 'match' ? 'bg-red-50' : ''}`}>
                            <td className="p-2 font-mono text-xs">{mr.marker_name}</td>
                            <td className="p-2 text-center font-mono text-xs">{mr.offspring_genotype}</td>
                            <td className="p-2 text-center font-mono text-xs">{mr.female_genotype}</td>
                            <td className="p-2 text-center font-mono text-xs">{mr.male_genotype}</td>
                            <td className="p-2 text-center">{getStatusBadge(mr.status)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="find-parents" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Find Potential Parents
              </CardTitle>
              <CardDescription>Search for likely parents from all available candidates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 items-end">
                <div className="flex-1 space-y-2">
                  <Label>Select Offspring</Label>
                  <Select value={selectedOffspring} onValueChange={setSelectedOffspring}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select offspring" />
                    </SelectTrigger>
                    <SelectContent position="popper" sideOffset={4}>
                      {individuals.filter(i => i.type === 'progeny' || i.type === 'F1' || i.type === 'unknown').map(ind => (
                        <SelectItem key={ind.individual_id} value={ind.individual_id}>
                          {ind.individual_id} ({ind.type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button 
                  onClick={() => findParentsMutation.mutate()} 
                  disabled={!selectedOffspring || findParentsMutation.isPending}
                >
                  {findParentsMutation.isPending ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Users className="h-4 w-4 mr-2" />}
                  Find Parents
                </Button>
              </div>

              {findParentsResult && (
                <div className="mt-6 space-y-4">
                  {findParentsResult.likely_parents.length > 0 && (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <h4 className="font-semibold text-green-800 mb-2">Likely Parents (No Exclusions)</h4>
                      <div className="flex flex-wrap gap-2">
                        {findParentsResult.likely_parents.map(p => (
                          <Badge key={p.candidate_id} className="bg-green-100 text-green-700">
                            {p.candidate_id} ({p.compatibility_score}%)
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <h4 className="font-medium">All Candidates (Ranked by Compatibility)</h4>
                  <div className="space-y-2">
                    {findParentsResult.all_candidates.map((cand, idx) => (
                      <div key={cand.candidate_id} className={`p-3 border rounded-lg ${cand.likely_parent ? 'border-green-500 bg-green-50' : ''}`}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Badge variant={idx === 0 ? 'default' : 'secondary'}>#{idx + 1}</Badge>
                            <span className="font-medium">{cand.candidate_id}</span>
                            <span className="text-sm text-muted-foreground">({cand.type})</span>
                          </div>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-green-600">{cand.matches} matches</span>
                            <span className="text-red-600">{cand.exclusions} exclusions</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm w-24">Compatibility:</span>
                          <Progress value={cand.compatibility_score} className="flex-1 h-2" />
                          <span className="text-sm w-12 text-right font-medium">{cand.compatibility_score}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Analysis History</CardTitle>
              <CardDescription>Previous parentage analyses</CardDescription>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No analyses performed yet</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Analysis ID</th>
                        <th className="text-left p-3">Offspring</th>
                        <th className="text-left p-3">Female</th>
                        <th className="text-left p-3">Male</th>
                        <th className="text-center p-3">Conclusion</th>
                        <th className="text-right p-3">Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((h: any) => (
                        <tr key={h.analysis_id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-mono text-xs">{h.analysis_id}</td>
                          <td className="p-3">{h.offspring_id}</td>
                          <td className="p-3">{h.claimed_female_id}</td>
                          <td className="p-3">{h.claimed_male_id || '-'}</td>
                          <td className="p-3 text-center">{getConclusionBadge(h.conclusion)}</td>
                          <td className="p-3 text-right">{h.confidence}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="markers" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Parentage Marker Panel</CardTitle>
              <CardDescription>SSR and SNP markers used for parentage analysis</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingMarkers ? (
                <div className="space-y-2">
                  {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-12 w-full" />)}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Marker ID</th>
                        <th className="text-left p-3">Name</th>
                        <th className="text-center p-3">Chromosome</th>
                        <th className="text-center p-3">Type</th>
                        <th className="text-left p-3">Alleles</th>
                      </tr>
                    </thead>
                    <tbody>
                      {markers.map((m) => (
                        <tr key={m.marker_id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-mono">{m.marker_id}</td>
                          <td className="p-3">{m.name}</td>
                          <td className="p-3 text-center">{m.chromosome}</td>
                          <td className="p-3 text-center">
                            <Badge variant={m.type === 'SSR' ? 'default' : 'secondary'}>{m.type}</Badge>
                          </td>
                          <td className="p-3 font-mono text-xs">{m.alleles.join(', ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

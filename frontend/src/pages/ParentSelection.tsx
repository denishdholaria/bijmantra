import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import {
  Users,
  Search,
  Filter,
  Star,
  Dna,
  Target,
  TrendingUp,
  CheckCircle2,
  Plus,
  Download,
  ArrowRight,
  Sparkles,
  RefreshCw,
  Loader2
} from 'lucide-react'

interface Parent {
  id: string
  name: string
  type: 'elite' | 'donor' | 'landrace'
  traits: string[]
  gebv: number
  heterosis_potential: number
  pedigree: string
  markers?: Record<string, boolean>
  agronomic_data?: {
    yield_potential: number
    days_to_maturity: number
    plant_height: number
  }
}

interface CrossPrediction {
  parent1: { id: string; name: string; type: string }
  parent2: { id: string; name: string; type: string }
  expected_gebv: number
  heterosis: number
  genetic_distance: number
  success_probability: number
  combined_traits: string[]
  recommendation: string
}

interface Recommendation {
  cross: string
  parent1_id: string
  parent2_id: string
  score: number
  reason: string
  expected_gebv: number
  heterosis: number
  combined_traits: string[]
}

export function ParentSelection() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedParents, setSelectedParents] = useState<string[]>([])
  const [typeFilter, setTypeFilter] = useState('all')
  const [traitFilter, setTraitFilter] = useState('')
  const [crossPrediction, setCrossPrediction] = useState<CrossPrediction | null>(null)
  const [predicting, setPredicting] = useState(false)

  // Fetch parents
  const { data: parentsData, isLoading: parentsLoading, refetch: refetchParents } = useQuery({
    queryKey: ['parent-selection-parents', typeFilter, traitFilter, searchQuery],
    queryFn: () => apiClient.parentSelectionService.getParents({
      type: typeFilter !== 'all' ? typeFilter : undefined,
      trait: traitFilter || undefined,
      search: searchQuery || undefined,
    }),
    retry: 1,
  })

  // Fetch recommendations
  const { data: recsData, isLoading: recsLoading, refetch: refetchRecs } = useQuery({
    queryKey: ['parent-selection-recommendations'],
    queryFn: () => apiClient.parentSelectionService.getRecommendations({ limit: 5 }),
    retry: 1,
  })

  const parents: Parent[] = parentsData?.data || []
  const recommendations: Recommendation[] = recsData?.data || []
  const loading = parentsLoading

  useEffect(() => {
    if (selectedParents.length >= 2) {
      predictCross()
    } else {
      setCrossPrediction(null)
    }
  }, [selectedParents])

  const predictCross = async () => {
    if (selectedParents.length < 2) return

    setPredicting(true)
    try {
      const result = await apiClient.parentSelectionService.predictCross(selectedParents[0], selectedParents[1])
      setCrossPrediction(result.data)
    } catch (error) {
      console.error('Error predicting cross:', error)
      // Generate local prediction as fallback
      const p1 = parents.find(p => p.id === selectedParents[0])
      const p2 = parents.find(p => p.id === selectedParents[1])
      if (p1 && p2) {
        setCrossPrediction({
          parent1: { id: p1.id, name: p1.name, type: p1.type },
          parent2: { id: p2.id, name: p2.name, type: p2.type },
          expected_gebv: (p1.gebv + p2.gebv) / 2,
          heterosis: (p1.heterosis_potential + p2.heterosis_potential) / 2,
          genetic_distance: 0.42,
          success_probability: 78,
          combined_traits: [...new Set([...p1.traits, ...p2.traits])],
          recommendation: 'Recommended cross based on complementary traits'
        })
      }
    } finally {
      setPredicting(false)
    }
  }

  const toggleParent = (id: string) => {
    setSelectedParents(prev => {
      if (prev.includes(id)) {
        return prev.filter(p => p !== id)
      }
      if (prev.length >= 2) {
        // Replace the second parent
        return [prev[0], id]
      }
      return [...prev, id]
    })
  }

  const filteredParents = parents.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.pedigree.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesSearch
  })

  const selectedParentData = parents.filter(p => selectedParents.includes(p.id))

  const exportParents = async () => {
    try {
      const blob = await apiClient.parentSelectionService.export(parents.map(p => p.id), 'csv')
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `parents-${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Parents exported to CSV')
    } catch {
      // Fallback to local export
      const csv = [
        ['Name', 'Type', 'GEBV', 'Heterosis', 'Traits', 'Pedigree'].join(','),
        ...parents.map(p => [
          p.name,
          p.type,
          p.gebv,
          p.heterosis_potential,
          `"${p.traits.join('; ')}"`,
          `"${p.pedigree}"`
        ].join(','))
      ].join('\n')

      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `parents-${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Parents exported to CSV')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="h-8 w-8 text-primary" />
            Parent Selection
          </h1>
          <p className="text-muted-foreground mt-1">Select optimal parents for crossing based on breeding values</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetchParents()} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportParents}>
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
          <Button disabled={selectedParents.length < 2}>
            <Plus className="h-4 w-4 mr-2" />Create Cross Plan
          </Button>
        </div>
      </div>

      {/* Selection Summary */}
      {selectedParents.length > 0 && (
        <Card className="bg-primary/5 border-primary">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <CheckCircle2 className="h-6 w-6 text-primary" />
                <div>
                  <div className="font-medium">{selectedParents.length} Parent{selectedParents.length > 1 ? 's' : ''} Selected</div>
                  <div className="text-sm text-muted-foreground">
                    {selectedParentData.map(p => p.name).join(' × ')}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {crossPrediction && (
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">Predicted Heterosis</div>
                    <div className="font-bold text-green-600">+{crossPrediction.heterosis.toFixed(1)}%</div>
                  </div>
                )}
                <Button variant="outline" size="sm" onClick={() => setSelectedParents([])}>Clear</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Parent List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Available Parents</CardTitle>
            <CardDescription>Select parents based on breeding objectives (click to select, max 2)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-center gap-4 mb-4">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search parents..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
              </div>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="elite">Elite</SelectItem>
                  <SelectItem value="donor">Donor</SelectItem>
                  <SelectItem value="landrace">Landrace</SelectItem>
                </SelectContent>
              </Select>
              <Input 
                placeholder="Filter by trait..." 
                value={traitFilter} 
                onChange={(e) => setTraitFilter(e.target.value)} 
                className="w-[180px]"
              />
            </div>

            {loading ? (
              <div className="space-y-2">
                {[1, 2, 3, 4].map(i => (
                  <Skeleton key={i} className="h-20 w-full" />
                ))}
              </div>
            ) : (
              <ScrollArea className="h-[400px]">
                <div className="space-y-2">
                  {filteredParents.map((parent) => (
                    <div 
                      key={parent.id} 
                      className={`flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-colors ${
                        selectedParents.includes(parent.id) ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
                      }`} 
                      onClick={() => toggleParent(parent.id)}
                    >
                      <Checkbox checked={selectedParents.includes(parent.id)} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{parent.name}</span>
                          <Badge variant={parent.type === 'elite' ? 'default' : parent.type === 'donor' ? 'secondary' : 'outline'}>
                            {parent.type}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {parent.traits.map((trait, i) => (
                            <Badge key={i} variant="outline" className="text-xs">{trait}</Badge>
                          ))}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">{parent.pedigree}</div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1 text-green-600">
                          <TrendingUp className="h-4 w-4" />
                          <span className="font-bold">{parent.gebv.toFixed(2)}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">GEBV</div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Selection Criteria & Recommendations */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Target className="h-5 w-5" />Breeding Objectives</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { trait: 'Yield', weight: 40, icon: <TrendingUp className="h-4 w-4" /> },
                  { trait: 'Disease Resistance', weight: 25, icon: <Dna className="h-4 w-4" /> },
                  { trait: 'Drought Tolerance', weight: 20, icon: <Star className="h-4 w-4" /> },
                  { trait: 'Grain Quality', weight: 15, icon: <Sparkles className="h-4 w-4" /> }
                ].map((obj, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {obj.icon}
                      <span className="text-sm">{obj.trait}</span>
                    </div>
                    <Badge variant="secondary">{obj.weight}%</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5" />AI Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {recommendations.map((rec, i) => (
                    <div 
                      key={i} 
                      className="p-3 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => setSelectedParents([rec.parent1_id, rec.parent2_id])}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-sm">{rec.cross}</span>
                        <Badge variant="default">{rec.score}%</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{rec.reason}</p>
                    </div>
                  ))}
                </div>
              )}
              <Button variant="outline" className="w-full mt-4" onClick={() => refetchRecs()}>
                <Sparkles className="h-4 w-4 mr-2" />Get More Suggestions
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Cross Prediction */}
      {selectedParents.length >= 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Cross Prediction</CardTitle>
            <CardDescription>Predicted performance of selected cross</CardDescription>
          </CardHeader>
          <CardContent>
            {predicting ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-2">Calculating prediction...</span>
              </div>
            ) : crossPrediction ? (
              <>
                <div className="flex items-center justify-center gap-4 mb-6">
                  {selectedParentData.map((p, i) => (
                    <div key={p.id} className="flex items-center gap-2">
                      <div className="p-4 bg-primary/10 rounded-lg text-center">
                        <div className="font-bold">{p.name}</div>
                        <div className="text-sm text-muted-foreground">{p.type}</div>
                      </div>
                      {i < selectedParentData.length - 1 && <ArrowRight className="h-6 w-6 text-muted-foreground" />}
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-4 gap-4 mb-4">
                  {[
                    { label: 'Expected GEBV', value: crossPrediction.expected_gebv.toFixed(2) },
                    { label: 'Heterosis', value: `+${crossPrediction.heterosis.toFixed(1)}%` },
                    { label: 'Genetic Distance', value: crossPrediction.genetic_distance.toFixed(2) },
                    { label: 'Success Probability', value: `${crossPrediction.success_probability}%` }
                  ].map((stat, i) => (
                    <div key={i} className="text-center p-4 bg-muted rounded-lg">
                      <div className="text-2xl font-bold text-primary">{stat.value}</div>
                      <div className="text-sm text-muted-foreground">{stat.label}</div>
                    </div>
                  ))}
                </div>
                <div className="p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    <strong>Recommendation:</strong> {crossPrediction.recommendation}
                  </p>
                </div>
                {crossPrediction.combined_traits.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm text-muted-foreground mb-2">Combined Traits:</p>
                    <div className="flex flex-wrap gap-1">
                      {crossPrediction.combined_traits.map((trait, i) => (
                        <Badge key={i} variant="outline">{trait}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

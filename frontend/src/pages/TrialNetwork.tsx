/**
 * Trial Network Page
 * Multi-environment trial coordination and analysis
 * Connected to /api/v2/trial-network/* endpoints
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Network, MapPin, Calendar, Users, Leaf, BarChart3, Globe, Filter, Download, Plus, Eye, Settings, TrendingUp, AlertCircle, RefreshCw } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface TrialSite {
  id: string
  name: string
  location: string
  country: string
  coordinates: { lat: number; lng: number }
  trials: number
  germplasm: number
  status: 'active' | 'completed' | 'planned'
  season: string
  lead: string
  region: string
}

interface NetworkStats {
  total_sites: number
  active_trials: number
  countries: number
  germplasm_entries: number
  collaborators: number
}

interface SharedGermplasm {
  id: string
  name: string
  sites: number
  performance: string
  crop: string
  type: string
}

interface PerformanceMetric {
  trait: string
  mean: number
  best: number
  worst: number
  cv: number
  n_sites: number
}

export function TrialNetwork() {
  const [selectedSeason, setSelectedSeason] = useState('2024-25')
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch trial sites
  const { data: sitesData, isLoading: sitesLoading, error: sitesError, refetch: refetchSites } = useQuery({
    queryKey: ['trial-network-sites', selectedSeason],
    queryFn: () => apiClient.trialNetworkService.getSites({ season: selectedSeason }),
    retry: 1,
  })

  // Fetch statistics
  const { data: statsData } = useQuery({
    queryKey: ['trial-network-stats', selectedSeason],
    queryFn: () => apiClient.trialNetworkService.getStatistics(selectedSeason),
    retry: 1,
  })

  // Fetch shared germplasm
  const { data: germplasmData } = useQuery({
    queryKey: ['trial-network-germplasm'],
    queryFn: () => apiClient.trialNetworkService.getSharedGermplasm(5),
    retry: 1,
  })

  // Fetch performance
  const { data: performanceData } = useQuery({
    queryKey: ['trial-network-performance'],
    queryFn: () => apiClient.trialNetworkService.getPerformance(),
    retry: 1,
  })

  // Use API data
  const sites: TrialSite[] = sitesData?.sites || []
  const stats: NetworkStats = statsData?.data || { total_sites: 0, active_trials: 0, countries: 0, germplasm_entries: 0, collaborators: 0 }
  const sharedGermplasm: SharedGermplasm[] = germplasmData?.germplasm || []
  const performance: PerformanceMetric[] = performanceData?.performance || []

  const filteredSites = searchQuery 
    ? sites.filter(s => s.name.toLowerCase().includes(searchQuery.toLowerCase()) || s.country.toLowerCase().includes(searchQuery.toLowerCase()))
    : sites

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'completed': return 'bg-blue-500'
      case 'planned': return 'bg-yellow-500'
      default: return 'bg-gray-500'
    }
  }

  if (sitesLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Network className="h-8 w-8 text-primary" />
            Trial Network
          </h1>
          <p className="text-muted-foreground mt-1">Multi-environment trial coordination and analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedSeason} onValueChange={setSelectedSeason}>
            <SelectTrigger className="w-[140px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="2024-25">2024-25</SelectItem>
              <SelectItem value="2023-24">2023-24</SelectItem>
              <SelectItem value="2022-23">2022-23</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
          <Button><Plus className="h-4 w-4 mr-2" />Add Site</Button>
        </div>
      </div>

      {sitesError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center gap-2">
            Failed to load trial network data. {sitesError instanceof Error ? sitesError.message : 'Please try again.'}
            <Button variant="outline" size="sm" onClick={() => refetchSites()}>
              <RefreshCw className="h-4 w-4 mr-2" />Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Network Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><MapPin className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.total_sites}</div>
                <div className="text-sm text-muted-foreground">Trial Sites</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><Calendar className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.active_trials}</div>
                <div className="text-sm text-muted-foreground">Active Trials</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Globe className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.countries}</div>
                <div className="text-sm text-muted-foreground">Countries</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Leaf className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.germplasm_entries.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Germplasm</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-pink-100 rounded-lg"><Users className="h-5 w-5 text-pink-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.collaborators}</div>
                <div className="text-sm text-muted-foreground">Collaborators</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="sites" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sites">Trial Sites</TabsTrigger>
          <TabsTrigger value="performance">Network Performance</TabsTrigger>
          <TabsTrigger value="germplasm">Shared Germplasm</TabsTrigger>
        </TabsList>

        <TabsContent value="sites" className="space-y-4">
          <div className="flex items-center gap-4">
            <Input placeholder="Search sites..." className="max-w-sm" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
            <Button variant="outline"><Filter className="h-4 w-4 mr-2" />Filter</Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSites.map((site) => (
              <Card key={site.id} className="hover:border-primary transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold">{site.name}</h3>
                      <p className="text-sm text-muted-foreground flex items-center gap-1">
                        <MapPin className="h-3 w-3" />{site.location}, {site.country}
                      </p>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(site.status)}`} />
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                    <div className="p-2 bg-muted rounded">
                      <div className="text-muted-foreground">Trials</div>
                      <div className="font-bold">{site.trials}</div>
                    </div>
                    <div className="p-2 bg-muted rounded">
                      <div className="text-muted-foreground">Germplasm</div>
                      <div className="font-bold">{site.germplasm}</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{site.lead}</span>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="sm"><Settings className="h-4 w-4" /></Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5" />Network-Wide Performance</CardTitle>
              <CardDescription>Aggregated trait performance across all sites</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {performance.map((trait, i) => (
                  <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">{trait.trait}</div>
                      <div className="flex items-center gap-4 mt-2">
                        <div className="text-sm"><span className="text-muted-foreground">Mean: </span><span className="font-bold">{trait.mean}</span></div>
                        <div className="text-sm"><span className="text-muted-foreground">Best: </span><span className="font-bold text-green-600">{trait.best}</span></div>
                        <div className="text-sm"><span className="text-muted-foreground">CV: </span><span className="font-bold">{trait.cv}%</span></div>
                      </div>
                    </div>
                    <TrendingUp className="h-5 w-5 text-green-500" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="germplasm" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Shared Germplasm Across Network</CardTitle>
              <CardDescription>Common entries tested at multiple locations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {sharedGermplasm.map((entry) => (
                  <div key={entry.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-medium">{entry.name}</div>
                      <div className="text-sm text-muted-foreground">{entry.performance}</div>
                    </div>
                    <Badge variant="secondary">{entry.sites} sites</Badge>
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

/**
 * Global Search Page
 * Search across all BrAPI entities
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'

type SearchCategory = 'all' | 'germplasm' | 'programs' | 'trials' | 'studies' | 'locations' | 'traits'

export function Search() {
  const [query, setQuery] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [category, setCategory] = useState<SearchCategory>('all')

  const { data: germplasmData, isLoading: loadingGermplasm } = useQuery({
    queryKey: ['search-germplasm', searchTerm],
    queryFn: () => apiClient.getGermplasm(0, 10, searchTerm),
    enabled: !!searchTerm && (category === 'all' || category === 'germplasm'),
  })

  const { data: programsData, isLoading: loadingPrograms } = useQuery({
    queryKey: ['search-programs', searchTerm],
    queryFn: () => apiClient.getPrograms(0, 10),
    enabled: !!searchTerm && (category === 'all' || category === 'programs'),
  })

  const { data: trialsData, isLoading: loadingTrials } = useQuery({
    queryKey: ['search-trials', searchTerm],
    queryFn: () => apiClient.getTrials(0, 10),
    enabled: !!searchTerm && (category === 'all' || category === 'trials'),
  })

  const { data: studiesData, isLoading: loadingStudies } = useQuery({
    queryKey: ['search-studies', searchTerm],
    queryFn: () => apiClient.getStudies(0, 10),
    enabled: !!searchTerm && (category === 'all' || category === 'studies'),
  })

  const { data: locationsData, isLoading: loadingLocations } = useQuery({
    queryKey: ['search-locations', searchTerm],
    queryFn: () => apiClient.getLocations(0, 10),
    enabled: !!searchTerm && (category === 'all' || category === 'locations'),
  })

  const { data: traitsData, isLoading: loadingTraits } = useQuery({
    queryKey: ['search-traits', searchTerm],
    queryFn: () => apiClient.getObservationVariables(0, 10),
    enabled: !!searchTerm && (category === 'all' || category === 'traits'),
  })

  const germplasm = germplasmData?.result?.data || []
  const programs = programsData?.result?.data || []
  const trials = trialsData?.result?.data || []
  const studies = studiesData?.result?.data || []
  const locations = locationsData?.result?.data || []
  const traits = traitsData?.result?.data || []

  const isLoading = loadingGermplasm || loadingPrograms || loadingTrials || loadingStudies || loadingLocations || loadingTraits

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchTerm(query)
  }

  const filterByQuery = (items: any[], fields: string[]) => {
    if (!searchTerm) return items
    const q = searchTerm.toLowerCase()
    return items.filter(item => 
      fields.some(field => item[field]?.toLowerCase?.()?.includes(q))
    )
  }

  const filteredGermplasm = filterByQuery(germplasm, ['germplasmName', 'accessionNumber', 'species'])
  const filteredPrograms = filterByQuery(programs, ['programName', 'abbreviation'])
  const filteredTrials = filterByQuery(trials, ['trialName', 'trialDescription'])
  const filteredStudies = filterByQuery(studies, ['studyName', 'studyDescription'])
  const filteredLocations = filterByQuery(locations, ['locationName', 'countryName'])
  const filteredTraits = filterByQuery(traits, ['observationVariableName', 'trait.traitName'])

  const totalResults = filteredGermplasm.length + filteredPrograms.length + filteredTrials.length + 
    filteredStudies.length + filteredLocations.length + filteredTraits.length

  const ResultCard = ({ icon, title, path, subtitle }: { icon: string; title: string; path: string; subtitle?: string }) => (
    <Link to={path} className="block p-3 rounded-lg border hover:bg-muted/50 transition-colors">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-primary truncate">{title}</p>
          {subtitle && <p className="text-sm text-muted-foreground truncate">{subtitle}</p>}
        </div>
      </div>
    </Link>
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">Search</h1>
        <p className="text-muted-foreground mt-1">Find anything across your breeding data</p>
      </div>

      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search germplasm, programs, trials, studies..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 text-lg"
              autoFocus
            />
            <Button type="submit" size="lg">🔍 Search</Button>
          </form>
        </CardContent>
      </Card>

      {searchTerm && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-muted-foreground">
              {isLoading ? 'Searching...' : `Found ${totalResults} results for "${searchTerm}"`}
            </p>
            <Tabs value={category} onValueChange={(v) => setCategory(v as SearchCategory)}>
              <TabsList>
                <TabsTrigger value="all">All</TabsTrigger>
                <TabsTrigger value="germplasm">Germplasm</TabsTrigger>
                <TabsTrigger value="programs">Programs</TabsTrigger>
                <TabsTrigger value="studies">Studies</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : totalResults === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-xl font-bold mb-2">No Results Found</h3>
                <p className="text-muted-foreground">Try a different search term or check your spelling</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {(category === 'all' || category === 'germplasm') && filteredGermplasm.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      🌱 Germplasm <Badge variant="secondary">{filteredGermplasm.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-2">
                    {filteredGermplasm.slice(0, 5).map((g: any) => (
                      <ResultCard key={g.germplasmDbId} icon="🌱" title={g.germplasmName} 
                        path={`/germplasm/${g.germplasmDbId}`} subtitle={g.species || g.accessionNumber} />
                    ))}
                    {filteredGermplasm.length > 5 && (
                      <Link to={`/germplasm?search=${searchTerm}`} className="text-primary hover:underline text-sm text-center py-2">
                        View all {filteredGermplasm.length} germplasm →
                      </Link>
                    )}
                  </CardContent>
                </Card>
              )}

              {(category === 'all' || category === 'programs') && filteredPrograms.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      🌾 Programs <Badge variant="secondary">{filteredPrograms.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-2">
                    {filteredPrograms.slice(0, 5).map((p: any) => (
                      <ResultCard key={p.programDbId} icon="🌾" title={p.programName} 
                        path={`/programs/${p.programDbId}`} subtitle={p.abbreviation} />
                    ))}
                  </CardContent>
                </Card>
              )}

              {(category === 'all' || category === 'studies') && filteredStudies.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      📈 Studies <Badge variant="secondary">{filteredStudies.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-2">
                    {filteredStudies.slice(0, 5).map((s: any) => (
                      <ResultCard key={s.studyDbId} icon="📈" title={s.studyName} 
                        path={`/studies/${s.studyDbId}`} subtitle={s.studyType} />
                    ))}
                  </CardContent>
                </Card>
              )}

              {(category === 'all' || category === 'trials') && filteredTrials.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      🧪 Trials <Badge variant="secondary">{filteredTrials.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-2">
                    {filteredTrials.slice(0, 5).map((t: any) => (
                      <ResultCard key={t.trialDbId} icon="🧪" title={t.trialName} 
                        path={`/trials/${t.trialDbId}`} subtitle={t.trialDescription?.slice(0, 50)} />
                    ))}
                  </CardContent>
                </Card>
              )}

              {(category === 'all' || category === 'locations') && filteredLocations.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      📍 Locations <Badge variant="secondary">{filteredLocations.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-2">
                    {filteredLocations.slice(0, 5).map((l: any) => (
                      <ResultCard key={l.locationDbId} icon="📍" title={l.locationName} 
                        path={`/locations/${l.locationDbId}`} subtitle={l.countryName} />
                    ))}
                  </CardContent>
                </Card>
              )}

              {(category === 'all' || category === 'traits') && filteredTraits.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      🔬 Traits <Badge variant="secondary">{filteredTraits.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-2">
                    {filteredTraits.slice(0, 5).map((t: any) => (
                      <ResultCard key={t.observationVariableDbId} icon="🔬" title={t.observationVariableName} 
                        path={`/traits/${t.observationVariableDbId}`} subtitle={t.trait?.traitClass} />
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </>
      )}

      {!searchTerm && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { icon: '🌱', label: 'Germplasm', path: '/germplasm', desc: 'Genetic material' },
            { icon: '🌾', label: 'Programs', path: '/programs', desc: 'Breeding programs' },
            { icon: '🧪', label: 'Trials', path: '/trials', desc: 'Field trials' },
            { icon: '📈', label: 'Studies', path: '/studies', desc: 'Research studies' },
            { icon: '📍', label: 'Locations', path: '/locations', desc: 'Field sites' },
            { icon: '🔬', label: 'Traits', path: '/traits', desc: 'Variables' },
          ].map((item) => (
            <Link key={item.path} to={item.path}>
              <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
                <CardContent className="p-6 text-center">
                  <div className="text-4xl mb-2">{item.icon}</div>
                  <p className="font-semibold">{item.label}</p>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

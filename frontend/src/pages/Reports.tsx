/**
 * Reports & Analytics Page
 * Data visualization and reporting
 */

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function Reports() {
  const { data: programsData, isLoading: loadingPrograms } = useQuery({
    queryKey: ['programs'],
    queryFn: () => apiClient.getPrograms(0, 100),
  })

  const { data: germplasmData, isLoading: loadingGermplasm } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.getGermplasm(0, 100),
  })

  const { data: trialsData, isLoading: loadingTrials } = useQuery({
    queryKey: ['trials'],
    queryFn: () => apiClient.getTrials(0, 100),
  })

  const { data: studiesData, isLoading: loadingStudies } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.getStudies(0, 100),
  })

  const { data: observationsData, isLoading: loadingObs } = useQuery({
    queryKey: ['observations'],
    queryFn: () => apiClient.getObservations(undefined, 0, 100),
  })

  const programs = programsData?.result?.data || []
  const germplasm = germplasmData?.result?.data || []
  const trials = trialsData?.result?.data || []
  const studies = studiesData?.result?.data || []
  const observations = observationsData?.result?.data || []

  const isLoading = loadingPrograms || loadingGermplasm || loadingTrials || loadingStudies || loadingObs

  // Calculate statistics
  const stats = {
    totalPrograms: programs.length,
    totalGermplasm: germplasm.length,
    totalTrials: trials.length,
    totalStudies: studies.length,
    totalObservations: observations.length,
    germplasmBySpecies: germplasm.reduce((acc: Record<string, number>, g: any) => {
      const species = g.species || 'Unknown'
      acc[species] = (acc[species] || 0) + 1
      return acc
    }, {}),
    trialsByYear: trials.reduce((acc: Record<string, number>, t: any) => {
      const year = t.startDate?.split('-')[0] || 'Unknown'
      acc[year] = (acc[year] || 0) + 1
      return acc
    }, {}),
  }

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Reports & Analytics</h1>
          <p className="text-muted-foreground mt-1">Data insights and summaries</p>
        </div>
        <Button variant="outline">📥 Export Report</Button>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="germplasm">Germplasm</TabsTrigger>
          <TabsTrigger value="trials">Trials</TabsTrigger>
          <TabsTrigger value="observations">Observations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-4xl font-bold text-primary">{isLoading ? '-' : stats.totalPrograms}</div>
                <div className="text-sm text-muted-foreground">Programs</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-4xl font-bold text-green-600">{isLoading ? '-' : stats.totalGermplasm}</div>
                <div className="text-sm text-muted-foreground">Germplasm</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-4xl font-bold text-blue-600">{isLoading ? '-' : stats.totalTrials}</div>
                <div className="text-sm text-muted-foreground">Trials</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-4xl font-bold text-purple-600">{isLoading ? '-' : stats.totalStudies}</div>
                <div className="text-sm text-muted-foreground">Studies</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-4xl font-bold text-orange-600">{isLoading ? '-' : stats.totalObservations}</div>
                <div className="text-sm text-muted-foreground">Observations</div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Reports */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest data entries</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {programs.slice(0, 5).map((p: any) => (
                    <div key={p.programDbId} className="flex items-center justify-between p-2 rounded hover:bg-muted/50">
                      <div className="flex items-center gap-2">
                        <span>🌾</span>
                        <span className="font-medium">{p.programName}</span>
                      </div>
                      <Badge variant="outline">Program</Badge>
                    </div>
                  ))}
                  {programs.length === 0 && <p className="text-muted-foreground text-center py-4">No recent activity</p>}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Data Quality</CardTitle>
                <CardDescription>Completeness metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Germplasm with species</span>
                      <span>{germplasm.filter((g: any) => g.species).length}/{germplasm.length}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-green-500" style={{ width: `${germplasm.length ? (germplasm.filter((g: any) => g.species).length / germplasm.length) * 100 : 0}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Trials with dates</span>
                      <span>{trials.filter((t: any) => t.startDate).length}/{trials.length}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500" style={{ width: `${trials.length ? (trials.filter((t: any) => t.startDate).length / trials.length) * 100 : 0}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Studies with location</span>
                      <span>{studies.filter((s: any) => s.locationDbId).length}/{studies.length}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500" style={{ width: `${studies.length ? (studies.filter((s: any) => s.locationDbId).length / studies.length) * 100 : 0}%` }} />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="germplasm" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Germplasm by Species</CardTitle>
              <CardDescription>Distribution of genetic material</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-48 w-full" />
              ) : Object.keys(stats.germplasmBySpecies).length === 0 ? (
                <p className="text-muted-foreground text-center py-8">No germplasm data available</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(stats.germplasmBySpecies).sort((a, b) => (b[1] as number) - (a[1] as number)).map(([species, count]) => (
                    <div key={species} className="flex items-center gap-4">
                      <div className="w-32 text-sm font-medium truncate italic">{species}</div>
                      <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-green-500 flex items-center justify-end pr-2" style={{ width: `${((count as number) / stats.totalGermplasm) * 100}%` }}>
                          <span className="text-xs text-white font-medium">{count as number}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trials" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Trials by Year</CardTitle>
              <CardDescription>Trial activity over time</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-48 w-full" />
              ) : Object.keys(stats.trialsByYear).length === 0 ? (
                <p className="text-muted-foreground text-center py-8">No trial data available</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(stats.trialsByYear).sort((a, b) => b[0].localeCompare(a[0])).map(([year, count]) => (
                    <div key={year} className="flex items-center gap-4">
                      <div className="w-20 text-sm font-medium">{year}</div>
                      <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 flex items-center justify-end pr-2" style={{ width: `${((count as number) / stats.totalTrials) * 100}%` }}>
                          <span className="text-xs text-white font-medium">{count as number}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="observations" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Observation Summary</CardTitle>
              <CardDescription>Phenotypic data overview</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-muted rounded-lg text-center">
                  <div className="text-3xl font-bold">{observations.length}</div>
                  <div className="text-sm text-muted-foreground">Total Observations</div>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <div className="text-3xl font-bold">{new Set(observations.map((o: any) => o.studyDbId)).size}</div>
                  <div className="text-sm text-muted-foreground">Studies with Data</div>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <div className="text-3xl font-bold">{new Set(observations.map((o: any) => o.observationVariableDbId)).size}</div>
                  <div className="text-sm text-muted-foreground">Variables Measured</div>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <div className="text-3xl font-bold">{new Set(observations.map((o: any) => o.observationUnitDbId)).size}</div>
                  <div className="text-sm text-muted-foreground">Observation Units</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

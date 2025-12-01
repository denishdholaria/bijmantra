/**
 * Observations Page - Data Collection Interface
 * BrAPI v2.1 Phenotyping Module
 */

import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export function Observations() {
  const [searchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [selectedStudy, setSelectedStudy] = useState(searchParams.get('studyDbId') || 'all')
  const pageSize = 50

  const { data: studiesData } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.getStudies(0, 100),
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['observations', selectedStudy, page],
    queryFn: () => apiClient.getObservations(selectedStudy === 'all' ? undefined : selectedStudy, page, pageSize),
    enabled: true,
  })

  const studies = studiesData?.result?.data || []
  const observations = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Observations</h1>
          <p className="text-muted-foreground mt-1">Phenotypic data collection and management</p>
        </div>
        <Button asChild>
          <Link to="/observations/collect">📝 Collect Data</Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Select value={selectedStudy} onValueChange={setSelectedStudy}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by study..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Studies</SelectItem>
                  {studies.map((s: any) => (
                    <SelectItem key={s.studyDbId} value={s.studyDbId}>{s.studyName}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" asChild>
              <Link to="/observations/import">📥 Import Data</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/observations/export">📤 Export Data</Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{totalCount}</div>
            <div className="text-sm text-muted-foreground">Total Observations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">{studies.length}</div>
            <div className="text-sm text-muted-foreground">Active Studies</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">-</div>
            <div className="text-sm text-muted-foreground">Variables Measured</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">-</div>
            <div className="text-sm text-muted-foreground">Observation Units</div>
          </CardContent>
        </Card>
      </div>

      {/* Observations Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Observations</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Observations</h3>
              <p className="text-muted-foreground">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
          ) : observations.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-2">No Observations Yet</h3>
              <p className="text-muted-foreground mb-6">Start collecting phenotypic data for your studies</p>
              <div className="flex gap-4 justify-center">
                <Button asChild>
                  <Link to="/observations/collect">📝 Collect Data</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/observations/import">📥 Import from File</Link>
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full" style={{ minWidth: '900px' }}>
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Study</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Obs. Unit</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Variable</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Value</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Collector</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {observations.map((obs: any) => (
                      <tr key={obs.observationDbId} className="hover:bg-muted/30">
                        <td className="px-4 py-3 text-sm">{obs.observationTimeStamp?.split('T')[0] || '-'}</td>
                        <td className="px-4 py-3 text-sm">{obs.studyDbId || '-'}</td>
                        <td className="px-4 py-3 text-sm font-mono">{obs.observationUnitDbId || '-'}</td>
                        <td className="px-4 py-3 text-sm">{obs.observationVariableName || obs.observationVariableDbId || '-'}</td>
                        <td className="px-4 py-3">
                          <Badge variant="secondary">{obs.value}</Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">{obs.collector || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-6 py-4 border-t flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Page {page + 1} of {totalPages} ({totalCount} total)
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>Previous</Button>
                    <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}>Next</Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

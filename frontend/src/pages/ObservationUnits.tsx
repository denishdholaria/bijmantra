/**
 * Observation Units Page
 * BrAPI v2.1 Phenotyping Module - Plot/Plant level management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export function ObservationUnits() {
  const [searchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [selectedStudy, setSelectedStudy] = useState(searchParams.get('studyDbId') || 'all')
  const pageSize = 50

  const { data: studiesData } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.getStudies(0, 100),
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['observationunits', selectedStudy, page],
    queryFn: () => apiClient.getObservationUnits(selectedStudy === 'all' ? undefined : selectedStudy, page, pageSize),
  })

  const studies = studiesData?.result?.data || []
  const units = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Observation Units</h1>
          <p className="text-muted-foreground mt-1">Plots, plants, and samples</p>
        </div>
        <Button asChild>
          <Link to="/observationunits/new">🌿 New Unit</Link>
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
            <Input placeholder="Search by unit name..." className="flex-1" />
            <Button variant="outline">🔍 Search</Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{totalCount}</div>
            <div className="text-sm text-muted-foreground">Total Units</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">-</div>
            <div className="text-sm text-muted-foreground">Plots</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">-</div>
            <div className="text-sm text-muted-foreground">Plants</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">-</div>
            <div className="text-sm text-muted-foreground">Samples</div>
          </CardContent>
        </Card>
      </div>

      {/* Units Table */}
      <Card>
        <CardHeader>
          <CardTitle>Observation Units</CardTitle>
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
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Units</h3>
              <p className="text-muted-foreground">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
          ) : units.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">🌿</div>
              <h3 className="text-xl font-bold mb-2">No Observation Units Yet</h3>
              <p className="text-muted-foreground mb-6">Create plots, plants, or samples for your studies</p>
              <Button asChild>
                <Link to="/observationunits/new">🌿 Create First Unit</Link>
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full" style={{ minWidth: '800px' }}>
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Unit Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Study</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Germplasm</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Position</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {units.map((unit: any) => (
                      <tr key={unit.observationUnitDbId} className="hover:bg-muted/30">
                        <td className="px-4 py-3">
                          <span className="font-medium">{unit.observationUnitName || unit.observationUnitDbId}</span>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline">{unit.observationUnitType || 'Plot'}</Badge>
                        </td>
                        <td className="px-4 py-3 text-sm">{unit.studyDbId || '-'}</td>
                        <td className="px-4 py-3 text-sm">{unit.germplasmName || unit.germplasmDbId || '-'}</td>
                        <td className="px-4 py-3 text-sm font-mono">
                          {unit.observationUnitPosition?.positionCoordinateX && unit.observationUnitPosition?.positionCoordinateY
                            ? `(${unit.observationUnitPosition.positionCoordinateX}, ${unit.observationUnitPosition.positionCoordinateY})`
                            : '-'}
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          <Link to={`/observationunits/${unit.observationUnitDbId}`} className="text-primary hover:underline text-sm">View</Link>
                          <Link to={`/observations/collect?unitDbId=${unit.observationUnitDbId}`} className="text-green-600 hover:underline text-sm">Collect</Link>
                        </td>
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

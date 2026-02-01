/**
 * Crosses Page - Breeding Cross Management
 * BrAPI v2.1 Germplasm Module
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
import { RefreshCw } from 'lucide-react'

export function Crosses() {
  const [searchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const [crossType, setCrossType] = useState('all')
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['crosses', page, crossType],
    queryFn: () => apiClient.crossService.getCrosses(page, pageSize),
  })

  const { data: statsData } = useQuery({
    queryKey: ['crosses-stats'],
    queryFn: () => apiClient.crossService.getCrossStats(),
  })

  const crosses = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)
  const stats = statsData?.result || { totalCount: 0, thisSeasonCount: 0, successfulCount: 0, pendingCount: 0 }

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Crosses</h1>
          <p className="text-muted-foreground mt-1">Breeding crosses and pedigrees</p>
        </div>
        <Button asChild>
          <Link to="/crosses/new">🧬 New Cross</Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input
              placeholder="Search by cross name or parent..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <Select value={crossType} onValueChange={setCrossType}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Cross type..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="BIPARENTAL">Biparental</SelectItem>
                <SelectItem value="SELF">Self</SelectItem>
                <SelectItem value="OPEN_POLLINATED">Open Pollinated</SelectItem>
                <SelectItem value="BACKCROSS">Backcross</SelectItem>
                <SelectItem value="DOUBLE_HAPLOID">Double Haploid</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">🔍 Search</Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{stats.totalCount}</div>
            <div className="text-sm text-muted-foreground">Total Crosses</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">{stats.thisSeasonCount}</div>
            <div className="text-sm text-muted-foreground">This Season</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">{stats.successfulCount}</div>
            <div className="text-sm text-muted-foreground">Successful</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">{stats.pendingCount}</div>
            <div className="text-sm text-muted-foreground">Pending</div>
          </CardContent>
        </Card>
      </div>

      {/* Crosses Table */}
      <Card>
        <CardHeader>
          <CardTitle>Breeding Crosses</CardTitle>
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
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Crosses</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button
                variant="outline"
                onClick={() => queryClient.invalidateQueries({ queryKey: ['crosses'] })}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : crosses.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">🧬</div>
              <h3 className="text-xl font-bold mb-2">No Crosses Yet</h3>
              <p className="text-muted-foreground mb-6">Plan and track your breeding crosses</p>
              <Button asChild>
                <Link to="/crosses/new">🧬 Create First Cross</Link>
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full" style={{ minWidth: '900px' }}>
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Cross Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Parent 1 (♀)</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Parent 2 (♂)</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Status</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {crosses.map((cross: any) => (
                      <tr key={cross.crossDbId} className="hover:bg-muted/30">
                        <td className="px-4 py-3">
                          <Link to={`/crosses/${cross.crossDbId}`} className="font-medium text-primary hover:underline">
                            {cross.crossName || cross.crossDbId}
                          </Link>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline">{cross.crossType || 'Unknown'}</Badge>
                        </td>
                        <td className="px-4 py-3 text-sm">{cross.parent1?.germplasmName || cross.parent1DbId || '-'}</td>
                        <td className="px-4 py-3 text-sm">{cross.parent2?.germplasmName || cross.parent2DbId || '-'}</td>
                        <td className="px-4 py-3 text-sm">{cross.crossingDate?.split('T')[0] || '-'}</td>
                        <td className="px-4 py-3">
                          <Badge variant={cross.status === 'successful' ? 'default' : 'secondary'}>
                            {cross.status || 'Planned'}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          <Link to={`/crosses/${cross.crossDbId}`} className="text-primary hover:underline text-sm">View</Link>
                          <Link to={`/crosses/${cross.crossDbId}/edit`} className="text-blue-600 hover:underline text-sm">Edit</Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-6 py-4 border-t flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Page {page + 1} of {totalPages}
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

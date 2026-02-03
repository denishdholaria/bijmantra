/**
 * Seed Lots Page - Inventory Management
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

export function SeedLots() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [germplasmFilter, setGermplasmFilter] = useState('all')
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data: germplasmData } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.germplasmService.getGermplasm(0, 100),
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['seedlots', page, germplasmFilter],
    queryFn: () => apiClient.seedLotService.getSeedLots(germplasmFilter === 'all' ? undefined : germplasmFilter, page, pageSize),
  })

  const germplasm = germplasmData?.result?.data || []
  const seedLots = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Seed Lots</h1>
          <p className="text-muted-foreground mt-1">Manage seed inventory and transactions</p>
        </div>
        <Button asChild>
          <Link to="/seedlots/new">📦 New Seed Lot</Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input
              placeholder="Search by lot name or ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <Select value={germplasmFilter} onValueChange={setGermplasmFilter}>
              <SelectTrigger className="w-full sm:w-64">
                <SelectValue placeholder="Filter by germplasm..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Germplasm</SelectItem>
                {germplasm.map((g: any) => (
                  <SelectItem key={g.germplasmDbId} value={g.germplasmDbId}>{g.germplasmName}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{totalCount}</div>
            <div className="text-sm text-muted-foreground">Total Lots</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">-</div>
            <div className="text-sm text-muted-foreground">Total Seeds</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">-</div>
            <div className="text-sm text-muted-foreground">Locations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-orange-600">-</div>
            <div className="text-sm text-muted-foreground">Low Stock</div>
          </CardContent>
        </Card>
      </div>

      {/* Seed Lots Table */}
      <Card>
        <CardHeader>
          <CardTitle>Inventory</CardTitle>
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
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Seed Lots</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button
                variant="outline"
                onClick={() => queryClient.invalidateQueries({ queryKey: ['seedlots'] })}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : seedLots.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📦</div>
              <h3 className="text-xl font-bold mb-2">No Seed Lots Yet</h3>
              <p className="text-muted-foreground mb-6">Start tracking your seed inventory</p>
              <Button asChild>
                <Link to="/seedlots/new">📦 Create First Seed Lot</Link>
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full" style={{ minWidth: '800px' }}>
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Lot Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Germplasm</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Amount</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Units</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Location</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Status</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {seedLots.map((lot: any) => (
                      <tr key={lot.seedLotDbId} className="hover:bg-muted/30">
                        <td className="px-4 py-3">
                          <Link to={`/seedlots/${lot.seedLotDbId}`} className="font-medium text-primary hover:underline">
                            {lot.seedLotName || lot.seedLotDbId}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-sm">{lot.germplasmDbId || '-'}</td>
                        <td className="px-4 py-3 text-sm font-mono">{lot.amount || '-'}</td>
                        <td className="px-4 py-3 text-sm">{lot.units || '-'}</td>
                        <td className="px-4 py-3 text-sm">{lot.locationDbId || '-'}</td>
                        <td className="px-4 py-3">
                          <Badge variant={lot.amount > 100 ? 'default' : 'destructive'}>
                            {lot.amount > 100 ? 'In Stock' : 'Low'}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          <Link to={`/seedlots/${lot.seedLotDbId}`} className="text-primary hover:underline text-sm">View</Link>
                          <button className="text-green-600 hover:underline text-sm">+ Add</button>
                          <button className="text-orange-600 hover:underline text-sm">- Remove</button>
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

/**
 * Scales Page
 * BrAPI v2.1 Phenotyping Module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { RefreshCw, Plus } from 'lucide-react'

export function Scales() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['scales', page, search],
    queryFn: () => apiClient.scalesService.getScales({ page, pageSize, scaleName: search }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.scalesService.deleteScale(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scales'] })
      setDeleteId(null)
    },
  })

  const scales = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(0)
    setSearchParams(search ? { search } : {})
  }

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Measurement Scales</h1>
          <p className="text-muted-foreground mt-1">Units and scales for phenotypic observation variables</p>
        </div>
        {/* Placeholder for Create Form */}
        <Button disabled title="Not implemented yet">
          <Plus className="mr-2 h-4 w-4" /> New Scale
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search scales..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <Button type="submit">🔍 Search</Button>
            {search && (
              <Button type="button" variant="outline" onClick={() => { setSearch(''); setSearchParams({}); }}>
                Clear
              </Button>
            )}
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Scales</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button
                variant="outline"
                onClick={() => queryClient.invalidateQueries({ queryKey: ['scales'] })}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : scales.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📏</div>
              <h3 className="text-xl font-bold mb-2">{search ? 'No Results Found' : 'No Scales Found'}</h3>
              <p className="text-muted-foreground mb-6">
                {search ? 'Try a different search term' : 'No measurement scales have been defined yet.'}
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full" style={{ minWidth: '800px' }}>
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Scale Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Data Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Decimal Places</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Valid Values</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {scales.map((s: any) => (
                      <tr key={s.scaleDbId} className="hover:bg-muted/30">
                        <td className="px-6 py-4 font-medium">{s.scaleName}</td>
                        <td className="px-6 py-4 text-sm">
                          <Badge variant="outline">{s.dataType}</Badge>
                        </td>
                        <td className="px-6 py-4 text-sm">{s.decimalPlaces !== null ? s.decimalPlaces : '-'}</td>
                        <td className="px-6 py-4 text-sm font-mono text-xs">
                          {s.validValues?.min !== undefined && `Min: ${s.validValues.min} `}
                          {s.validValues?.max !== undefined && `Max: ${s.validValues.max}`}
                          {s.validValues?.categories && `${s.validValues.categories.length} categories`}
                          {!s.validValues?.min && !s.validValues?.max && !s.validValues?.categories && '-'}
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          <button onClick={() => setDeleteId(s.scaleDbId)} className="text-red-600 hover:underline text-sm">Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-6 py-4 border-t flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, totalCount)} of {totalCount}
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

      <ConfirmDialog
        isOpen={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        title="Delete Scale"
        message="Are you sure you want to delete this scale? This may affect existing observation variables."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

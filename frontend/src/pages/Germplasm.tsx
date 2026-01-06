/**
 * Germplasm Page - List all germplasm/accessions
 * Core module for plant breeding - manages genetic material
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

export function Germplasm() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['germplasm', page, search],
    queryFn: () => apiClient.getGermplasm(page, pageSize, search),
  })

  const deleteMutation = useMutation({
    mutationFn: (germplasmDbId: string) => apiClient.deleteGermplasm(germplasmDbId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['germplasm'] })
      setDeleteId(null)
    },
  })

  const germplasm = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(0)
    setSearchParams(search ? { search } : {})
  }

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Germplasm</h1>
          <p className="text-muted-foreground mt-1">Manage your genetic material and accessions</p>
        </div>
        <Button asChild>
          <Link to="/germplasm/new">🌱 New Germplasm</Link>
        </Button>
      </div>

      {/* Search Bar */}
      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search by name, accession number, or pedigree..."
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

      {/* Germplasm List */}
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
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Germplasm</h3>
              <p className="text-muted-foreground">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
          ) : germplasm.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">🌱</div>
              <h3 className="text-xl font-bold mb-2">{search ? 'No Results Found' : 'No Germplasm Yet'}</h3>
              <p className="text-muted-foreground mb-6">
                {search ? 'Try a different search term' : 'Start by adding your first germplasm entry'}
              </p>
              {!search && (
                <Button asChild>
                  <Link to="/germplasm/new">🌱 Add First Germplasm</Link>
                </Button>
              )}
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full" style={{ minWidth: '800px' }}>
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Accession</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Species</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Pedigree</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Type</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {germplasm.map((g: any) => (
                      <tr key={g.germplasmDbId} className="hover:bg-muted/30">
                        <td className="px-6 py-4">
                          <Link to={`/germplasm/${g.germplasmDbId}`} className="font-medium text-primary hover:underline">
                            {g.germplasmName}
                          </Link>
                          {g.synonyms?.length > 0 && (
                            <p className="text-xs text-muted-foreground">{g.synonyms.slice(0, 2).join(', ')}</p>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm font-mono">{g.accessionNumber || '-'}</td>
                        <td className="px-6 py-4 text-sm italic">{g.species || g.genus || '-'}</td>
                        <td className="px-6 py-4 text-sm">{g.pedigree || '-'}</td>
                        <td className="px-6 py-4">
                          {g.germplasmType && <Badge variant="secondary">{g.germplasmType}</Badge>}
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          <Link to={`/germplasm/${g.germplasmDbId}`} className="text-primary hover:underline text-sm">View</Link>
                          <Link to={`/germplasm/${g.germplasmDbId}/edit`} className="text-blue-600 hover:underline text-sm">Edit</Link>
                          <button onClick={() => setDeleteId(g.germplasmDbId)} className="text-red-600 hover:underline text-sm">Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, totalCount)} of {totalCount}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}>
                      Next
                    </Button>
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
        title="Delete Germplasm"
        message="Are you sure you want to delete this germplasm entry? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

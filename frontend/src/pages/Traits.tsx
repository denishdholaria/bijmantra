/**
 * Traits/Observation Variables Page
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

export function Traits() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['variables', page, search],
    queryFn: () => apiClient.getObservationVariables(page, pageSize),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.deleteObservationVariable(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['variables'] })
      setDeleteId(null)
    },
  })

  const variables = data?.result?.data || []
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
          <h1 className="text-2xl lg:text-3xl font-bold">Observation Variables</h1>
          <p className="text-muted-foreground mt-1">Traits, methods, and scales for phenotyping</p>
        </div>
        <Button asChild>
          <Link to="/traits/new">📊 New Variable</Link>
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search by trait name or ontology term..."
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
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Variables</h3>
              <p className="text-muted-foreground">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
          ) : variables.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-2">{search ? 'No Results Found' : 'No Observation Variables Yet'}</h3>
              <p className="text-muted-foreground mb-6">
                {search ? 'Try a different search term' : 'Define traits, methods, and scales for phenotyping'}
              </p>
              {!search && (
                <Button asChild>
                  <Link to="/traits/new">📊 Create First Variable</Link>
                </Button>
              )}
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full" style={{ minWidth: '800px' }}>
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Variable Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Trait</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Method</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Scale</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Ontology</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {variables.map((v: any) => (
                      <tr key={v.observationVariableDbId} className="hover:bg-muted/30">
                        <td className="px-6 py-4">
                          <Link to={`/traits/${v.observationVariableDbId}`} className="font-medium text-primary hover:underline">
                            {v.observationVariableName}
                          </Link>
                        </td>
                        <td className="px-6 py-4 text-sm">{v.trait?.traitName || '-'}</td>
                        <td className="px-6 py-4 text-sm">{v.method?.methodName || '-'}</td>
                        <td className="px-6 py-4 text-sm">
                          {v.scale?.scaleName && (
                            <Badge variant="outline">{v.scale.scaleName}</Badge>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm font-mono text-xs">
                          {v.ontologyReference?.ontologyDbId || '-'}
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          <Link to={`/traits/${v.observationVariableDbId}`} className="text-primary hover:underline text-sm">View</Link>
                          <Link to={`/traits/${v.observationVariableDbId}/edit`} className="text-blue-600 hover:underline text-sm">Edit</Link>
                          <button onClick={() => setDeleteId(v.observationVariableDbId)} className="text-red-600 hover:underline text-sm">Delete</button>
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
        title="Delete Observation Variable"
        message="Are you sure you want to delete this variable? This may affect existing observations."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

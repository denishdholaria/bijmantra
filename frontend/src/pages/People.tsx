/**
 * People/Contacts Page
 * BrAPI v2.1 Core Module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { RefreshCw } from 'lucide-react'

export function People() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['people', page, search],
    queryFn: () => apiClient.peopleService.getPeople(page, pageSize),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.peopleService.deletePerson(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      setDeleteId(null)
    },
  })

  const people = data?.result?.data || []
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
          <h1 className="text-2xl lg:text-3xl font-bold">People</h1>
          <p className="text-muted-foreground mt-1">Contacts and team members</p>
        </div>
        <Button asChild>
          <Link to="/people/new">👤 Add Person</Link>
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
              aria-label="Search people"
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

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{totalCount}</div>
            <div className="text-sm text-muted-foreground">Total People</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600 dark:text-green-400">-</div>
            <div className="text-sm text-muted-foreground">Researchers</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">-</div>
            <div className="text-sm text-muted-foreground">Technicians</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">-</div>
            <div className="text-sm text-muted-foreground">Organizations</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Directory</CardTitle>
        </CardHeader>
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
              <h3 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-2">Error Loading People</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['people'] })}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : people.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">👥</div>
              <h3 className="text-xl font-bold mb-2">{search ? 'No Results Found' : 'No People Yet'}</h3>
              <p className="text-muted-foreground mb-6">
                {search ? 'Try a different search term' : 'Add team members and contacts'}
              </p>
              {!search && (
                <Button asChild>
                  <Link to="/people/new">👤 Add First Person</Link>
                </Button>
              )}
            </div>
          ) : (
            <>
              <div className="divide-y">
                {people.map((person: any) => (
                  <div key={person.personDbId} className="p-4 hover:bg-muted/30 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-xl">
                        {person.firstName?.[0] || person.lastName?.[0] || '👤'}
                      </div>
                      <div>
                        <Link to={`/people/${person.personDbId}`} className="font-medium text-primary hover:underline">
                          {person.firstName} {person.lastName}
                        </Link>
                        <p className="text-sm text-muted-foreground">{person.emailAddress || '-'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge variant="outline">{person.userType || 'User'}</Badge>
                      <div className="flex gap-2 items-center">
                        <Button variant="link" size="sm" asChild className="px-0"><Link to={`/people/${person.personDbId}`}>View</Link></Button>
                        <Button variant="link" size="sm" asChild className="px-0 text-blue-600 dark:text-blue-400"><Link to={`/people/${person.personDbId}/edit`}>Edit</Link></Button>
                        <Button variant="link" size="sm" onClick={() => setDeleteId(person.personDbId)} className="px-0 text-red-600 dark:text-red-400">Delete</Button>
                      </div>
                    </div>
                  </div>
                ))}
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

      <ConfirmDialog
        isOpen={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        title="Delete Person"
        message="Are you sure you want to delete this person?"
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

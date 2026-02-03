/**
 * Lists Page - Generic List Management
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'
import { RefreshCw } from 'lucide-react'

export function Lists() {
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const [listType, setListType] = useState('all')
  const [showCreate, setShowCreate] = useState(false)
  const [newListName, setNewListName] = useState('')
  const [newListType, setNewListType] = useState('germplasm')
  const [newListDesc, setNewListDesc] = useState('')
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['lists', page, listType],
    queryFn: () => apiClient.listService.getLists(page, pageSize),
  })

  const createMutation = useMutation({
    mutationFn: () => apiClient.listService.createList({
      listName: newListName,
      listType: newListType,
      listDescription: newListDesc || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lists'] })
      toast.success('List created!')
      setShowCreate(false)
      setNewListName('')
      setNewListDesc('')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create list'),
  })

  const lists = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  const listTypeColors: Record<string, string> = {
    germplasm: 'bg-green-100 text-green-800',
    studies: 'bg-blue-100 text-blue-800',
    programs: 'bg-purple-100 text-purple-800',
    trials: 'bg-orange-100 text-orange-800',
    observations: 'bg-pink-100 text-pink-800',
  }

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Lists</h1>
          <p className="text-muted-foreground mt-1">Organize and group your data</p>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger asChild>
            <Button>📋 New List</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New List</DialogTitle>
              <DialogDescription>Create a list to organize germplasm, studies, or other items</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="listName">List Name *</Label>
                <Input id="listName" value={newListName} onChange={(e) => setNewListName(e.target.value)} placeholder="My Selection List" />
              </div>
              <div className="space-y-2">
                <Label>List Type</Label>
                <Select value={newListType} onValueChange={setNewListType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="germplasm">Germplasm</SelectItem>
                    <SelectItem value="studies">Studies</SelectItem>
                    <SelectItem value="programs">Programs</SelectItem>
                    <SelectItem value="trials">Trials</SelectItem>
                    <SelectItem value="observations">Observations</SelectItem>
                    <SelectItem value="observationUnits">Observation Units</SelectItem>
                    <SelectItem value="observationVariables">Variables</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="listDesc">Description</Label>
                <Textarea id="listDesc" value={newListDesc} onChange={(e) => setNewListDesc(e.target.value)} rows={2} placeholder="Optional description..." />
              </div>
              <Button onClick={() => createMutation.mutate()} disabled={!newListName || createMutation.isPending} className="w-full">
                {createMutation.isPending ? 'Creating...' : '📋 Create List'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input placeholder="Search lists..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1" />
            <Select value={listType} onValueChange={setListType}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="All types..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="germplasm">Germplasm</SelectItem>
                <SelectItem value="studies">Studies</SelectItem>
                <SelectItem value="programs">Programs</SelectItem>
                <SelectItem value="trials">Trials</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{totalCount}</div>
            <div className="text-sm text-muted-foreground">Total Lists</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">-</div>
            <div className="text-sm text-muted-foreground">Germplasm Lists</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">-</div>
            <div className="text-sm text-muted-foreground">Study Lists</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">-</div>
            <div className="text-sm text-muted-foreground">Total Items</div>
          </CardContent>
        </Card>
      </div>

      {/* Lists Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Your Lists</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Lists</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['lists'] })}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : lists.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-xl font-bold mb-2">No Lists Yet</h3>
              <p className="text-muted-foreground mb-6">Create lists to organize your germplasm, studies, and more</p>
              <Button onClick={() => setShowCreate(true)}>📋 Create First List</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {lists.map((list: any) => (
                <Link key={list.listDbId} to={`/lists/${list.listDbId}`} className="block">
                  <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-primary">{list.listName}</h3>
                        <Badge className={listTypeColors[list.listType] || 'bg-gray-100 text-gray-800'}>
                          {list.listType}
                        </Badge>
                      </div>
                      {list.listDescription && (
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{list.listDescription}</p>
                      )}
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{list.listSize || 0} items</span>
                        <span className="text-muted-foreground">{list.dateCreated?.split('T')[0] || '-'}</span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Page {page + 1} of {totalPages}</div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>Previous</Button>
                <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}>Next</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

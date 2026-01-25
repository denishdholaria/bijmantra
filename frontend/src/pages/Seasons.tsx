/**
 * Seasons Page
 * BrAPI v2.1 Core Module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import { useActiveWorkspace } from '@/store/workspaceStore'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { RefreshCw } from 'lucide-react'

export function Seasons() {
  const [page, setPage] = useState(0)
  const [showCreate, setShowCreate] = useState(false)
  const [newSeasonName, setNewSeasonName] = useState('')
  const [newYear, setNewYear] = useState(new Date().getFullYear().toString())
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['seasons', page],
    queryFn: () => apiClient.getSeasons(page, pageSize),
  })

  const createMutation = useMutation({
    mutationFn: () => apiClient.createSeason({
      seasonName: newSeasonName,
      year: parseInt(newYear),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seasons'] })
      toast.success('Season created!')
      setShowCreate(false)
      setNewSeasonName('')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create season'),
  })

  const seasons = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  const currentYear = new Date().getFullYear()

  // Strict Workspace Isolation
  const activeWorkspace = useActiveWorkspace()

  useEffect(() => {
    if (!activeWorkspace) {
      console.warn('Seasons: No active workspace selected')
    }
  }, [activeWorkspace])

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Seasons</h1>
          <p className="text-muted-foreground mt-1">Growing seasons and time periods</p>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger asChild>
            <Button>📅 New Season</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Season</DialogTitle>
              <DialogDescription>Define a growing season for your trials and studies</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="seasonName">Season Name *</Label>
                <Input id="seasonName" value={newSeasonName} onChange={(e) => setNewSeasonName(e.target.value)} placeholder="e.g., Spring 2025, Wet Season" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="year">Year</Label>
                <Input id="year" type="number" value={newYear} onChange={(e) => setNewYear(e.target.value)} min="2000" max="2100" />
              </div>
              <Button onClick={() => createMutation.mutate()} disabled={!newSeasonName || createMutation.isPending} className="w-full">
                {createMutation.isPending ? 'Creating...' : '📅 Create Season'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{totalCount}</div>
            <div className="text-sm text-muted-foreground">Total Seasons</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">{currentYear}</div>
            <div className="text-sm text-muted-foreground">Current Year</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">-</div>
            <div className="text-sm text-muted-foreground">Active Trials</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">-</div>
            <div className="text-sm text-muted-foreground">Active Studies</div>
          </CardContent>
        </Card>
      </div>

      {/* Seasons Grid */}
      <Card>
        <CardHeader>
          <CardTitle>All Seasons</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Seasons</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['seasons'] })}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : seasons.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📅</div>
              <h3 className="text-xl font-bold mb-2">No Seasons Yet</h3>
              <p className="text-muted-foreground mb-6">Define growing seasons for your breeding activities</p>
              <Button onClick={() => setShowCreate(true)}>📅 Create First Season</Button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {seasons.map((season: any) => (
                <Card key={season.seasonDbId} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4 text-center">
                    <div className="text-3xl mb-2">📅</div>
                    <h3 className="font-semibold">{season.seasonName}</h3>
                    <Badge variant="outline" className="mt-2">{season.year}</Badge>
                  </CardContent>
                </Card>
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

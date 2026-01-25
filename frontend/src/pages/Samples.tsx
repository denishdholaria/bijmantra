/**
 * Samples Page - Genotyping Samples Management
 * BrAPI v2.1 Genotyping Module
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
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { RefreshCw } from 'lucide-react'

export function Samples() {
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newSampleName, setNewSampleName] = useState('')
  const [newSampleType, setNewSampleType] = useState('')
  const [newGermplasmId, setNewGermplasmId] = useState('')
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data: germplasmData } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.getGermplasm(0, 200),
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['samples', page],
    queryFn: () => apiClient.getSamples(page, pageSize),
  })

  const createMutation = useMutation({
    mutationFn: () => apiClient.createSample({
      sampleName: newSampleName,
      sampleType: newSampleType || undefined,
      germplasmDbId: newGermplasmId || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] })
      toast.success('Sample created!')
      setShowCreate(false)
      setNewSampleName('')
      setNewSampleType('')
      setNewGermplasmId('')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed'),
  })

  const germplasm = germplasmData?.result?.data || []
  const samples = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Samples</h1>
          <p className="text-muted-foreground mt-1">Genotyping samples and DNA extractions</p>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger asChild>
            <Button>🧫 New Sample</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Sample</DialogTitle>
              <DialogDescription>Register a sample for genotyping</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="sampleName">Sample Name *</Label>
                <Input id="sampleName" value={newSampleName} onChange={(e) => setNewSampleName(e.target.value)} placeholder="e.g., SAMPLE-2025-001" />
              </div>
              <div className="space-y-2">
                <Label>Sample Type</Label>
                <Select value={newSampleType} onValueChange={setNewSampleType}>
                  <SelectTrigger><SelectValue placeholder="Select type..." /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DNA">DNA</SelectItem>
                    <SelectItem value="RNA">RNA</SelectItem>
                    <SelectItem value="Tissue">Tissue</SelectItem>
                    <SelectItem value="Leaf">Leaf</SelectItem>
                    <SelectItem value="Seed">Seed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Source Germplasm</Label>
                <Select value={newGermplasmId} onValueChange={setNewGermplasmId}>
                  <SelectTrigger><SelectValue placeholder="Select germplasm..." /></SelectTrigger>
                  <SelectContent>
                    {germplasm.map((g: any) => (
                      <SelectItem key={g.germplasmDbId} value={g.germplasmDbId}>{g.germplasmName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={() => createMutation.mutate()} disabled={!newSampleName || createMutation.isPending} className="w-full">
                {createMutation.isPending ? 'Creating...' : '🧫 Create Sample'}
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
            <div className="text-sm text-muted-foreground">Total Samples</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">-</div>
            <div className="text-sm text-muted-foreground">DNA Extracted</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">-</div>
            <div className="text-sm text-muted-foreground">Genotyped</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">-</div>
            <div className="text-sm text-muted-foreground">Pending</div>
          </CardContent>
        </Card>
      </div>

      {/* Samples Table */}
      <Card>
        <CardHeader>
          <CardTitle>Sample Registry</CardTitle>
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
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Samples</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['samples'] })}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : samples.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">🧫</div>
              <h3 className="text-xl font-bold mb-2">No Samples Yet</h3>
              <p className="text-muted-foreground mb-6">Register samples for genotyping analysis</p>
              <Button onClick={() => setShowCreate(true)}>🧫 Create First Sample</Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full" style={{ minWidth: '800px' }}>
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Sample Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Germplasm</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Collection Date</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Status</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {samples.map((sample: any) => (
                      <tr key={sample.sampleDbId} className="hover:bg-muted/30">
                        <td className="px-4 py-3">
                          <span className="font-medium">{sample.sampleName || sample.sampleDbId}</span>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline">{sample.sampleType || 'Unknown'}</Badge>
                        </td>
                        <td className="px-4 py-3 text-sm">{sample.germplasmDbId || '-'}</td>
                        <td className="px-4 py-3 text-sm">{sample.sampleTimestamp?.split('T')[0] || '-'}</td>
                        <td className="px-4 py-3">
                          <Badge variant="secondary">{sample.sampleStatus || 'Registered'}</Badge>
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          <Link to={`/samples/${sample.sampleDbId}`} className="text-primary hover:underline text-sm">View</Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-6 py-4 border-t flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">Page {page + 1} of {totalPages}</div>
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

/**
 * Cross Detail Page
 * BrAPI v2.1 Germplasm Module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'

export function CrossDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDelete, setShowDelete] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['cross', id],
    queryFn: () => apiClient.getCross(id!),
    enabled: !!id,
  })

  const { data: parent1Data } = useQuery({
    queryKey: ['germplasm', data?.result?.parent1DbId],
    queryFn: () => apiClient.getGermplasmById(data!.result.parent1DbId),
    enabled: !!data?.result?.parent1DbId,
  })

  const { data: parent2Data } = useQuery({
    queryKey: ['germplasm', data?.result?.parent2DbId],
    queryFn: () => apiClient.getGermplasmById(data!.result.parent2DbId),
    enabled: !!data?.result?.parent2DbId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteCross(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crosses'] })
      toast.success('Cross deleted')
      navigate('/crosses')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Delete failed'),
  })

  const cross = data?.result
  const parent1 = parent1Data?.result
  const parent2 = parent2Data?.result

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !cross) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold mb-2">Cross Not Found</h2>
        <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Could not load cross'}</p>
        <Button asChild><Link to="/crosses">← Back to Crosses</Link></Button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild><Link to="/crosses">←</Link></Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">{cross.crossName || cross.crossDbId}</h1>
            <p className="text-muted-foreground">Breeding Cross</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild><Link to={`/crosses/${id}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDelete(true)}>🗑️ Delete</Button>
        </div>
      </div>

      {/* Cross Type Badge */}
      <div className="flex items-center gap-4">
        <Badge variant="outline" className="text-lg px-4 py-2">
          {cross.crossType || 'Unknown Type'}
        </Badge>
        {cross.pollinationTimeStamp && (
          <span className="text-muted-foreground">
            Pollinated: {cross.pollinationTimeStamp.split('T')[0]}
          </span>
        )}
      </div>

      {/* Parents */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-pink-200 bg-pink-50/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">♀</span> Female Parent
            </CardTitle>
          </CardHeader>
          <CardContent>
            {parent1 ? (
              <div className="space-y-2">
                <Link to={`/germplasm/${parent1.germplasmDbId}`} className="text-lg font-semibold text-primary hover:underline">
                  {parent1.germplasmName}
                </Link>
                <p className="text-sm text-muted-foreground italic">{parent1.species || 'Species unknown'}</p>
                <p className="text-sm text-muted-foreground">{parent1.accessionNumber || parent1.germplasmDbId}</p>
              </div>
            ) : cross.parent1DbId ? (
              <p className="text-muted-foreground">Loading parent...</p>
            ) : (
              <p className="text-muted-foreground">No female parent specified</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">♂</span> Male Parent
            </CardTitle>
          </CardHeader>
          <CardContent>
            {parent2 ? (
              <div className="space-y-2">
                <Link to={`/germplasm/${parent2.germplasmDbId}`} className="text-lg font-semibold text-primary hover:underline">
                  {parent2.germplasmName}
                </Link>
                <p className="text-sm text-muted-foreground italic">{parent2.species || 'Species unknown'}</p>
                <p className="text-sm text-muted-foreground">{parent2.accessionNumber || parent2.germplasmDbId}</p>
              </div>
            ) : cross.parent2DbId ? (
              <p className="text-muted-foreground">Loading parent...</p>
            ) : (
              <p className="text-muted-foreground">No male parent specified</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Cross Details */}
      <Card>
        <CardHeader>
          <CardTitle>Cross Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Cross ID</p>
              <p className="font-mono">{cross.crossDbId}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Cross Type</p>
              <p>{cross.crossType || '-'}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Crossing Project</p>
              <p>{cross.crossingProjectDbId || '-'}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Planned Cross</p>
              <p>{cross.plannedCrossDbId || '-'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progeny Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Progeny</CardTitle>
          <CardDescription>Offspring from this cross</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-8 text-center text-muted-foreground">
            <div className="text-4xl mb-2">🌱</div>
            <p>Progeny tracking coming soon</p>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Cross"
        message="Are you sure you want to delete this cross? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

/**
 * Sample Detail Page
 * BrAPI v2.1 Genotyping Module
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

export function SampleDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDelete, setShowDelete] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['sample', id],
    queryFn: () => apiClient.getSample(id!),
    enabled: !!id,
  })

  const { data: germplasmData } = useQuery({
    queryKey: ['germplasm', data?.result?.germplasmDbId],
    queryFn: () => apiClient.getGermplasmById(data!.result.germplasmDbId),
    enabled: !!data?.result?.germplasmDbId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteSample(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] })
      toast.success('Sample deleted')
      navigate('/samples')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Delete failed'),
  })

  const sample = data?.result
  const germplasm = germplasmData?.result

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !sample) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold mb-2">Sample Not Found</h2>
        <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Could not load sample'}</p>
        <Button asChild><Link to="/samples">← Back to Samples</Link></Button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label="Back to samples"><Link to="/samples">←</Link></Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">{sample.sampleName || sample.sampleDbId}</h1>
            <p className="text-muted-foreground">Genotyping Sample</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild><Link to={`/samples/${id}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDelete(true)}>🗑️ Delete</Button>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-4">
        <Badge variant="outline" className="text-lg px-4 py-2">
          {sample.sampleType || 'Unknown Type'}
        </Badge>
        <Badge variant={sample.sampleStatus === 'Genotyped' ? 'default' : 'secondary'}>
          {sample.sampleStatus || 'Registered'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sample Info */}
        <Card>
          <CardHeader>
            <CardTitle>Sample Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Sample ID</p>
                <p className="font-mono">{sample.sampleDbId}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Sample Type</p>
                <p>{sample.sampleType || '-'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Collection Date</p>
                <p>{sample.sampleTimestamp?.split('T')[0] || '-'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Tissue Type</p>
                <p>{sample.tissueType || '-'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Source Germplasm */}
        <Card>
          <CardHeader>
            <CardTitle>Source Germplasm</CardTitle>
          </CardHeader>
          <CardContent>
            {germplasm ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">🌱</span>
                  <div>
                    <Link to={`/germplasm/${germplasm.germplasmDbId}`} className="font-semibold text-primary hover:underline">
                      {germplasm.germplasmName}
                    </Link>
                    <p className="text-sm text-muted-foreground">{germplasm.accessionNumber || germplasm.germplasmDbId}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Species</p>
                    <p className="italic">{germplasm.species || '-'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Genus</p>
                    <p className="italic">{germplasm.genus || '-'}</p>
                  </div>
                </div>
              </div>
            ) : sample.germplasmDbId ? (
              <p className="text-muted-foreground">Loading germplasm...</p>
            ) : (
              <p className="text-muted-foreground">No germplasm linked</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Genotyping Results Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Genotyping Results</CardTitle>
          <CardDescription>Marker data and variant calls</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-8 text-center text-muted-foreground">
            <div className="text-4xl mb-2">🧬</div>
            <p>Genotyping results coming soon</p>
            <p className="text-sm mt-2">This will display marker data, variant calls, and allele information</p>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Sample"
        message="Are you sure you want to delete this sample? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

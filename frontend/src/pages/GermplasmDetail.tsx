/**
 * Germplasm Detail Page
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

export function GermplasmDetail() {
  const { germplasmDbId } = useParams<{ germplasmDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['germplasm', germplasmDbId],
    queryFn: () => apiClient.germplasmService.getGermplasmById(germplasmDbId!),
    enabled: !!germplasmDbId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.germplasmService.deleteGermplasm(germplasmDbId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['germplasm'] })
      toast.success('Germplasm deleted successfully')
      navigate('/germplasm')
    },
    onError: () => toast.error('Failed to delete germplasm'),
  })

  const germplasm = data?.result

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !germplasm) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-6xl mb-4">🌱</div>
            <h2 className="text-2xl font-bold mb-2">Germplasm Not Found</h2>
            <p className="text-muted-foreground mb-6">
              {error instanceof Error ? error.message : 'The germplasm entry does not exist.'}
            </p>
            <Button asChild><Link to="/germplasm">← Back to Germplasm</Link></Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label="Back to germplasm">
            <Link to="/germplasm">←</Link>
          </Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">{germplasm.germplasmName}</h1>
            <div className="flex flex-wrap gap-2 mt-1">
              {germplasm.accessionNumber && <Badge variant="outline">{germplasm.accessionNumber}</Badge>}
              {germplasm.germplasmType && <Badge variant="secondary">{germplasm.germplasmType}</Badge>}
              {germplasm.species && <Badge variant="outline" className="italic">{germplasm.genus} {germplasm.species}</Badge>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild><Link to={`/germplasm/${germplasmDbId}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDeleteDialog(true)}>🗑️ Delete</Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="pedigree">Pedigree</TabsTrigger>
          <TabsTrigger value="attributes">Attributes</TabsTrigger>
          <TabsTrigger value="studies">Studies</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader><CardTitle>🧬 Taxonomy</CardTitle></CardHeader>
                <CardContent>
                  <dl className="grid grid-cols-2 gap-4">
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Genus</dt>
                      <dd className="mt-1 italic">{germplasm.genus || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Species</dt>
                      <dd className="mt-1 italic">{germplasm.species || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Subtaxa</dt>
                      <dd className="mt-1">{germplasm.subtaxa || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Common Name</dt>
                      <dd className="mt-1">{germplasm.commonCropName || '-'}</dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>📋 Origin & Source</CardTitle></CardHeader>
                <CardContent>
                  <dl className="grid grid-cols-2 gap-4">
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Country of Origin</dt>
                      <dd className="mt-1">{germplasm.countryOfOriginCode || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Seed Source</dt>
                      <dd className="mt-1">{germplasm.seedSource || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Biological Status</dt>
                      <dd className="mt-1">{germplasm.biologicalStatusOfAccessionCode || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Acquisition Date</dt>
                      <dd className="mt-1">{germplasm.acquisitionDate || '-'}</dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader><CardTitle>Germplasm Info</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <dt className="text-sm font-semibold text-muted-foreground">Germplasm ID</dt>
                    <dd className="font-mono text-sm bg-muted px-2 py-1 rounded mt-1">{germplasm.germplasmDbId}</dd>
                  </div>
                  {germplasm.germplasmPUI && (
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">PUI</dt>
                      <dd className="font-mono text-xs mt-1 break-all">{germplasm.germplasmPUI}</dd>
                    </div>
                  )}
                  {germplasm.synonyms?.length > 0 && (
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Synonyms</dt>
                      <dd className="mt-1 flex flex-wrap gap-1">
                        {germplasm.synonyms.map((s: string, i: number) => (
                          <Badge key={i} variant="outline">{s}</Badge>
                        ))}
                      </dd>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  <Button variant="outline" className="w-full">📊 View Observations</Button>
                  <Button variant="outline" className="w-full">🧬 View Genotype</Button>
                  <Button variant="outline" className="w-full">📥 Export Data</Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="pedigree" className="mt-6">
          <Card>
            <CardHeader><CardTitle>🌳 Pedigree Information</CardTitle></CardHeader>
            <CardContent>
              {germplasm.pedigree ? (
                <div className="space-y-4">
                  <div className="p-4 bg-muted rounded-lg font-mono text-lg text-center">
                    {germplasm.pedigree}
                  </div>
                  <p className="text-sm text-muted-foreground text-center">
                    Pedigree notation showing breeding history and parentage
                  </p>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No pedigree information available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="attributes" className="mt-6">
          <Card>
            <CardContent className="p-12 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-2">Germplasm Attributes</h3>
              <p className="text-muted-foreground mb-4">Passport data and characterization attributes</p>
              <Button>➕ Add Attribute</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="studies" className="mt-6">
          <Card>
            <CardContent className="p-12 text-center">
              <div className="text-6xl mb-4">📈</div>
              <h3 className="text-xl font-bold mb-2">Associated Studies</h3>
              <p className="text-muted-foreground mb-4">Studies where this germplasm has been evaluated</p>
              <Button>🔗 Link to Study</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Germplasm"
        message={`Are you sure you want to delete "${germplasm.germplasmName}"?`}
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

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
import { GermplasmSummaryPanel } from '@/components/germplasm/GermplasmSummaryPanel'
import { TraitsSummary } from '@/components/germplasm/TraitsSummary'
import { AddToListDialog } from '@/components/germplasm/AddToListDialog'
import { Printer, Package } from 'lucide-react'

const biologicalStatusMap: Record<string, string> = {
  '100': 'Wild',
  '110': 'Natural',
  '120': 'Semi-natural/Wild',
  '200': 'Weedy',
  '300': 'Traditional cultivar/Landrace',
  '400': 'Breeding/Research Material',
  '410': "Breeder's Line",
  '411': 'Synthetic Population',
  '412': 'Hybrid',
  '413': 'Founder Stock',
  '414': 'Mutant',
  '415': 'Near Isogenic Line',
  '500': 'Advanced/Improved Cultivar',
  '999': 'Other'
}

interface Germplasm {
  germplasmDbId: string
  germplasmName: string
  accessionNumber?: string
  germplasmType?: string
  genus?: string
  species?: string
  subtaxa?: string
  commonCropName?: string
  countryOfOriginCode?: string
  seedSource?: string
  biologicalStatusOfAccessionCode?: string
  acquisitionDate?: string
  germplasmPUI?: string
  synonyms?: string[]
  pedigree?: string
}

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

  const { data: trialsData } = useQuery({
    queryKey: ['germplasm-trials', germplasmDbId],
    queryFn: () => apiClient.trialService.searchTrials({ germplasmDbIds: [germplasmDbId] }),
    enabled: !!germplasmDbId,
  })

  const { data: observationsData } = useQuery({
    queryKey: ['germplasm-observations', germplasmDbId],
    queryFn: () => apiClient.observationService.searchObservations({ germplasmDbIds: [germplasmDbId] }),
    enabled: !!germplasmDbId,
  })

  const { data: seedLotsData } = useQuery({
    queryKey: ['germplasm-seedlots', germplasmDbId],
    queryFn: () => apiClient.seedLotService.getSeedLots(germplasmDbId),
    enabled: !!germplasmDbId,
  })

  const { data: imagesData } = useQuery({
    queryKey: ['germplasm-images', germplasmDbId],
    queryFn: () => apiClient.imagesService.searchImages({ germplasmDbIds: [germplasmDbId] }),
    enabled: !!germplasmDbId,
  })

  const { data: pedigreeData } = useQuery({
    queryKey: ['germplasm-pedigree', germplasmDbId],
    queryFn: () => apiClient.pedigreeAnalysisService.getAncestors(germplasmDbId!),
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

  const germplasm = data?.result as Germplasm | undefined

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
        <div className="flex items-center gap-2 print:hidden">
          <AddToListDialog germplasmDbId={germplasm.germplasmDbId} germplasmName={germplasm.germplasmName} />
          <Button variant="outline" size="icon" onClick={() => window.print()} title="Print Passport">
            <Printer className="h-4 w-4" />
          </Button>
          <Button asChild><Link to={`/germplasm/${germplasmDbId}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDeleteDialog(true)}>🗑️ Delete</Button>
        </div>
      </div>

      <GermplasmSummaryPanel
        germplasm={germplasm}
        stats={{
          trialsCount: trialsData?.result?.data?.length ?? 0,
          observationsCount: observationsData?.result?.data?.length ?? 0,
          pedigreeDepth: pedigreeData?.n_ancestors ?? 0,
          imagesCount: imagesData?.result?.data?.length ?? 0
        }}
      />

      <Tabs defaultValue="overview" className="w-full mt-6">
        <TabsList className="grid w-full grid-cols-6 overflow-x-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="pedigree">Pedigree</TabsTrigger>
          <TabsTrigger value="trials">Trials</TabsTrigger>
          <TabsTrigger value="observations">Observations</TabsTrigger>
          <TabsTrigger value="inventory">Inventory</TabsTrigger>
          <TabsTrigger value="images">Images</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <TraitsSummary traits={[]} isLoading={false} /> {/* Placeholder for traits data */}

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
                      <dd className="mt-1">
                        {germplasm.biologicalStatusOfAccessionCode && biologicalStatusMap[germplasm.biologicalStatusOfAccessionCode]
                          ? `${germplasm.biologicalStatusOfAccessionCode} - ${biologicalStatusMap[germplasm.biologicalStatusOfAccessionCode]}`
                          : germplasm.biologicalStatusOfAccessionCode || '-'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Acquisition Date</dt>
                      <dd className="mt-1">
                        {germplasm.acquisitionDate
                          ? new Date(germplasm.acquisitionDate).toLocaleDateString()
                          : '-'}
                      </dd>
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
                  {germplasm.synonyms && germplasm.synonyms.length > 0 && (
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Synonyms</dt>
                      <dd className="mt-1 flex flex-wrap gap-1">
                        {germplasm.synonyms.map((s, i) => (
                          <Badge key={i} variant="outline">{s}</Badge>
                        ))}
                      </dd>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>🌍 Climate Suitability</CardTitle></CardHeader>
                <CardContent>
                  <div className="bg-muted p-6 rounded-lg text-center text-muted-foreground">
                    Environmental physics integration point
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>💰 Market Potential</CardTitle></CardHeader>
                <CardContent>
                   <div className="bg-muted p-6 rounded-lg text-center text-muted-foreground">
                    Economics integration point
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  <Button variant="outline" className="w-full">Request Seeds</Button>
                  <Button variant="outline" className="w-full">Plan Cross</Button>
                  <Button variant="outline" className="w-full">🧬 View Genotype</Button>
                  <Button variant="outline" className="w-full">📥 Export Data</Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="pedigree" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
               <CardTitle>🌳 Pedigree Information</CardTitle>
               <Button variant="outline" size="sm" asChild>
                 <Link to={`/breeding/pedigree-viewer?root=${germplasmDbId}`}>Open Viewer ↗</Link>
               </Button>
            </CardHeader>
            <CardContent>
              {germplasm.pedigree ? (
                <div className="space-y-4">
                  <div className="p-4 bg-muted rounded-lg font-mono text-lg text-center">
                    {germplasm.pedigree}
                  </div>
                  <p className="text-sm text-muted-foreground text-center">
                    {pedigreeData?.n_ancestors ? `${pedigreeData.n_ancestors} ancestors found.` : 'Pedigree notation showing breeding history.'}
                  </p>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No pedigree information available</p>
                </div>
              )}
              {/* Future: Embed mini-graph here */}
            </CardContent>
          </Card>

          <Card className="mt-6">
             <CardHeader><CardTitle>Breeding History</CardTitle></CardHeader>
             <CardContent>
                <p className="text-muted-foreground">Derived lines and progeny information will appear here.</p>
             </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trials" className="mt-6">
           <Card>
            <CardHeader><CardTitle>Participated Trials</CardTitle></CardHeader>
            <CardContent>
              {trialsData?.result?.data && trialsData.result.data.length > 0 ? (
                <div className="space-y-4">
                   {trialsData.result.data.map((trial: any) => (
                      <div key={trial.trialDbId} className="flex justify-between items-center border-b pb-2 last:border-0">
                         <div>
                            <Link to={`/trials/${trial.trialDbId}`} className="font-medium hover:underline text-primary">{trial.trialName}</Link>
                            <p className="text-sm text-muted-foreground">{trial.programName} • {trial.startDate}</p>
                         </div>
                         <Badge variant={trial.active ? "default" : "secondary"}>{trial.active ? 'Active' : 'Completed'}</Badge>
                      </div>
                   ))}
                </div>
              ) : (
                <div className="text-center py-12">
                   <p className="text-muted-foreground">No trials found for this germplasm.</p>
                </div>
              )}
            </CardContent>
           </Card>
        </TabsContent>

        <TabsContent value="observations" className="mt-6">
           <Card>
            <CardHeader><CardTitle>Phenotypic Observations</CardTitle></CardHeader>
            <CardContent>
               {observationsData?.result?.data && observationsData.result.data.length > 0 ? (
                 <div className="space-y-2">
                    {observationsData.result.data.slice(0, 10).map((obs: any, i: number) => (
                       <div key={i} className="flex justify-between items-center border-b p-2">
                          <span className="font-medium">{obs.observationVariableName}</span>
                          <span>{obs.value}</span>
                       </div>
                    ))}
                    {observationsData.result.data.length > 10 && <p className="text-sm text-muted-foreground text-center mt-2">Showing top 10 recent observations</p>}
                 </div>
               ) : (
                 <div className="text-center py-12">
                    <p className="text-muted-foreground">No observations found.</p>
                 </div>
               )}
            </CardContent>
           </Card>
        </TabsContent>

        <TabsContent value="inventory" className="mt-6">
           <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2"><Package className="h-5 w-5" /> Seed Inventory</CardTitle>
              <Button size="sm">Request Seeds</Button>
            </CardHeader>
            <CardContent>
               {seedLotsData?.result?.data && seedLotsData.result.data.length > 0 ? (
                 <div className="grid gap-4">
                    {seedLotsData.result.data.map((lot: any) => (
                       <div key={lot.seedLotDbId} className="flex justify-between items-center p-4 border rounded-lg">
                          <div>
                             <p className="font-medium">{lot.seedLotDescription || 'Seed Lot'}</p>
                             <p className="text-sm text-muted-foreground">Location: {lot.locationName || 'Unknown'}</p>
                          </div>
                          <div className="text-right">
                             <p className="font-bold">{lot.amount} {lot.units}</p>
                             <p className="text-xs text-muted-foreground">Available</p>
                          </div>
                       </div>
                    ))}
                 </div>
               ) : (
                 <div className="text-center py-12">
                    <p className="text-muted-foreground">No seed inventory available.</p>
                 </div>
               )}
            </CardContent>
           </Card>
        </TabsContent>

        <TabsContent value="images" className="mt-6">
           <Card>
            <CardHeader><CardTitle>📷 Images</CardTitle></CardHeader>
            <CardContent>
               {imagesData?.result?.data && imagesData.result.data.length > 0 ? (
                 <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {imagesData.result.data.map((img: any) => (
                       <div key={img.imageDbId} className="relative aspect-square bg-muted rounded-lg overflow-hidden group">
                          <img src={img.imageURL} alt={img.imageName} className="object-cover w-full h-full" />
                          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs p-2 text-center">
                             {img.imageName}
                          </div>
                       </div>
                    ))}
                 </div>
               ) : (
                 <div className="text-center py-12">
                    <p className="text-muted-foreground">No images found.</p>
                 </div>
               )}
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

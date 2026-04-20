/**
 * Variant Detail Page - BrAPI Genotyping
 */
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { apiClient } from '@/lib/api-client'
import type { BrAPIMetadata } from '@/lib/api/core/types'

export function VariantDetail() {
  const { id } = useParams<{ id: string }>()

  const { data, isLoading } = useQuery({
    queryKey: ['variant', id],
    queryFn: () => apiClient.genotypingResultsService.getVariant(id!),
    enabled: Boolean(id),
  })

  const { data: callsResponse, isLoading: callsLoading } = useQuery({
    queryKey: ['variant', id, 'calls'],
    queryFn: () => apiClient.genotypingResultsService.getVariantCalls(id!, { pageSize: 25 }),
    enabled: Boolean(id),
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  const variant = data?.result
  const calls = callsResponse?.result?.data ?? []
  const callCount = callsResponse?.metadata?.pagination?.totalCount ?? calls.length
  const notFoundMessage = data?.metadata?.status?.find((status: BrAPIMetadata['status'][number]) => status.messageType === 'ERROR')?.message

  if (!variant) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center gap-2">
          <Link to="/variants" className="text-muted-foreground hover:text-primary">
            ← Variants
          </Link>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Variant unavailable</CardTitle>
            <CardDescription>{notFoundMessage || 'This variant could not be loaded from the BrAPI variants API.'}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const passedFilters = variant.filtersPassed || []
  const failedFilters = variant.filtersFailed || []
  const formatTimestamp = (value?: string | null) => {
    if (!value) return 'Not reported'
    const timestamp = new Date(value)
    return Number.isNaN(timestamp.getTime()) ? value : timestamp.toLocaleString()
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link to="/variants" className="text-muted-foreground hover:text-primary">
              ← Variants
            </Link>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-3">
            {variant?.variantName}
            <Badge className="bg-blue-100 text-blue-800">{variant?.variantType}</Badge>
          </h1>
          <p className="text-muted-foreground mt-1">
            {variant?.referenceName}:{variant?.start}-{variant?.end}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" disabled>
            Export unavailable
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/calls?variantDbId=${variant.variantDbId}`}>View Calls</Link>
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="calls">Genotype Calls</TabsTrigger>
          <TabsTrigger value="annotations">Annotations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Position Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Chromosome</p>
                    <p className="font-medium">{variant?.referenceName}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Position</p>
                    <p className="font-medium">{variant?.start?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Variant Sets</p>
                    <p className="font-medium">{variant.variantSetDbId?.length ? variant.variantSetDbId.join(', ') : 'Not reported'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Reference DB</p>
                    <p className="font-medium">{variant.referenceDbId || 'Not reported'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Start</p>
                    <p className="font-medium">{variant?.start}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">End</p>
                    <p className="font-medium">{variant?.end}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Allele Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Reference Allele</p>
                  <p className="font-mono text-lg bg-green-100 text-green-800 px-3 py-1 rounded inline-block">
                    {variant?.referenceBases}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Alternate Allele(s)</p>
                  <div className="flex gap-2">
                    {variant?.alternateBases?.map((alt: string, i: number) => (
                      <span key={i} className="font-mono text-lg bg-red-100 text-red-800 px-3 py-1 rounded">
                        {alt}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Variant Type</p>
                  <Badge>{variant?.variantType}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                  <div>
                    <p className="text-sm text-muted-foreground">Created</p>
                    <p className="font-medium text-foreground">{formatTimestamp(variant.created)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Updated</p>
                    <p className="font-medium text-foreground">{formatTimestamp(variant.updated)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Quality & Filters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Passed Filters</p>
                <div className="flex flex-wrap gap-2">
                  {passedFilters.length > 0 ? (
                    passedFilters.map((filter: string) => (
                      <Badge key={filter} variant="default">
                        {filter}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No passed filters reported.</p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Failed Filters</p>
                <div className="flex flex-wrap gap-2">
                  {failedFilters.length > 0 ? (
                    failedFilters.map((filter: string) => (
                      <Badge key={filter} variant="destructive">
                        {filter}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No failed filters reported.</p>
                  )}
                </div>
              </div>
              <div className="text-sm text-muted-foreground">
                Filters applied: {variant.filtersApplied ? 'Yes' : 'No'}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calls" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Genotype Calls</CardTitle>
              <CardDescription>Showing {callCount.toLocaleString()} reported calls for this variant</CardDescription>
            </CardHeader>
            <CardContent>
              {callsLoading ? (
                <Skeleton className="h-40 w-full" />
              ) : calls.length > 0 ? (
                <div className="space-y-3">
                  {calls.map((call: { callSetDbId?: string | null; callSetName?: string | null; genotype?: string | null; genotype_value?: string | null; genotype_likelihood?: number | null }) => (
                    <div key={`${call.callSetDbId || 'unknown'}-${call.genotype || 'missing'}`} className="rounded-lg border p-4">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="font-medium">{call.callSetName || call.callSetDbId || 'Unnamed call set'}</p>
                          <p className="text-sm text-muted-foreground">Call set ID: {call.callSetDbId || 'Not reported'}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-mono text-lg">{call.genotype || call.genotype_value || 'Not reported'}</p>
                          <p className="text-xs text-muted-foreground">
                            Likelihood: {call.genotype_likelihood ?? 'Not reported'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                  <Button variant="link" asChild className="px-0">
                    <Link to={`/calls?variantDbId=${variant.variantDbId}`}>View full call list</Link>
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No genotype calls are currently reported for this variant.</p>
                  <Button variant="link" asChild className="mt-2">
                    <Link to={`/calls?variantDbId=${variant.variantDbId}`}>Open call search</Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="annotations" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Functional Annotations</CardTitle>
              <CardDescription>Annotation detail is not yet wired for this route.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <p>This page does not currently expose a backend annotation source for the selected variant.</p>
                <p className="text-sm mt-2">Use the overview and calls tabs for the live variant data currently available.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

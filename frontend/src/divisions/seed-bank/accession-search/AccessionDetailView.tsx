import { Link2, Package, History, Sprout, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useAccessionDetail } from './hooks/useAccessionDetail';

interface AccessionDetailViewProps {
  accessionId: string | null;
}

function getStatusTone(status: string) {
  const normalized = status.toLowerCase();
  if (normalized.includes('active')) {
    return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300';
  }
  if (normalized.includes('depleted') || normalized.includes('failed')) {
    return 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300';
  }
  return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300';
}

export function AccessionDetailView({ accessionId }: AccessionDetailViewProps) {
  const detailQuery = useAccessionDetail(accessionId);

  if (!accessionId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Accession Detail</CardTitle>
          <CardDescription>
            Choose an accession from the search results to inspect inventory, history, and related germplasm.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (detailQuery.isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (detailQuery.isError) {
    return (
      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle>Unable to load accession detail</CardTitle>
          <CardDescription>
            {detailQuery.error instanceof Error
              ? detailQuery.error.message
              : 'The accession detail request failed.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => detailQuery.refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const detail = detailQuery.data;

  if (!detail) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No accession detail available</CardTitle>
          <CardDescription>
            The requested accession could not be resolved from the current data surface.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle>{detail.accessionNumber}</CardTitle>
              <Badge className={getStatusTone(detail.status)}>{detail.status}</Badge>
            </div>
            <CardDescription>
              {detail.name} · {detail.species}
              {detail.subspecies ? ` · ${detail.subspecies}` : ''} · {detail.institute}
            </CardDescription>
          </div>
          <div className="text-sm text-muted-foreground">
            <div>Origin: {detail.origin}</div>
            <div>Traits: {detail.traits.length > 0 ? detail.traits.join(', ') : 'Not recorded'}</div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="inventory" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="inventory">
              <Package className="mr-2 h-4 w-4" />
              Seedlot Inventory
            </TabsTrigger>
            <TabsTrigger value="history">
              <History className="mr-2 h-4 w-4" />
              Observation History
            </TabsTrigger>
            <TabsTrigger value="related">
              <Sprout className="mr-2 h-4 w-4" />
              Related Germplasm
            </TabsTrigger>
          </TabsList>

          <TabsContent value="inventory">
            {detail.seedlots.length === 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">No seedlots linked</CardTitle>
                  <CardDescription>
                    No inventory lots are currently linked to this accession in the verified backend surface.
                  </CardDescription>
                </CardHeader>
              </Card>
            ) : (
              <div className="space-y-3">
                {detail.seedlots.map((lot) => (
                  <div key={lot.lotId} className="rounded-lg border p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-1">
                        <h3 className="font-semibold">{lot.lotId}</h3>
                        <p className="text-sm text-muted-foreground">
                          {lot.variety} · {lot.storageLocation}
                        </p>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        <div>{lot.quantityGrams.toLocaleString()} g</div>
                        <div>Viability: {lot.currentViabilityPercent ?? 'n/a'}%</div>
                        <div>Status: {lot.status}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="history">
            {detail.observationHistory.length === 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">No observation history available</CardTitle>
                  <CardDescription>
                    The current API surface exposes viability history only when linked seedlots have recorded tests.
                  </CardDescription>
                </CardHeader>
              </Card>
            ) : (
              <div className="space-y-3">
                {detail.observationHistory.map((entry) => (
                  <div key={entry.id} className="rounded-lg border p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-1">
                        <h3 className="font-semibold">{entry.label}</h3>
                        <p className="text-sm text-muted-foreground">
                          Lot {entry.lotId} · {new Date(entry.observedAt).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        <div className="font-medium text-foreground">{entry.value}</div>
                        <div>{entry.method ?? 'Method not recorded'}</div>
                      </div>
                    </div>
                    {entry.notes ? (
                      <p className="mt-3 text-sm text-muted-foreground">{entry.notes}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="related">
            {detail.relatedGermplasm.length === 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">No related germplasm found</CardTitle>
                  <CardDescription>
                    No additional germplasm entries matched the related-species query for this accession.
                  </CardDescription>
                </CardHeader>
              </Card>
            ) : (
              <div className="space-y-3">
                {detail.relatedGermplasm.map((item) => (
                  <div key={item.id} className="rounded-lg border p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="font-semibold">{item.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {item.accessionNumber} · {item.species} · {item.institute}
                        </p>
                      </div>
                      <Link2 className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

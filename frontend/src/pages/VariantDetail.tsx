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

export function VariantDetail() {
  const { id } = useParams<{ id: string }>()

  const { data, isLoading } = useQuery({
    queryKey: ['variant', id],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 300))
      return {
        variantDbId: id,
        variantName: `SNP_Chr1_${id?.replace('var', '')}`,
        variantType: 'SNP',
        referenceName: 'Chr1',
        start: 12345,
        end: 12346,
        referenceBases: 'A',
        alternateBases: ['G'],
        cipos: [-5, 5],
        ciend: [-5, 5],
        filters: ['PASS'],
        created: '2024-01-15',
        updated: '2024-01-20',
      }
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  const variant = data

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
          <Button variant="outline">Export VCF</Button>
          <Button variant="outline">View Calls</Button>
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
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Quality & Filters</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                {variant?.filters?.map((filter: string) => (
                  <Badge key={filter} variant={filter === 'PASS' ? 'default' : 'destructive'}>
                    {filter}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calls" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Genotype Calls</CardTitle>
              <CardDescription>Sample genotypes for this variant</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <p>🧬 Genotype calls will be displayed here</p>
                <Button variant="link" asChild className="mt-2">
                  <Link to="/calls">View All Calls</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="annotations" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Functional Annotations</CardTitle>
              <CardDescription>Predicted effects and annotations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <p>📝 Variant annotations will be displayed here</p>
                <p className="text-sm mt-2">Gene impact, consequence, etc.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

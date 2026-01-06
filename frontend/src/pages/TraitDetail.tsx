/**
 * Trait/Observation Variable Detail Page
 * BrAPI v2.1 Phenotyping Module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

export function TraitDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDelete, setShowDelete] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['variable', id],
    queryFn: () => apiClient.getObservationVariable(id!),
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteObservationVariable(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['variables'] })
      toast.success('Variable deleted')
      navigate('/traits')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Delete failed'),
  })

  const variable = data?.result

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !variable) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold mb-2">Variable Not Found</h2>
        <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Could not load variable'}</p>
        <Button asChild><Link to="/traits">← Back to Variables</Link></Button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild><Link to="/traits">←</Link></Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">{variable.observationVariableName}</h1>
            <p className="text-muted-foreground">Observation Variable</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild><Link to={`/traits/${id}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDelete(true)}>🗑️ Delete</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl mb-1">🔬</div>
            <p className="text-sm text-muted-foreground">Trait Class</p>
            <p className="font-semibold">{variable.trait?.traitClass || '-'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl mb-1">📏</div>
            <p className="text-sm text-muted-foreground">Data Type</p>
            <p className="font-semibold">{variable.scale?.dataType || '-'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl mb-1">📐</div>
            <p className="text-sm text-muted-foreground">Scale</p>
            <p className="font-semibold">{variable.scale?.scaleName || '-'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl mb-1">🏷️</div>
            <p className="text-sm text-muted-foreground">Ontology</p>
            <p className="font-semibold font-mono text-xs">{variable.ontologyReference?.ontologyDbId || '-'}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="trait" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="trait">Trait</TabsTrigger>
          <TabsTrigger value="method">Method</TabsTrigger>
          <TabsTrigger value="scale">Scale</TabsTrigger>
          <TabsTrigger value="ontology">Ontology</TabsTrigger>
        </TabsList>

        <TabsContent value="trait" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trait Information</CardTitle>
              <CardDescription>What is being measured</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Trait Name</p>
                  <p className="font-semibold">{variable.trait?.traitName || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Trait Class</p>
                  <Badge variant="outline">{variable.trait?.traitClass || 'Unclassified'}</Badge>
                </div>
              </div>
              {variable.trait?.traitDescription && (
                <div>
                  <p className="text-sm text-muted-foreground">Description</p>
                  <p>{variable.trait.traitDescription}</p>
                </div>
              )}
              {variable.trait?.synonyms?.length > 0 && (
                <div>
                  <p className="text-sm text-muted-foreground">Synonyms</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {variable.trait.synonyms.map((s: string, i: number) => (
                      <Badge key={i} variant="secondary">{s}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="method" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Method Information</CardTitle>
              <CardDescription>How the trait is measured</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Method Name</p>
                  <p className="font-semibold">{variable.method?.methodName || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Method Class</p>
                  <Badge variant="outline">{variable.method?.methodClass || 'Unclassified'}</Badge>
                </div>
              </div>
              {variable.method?.methodDescription && (
                <div>
                  <p className="text-sm text-muted-foreground">Description</p>
                  <p>{variable.method.methodDescription}</p>
                </div>
              )}
              {variable.method?.formula && (
                <div>
                  <p className="text-sm text-muted-foreground">Formula</p>
                  <code className="bg-muted px-2 py-1 rounded">{variable.method.formula}</code>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scale" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Scale Information</CardTitle>
              <CardDescription>Units and valid values</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Scale Name</p>
                  <p className="font-semibold">{variable.scale?.scaleName || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Data Type</p>
                  <Badge>{variable.scale?.dataType || 'Unknown'}</Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Decimal Places</p>
                  <p className="font-semibold">{variable.scale?.decimalPlaces ?? '-'}</p>
                </div>
              </div>
              {variable.scale?.validValues && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm font-semibold mb-2">Valid Values</p>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Minimum</p>
                      <p className="font-mono">{variable.scale.validValues.min ?? 'No limit'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Maximum</p>
                      <p className="font-mono">{variable.scale.validValues.max ?? 'No limit'}</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ontology" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Ontology Reference</CardTitle>
              <CardDescription>Standardized term definitions</CardDescription>
            </CardHeader>
            <CardContent>
              {variable.ontologyReference ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Ontology ID</p>
                      <p className="font-mono">{variable.ontologyReference.ontologyDbId}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Ontology Name</p>
                      <p>{variable.ontologyReference.ontologyName || '-'}</p>
                    </div>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm">
                      🔗 <a href={`https://cropontology.org/term/${variable.ontologyReference.ontologyDbId}`} 
                        target="_blank" rel="noopener" className="text-primary hover:underline">
                        View in Crop Ontology
                      </a>
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-muted-foreground">
                  <p>No ontology reference linked</p>
                  <p className="text-sm mt-2">Consider linking to Crop Ontology for standardization</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <ConfirmDialog
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Observation Variable"
        message="Are you sure you want to delete this variable? This may affect existing observations."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

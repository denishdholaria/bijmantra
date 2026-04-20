/**
 * Ontologies Page - BrAPI Phenotyping Module
 * Crop ontology management
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import type { OntologyRecord } from '@/lib/api/brapi/phenotyping/ontologies'

type OntologyFormState = {
  ontologyName: string
  version: string
  authors: string
  documentationURL: string
  description: string
}

const EMPTY_FORM: OntologyFormState = {
  ontologyName: '',
  version: '',
  authors: '',
  documentationURL: '',
  description: '',
}

export function Ontologies() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [formState, setFormState] = useState<OntologyFormState>(EMPTY_FORM)

  // Use real BrAPI endpoint
  const { data, isLoading } = useQuery({
    queryKey: ['ontologies', search],
    queryFn: () => apiClient.ontologiesService.getOntologies({ ontologyName: search || undefined }),
  })

  const ontologies: OntologyRecord[] = data?.result?.data || []

  const createOntologyMutation = useMutation({
    mutationFn: () =>
      apiClient.ontologiesService.createOntology({
        ontologyName: formState.ontologyName.trim(),
        version: formState.version.trim() || undefined,
        authors: formState.authors.trim() || undefined,
        documentationURL: formState.documentationURL.trim() || undefined,
        description: formState.description.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ontologies'] })
      toast.success('Ontology created')
      setFormState(EMPTY_FORM)
      setIsCreateOpen(false)
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to create ontology')
    },
  })

  const handleCreate = () => {
    if (!formState.ontologyName.trim()) {
      toast.error('Ontology name is required')
      return
    }

    createOntologyMutation.mutate()
  }

  const handleDialogChange = (open: boolean) => {
    setIsCreateOpen(open)
    if (!open && !createOntologyMutation.isPending) {
      setFormState(EMPTY_FORM)
    }
  }

  const updateFormField = <Field extends keyof OntologyFormState>(field: Field, value: OntologyFormState[Field]) => {
    setFormState((current) => ({
      ...current,
      [field]: value,
    }))
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Ontologies</h1>
          <p className="text-muted-foreground mt-1">Crop and trait ontology management</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={handleDialogChange}>
          <DialogTrigger asChild>
            <Button>📚 Add Ontology</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Ontology</DialogTitle>
              <DialogDescription>Register a new ontology in the shared catalog</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ontology-name">Ontology Name</Label>
                  <Input
                    id="ontology-name"
                    placeholder="Rice Ontology"
                    value={formState.ontologyName}
                    onChange={(event) => updateFormField('ontologyName', event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ontology-version">Version</Label>
                  <Input
                    id="ontology-version"
                    placeholder="1.0"
                    value={formState.version}
                    onChange={(event) => updateFormField('version', event.target.value)}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ontology-authors">Authors</Label>
                  <Input
                    id="ontology-authors"
                    placeholder="Crop Ontology Consortium"
                    value={formState.authors}
                    onChange={(event) => updateFormField('authors', event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ontology-documentation-url">Documentation URL</Label>
                  <Input
                    id="ontology-documentation-url"
                    placeholder="https://cropontology.org/..."
                    value={formState.documentationURL}
                    onChange={(event) => updateFormField('documentationURL', event.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="ontology-description">Description</Label>
                <Input
                  id="ontology-description"
                  placeholder="Trait vocabulary and metadata reference"
                  value={formState.description}
                  onChange={(event) => updateFormField('description', event.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => handleDialogChange(false)} disabled={createOntologyMutation.isPending}>Cancel</Button>
              <Button onClick={handleCreate} disabled={createOntologyMutation.isPending || !formState.ontologyName.trim()}>
                {createOntologyMutation.isPending ? 'Adding...' : 'Add Ontology'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Input
            placeholder="Search ontologies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-md"
            aria-label="Search ontologies"
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{ontologies.length}</div>
            <p className="text-sm text-muted-foreground">Ontologies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{ontologies.length > 0 ? (ontologies.reduce((total, ontology) => total + (ontology.termCount || 0), 0) / 1000).toFixed(1) : 0}K</div>
            <p className="text-sm text-muted-foreground">Total Terms</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{ontologies.filter((ontology) => ontology.ontologyDbId.startsWith('CO_')).length}</div>
            <p className="text-sm text-muted-foreground">Crop Ontologies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{ontologies.length > 0 ? new Set(ontologies.map((ontology) => ontology.authors)).size : 0}</div>
            <p className="text-sm text-muted-foreground">Sources</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map(i => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      ) : ontologies.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No ontologies found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ontologies.map((ontology) => (
            <Card key={ontology.ontologyDbId} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{ontology.ontologyName}</CardTitle>
                    <CardDescription>{ontology.ontologyDbId}</CardDescription>
                  </div>
                  {ontology.version && (
                    <Badge variant="outline">v{ontology.version}</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {ontology.description && (
                  <p className="text-sm text-muted-foreground mb-4">{ontology.description}</p>
                )}
                <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                  <div>
                    <p className="text-muted-foreground">Terms</p>
                    <p className="font-semibold">{(ontology.termCount || 0).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Authors</p>
                    <p className="font-semibold">{ontology.authors || '-'}</p>
                  </div>
                </div>
                {ontology.documentationURL && (
                  <Button size="sm" variant="outline" asChild className="w-full">
                    <a href={ontology.documentationURL} target="_blank" rel="noopener noreferrer">
                      🔗 View Documentation
                    </a>
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

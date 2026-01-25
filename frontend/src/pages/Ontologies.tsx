/**
 * Ontologies Page - BrAPI Phenotyping Module
 * Crop ontology management
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface Ontology {
  ontologyDbId: string
  ontologyName: string
  description?: string
  authors?: string
  version?: string
  copyright?: string
  licence?: string
  documentationURL?: string
  termCount?: number
}

export function Ontologies() {
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  // Use real BrAPI endpoint
  const { data, isLoading } = useQuery({
    queryKey: ['ontologies', search],
    queryFn: () => apiClient.getOntologies({ ontologyName: search || undefined }),
  })

  const ontologies: Ontology[] = data?.result?.data || []

  const handleCreate = () => {
    toast.success('Ontology added (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Ontologies</h1>
          <p className="text-muted-foreground mt-1">Crop and trait ontology management</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>📚 Add Ontology</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Ontology</DialogTitle>
              <DialogDescription>Register a new ontology reference</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Ontology ID</Label>
                  <Input placeholder="CO_320" />
                </div>
                <div className="space-y-2">
                  <Label>Version</Label>
                  <Input placeholder="1.0" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Ontology Name</Label>
                <Input placeholder="Rice Ontology" />
              </div>
              <div className="space-y-2">
                <Label>Documentation URL</Label>
                <Input placeholder="https://cropontology.org/..." />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Add Ontology</Button>
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
            <div className="text-2xl font-bold">{ontologies.length > 0 ? (ontologies.reduce((a: number, o: Ontology) => a + (o.termCount || 0), 0) / 1000).toFixed(1) : 0}K</div>
            <p className="text-sm text-muted-foreground">Total Terms</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{ontologies.filter((o: Ontology) => o.ontologyDbId.startsWith('CO_')).length}</div>
            <p className="text-sm text-muted-foreground">Crop Ontologies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{ontologies.length > 0 ? new Set(ontologies.map((o: Ontology) => o.authors)).size : 0}</div>
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

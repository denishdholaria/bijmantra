/**
 * Variant Sets Page - BrAPI Genotyping Module
 * Collections of variants (e.g., from VCF files)
 * Connected to BrAPI v2.1 /brapi/v2/variantsets endpoint
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface VariantSet {
  variantSetDbId: string
  variantSetName: string
  studyDbId?: string
  studyName?: string
  referenceSetDbId?: string
  variantCount: number
  callSetCount: number
  analysis?: { analysisName: string; software: string }[]
  created?: string
}

export function VariantSets() {
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newVS, setNewVS] = useState({ variantSetName: '', studyName: '', referenceSetDbId: '' })
  const queryClient = useQueryClient()

  // Fetch variant sets from BrAPI endpoint
  const { data, isLoading, error } = useQuery({
    queryKey: ['brapi-variantsets'],
    queryFn: () => apiClient.genotypingResultsService.getVariantSets({ pageSize: 100 }),
  })

  // Fetch reference sets from BrAPI endpoint
  const { data: refSetsData } = useQuery({
    queryKey: ['brapi-referencesets'],
    queryFn: () => apiClient.genomicMapService.getReferenceSets({ pageSize: 100 }),
  })

  // Fetch call sets for summary stats
  const { data: callSetsData } = useQuery({
    queryKey: ['brapi-callsets-summary'],
    queryFn: () => apiClient.genotypingResultsService.getCallSets({ pageSize: 1 }),
  })

  const createMutation = useMutation({
    mutationFn: async (data: typeof newVS) => {
      // Use extractVariantSet to create a new variant set
      return apiClient.genotypingResultsService.extractVariantSet({
        variantSetDbId: data.referenceSetDbId || 'new',
        callSetDbIds: [],
        variantDbIds: [],
      })
    },
    onSuccess: () => {
      toast.success('Variant set created')
      setIsCreateOpen(false)
      setNewVS({ variantSetName: '', studyName: '', referenceSetDbId: '' })
      queryClient.invalidateQueries({ queryKey: ['brapi-variantsets'] })
    },
    onError: () => toast.error('Failed to create variant set'),
  })

  const variantSets: VariantSet[] = data?.result?.data || []
  const referenceSets = refSetsData?.result?.data || []
  const totalCallSets = callSetsData?.metadata?.pagination?.totalCount || 0

  const filteredSets = search
    ? variantSets.filter(vs => vs.variantSetName.toLowerCase().includes(search.toLowerCase()) || vs.studyName?.toLowerCase().includes(search.toLowerCase()))
    : variantSets

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Variant Sets</h1>
          <p className="text-muted-foreground mt-1">Collections of genetic variants</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild><Button>📁 New Variant Set</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Variant Set</DialogTitle><DialogDescription>Import variants from VCF or create a new set</DialogDescription></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>Variant Set Name</Label><Input placeholder="Rice_GBS_2024" value={newVS.variantSetName} onChange={(e) => setNewVS({ ...newVS, variantSetName: e.target.value })} /></div>
              <div className="space-y-2"><Label>Study Name (optional)</Label><Input placeholder="Rice Diversity Panel" value={newVS.studyName} onChange={(e) => setNewVS({ ...newVS, studyName: e.target.value })} /></div>
              <div className="space-y-2">
                <Label>Reference Genome</Label>
                <Select value={newVS.referenceSetDbId} onValueChange={(v) => setNewVS({ ...newVS, referenceSetDbId: v })}>
                  <SelectTrigger><SelectValue placeholder="Select reference" /></SelectTrigger>
                  <SelectContent>{referenceSets.map((rs: any) => <SelectItem key={rs.referenceSetDbId} value={rs.referenceSetDbId}>{rs.referenceSetName}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={() => createMutation.mutate(newVS)} disabled={!newVS.variantSetName}>Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card><CardContent className="pt-6"><Input placeholder="Search variant sets..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-md" /></CardContent></Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{variantSets.length}</div><p className="text-sm text-muted-foreground">Variant Sets</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{((variantSets.reduce((a, vs) => a + (vs.variantCount || 0), 0)) / 1000).toFixed(0)}K</div><p className="text-sm text-muted-foreground">Total Variants</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{totalCallSets || variantSets.reduce((a, vs) => a + (vs.callSetCount || 0), 0)}</div><p className="text-sm text-muted-foreground">Total Samples</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{referenceSets.length}</div><p className="text-sm text-muted-foreground">Reference Genomes</p></CardContent></Card>
      </div>

      {error ? (
        <Card>
          <CardContent className="py-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                <span>Failed to load variant sets. {(error as Error).message}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ['brapi-variantsets'] })}
                  className="ml-4"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      ) : isLoading ? <div className="space-y-4">{[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full" />)}</div> : filteredSets.length === 0 ? (
        <Card><CardContent className="py-12 text-center"><p className="text-muted-foreground">No variant sets found</p></CardContent></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSets.map((vs) => (
            <Card key={vs.variantSetDbId} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div><CardTitle className="text-lg">{vs.variantSetName}</CardTitle><CardDescription>{vs.studyName || 'No study linked'}</CardDescription></div>
                  <Badge variant="outline">{vs.created}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div><p className="text-sm text-muted-foreground">Variants</p><p className="font-semibold">{vs.variantCount.toLocaleString()}</p></div>
                  <div><p className="text-sm text-muted-foreground">Samples</p><p className="font-semibold">{vs.callSetCount}</p></div>
                </div>
                {vs.analysis && vs.analysis.length > 0 && <div className="mb-4"><p className="text-sm text-muted-foreground">Analysis</p><p className="text-sm">{vs.analysis[0].analysisName} ({vs.analysis[0].software})</p></div>}
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" asChild><Link to={`/variants?variantSetDbId=${vs.variantSetDbId}`}>View Variants</Link></Button>
                  <Button size="sm" variant="outline" asChild><Link to={`/calls?variantSetDbId=${vs.variantSetDbId}`}>View Calls</Link></Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

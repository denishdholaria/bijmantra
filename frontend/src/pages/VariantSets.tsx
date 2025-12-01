/**
 * Variant Sets Page - BrAPI Genotyping Module
 * Collections of variants (e.g., from VCF files)
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

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

const mockVariantSets: VariantSet[] = [
  { variantSetDbId: 'vs001', variantSetName: 'Rice_GBS_2024', studyDbId: 'study001', studyName: 'Rice Diversity Panel', variantCount: 45000, callSetCount: 384, analysis: [{ analysisName: 'GATK HaplotypeCaller', software: 'GATK 4.2' }], created: '2024-01-15' },
  { variantSetDbId: 'vs002', variantSetName: 'Wheat_SNP_Array', studyDbId: 'study002', studyName: 'Wheat Breeding Lines', variantCount: 90000, callSetCount: 192, analysis: [{ analysisName: 'Axiom Analysis', software: 'Axiom Suite' }], created: '2024-02-01' },
  { variantSetDbId: 'vs003', variantSetName: 'Maize_WGS_Pilot', studyDbId: 'study003', studyName: 'Maize Inbred Lines', variantCount: 125000, callSetCount: 48, analysis: [{ analysisName: 'DeepVariant', software: 'DeepVariant 1.4' }], created: '2024-02-20' },
]

export function VariantSets() {
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['variantSets', search],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockVariantSets
      if (search) {
        filtered = filtered.filter(vs => 
          vs.variantSetName.toLowerCase().includes(search.toLowerCase()) ||
          vs.studyName?.toLowerCase().includes(search.toLowerCase())
        )
      }
      return { result: { data: filtered } }
    },
  })

  const variantSets = data?.result?.data || []

  const handleCreate = () => {
    toast.success('Variant set created (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Variant Sets</h1>
          <p className="text-muted-foreground mt-1">Collections of genetic variants</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>📁 New Variant Set</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Variant Set</DialogTitle>
              <DialogDescription>Import variants from VCF or create a new set</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Variant Set Name</Label>
                <Input placeholder="Rice_GBS_2024" />
              </div>
              <div className="space-y-2">
                <Label>Study (optional)</Label>
                <Input placeholder="Select or enter study name" />
              </div>
              <div className="space-y-2">
                <Label>VCF File</Label>
                <Input type="file" accept=".vcf,.vcf.gz" />
              </div>
              <div className="space-y-2">
                <Label>Reference Genome</Label>
                <Input placeholder="e.g., GRCh38, IRGSP-1.0" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Input
            placeholder="Search variant sets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-md"
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockVariantSets.length}</div>
            <p className="text-sm text-muted-foreground">Variant Sets</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{(mockVariantSets.reduce((a, vs) => a + vs.variantCount, 0) / 1000).toFixed(0)}K</div>
            <p className="text-sm text-muted-foreground">Total Variants</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockVariantSets.reduce((a, vs) => a + vs.callSetCount, 0)}</div>
            <p className="text-sm text-muted-foreground">Total Samples</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{new Set(mockVariantSets.map(vs => vs.studyDbId)).size}</div>
            <p className="text-sm text-muted-foreground">Studies</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
      ) : variantSets.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No variant sets found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {variantSets.map((vs) => (
            <Card key={vs.variantSetDbId} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{vs.variantSetName}</CardTitle>
                    <CardDescription>{vs.studyName || 'No study linked'}</CardDescription>
                  </div>
                  <Badge variant="outline">{vs.created}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Variants</p>
                    <p className="font-semibold">{vs.variantCount.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Samples</p>
                    <p className="font-semibold">{vs.callSetCount}</p>
                  </div>
                </div>
                {vs.analysis && vs.analysis.length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm text-muted-foreground">Analysis</p>
                    <p className="text-sm">{vs.analysis[0].analysisName} ({vs.analysis[0].software})</p>
                  </div>
                )}
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" asChild>
                    <Link to={`/variants?variantSetDbId=${vs.variantSetDbId}`}>View Variants</Link>
                  </Button>
                  <Button size="sm" variant="outline" asChild>
                    <Link to={`/allelematrix?variantSetDbId=${vs.variantSetDbId}`}>Matrix</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

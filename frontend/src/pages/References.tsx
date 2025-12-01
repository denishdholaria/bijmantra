/**
 * References Page - BrAPI Genotyping Module
 * Genome reference sequences
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

interface Reference {
  referenceDbId: string
  referenceName: string
  referenceSetDbId: string
  referenceSetName: string
  length: number
  md5checksum?: string
  sourceURI?: string
  species?: { genus: string; species: string }
}

const mockReferences: Reference[] = [
  { referenceDbId: 'ref001', referenceName: 'Chr1', referenceSetDbId: 'rs001', referenceSetName: 'IRGSP-1.0', length: 43270923, md5checksum: 'abc123...', species: { genus: 'Oryza', species: 'sativa' } },
  { referenceDbId: 'ref002', referenceName: 'Chr2', referenceSetDbId: 'rs001', referenceSetName: 'IRGSP-1.0', length: 35937250, md5checksum: 'def456...', species: { genus: 'Oryza', species: 'sativa' } },
  { referenceDbId: 'ref003', referenceName: 'Chr3', referenceSetDbId: 'rs001', referenceSetName: 'IRGSP-1.0', length: 36413819, md5checksum: 'ghi789...', species: { genus: 'Oryza', species: 'sativa' } },
  { referenceDbId: 'ref004', referenceName: '1A', referenceSetDbId: 'rs002', referenceSetName: 'IWGSC RefSeq v2.1', length: 594102056, md5checksum: 'jkl012...', species: { genus: 'Triticum', species: 'aestivum' } },
  { referenceDbId: 'ref005', referenceName: '1B', referenceSetDbId: 'rs002', referenceSetName: 'IWGSC RefSeq v2.1', length: 689851870, md5checksum: 'mno345...', species: { genus: 'Triticum', species: 'aestivum' } },
]

export function References() {
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['references', search],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockReferences
      if (search) {
        filtered = filtered.filter(r => 
          r.referenceName.toLowerCase().includes(search.toLowerCase()) ||
          r.referenceSetName.toLowerCase().includes(search.toLowerCase())
        )
      }
      return { result: { data: filtered } }
    },
  })

  const references = data?.result?.data || []
  const referenceSets = [...new Set(mockReferences.map(r => r.referenceSetName))]

  const formatLength = (length: number) => {
    if (length >= 1e9) return `${(length / 1e9).toFixed(2)} Gb`
    if (length >= 1e6) return `${(length / 1e6).toFixed(2)} Mb`
    if (length >= 1e3) return `${(length / 1e3).toFixed(2)} Kb`
    return `${length} bp`
  }

  const handleCreate = () => {
    toast.success('Reference added (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genome References</h1>
          <p className="text-muted-foreground mt-1">Reference sequences for variant calling</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>🧬 Add Reference</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Reference Sequence</DialogTitle>
              <DialogDescription>Register a new genome reference</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Reference Name</Label>
                <Input placeholder="Chr1" />
              </div>
              <div className="space-y-2">
                <Label>Reference Set</Label>
                <Input placeholder="IRGSP-1.0" />
              </div>
              <div className="space-y-2">
                <Label>Length (bp)</Label>
                <Input type="number" placeholder="43270923" />
              </div>
              <div className="space-y-2">
                <Label>Source URI</Label>
                <Input placeholder="https://..." />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Add Reference</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Input
            placeholder="Search references..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-md"
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockReferences.length}</div>
            <p className="text-sm text-muted-foreground">References</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{referenceSets.length}</div>
            <p className="text-sm text-muted-foreground">Reference Sets</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{formatLength(mockReferences.reduce((a, r) => a + r.length, 0))}</div>
            <p className="text-sm text-muted-foreground">Total Length</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{new Set(mockReferences.map(r => `${r.species?.genus} ${r.species?.species}`)).size}</div>
            <p className="text-sm text-muted-foreground">Species</p>
          </CardContent>
        </Card>
      </div>

      {/* Reference Sets */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {referenceSets.map(setName => {
          const setRefs = mockReferences.filter(r => r.referenceSetName === setName)
          const totalLength = setRefs.reduce((a, r) => a + r.length, 0)
          const species = setRefs[0]?.species
          return (
            <Card key={setName}>
              <CardHeader>
                <CardTitle className="text-lg">{setName}</CardTitle>
                <CardDescription>
                  {species && <em>{species.genus} {species.species}</em>}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Chromosomes</p>
                    <p className="font-semibold">{setRefs.length}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Total Size</p>
                    <p className="font-semibold">{formatLength(totalLength)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Avg Size</p>
                    <p className="font-semibold">{formatLength(totalLength / setRefs.length)}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {setRefs.map(ref => (
                    <Badge key={ref.referenceDbId} variant="outline" className="text-xs">
                      {ref.referenceName}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>All References</CardTitle>
            <CardDescription>{references.length} reference sequences</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Reference Set</TableHead>
                  <TableHead>Species</TableHead>
                  <TableHead className="text-right">Length</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {references.map((ref) => (
                  <TableRow key={ref.referenceDbId}>
                    <TableCell className="font-medium">{ref.referenceName}</TableCell>
                    <TableCell>{ref.referenceSetName}</TableCell>
                    <TableCell>
                      {ref.species && <em>{ref.species.genus} {ref.species.species}</em>}
                    </TableCell>
                    <TableCell className="text-right font-mono">{formatLength(ref.length)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

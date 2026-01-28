/**
 * References Page - BrAPI Genotyping Module
 * Genome reference sequences
 * Connected to BrAPI v2.1 /brapi/v2/references endpoint
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { useQueryClient } from '@tanstack/react-query'

interface Reference {
  referenceDbId: string
  referenceName: string
  referenceSetDbId: string
  length: number
  md5checksum?: string
}

interface ReferenceSet {
  referenceSetDbId: string
  referenceSetName: string
  description?: string
  species?: { genus: string; species: string }
}

export function References() {
  const [search, setSearch] = useState('')
  const [refSetFilter, setRefSetFilter] = useState<string>('all')
  const queryClient = useQueryClient()

  // Fetch references from BrAPI endpoint
  const { data: refsData, isLoading, error } = useQuery({
    queryKey: ['brapi-references', refSetFilter],
    queryFn: () => apiClient.referencesService.getReferences({
      referenceSetDbId: refSetFilter !== 'all' ? refSetFilter : undefined,
      pageSize: 100,
    }),
  })

  // Fetch reference sets from BrAPI endpoint
  const { data: refSetsData } = useQuery({
    queryKey: ['brapi-referencesets'],
    queryFn: () => apiClient.referencesService.getReferenceSets({ pageSize: 100 }),
  })

  const references: Reference[] = refsData?.result?.data || []
  const referenceSets: ReferenceSet[] = refSetsData?.result?.data || []

  const filteredRefs = search
    ? references.filter(r => r.referenceName.toLowerCase().includes(search.toLowerCase()))
    : references

  const formatLength = (length: number) => {
    if (length >= 1e9) return `${(length / 1e9).toFixed(2)} Gb`
    if (length >= 1e6) return `${(length / 1e6).toFixed(2)} Mb`
    if (length >= 1e3) return `${(length / 1e3).toFixed(2)} Kb`
    return `${length} bp`
  }

  const getRefSetName = (refSetId: string) => referenceSets.find(r => r.referenceSetDbId === refSetId)?.referenceSetName || refSetId
  const totalLength = filteredRefs.reduce((a, r) => a + (r.length || 0), 0)
  const uniqueSpecies = new Set(referenceSets.map(rs => rs.species?.genus)).size

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genome References</h1>
          <p className="text-muted-foreground mt-1">Reference sequences for variant calling (BrAPI v2.1)</p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input placeholder="Search references..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1" />
            <Select value={refSetFilter} onValueChange={setRefSetFilter}>
              <SelectTrigger className="w-[200px]"><SelectValue placeholder="Reference Set" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Reference Sets</SelectItem>
                {referenceSets.map(rs => <SelectItem key={rs.referenceSetDbId} value={rs.referenceSetDbId}>{rs.referenceSetName}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{filteredRefs.length}</div><p className="text-sm text-muted-foreground">References</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{referenceSets.length}</div><p className="text-sm text-muted-foreground">Reference Sets</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{formatLength(totalLength)}</div><p className="text-sm text-muted-foreground">Total Length</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{uniqueSpecies}</div><p className="text-sm text-muted-foreground">Species</p></CardContent></Card>
      </div>

      {/* Reference Sets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {referenceSets.map(rs => {
          const setRefs = references.filter(r => r.referenceSetDbId === rs.referenceSetDbId)
          const totalLength = setRefs.reduce((a, r) => a + r.length, 0)
          return (
            <Card key={rs.referenceSetDbId} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <CardTitle className="text-lg">{rs.referenceSetName}</CardTitle>
                <CardDescription>{rs.species && <em>{rs.species.genus} {rs.species.species}</em>}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                  <div><p className="text-muted-foreground">Chromosomes</p><p className="font-semibold">{setRefs.length}</p></div>
                  <div><p className="text-muted-foreground">Total Size</p><p className="font-semibold">{formatLength(totalLength)}</p></div>
                </div>
                {rs.description && <p className="text-sm text-muted-foreground mb-2">{rs.description}</p>}
                <div className="flex flex-wrap gap-1">
                  {setRefs.slice(0, 6).map(ref => <Badge key={ref.referenceDbId} variant="outline" className="text-xs">{ref.referenceName}</Badge>)}
                  {setRefs.length > 6 && <Badge variant="outline" className="text-xs">+{setRefs.length - 6} more</Badge>}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {error ? (
        <Card>
          <CardContent className="py-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                <span>Failed to load references. {(error as Error).message}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ['brapi-references'] })}
                  className="ml-4"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      ) : isLoading ? <Skeleton className="h-64 w-full" /> : (
        <Card>
          <CardHeader><CardTitle>All References</CardTitle><CardDescription>{filteredRefs.length} reference sequences</CardDescription></CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Reference Set</TableHead><TableHead className="text-right">Length</TableHead><TableHead>MD5</TableHead></TableRow></TableHeader>
              <TableBody>
                {filteredRefs.slice(0, 50).map((ref) => (
                  <TableRow key={ref.referenceDbId}>
                    <TableCell className="font-medium">{ref.referenceName}</TableCell>
                    <TableCell>{getRefSetName(ref.referenceSetDbId)}</TableCell>
                    <TableCell className="text-right font-mono">{formatLength(ref.length)}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">{ref.md5checksum?.slice(0, 8)}...</TableCell>
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

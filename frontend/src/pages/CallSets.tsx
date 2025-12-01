/**
 * Call Sets Page - BrAPI Genotyping Module
 * Sample-level genotype data containers
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface CallSet {
  callSetDbId: string
  callSetName: string
  sampleDbId: string
  variantSetDbIds: string[]
  created?: string
  updated?: string
}

const mockCallSets: CallSet[] = [
  { callSetDbId: 'cs001', callSetName: 'Sample_001_GBS', sampleDbId: 'sample001', variantSetDbIds: ['vs001'], created: '2024-01-15' },
  { callSetDbId: 'cs002', callSetName: 'Sample_002_GBS', sampleDbId: 'sample002', variantSetDbIds: ['vs001'], created: '2024-01-15' },
  { callSetDbId: 'cs003', callSetName: 'Sample_003_GBS', sampleDbId: 'sample003', variantSetDbIds: ['vs001'], created: '2024-01-15' },
  { callSetDbId: 'cs004', callSetName: 'Sample_001_SNPArray', sampleDbId: 'sample001', variantSetDbIds: ['vs002'], created: '2024-02-01' },
  { callSetDbId: 'cs005', callSetName: 'Sample_004_WGS', sampleDbId: 'sample004', variantSetDbIds: ['vs003'], created: '2024-02-20' },
]

export function CallSets() {
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['callSets', search],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockCallSets
      if (search) {
        filtered = filtered.filter(cs => 
          cs.callSetName.toLowerCase().includes(search.toLowerCase())
        )
      }
      return { result: { data: filtered } }
    },
  })

  const callSets = data?.result?.data || []

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Call Sets</h1>
          <p className="text-muted-foreground mt-1">Sample-level genotype data containers</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/allelematrix">📊 View Matrix</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/calls">🧬 View Calls</Link>
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Input
            placeholder="Search call sets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-md"
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockCallSets.length}</div>
            <p className="text-sm text-muted-foreground">Call Sets</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{new Set(mockCallSets.map(cs => cs.sampleDbId)).size}</div>
            <p className="text-sm text-muted-foreground">Unique Samples</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{new Set(mockCallSets.flatMap(cs => cs.variantSetDbIds)).size}</div>
            <p className="text-sm text-muted-foreground">Variant Sets</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">98.5%</div>
            <p className="text-sm text-muted-foreground">Avg Call Rate</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Call Sets</CardTitle>
            <CardDescription>{callSets.length} call sets found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Call Set Name</TableHead>
                  <TableHead>Sample ID</TableHead>
                  <TableHead>Variant Sets</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {callSets.map((cs) => (
                  <TableRow key={cs.callSetDbId}>
                    <TableCell className="font-medium">{cs.callSetName}</TableCell>
                    <TableCell>
                      <Link to={`/samples/${cs.sampleDbId}`} className="text-primary hover:underline">
                        {cs.sampleDbId}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {cs.variantSetDbIds.map(vsId => (
                          <Badge key={vsId} variant="outline">{vsId}</Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>{cs.created}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost" asChild>
                        <Link to={`/calls?callSetDbId=${cs.callSetDbId}`}>View Calls</Link>
                      </Button>
                    </TableCell>
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

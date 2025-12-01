/**
 * Genotype Calls Page - BrAPI Genotyping Module
 * Genotype calls for samples at variant positions
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'

interface GenotypeCall {
  callSetDbId: string
  callSetName: string
  variantDbId: string
  variantName: string
  genotype: { values: string[] }
  genotypeValue: string
  genotypeQuality: number
  readDepth: number
  phaseSet?: string
}

// Mock data
const mockCalls: GenotypeCall[] = [
  { callSetDbId: 'cs001', callSetName: 'Sample_001', variantDbId: 'var001', variantName: 'SNP_Chr1_12345', genotype: { values: ['0', '1'] }, genotypeValue: '0/1', genotypeQuality: 99, readDepth: 45 },
  { callSetDbId: 'cs002', callSetName: 'Sample_002', variantDbId: 'var001', variantName: 'SNP_Chr1_12345', genotype: { values: ['1', '1'] }, genotypeValue: '1/1', genotypeQuality: 95, readDepth: 38 },
  { callSetDbId: 'cs003', callSetName: 'Sample_003', variantDbId: 'var001', variantName: 'SNP_Chr1_12345', genotype: { values: ['0', '0'] }, genotypeValue: '0/0', genotypeQuality: 99, readDepth: 52 },
  { callSetDbId: 'cs001', callSetName: 'Sample_001', variantDbId: 'var002', variantName: 'SNP_Chr1_23456', genotype: { values: ['0', '0'] }, genotypeValue: '0/0', genotypeQuality: 98, readDepth: 41 },
  { callSetDbId: 'cs002', callSetName: 'Sample_002', variantDbId: 'var002', variantName: 'SNP_Chr1_23456', genotype: { values: ['0', '1'] }, genotypeValue: '0/1', genotypeQuality: 92, readDepth: 35 },
]

export function Calls() {
  const [search, setSearch] = useState('')
  const [sampleFilter, setSampleFilter] = useState<string>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['calls', search, sampleFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockCalls
      if (search) {
        filtered = filtered.filter(c => 
          c.variantName.toLowerCase().includes(search.toLowerCase()) ||
          c.callSetName.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (sampleFilter !== 'all') {
        filtered = filtered.filter(c => c.callSetDbId === sampleFilter)
      }
      return { result: { data: filtered } }
    },
  })

  const calls = data?.result?.data || []
  const samples = [...new Set(mockCalls.map(c => ({ id: c.callSetDbId, name: c.callSetName })))]

  const getGenotypeColor = (gt: string) => {
    if (gt === '0/0') return 'bg-green-100 text-green-800'
    if (gt === '1/1') return 'bg-red-100 text-red-800'
    return 'bg-yellow-100 text-yellow-800'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genotype Calls</h1>
          <p className="text-muted-foreground mt-1">Sample genotypes at variant positions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => toast.success('Export started (demo)')}>
            📥 Export VCF
          </Button>
          <Button variant="outline" onClick={() => toast.success('Matrix view (demo)')}>
            📊 Matrix View
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by variant or sample..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={sampleFilter} onValueChange={setSampleFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by sample" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Samples</SelectItem>
                {samples.map(s => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockCalls.length}</div>
            <p className="text-sm text-muted-foreground">Total Calls</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockCalls.filter(c => c.genotypeValue === '0/1').length}</div>
            <p className="text-sm text-muted-foreground">Heterozygous</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockCalls.filter(c => c.genotypeValue === '1/1').length}</div>
            <p className="text-sm text-muted-foreground">Homozygous Alt</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{(mockCalls.reduce((a, c) => a + c.genotypeQuality, 0) / mockCalls.length).toFixed(1)}</div>
            <p className="text-sm text-muted-foreground">Avg Quality</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Genotype Calls</CardTitle>
            <CardDescription>{calls.length} calls found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sample</TableHead>
                  <TableHead>Variant</TableHead>
                  <TableHead>Genotype</TableHead>
                  <TableHead>Quality</TableHead>
                  <TableHead>Depth</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {calls.map((call, i) => (
                  <TableRow key={`${call.callSetDbId}-${call.variantDbId}-${i}`}>
                    <TableCell className="font-medium">{call.callSetName}</TableCell>
                    <TableCell>{call.variantName}</TableCell>
                    <TableCell>
                      <Badge className={getGenotypeColor(call.genotypeValue)}>
                        {call.genotypeValue}
                      </Badge>
                    </TableCell>
                    <TableCell>{call.genotypeQuality}</TableCell>
                    <TableCell>{call.readDepth}x</TableCell>
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

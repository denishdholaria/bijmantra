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
import { apiClient } from '@/lib/api-client'

interface GenotypeCall {
  callSetDbId: string
  callSetName: string
  variantDbId: string
  variantName: string
  genotypeValue: string
  genotypeQuality: number
  readDepth: number
}

export function Calls() {
  const [search, setSearch] = useState('')
  const [sampleFilter, setSampleFilter] = useState<string>('all')
  const [variantSetFilter, setVariantSetFilter] = useState<string>('all')

  const { data: callsData, isLoading } = useQuery({
    queryKey: ['genotyping-calls', sampleFilter, variantSetFilter],
    queryFn: () => apiClient.getCalls({
      callSetDbId: sampleFilter !== 'all' ? sampleFilter : undefined,
      variantSetDbId: variantSetFilter !== 'all' ? variantSetFilter : undefined,
      pageSize: 500,
    }),
  })

  const { data: callSetsData } = useQuery({
    queryKey: ['genotyping-callsets'],
    queryFn: () => apiClient.getCallSets({ pageSize: 100 }),
  })

  const { data: variantSetsData } = useQuery({
    queryKey: ['genotyping-variantsets'],
    queryFn: () => apiClient.getVariantSets(),
  })

  const { data: statsData } = useQuery({
    queryKey: ['genotyping-calls-stats', variantSetFilter],
    queryFn: () => apiClient.getCallsStatistics(variantSetFilter !== 'all' ? variantSetFilter : undefined),
  })

  const calls: GenotypeCall[] = callsData?.result?.data || []
  const callSets = callSetsData?.result?.data || []
  const variantSets = variantSetsData?.result?.data || []
  const stats = statsData?.result || { total: 0, heterozygous: 0, homozygousAlt: 0, avgQuality: 0 }

  const filteredCalls = search
    ? calls.filter(c => c.variantName?.toLowerCase().includes(search.toLowerCase()) || c.callSetName?.toLowerCase().includes(search.toLowerCase()))
    : calls

  const getGenotypeColor = (gt: string) => {
    if (gt === '0/0') return 'bg-green-100 text-green-800'
    if (gt === '1/1') return 'bg-red-100 text-red-800'
    if (gt === './.') return 'bg-gray-100 text-gray-500'
    return 'bg-yellow-100 text-yellow-800'
  }

  const handleExport = () => {
    const header = '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n'
    const rows = filteredCalls.map(c => `.\t.\t${c.variantName}\t.\t.\t${c.genotypeQuality}\tPASS\t.\tGT:DP\t${c.genotypeValue}:${c.readDepth}`).join('\n')
    const blob = new Blob([header + rows], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'genotype_calls.vcf'
    a.click()
    toast.success('Exported to VCF format')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genotype Calls</h1>
          <p className="text-muted-foreground mt-1">Sample genotypes at variant positions</p>
        </div>
        <Button variant="outline" onClick={handleExport}>📥 Export VCF</Button>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1" />
            <Select value={variantSetFilter} onValueChange={setVariantSetFilter}>
              <SelectTrigger className="w-[200px]"><SelectValue placeholder="Variant Set" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Variant Sets</SelectItem>
                {variantSets.map((vs: any) => <SelectItem key={vs.variantSetDbId} value={vs.variantSetDbId}>{vs.variantSetName}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={sampleFilter} onValueChange={setSampleFilter}>
              <SelectTrigger className="w-[180px]"><SelectValue placeholder="Sample" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Samples</SelectItem>
                {callSets.slice(0, 20).map((s: any) => <SelectItem key={s.callSetDbId} value={s.callSetDbId}>{s.callSetName}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.total?.toLocaleString()}</div><p className="text-sm text-muted-foreground">Total Calls</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.heterozygous?.toLocaleString()}</div><p className="text-sm text-muted-foreground">Heterozygous</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.homozygousAlt}</div><p className="text-sm text-muted-foreground">Homozygous Alt</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.avgQuality}</div><p className="text-sm text-muted-foreground">Avg Quality</p></CardContent></Card>
      </div>

      {isLoading ? <Skeleton className="h-64 w-full" /> : (
        <Card>
          <CardHeader><CardTitle>Genotype Calls</CardTitle><CardDescription>{filteredCalls.length} calls</CardDescription></CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow><TableHead>Sample</TableHead><TableHead>Variant</TableHead><TableHead>Genotype</TableHead><TableHead>Quality</TableHead><TableHead>Depth</TableHead></TableRow></TableHeader>
              <TableBody>
                {filteredCalls.slice(0, 100).map((call, i) => (
                  <TableRow key={`${call.callSetDbId}-${call.variantDbId}-${i}`}>
                    <TableCell className="font-medium">{call.callSetName}</TableCell>
                    <TableCell>{call.variantName}</TableCell>
                    <TableCell><Badge className={getGenotypeColor(call.genotypeValue)}>{call.genotypeValue}</Badge></TableCell>
                    <TableCell>{call.genotypeQuality}</TableCell>
                    <TableCell>{call.readDepth}x</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {filteredCalls.length > 100 && <p className="text-sm text-muted-foreground mt-4 text-center">Showing first 100 of {filteredCalls.length}</p>}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

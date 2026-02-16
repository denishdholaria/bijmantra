/**
 * Genotype Calls Page - BrAPI v2.1 Genotyping Module
 * Connected to /brapi/v2/calls endpoint
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
import { Alert, AlertDescription } from '@/components/ui/alert'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import { AlertCircle, Download, RefreshCw } from 'lucide-react'
import { useWorkspace } from '@/hooks/useWorkspace'
import { Navigate } from 'react-router-dom'

export function Calls() {
  const { activeWorkspaceId } = useWorkspace()
  const [search, setSearch] = useState('')

  // Strict Workspace Isolation
  if (!activeWorkspaceId) {
    return <Navigate to="/gateway" replace />
  }
  const [callSetFilter, setCallSetFilter] = useState<string>('all')
  const [variantSetFilter, setVariantSetFilter] = useState<string>('all')

  const { data: callsData, isLoading, error, refetch } = useQuery({
    queryKey: ['brapi-calls', callSetFilter, variantSetFilter],
    queryFn: () => apiClient.genotypingService.getCalls({
      callSetDbId: callSetFilter !== 'all' ? callSetFilter : undefined,
      variantSetDbId: variantSetFilter !== 'all' ? variantSetFilter : undefined,
      pageSize: 500,
    }),
  })

  const { data: callSetsData } = useQuery({
    queryKey: ['brapi-callsets-filter'],
    queryFn: () => apiClient.genotypingService.getCallSets({ pageSize: 100 }),
  })

  const { data: variantSetsData } = useQuery({
    queryKey: ['brapi-variantsets-filter'],
    queryFn: () => apiClient.genotypingService.getVariantSets({ pageSize: 100 }),
  })

  const calls = callsData?.result?.data || []
  const callSets = callSetsData?.result?.data || []
  const variantSets = variantSetsData?.result?.data || []
  const totalCount = callsData?.metadata?.pagination?.totalCount || calls.length

  const filteredCalls = search
    ? calls.filter((c: any) => 
        c.variantName?.toLowerCase().includes(search.toLowerCase()) || 
        c.callSetName?.toLowerCase().includes(search.toLowerCase())
      )
    : calls

  // Calculate stats
  const stats = {
    total: totalCount,
    heterozygous: calls.filter((c: any) => {
      const gt = c.genotype?.values || []
      return gt.length === 2 && gt[0] !== gt[1]
    }).length,
    homozygousRef: calls.filter((c: any) => {
      const gt = c.genotype?.values || []
      return gt.length === 2 && gt[0] === gt[1] && gt[0] === gt[0]
    }).length,
    missing: calls.filter((c: any) => {
      const gt = c.genotype?.values || []
      return gt.includes('.') || gt.length === 0
    }).length,
  }

  const getGenotypeDisplay = (call: any) => {
    const gt = call.genotype?.values || []
    if (gt.length === 0) return './.'
    return gt.join('/')
  }

  const getGenotypeColor = (call: any) => {
    const gt = call.genotype?.values || []
    if (gt.includes('.') || gt.length === 0) return 'bg-gray-100 text-gray-500'
    if (gt.length === 2 && gt[0] === gt[1]) return 'bg-green-100 text-green-800'
    return 'bg-yellow-100 text-yellow-800'
  }

  const handleExport = () => {
    const header = '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n'
    const rows = filteredCalls.map((c: any) => {
      const gt = getGenotypeDisplay(c)
      return `.\t.\t${c.variantName || c.variantDbId}\t.\t.\t30\tPASS\t.\tGT\t${gt}`
    }).join('\n')
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
          <p className="text-muted-foreground mt-1">BrAPI v2.1 - Sample genotypes at variant positions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />Export VCF
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center gap-2">
            Failed to load calls. {error instanceof Error ? error.message : 'Please try again.'}
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input 
              placeholder="Search by variant or sample..." 
              value={search} 
              onChange={(e) => setSearch(e.target.value)} 
              className="flex-1" 
            />
            <Select value={variantSetFilter} onValueChange={setVariantSetFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Variant Set" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Variant Sets</SelectItem>
                {variantSets.map((vs: any) => (
                  <SelectItem key={vs.variantSetDbId} value={vs.variantSetDbId}>
                    {vs.variantSetName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={callSetFilter} onValueChange={setCallSetFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Sample" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Samples</SelectItem>
                {callSets.slice(0, 20).map((s: any) => (
                  <SelectItem key={s.callSetDbId} value={s.callSetDbId}>
                    {s.callSetName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">Total Calls</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-yellow-600">{stats.heterozygous.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">Heterozygous</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">{stats.homozygousRef}</div>
            <p className="text-sm text-muted-foreground">Homozygous</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-gray-500">{stats.missing}</div>
            <p className="text-sm text-muted-foreground">Missing</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Genotype Calls</CardTitle>
            <CardDescription>{filteredCalls.length} calls displayed</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sample</TableHead>
                  <TableHead>Variant</TableHead>
                  <TableHead>Genotype</TableHead>
                  <TableHead>Phase Set</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCalls.slice(0, 100).map((call: any, i: number) => (
                  <TableRow key={`${call.callSetDbId}-${call.variantDbId}-${i}`}>
                    <TableCell className="font-medium">{call.callSetName || call.callSetDbId}</TableCell>
                    <TableCell>{call.variantName || call.variantDbId}</TableCell>
                    <TableCell>
                      <Badge className={getGenotypeColor(call)}>
                        {getGenotypeDisplay(call)}
                      </Badge>
                    </TableCell>
                    <TableCell>{call.phaseSet || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {filteredCalls.length > 100 && (
              <p className="text-sm text-muted-foreground mt-4 text-center">
                Showing first 100 of {filteredCalls.length} calls
              </p>
            )}
            {filteredCalls.length === 0 && (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No genotype calls found. Try adjusting your filters.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Calls

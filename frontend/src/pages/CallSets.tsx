/**
 * Call Sets Page - BrAPI v2.1 Genotyping Module
 * Connected to /brapi/v2/callsets endpoint
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiClient } from '@/lib/api-client'
import { AlertCircle, RefreshCw, Grid3X3, Dna } from 'lucide-react'

export function CallSets() {
  const [search, setSearch] = useState('')
  const [variantSetFilter, setVariantSetFilter] = useState<string>('all')

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['brapi-callsets', variantSetFilter],
    queryFn: () => apiClient.genotypingService.getCallSets({
      variantSetDbId: variantSetFilter !== 'all' ? variantSetFilter : undefined,
      pageSize: 100,
    }),
  })

  const { data: variantSetsData } = useQuery({
    queryKey: ['brapi-variantsets-for-filter'],
    queryFn: () => apiClient.genotypingService.getVariantSets({ pageSize: 100 }),
  })

  const { data: summaryData } = useQuery({
    queryKey: ['brapi-genotyping-summary'],
    queryFn: () => apiClient.genotypingService.getGenotypingSummary(),
  })

  const callSets = data?.result?.data || []
  const variantSets = variantSetsData?.result?.data || []
  const summary: { variantSets?: number; callsStatistics?: { heterozygosityRate?: number } } = summaryData?.result || {}
  const totalCount = data?.metadata?.pagination?.totalCount || callSets.length

  const filteredCallSets = search
    ? callSets.filter((cs: any) => cs.callSetName?.toLowerCase().includes(search.toLowerCase()))
    : callSets

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Call Sets</h1>
          <p className="text-muted-foreground mt-1">BrAPI v2.1 - Sample-level genotype data containers</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button variant="outline" asChild>
            <Link to="/allelematrix"><Grid3X3 className="h-4 w-4 mr-2" />View Matrix</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/calls"><Dna className="h-4 w-4 mr-2" />View Calls</Link>
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center gap-2">
            Failed to load call sets. {error instanceof Error ? error.message : 'Please try again.'}
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
              placeholder="Search call sets..." 
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
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{totalCount}</div>
            <p className="text-sm text-muted-foreground">Call Sets</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">
              {new Set(filteredCallSets.map((cs: any) => cs.sampleDbId)).size}
            </div>
            <p className="text-sm text-muted-foreground">Unique Samples</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{summary.variantSets || variantSets.length}</div>
            <p className="text-sm text-muted-foreground">Variant Sets</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{summary.callsStatistics?.heterozygosityRate || 35}%</div>
            <p className="text-sm text-muted-foreground">Heterozygosity</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Call Sets</CardTitle>
            <CardDescription>{filteredCallSets.length} call sets</CardDescription>
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
                {filteredCallSets.slice(0, 50).map((cs: any) => (
                  <TableRow key={cs.callSetDbId}>
                    <TableCell className="font-medium">{cs.callSetName}</TableCell>
                    <TableCell>
                      <Link to={`/samples/${cs.sampleDbId}`} className="text-primary hover:underline">
                        {cs.sampleDbId}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1 flex-wrap">
                        {cs.variantSetDbIds?.map((vsId: string) => (
                          <Badge key={vsId} variant="outline" className="text-xs">{vsId}</Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>{cs.created || '-'}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost" asChild>
                        <Link to={`/calls?callSetDbId=${cs.callSetDbId}`}>View Calls</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {filteredCallSets.length > 50 && (
              <p className="text-sm text-muted-foreground mt-4 text-center">
                Showing first 50 of {filteredCallSets.length}
              </p>
            )}
            {filteredCallSets.length === 0 && (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No call sets found. Try adjusting your filters.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default CallSets

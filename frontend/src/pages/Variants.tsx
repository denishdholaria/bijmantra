/**
 * Variants Page - BrAPI v2.1 Genotyping Module
 * Connected to /brapi/v2/variants endpoint
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import { AlertCircle, RefreshCw, Plus, Download } from 'lucide-react'

export function Variants() {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [chrFilter, setChrFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['brapi-variants', typeFilter, chrFilter],
    queryFn: () => apiClient.getVariants({
      variantType: typeFilter !== 'all' ? typeFilter : undefined,
      referenceName: chrFilter !== 'all' ? chrFilter : undefined,
      pageSize: 1000,
    }),
  })

  const { data: refsData } = useQuery({
    queryKey: ['brapi-references-filter'],
    queryFn: () => apiClient.getReferences({ pageSize: 100 }),
  })

  const variants = data?.result?.data || []
  const references = refsData?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || variants.length

  // Get unique chromosomes from references
  const chromosomes = useMemo(() => {
    const chrSet = new Set<string>()
    references.forEach((r: any) => {
      if (r.referenceName) chrSet.add(r.referenceName)
    })
    variants.forEach((v: any) => {
      if (v.referenceName) chrSet.add(v.referenceName)
    })
    return Array.from(chrSet).sort()
  }, [references, variants])

  // Filter variants
  const filteredVariants = useMemo(() => {
    let filtered = variants
    if (search) {
      filtered = filtered.filter((v: any) => 
        v.variantName?.toLowerCase().includes(search.toLowerCase()) ||
        v.variantDbId?.toLowerCase().includes(search.toLowerCase())
      )
    }
    return filtered
  }, [variants, search])

  // Stats
  const stats = useMemo(() => ({
    total: totalCount,
    snps: variants.filter((v: any) => v.variantType === 'SNP').length,
    indels: variants.filter((v: any) => v.variantType === 'INDEL').length,
    chromosomes: chromosomes.length,
  }), [variants, chromosomes, totalCount])

  const getVariantTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      SNP: 'bg-blue-100 text-blue-800',
      INDEL: 'bg-orange-100 text-orange-800',
      MNP: 'bg-purple-100 text-purple-800',
      SV: 'bg-red-100 text-red-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const handleExport = () => {
    const header = 'variantDbId,variantName,variantType,referenceName,start,end,referenceBases,alternateBases\n'
    const rows = filteredVariants.map((v: any) => 
      `${v.variantDbId},${v.variantName},${v.variantType},${v.referenceName},${v.start},${v.end},${v.referenceBases},${v.alternateBases?.join(';')}`
    ).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'variants.csv'
    a.click()
    toast.success('Exported variants to CSV')
  }

  const handleCreate = () => {
    toast.success('Variant created (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Variants</h1>
          <p className="text-muted-foreground mt-1">BrAPI v2.1 - Genetic variants (SNPs, InDels, etc.)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />Add Variant</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Variant</DialogTitle>
                <DialogDescription>Register a new genetic variant</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Variant Name</Label>
                  <Input placeholder="SNP_Chr1_12345" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Variant Type</Label>
                    <Select defaultValue="SNP">
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="SNP">SNP</SelectItem>
                        <SelectItem value="INDEL">INDEL</SelectItem>
                        <SelectItem value="MNP">MNP</SelectItem>
                        <SelectItem value="SV">Structural Variant</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Chromosome</Label>
                    <Input placeholder="Chr1" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Start Position</Label>
                    <Input type="number" placeholder="12345" />
                  </div>
                  <div className="space-y-2">
                    <Label>End Position</Label>
                    <Input type="number" placeholder="12346" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Reference Bases</Label>
                    <Input placeholder="A" />
                  </div>
                  <div className="space-y-2">
                    <Label>Alternate Bases</Label>
                    <Input placeholder="G" />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate}>Create Variant</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load variants from API. Using demo data.</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <Input 
                placeholder="Search variants..." 
                value={search} 
                onChange={(e) => setSearch(e.target.value)} 
              />
            </div>
            <div className="space-y-1">
              <Label className="text-sm">Type</Label>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[120px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="SNP">SNP</SelectItem>
                  <SelectItem value="INDEL">INDEL</SelectItem>
                  <SelectItem value="MNP">MNP</SelectItem>
                  <SelectItem value="SV">SV</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-sm">Chromosome</Label>
              <Select value={chrFilter} onValueChange={setChrFilter}>
                <SelectTrigger className="w-[120px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  {chromosomes.map((chr: string) => (
                    <SelectItem key={chr} value={chr}>{chr}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">Total Variants</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-blue-600">{stats.snps.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">SNPs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-orange-600">{stats.indels.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">InDels</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.chromosomes}</div>
            <p className="text-sm text-muted-foreground">Chromosomes</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Variant List</CardTitle>
            <CardDescription>
              Showing {filteredVariants.length.toLocaleString()} variants
              {(typeFilter !== 'all' || chrFilter !== 'all' || search) && 
                ` (filtered from ${variants.length.toLocaleString()})`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Variant Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Chromosome</TableHead>
                  <TableHead className="text-right">Position</TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredVariants.slice(0, 100).map((v: any) => (
                  <TableRow key={v.variantDbId}>
                    <TableCell>
                      <Link 
                        to={`/variants/${v.variantDbId}`}
                        className="font-semibold hover:text-primary hover:underline"
                      >
                        {v.variantName || v.variantDbId}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge className={getVariantTypeBadge(v.variantType)}>
                        {v.variantType}
                      </Badge>
                    </TableCell>
                    <TableCell>{v.referenceName}</TableCell>
                    <TableCell className="text-right font-mono">
                      {v.start?.toLocaleString()}-{v.end?.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
                        {v.referenceBases} → {v.alternateBases?.join(', ')}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost" asChild>
                        <Link to={`/calls?variantDbId=${v.variantDbId}`}>View Calls</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {filteredVariants.length > 100 && (
              <p className="text-sm text-muted-foreground mt-4 text-center">
                Showing first 100 of {filteredVariants.length.toLocaleString()} variants
              </p>
            )}
            {filteredVariants.length === 0 && (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No variants found. Try adjusting your filters.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Variants

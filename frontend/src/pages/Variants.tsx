/**
 * Variants Page - BrAPI Genotyping Module
 * Genetic variants (SNPs, InDels, etc.) with virtual scrolling for large datasets
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
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { VirtualDataGrid, Column } from '@/components/VirtualDataGrid'
import { toast } from 'sonner'

interface Variant {
  variantDbId: string
  variantName: string
  variantType: string
  referenceName: string
  start: number
  end: number
  referenceBases: string
  alternateBases: string[]
  cipos?: number[]
  ciend?: number[]
  svlen?: number
  created?: string
  updated?: string
}

// Generate larger mock data for demo
function generateMockVariants(count: number): Variant[] {
  const types = ['SNP', 'INDEL', 'MNP', 'SV']
  const bases = ['A', 'T', 'G', 'C']
  
  return Array.from({ length: count }, (_, i) => {
    const chr = Math.floor(i / 500) + 1
    const pos = (i % 500) * 1000 + Math.floor(Math.random() * 1000)
    const type = types[Math.floor(Math.random() * types.length)]
    const refBase = bases[Math.floor(Math.random() * bases.length)]
    const altBase = bases.filter(b => b !== refBase)[Math.floor(Math.random() * 3)]
    
    return {
      variantDbId: `var${String(i + 1).padStart(6, '0')}`,
      variantName: `${type}_Chr${chr}_${pos}`,
      variantType: type,
      referenceName: `Chr${chr}`,
      start: pos,
      end: pos + (type === 'SNP' ? 1 : Math.floor(Math.random() * 10) + 1),
      referenceBases: type === 'INDEL' ? refBase.repeat(Math.floor(Math.random() * 4) + 1) : refBase,
      alternateBases: [altBase],
      created: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString().split('T')[0],
    }
  })
}

export function Variants() {
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [chrFilter, setChrFilter] = useState<string>('all')
  const [variantCount, setVariantCount] = useState<string>('1000')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  // Generate mock data
  const { data, isLoading } = useQuery({
    queryKey: ['variants', variantCount],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 300))
      return generateMockVariants(parseInt(variantCount))
    },
  })

  const allVariants = data || []
  
  // Filter variants
  const variants = useMemo(() => {
    let filtered = allVariants
    if (typeFilter !== 'all') {
      filtered = filtered.filter(v => v.variantType === typeFilter)
    }
    if (chrFilter !== 'all') {
      filtered = filtered.filter(v => v.referenceName === chrFilter)
    }
    return filtered
  }, [allVariants, typeFilter, chrFilter])

  const chromosomes = useMemo(() => 
    [...new Set(allVariants.map(v => v.referenceName))].sort((a, b) => {
      const numA = parseInt(a.replace('Chr', ''))
      const numB = parseInt(b.replace('Chr', ''))
      return numA - numB
    }),
    [allVariants]
  )

  const getVariantTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      SNP: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      INDEL: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      MNP: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      SV: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  // Define columns for VirtualDataGrid
  const columns: Column<Variant>[] = useMemo(() => [
    {
      id: 'variantName',
      header: 'Variant Name',
      accessor: (row) => (
        <Link 
          to={`/variants/${row.variantDbId}`}
          className="font-semibold hover:text-primary hover:underline"
        >
          {row.variantName}
        </Link>
      ),
      width: 200,
      sortable: true,
      sticky: true,
    },
    {
      id: 'variantType',
      header: 'Type',
      accessor: (row) => (
        <Badge className={getVariantTypeBadge(row.variantType)}>
          {row.variantType}
        </Badge>
      ),
      width: 100,
      sortable: true,
    },
    {
      id: 'referenceName',
      header: 'Chromosome',
      accessor: 'referenceName',
      width: 100,
      sortable: true,
    },
    {
      id: 'position',
      header: 'Position',
      accessor: (row) => `${row.start.toLocaleString()}-${row.end.toLocaleString()}`,
      width: 150,
      align: 'right',
      sortable: true,
    },
    {
      id: 'change',
      header: 'Change',
      accessor: (row) => (
        <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
          {row.referenceBases} → {row.alternateBases.join(', ')}
        </span>
      ),
      width: 150,
    },
    {
      id: 'created',
      header: 'Created',
      accessor: 'created',
      width: 120,
      sortable: true,
    },
  ], [])

  const handleCreate = () => {
    toast.success('Variant created (demo)')
    setIsCreateOpen(false)
  }

  // Stats
  const stats = useMemo(() => ({
    total: allVariants.length,
    snps: allVariants.filter(v => v.variantType === 'SNP').length,
    indels: allVariants.filter(v => v.variantType === 'INDEL').length,
    chromosomes: chromosomes.length,
  }), [allVariants, chromosomes])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Variants</h1>
          <p className="text-muted-foreground mt-1">Genetic variants with virtual scrolling for large datasets</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>🧬 Add Variant</Button>
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
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
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
                  <Input placeholder="G (comma-separated)" />
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

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-1">
              <Label className="text-sm">Dataset Size</Label>
              <Select value={variantCount} onValueChange={setVariantCount}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="1000">1,000</SelectItem>
                  <SelectItem value="5000">5,000</SelectItem>
                  <SelectItem value="10000">10,000</SelectItem>
                  <SelectItem value="50000">50,000</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-sm">Type</Label>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
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
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Chromosome" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  {chromosomes.map(chr => (
                    <SelectItem key={chr} value={chr}>{chr}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">Total Variants</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.snps.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">SNPs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.indels.toLocaleString()}</div>
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

      {/* Variants Table with Virtual Scrolling */}
      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Variant List</CardTitle>
            <CardDescription>
              Showing {variants.length.toLocaleString()} variants
              {(typeFilter !== 'all' || chrFilter !== 'all') && ` (filtered from ${allVariants.length.toLocaleString()})`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <VirtualDataGrid
              data={variants}
              columns={columns}
              rowHeight={48}
              maxHeight={500}
              searchable
              searchPlaceholder="Search variants..."
              exportable
              exportFilename="variants"
              selectable
              onSelectionChange={(selected) => {
                if (selected.length > 0) {
                  toast.info(`${selected.length} variants selected`)
                }
              }}
              getRowId={(row) => row.variantDbId}
              emptyMessage="No variants found matching your filters"
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Variants

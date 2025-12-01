/**
 * Variants Page - BrAPI Genotyping Module
 * Genetic variants (SNPs, InDels, etc.)
 */
import { useState } from 'react'
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

// Mock data for demo
const mockVariants: Variant[] = [
  {
    variantDbId: 'var001',
    variantName: 'SNP_Chr1_12345',
    variantType: 'SNP',
    referenceName: 'Chr1',
    start: 12345,
    end: 12346,
    referenceBases: 'A',
    alternateBases: ['G'],
    created: '2024-01-15',
  },
  {
    variantDbId: 'var002',
    variantName: 'SNP_Chr1_23456',
    variantType: 'SNP',
    referenceName: 'Chr1',
    start: 23456,
    end: 23457,
    referenceBases: 'C',
    alternateBases: ['T'],
    created: '2024-01-15',
  },
  {
    variantDbId: 'var003',
    variantName: 'INDEL_Chr2_5678',
    variantType: 'INDEL',
    referenceName: 'Chr2',
    start: 5678,
    end: 5682,
    referenceBases: 'ATCG',
    alternateBases: ['A'],
    created: '2024-01-16',
  },
  {
    variantDbId: 'var004',
    variantName: 'SNP_Chr3_78901',
    variantType: 'SNP',
    referenceName: 'Chr3',
    start: 78901,
    end: 78902,
    referenceBases: 'G',
    alternateBases: ['A', 'C'],
    created: '2024-01-17',
  },
  {
    variantDbId: 'var005',
    variantName: 'MNP_Chr4_11111',
    variantType: 'MNP',
    referenceName: 'Chr4',
    start: 11111,
    end: 11114,
    referenceBases: 'ATG',
    alternateBases: ['GCA'],
    created: '2024-01-18',
  },
]

export function Variants() {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [chrFilter, setChrFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  // Mock query - replace with actual API call
  const { data, isLoading } = useQuery({
    queryKey: ['variants', search, typeFilter, chrFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 500))
      let filtered = mockVariants
      if (search) {
        filtered = filtered.filter(v => 
          v.variantName.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (typeFilter !== 'all') {
        filtered = filtered.filter(v => v.variantType === typeFilter)
      }
      if (chrFilter !== 'all') {
        filtered = filtered.filter(v => v.referenceName === chrFilter)
      }
      return { result: { data: filtered } }
    },
  })

  const variants = data?.result?.data || []
  const chromosomes = [...new Set(mockVariants.map(v => v.referenceName))]

  const getVariantTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      SNP: 'bg-blue-100 text-blue-800',
      INDEL: 'bg-orange-100 text-orange-800',
      MNP: 'bg-purple-100 text-purple-800',
      SV: 'bg-red-100 text-red-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
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
          <p className="text-muted-foreground mt-1">Genetic variants (SNPs, InDels, MNPs)</p>
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
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search variants..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[150px]">
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
            <Select value={chrFilter} onValueChange={setChrFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Chromosome" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Chromosomes</SelectItem>
                {chromosomes.map(chr => (
                  <SelectItem key={chr} value={chr}>{chr}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockVariants.length}</div>
            <p className="text-sm text-muted-foreground">Total Variants</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockVariants.filter(v => v.variantType === 'SNP').length}</div>
            <p className="text-sm text-muted-foreground">SNPs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockVariants.filter(v => v.variantType === 'INDEL').length}</div>
            <p className="text-sm text-muted-foreground">InDels</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{chromosomes.length}</div>
            <p className="text-sm text-muted-foreground">Chromosomes</p>
          </CardContent>
        </Card>
      </div>

      {/* Variants List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : variants.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No variants found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {variants.map((variant) => (
            <Card key={variant.variantDbId} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Link 
                        to={`/variants/${variant.variantDbId}`}
                        className="font-semibold hover:text-primary"
                      >
                        {variant.variantName}
                      </Link>
                      <Badge className={getVariantTypeBadge(variant.variantType)}>
                        {variant.variantType}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {variant.referenceName}:{variant.start}-{variant.end}
                    </p>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="font-mono bg-muted px-2 py-0.5 rounded">
                        {variant.referenceBases} → {variant.alternateBases.join(', ')}
                      </span>
                    </div>
                  </div>
                  <div className="text-right text-sm text-muted-foreground">
                    {variant.created}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

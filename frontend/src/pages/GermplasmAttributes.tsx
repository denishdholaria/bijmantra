/**
 * Germplasm Attributes Page - BrAPI Germplasm Module
 * Manage germplasm attribute definitions
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'

interface GermplasmAttribute {
  attributeDbId: string
  attributeName: string
  attributeCategory: string
  attributeDescription?: string
  dataType: string
  commonCropName?: string
  values?: string[]
}

const mockAttributes: GermplasmAttribute[] = [
  { attributeDbId: 'attr001', attributeName: 'Grain Color', attributeCategory: 'Morphological', attributeDescription: 'Color of mature grain', dataType: 'Categorical', commonCropName: 'Rice', values: ['White', 'Brown', 'Red', 'Black'] },
  { attributeDbId: 'attr002', attributeName: 'Plant Height Class', attributeCategory: 'Morphological', attributeDescription: 'Height classification', dataType: 'Categorical', commonCropName: 'Rice', values: ['Dwarf', 'Semi-dwarf', 'Intermediate', 'Tall'] },
  { attributeDbId: 'attr003', attributeName: 'Maturity Days', attributeCategory: 'Agronomic', attributeDescription: 'Days to maturity', dataType: 'Numerical', commonCropName: 'Rice' },
  { attributeDbId: 'attr004', attributeName: 'Disease Resistance', attributeCategory: 'Biotic Stress', attributeDescription: 'Resistance to major diseases', dataType: 'Categorical', values: ['Susceptible', 'Moderately Resistant', 'Resistant', 'Highly Resistant'] },
  { attributeDbId: 'attr005', attributeName: 'Drought Tolerance', attributeCategory: 'Abiotic Stress', attributeDescription: 'Tolerance to water stress', dataType: 'Scale', values: ['1', '2', '3', '4', '5'] },
  { attributeDbId: 'attr006', attributeName: 'Protein Content', attributeCategory: 'Quality', attributeDescription: 'Grain protein percentage', dataType: 'Numerical' },
]

export function GermplasmAttributes() {
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['germplasmAttributes', search, categoryFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockAttributes
      if (search) {
        filtered = filtered.filter(a => 
          a.attributeName.toLowerCase().includes(search.toLowerCase()) ||
          a.attributeDescription?.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (categoryFilter !== 'all') {
        filtered = filtered.filter(a => a.attributeCategory === categoryFilter)
      }
      return { result: { data: filtered } }
    },
  })

  const attributes = data?.result?.data || []
  const categories = [...new Set(mockAttributes.map(a => a.attributeCategory))]

  const getDataTypeBadge = (dataType: string) => {
    const colors: Record<string, string> = {
      Categorical: 'bg-blue-100 text-blue-800',
      Numerical: 'bg-green-100 text-green-800',
      Scale: 'bg-purple-100 text-purple-800',
      Text: 'bg-gray-100 text-gray-800',
    }
    return colors[dataType] || 'bg-gray-100 text-gray-800'
  }

  const handleCreate = () => {
    toast.success('Attribute created (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Germplasm Attributes</h1>
          <p className="text-muted-foreground mt-1">Define and manage germplasm characteristics</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>➕ New Attribute</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Attribute</DialogTitle>
              <DialogDescription>Define a new germplasm attribute</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Attribute Name</Label>
                <Input placeholder="Grain Color" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(cat => (
                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Data Type</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Categorical">Categorical</SelectItem>
                      <SelectItem value="Numerical">Numerical</SelectItem>
                      <SelectItem value="Scale">Scale</SelectItem>
                      <SelectItem value="Text">Text</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input placeholder="Attribute description..." />
              </div>
              <div className="space-y-2">
                <Label>Valid Values (comma-separated, for categorical)</Label>
                <Input placeholder="White, Brown, Red, Black" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search attributes..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map(cat => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockAttributes.length}</div>
            <p className="text-sm text-muted-foreground">Total Attributes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{categories.length}</div>
            <p className="text-sm text-muted-foreground">Categories</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockAttributes.filter(a => a.dataType === 'Categorical').length}</div>
            <p className="text-sm text-muted-foreground">Categorical</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockAttributes.filter(a => a.dataType === 'Numerical').length}</div>
            <p className="text-sm text-muted-foreground">Numerical</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Attributes</CardTitle>
            <CardDescription>{attributes.length} attributes found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Attribute Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Data Type</TableHead>
                  <TableHead>Valid Values</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {attributes.map((attr) => (
                  <TableRow key={attr.attributeDbId}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{attr.attributeName}</p>
                        {attr.attributeDescription && (
                          <p className="text-xs text-muted-foreground">{attr.attributeDescription}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{attr.attributeCategory}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getDataTypeBadge(attr.dataType)}>{attr.dataType}</Badge>
                    </TableCell>
                    <TableCell>
                      {attr.values ? (
                        <div className="flex flex-wrap gap-1">
                          {attr.values.slice(0, 3).map(v => (
                            <Badge key={v} variant="secondary" className="text-xs">{v}</Badge>
                          ))}
                          {attr.values.length > 3 && (
                            <Badge variant="secondary" className="text-xs">+{attr.values.length - 3}</Badge>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost">Edit</Button>
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

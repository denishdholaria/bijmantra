/**
 * Germplasm Attribute Values Page - BrAPI Germplasm Module
 * Manage attribute values for germplasm entries
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

interface AttributeValue {
  attributeValueDbId: string
  germplasmDbId: string
  germplasmName: string
  attributeDbId: string
  attributeName: string
  value: string
  determinedDate?: string
}

const mockAttributeValues: AttributeValue[] = [
  { attributeValueDbId: 'av001', germplasmDbId: 'g001', germplasmName: 'IR64', attributeDbId: 'attr001', attributeName: 'Grain Color', value: 'White', determinedDate: '2024-01-15' },
  { attributeValueDbId: 'av002', germplasmDbId: 'g001', germplasmName: 'IR64', attributeDbId: 'attr002', attributeName: 'Plant Height Class', value: 'Semi-dwarf', determinedDate: '2024-01-15' },
  { attributeValueDbId: 'av003', germplasmDbId: 'g001', germplasmName: 'IR64', attributeDbId: 'attr003', attributeName: 'Maturity Days', value: '115', determinedDate: '2024-01-15' },
  { attributeValueDbId: 'av004', germplasmDbId: 'g002', germplasmName: 'Nipponbare', attributeDbId: 'attr001', attributeName: 'Grain Color', value: 'White', determinedDate: '2024-01-10' },
  { attributeValueDbId: 'av005', germplasmDbId: 'g002', germplasmName: 'Nipponbare', attributeDbId: 'attr002', attributeName: 'Plant Height Class', value: 'Intermediate', determinedDate: '2024-01-10' },
  { attributeValueDbId: 'av006', germplasmDbId: 'g003', germplasmName: 'Kasalath', attributeDbId: 'attr001', attributeName: 'Grain Color', value: 'Brown', determinedDate: '2024-01-12' },
  { attributeValueDbId: 'av007', germplasmDbId: 'g003', germplasmName: 'Kasalath', attributeDbId: 'attr004', attributeName: 'Disease Resistance', value: 'Resistant', determinedDate: '2024-01-12' },
]

export function GermplasmAttributeValues() {
  const [search, setSearch] = useState('')
  const [germplasmFilter, setGermplasmFilter] = useState<string>('all')
  const [attributeFilter, setAttributeFilter] = useState<string>('all')
  const [isAddOpen, setIsAddOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['attributeValues', search, germplasmFilter, attributeFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockAttributeValues
      if (search) {
        filtered = filtered.filter(av => 
          av.germplasmName.toLowerCase().includes(search.toLowerCase()) ||
          av.attributeName.toLowerCase().includes(search.toLowerCase()) ||
          av.value.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (germplasmFilter !== 'all') {
        filtered = filtered.filter(av => av.germplasmDbId === germplasmFilter)
      }
      if (attributeFilter !== 'all') {
        filtered = filtered.filter(av => av.attributeDbId === attributeFilter)
      }
      return filtered
    },
  })

  const values = data || []
  const germplasm = [...new Map(mockAttributeValues.map(av => [av.germplasmDbId, { id: av.germplasmDbId, name: av.germplasmName }])).values()]
  const attributes = [...new Map(mockAttributeValues.map(av => [av.attributeDbId, { id: av.attributeDbId, name: av.attributeName }])).values()]

  const handleAdd = () => {
    toast.success('Attribute value added (demo)')
    setIsAddOpen(false)
  }

  const handleEdit = (id: string) => {
    toast.success('Edit attribute value (demo)')
  }

  const handleDelete = (id: string) => {
    toast.success('Attribute value deleted (demo)')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Attribute Values</h1>
          <p className="text-muted-foreground mt-1">Germplasm characteristic values</p>
        </div>
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button>➕ Add Value</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Attribute Value</DialogTitle>
              <DialogDescription>Assign an attribute value to a germplasm</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Germplasm</Label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select germplasm..." />
                  </SelectTrigger>
                  <SelectContent>
                    {germplasm.map(g => (
                      <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Attribute</Label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select attribute..." />
                  </SelectTrigger>
                  <SelectContent>
                    {attributes.map(a => (
                      <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Value</Label>
                <Input placeholder="Enter value..." />
              </div>
              <div className="space-y-2">
                <Label>Determined Date</Label>
                <Input type="date" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsAddOpen(false)}>Cancel</Button>
              <Button onClick={handleAdd}>Add Value</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search values..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={germplasmFilter} onValueChange={setGermplasmFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Germplasm" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Germplasm</SelectItem>
                {germplasm.map(g => (
                  <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={attributeFilter} onValueChange={setAttributeFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Attribute" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Attributes</SelectItem>
                {attributes.map(a => (
                  <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockAttributeValues.length}</div>
            <p className="text-sm text-muted-foreground">Total Values</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{germplasm.length}</div>
            <p className="text-sm text-muted-foreground">Germplasm</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{attributes.length}</div>
            <p className="text-sm text-muted-foreground">Attributes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{(mockAttributeValues.length / germplasm.length).toFixed(1)}</div>
            <p className="text-sm text-muted-foreground">Avg per Entry</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Attribute Values</CardTitle>
            <CardDescription>{values.length} values found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Germplasm</TableHead>
                  <TableHead>Attribute</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {values.map((av) => (
                  <TableRow key={av.attributeValueDbId}>
                    <TableCell className="font-medium">{av.germplasmName}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{av.attributeName}</Badge>
                    </TableCell>
                    <TableCell>{av.value}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{av.determinedDate || '-'}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost" onClick={() => handleEdit(av.attributeValueDbId)}>Edit</Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDelete(av.attributeValueDbId)}>Delete</Button>
                      </div>
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

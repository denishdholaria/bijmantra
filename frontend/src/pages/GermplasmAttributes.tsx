/**
 * Germplasm Attributes Page
 * Manage germplasm attributes and categories - Connected to BrAPI API
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Loader2, Plus, Search, Tags, Database } from 'lucide-react'
import { germplasmAttributesAPI, GermplasmAttribute } from '@/lib/api-client'
import { toast } from 'sonner'

export function GermplasmAttributes() {
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newAttribute, setNewAttribute] = useState({
    attributeName: '',
    attributeCategory: '',
    attributeDescription: '',
    dataType: 'Text',
    commonCropName: '',
  })

  const queryClient = useQueryClient()

  // Fetch attributes from BrAPI
  const { data: attributesData, isLoading, error } = useQuery({
    queryKey: ['germplasm-attributes', categoryFilter],
    queryFn: async () => {
      const params: { attributeCategory?: string; pageSize?: number } = { pageSize: 100 }
      if (categoryFilter !== 'all') params.attributeCategory = categoryFilter
      const response = await germplasmAttributesAPI.getAttributes(params)
      return response.result.data
    },
  })

  // Fetch categories from BrAPI
  const { data: categoriesData } = useQuery({
    queryKey: ['attribute-categories'],
    queryFn: async () => {
      const response = await germplasmAttributesAPI.getCategories()
      return response.result.data
    },
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newAttribute) => germplasmAttributesAPI.createAttribute(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['germplasm-attributes'] })
      setIsCreateOpen(false)
      setNewAttribute({ attributeName: '', attributeCategory: '', attributeDescription: '', dataType: 'Text', commonCropName: '' })
      toast.success('Attribute created')
    },
    onError: () => toast.error('Failed to create attribute'),
  })

  const attributes: GermplasmAttribute[] = attributesData || []
  const categories: string[] = categoriesData || []
  
  // Filter by search
  const filteredAttributes = attributes.filter(a => 
    a.attributeName.toLowerCase().includes(search.toLowerCase()) ||
    a.attributeDescription?.toLowerCase().includes(search.toLowerCase())
  )

  // Group by category
  const groupedAttributes = filteredAttributes.reduce((acc, attr) => {
    const cat = attr.attributeCategory || 'Uncategorized'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(attr)
    return acc
  }, {} as Record<string, GermplasmAttribute[]>)

  const getDataTypeBadge = (dataType?: string) => {
    switch (dataType?.toLowerCase()) {
      case 'categorical': return <Badge variant="outline" className="bg-purple-50">Categorical</Badge>
      case 'numerical': return <Badge variant="outline" className="bg-blue-50">Numerical</Badge>
      case 'scale': return <Badge variant="outline" className="bg-green-50">Scale</Badge>
      case 'text': return <Badge variant="outline" className="bg-gray-50">Text</Badge>
      default: return <Badge variant="secondary">{dataType || 'Unknown'}</Badge>
    }
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">
        Failed to load attributes. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Germplasm Attributes</h1>
          <p className="text-muted-foreground mt-1">Manage attribute definitions for germplasm characterization</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Attribute
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Attribute</DialogTitle>
              <DialogDescription>Define a new germplasm attribute</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Attribute Name</Label>
                <Input
                  value={newAttribute.attributeName}
                  onChange={(e) => setNewAttribute({ ...newAttribute, attributeName: e.target.value })}
                  placeholder="e.g., Grain Color"
                />
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <Select
                  value={newAttribute.attributeCategory}
                  onValueChange={(v) => setNewAttribute({ ...newAttribute, attributeCategory: v })}
                >
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
                <Label>Description</Label>
                <Textarea
                  value={newAttribute.attributeDescription}
                  onChange={(e) => setNewAttribute({ ...newAttribute, attributeDescription: e.target.value })}
                  placeholder="Describe the attribute..."
                />
              </div>
              <div className="space-y-2">
                <Label>Data Type</Label>
                <Select
                  value={newAttribute.dataType}
                  onValueChange={(v) => setNewAttribute({ ...newAttribute, dataType: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Text">Text</SelectItem>
                    <SelectItem value="Numerical">Numerical</SelectItem>
                    <SelectItem value="Categorical">Categorical</SelectItem>
                    <SelectItem value="Scale">Scale</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Crop</Label>
                <Select
                  value={newAttribute.commonCropName}
                  onValueChange={(v) => setNewAttribute({ ...newAttribute, commonCropName: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select crop (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Rice">Rice</SelectItem>
                    <SelectItem value="Wheat">Wheat</SelectItem>
                    <SelectItem value="Maize">Maize</SelectItem>
                    <SelectItem value="Soybean">Soybean</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button 
                onClick={() => createMutation.mutate(newAttribute)}
                disabled={!newAttribute.attributeName || createMutation.isPending}
              >
                {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <Database className="w-6 h-6 mx-auto mb-2 text-blue-500" />
            <p className="text-2xl font-bold">{attributes.length}</p>
            <p className="text-xs text-muted-foreground">Total Attributes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <Tags className="w-6 h-6 mx-auto mb-2 text-purple-500" />
            <p className="text-2xl font-bold">{Object.keys(groupedAttributes).length}</p>
            <p className="text-xs text-muted-foreground">Categories</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-green-600">
              {attributes.filter(a => a.dataType === 'Numerical').length}
            </p>
            <p className="text-xs text-muted-foreground">Numerical</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-purple-600">
              {attributes.filter(a => a.dataType === 'Categorical').length}
            </p>
            <p className="text-xs text-muted-foreground">Categorical</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search attributes..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Categories" />
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

      {/* Attributes by Category */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : filteredAttributes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Database className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No attributes found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedAttributes).map(([category, attrs]) => (
            <Card key={category}>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Tags className="w-5 h-5" />
                  {category}
                  <Badge variant="secondary" className="ml-2">{attrs.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {attrs.map((attr) => (
                    <div 
                      key={attr.attributeDbId}
                      className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium">{attr.attributeName}</h4>
                        {getDataTypeBadge(attr.dataType)}
                      </div>
                      <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                        {attr.attributeDescription || 'No description'}
                      </p>
                      {attr.values && attr.values.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {attr.values.slice(0, 4).map((v, i) => (
                            <Badge key={i} variant="outline" className="text-xs">{v}</Badge>
                          ))}
                          {attr.values.length > 4 && (
                            <Badge variant="outline" className="text-xs">+{attr.values.length - 4}</Badge>
                          )}
                        </div>
                      )}
                      {attr.commonCropName && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Crop: {attr.commonCropName}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Genome Maps Page - BrAPI Genotyping Module
 * Genetic and physical maps
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
import { toast } from 'sonner'

interface GenomeMap {
  mapDbId: string
  mapName: string
  mapType: string
  commonCropName: string
  unit: string
  linkageGroupCount: number
  markerCount: number
  publishedDate?: string
  scientificName?: string
}

const mockMaps: GenomeMap[] = [
  { mapDbId: 'map001', mapName: 'Rice_GBS_Map_2024', mapType: 'genetic', commonCropName: 'Rice', unit: 'cM', linkageGroupCount: 12, markerCount: 5420, publishedDate: '2024-01-15', scientificName: 'Oryza sativa' },
  { mapDbId: 'map002', mapName: 'Rice_Physical_Map', mapType: 'physical', commonCropName: 'Rice', unit: 'bp', linkageGroupCount: 12, markerCount: 45000, publishedDate: '2023-06-01', scientificName: 'Oryza sativa' },
  { mapDbId: 'map003', mapName: 'Wheat_Consensus_Map', mapType: 'genetic', commonCropName: 'Wheat', unit: 'cM', linkageGroupCount: 21, markerCount: 12500, publishedDate: '2024-02-20', scientificName: 'Triticum aestivum' },
  { mapDbId: 'map004', mapName: 'Maize_NAM_Map', mapType: 'genetic', commonCropName: 'Maize', unit: 'cM', linkageGroupCount: 10, markerCount: 8200, publishedDate: '2023-11-10', scientificName: 'Zea mays' },
]

export function GenomeMaps() {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['genomeMaps', search, typeFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockMaps
      if (search) {
        filtered = filtered.filter(m => 
          m.mapName.toLowerCase().includes(search.toLowerCase()) ||
          m.commonCropName.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (typeFilter !== 'all') {
        filtered = filtered.filter(m => m.mapType === typeFilter)
      }
      return { result: { data: filtered } }
    },
  })

  const maps = data?.result?.data || []

  const handleCreate = () => {
    toast.success('Genome map created (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genome Maps</h1>
          <p className="text-muted-foreground mt-1">Genetic and physical maps</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>🗺️ New Map</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Genome Map</DialogTitle>
              <DialogDescription>Register a new genetic or physical map</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Map Name</Label>
                <Input placeholder="Rice_GBS_Map_2024" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Map Type</Label>
                  <Select defaultValue="genetic">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="genetic">Genetic</SelectItem>
                      <SelectItem value="physical">Physical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Unit</Label>
                  <Select defaultValue="cM">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cM">cM (centiMorgan)</SelectItem>
                      <SelectItem value="bp">bp (base pairs)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Crop</Label>
                <Input placeholder="Rice" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Create Map</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search maps..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Map Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="genetic">Genetic</SelectItem>
                <SelectItem value="physical">Physical</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockMaps.length}</div>
            <p className="text-sm text-muted-foreground">Total Maps</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockMaps.filter(m => m.mapType === 'genetic').length}</div>
            <p className="text-sm text-muted-foreground">Genetic Maps</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{(mockMaps.reduce((a, m) => a + m.markerCount, 0) / 1000).toFixed(1)}K</div>
            <p className="text-sm text-muted-foreground">Total Markers</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{new Set(mockMaps.map(m => m.commonCropName)).size}</div>
            <p className="text-sm text-muted-foreground">Crops</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map(i => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      ) : maps.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No genome maps found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {maps.map((map) => (
            <Card key={map.mapDbId} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{map.mapName}</CardTitle>
                    <CardDescription>
                      <em>{map.scientificName}</em> ({map.commonCropName})
                    </CardDescription>
                  </div>
                  <Badge variant={map.mapType === 'genetic' ? 'default' : 'secondary'}>
                    {map.mapType}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Linkage Groups</p>
                    <p className="font-semibold">{map.linkageGroupCount}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Markers</p>
                    <p className="font-semibold">{map.markerCount.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Unit</p>
                    <p className="font-semibold">{map.unit}</p>
                  </div>
                </div>
                {map.publishedDate && (
                  <p className="text-xs text-muted-foreground">Published: {map.publishedDate}</p>
                )}
                <div className="flex gap-2 mt-4">
                  <Button size="sm" variant="outline">View Markers</Button>
                  <Button size="sm" variant="outline">Export</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

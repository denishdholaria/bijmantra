/**
 * Genome Maps Page - BrAPI Genotyping Module
 * Genetic and physical maps
 * Connected to BrAPI v2.1 /brapi/v2/maps endpoint
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface GenomeMap {
  mapDbId: string
  mapName: string
  mapPUI?: string
  type: string
  commonCropName: string
  unit: string
  linkageGroupCount: number
  markerCount: number
  publishedDate?: string
  scientificName?: string
  comments?: string
  documentationURL?: string
}

export function GenomeMaps() {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newMap, setNewMap] = useState({
    mapName: '',
    type: 'Genetic',
    unit: 'cM',
    commonCropName: '',
  })
  const queryClient = useQueryClient()

  // Fetch maps from BrAPI endpoint
  const { data, isLoading, error } = useQuery({
    queryKey: ['brapi-maps', search, typeFilter],
    queryFn: () => apiClient.getMaps({
      commonCropName: search || undefined,
      type: typeFilter !== 'all' ? typeFilter : undefined,
      pageSize: 100,
    }),
  })

  const maps: GenomeMap[] = data?.result?.data || []
  const totalMarkers = maps.reduce((a, m) => a + (m.markerCount || 0), 0)
  const geneticMaps = maps.filter(m => m.type === 'Genetic').length
  const uniqueCrops = new Set(maps.map(m => m.commonCropName)).size

  const handleCreate = () => {
    toast.success('Genome map created (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genome Maps</h1>
          <p className="text-muted-foreground mt-1">Genetic and physical maps (BrAPI v2.1)</p>
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
                <Input 
                  placeholder="Rice_GBS_Map_2024" 
                  value={newMap.mapName}
                  onChange={(e) => setNewMap({ ...newMap, mapName: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Map Type</Label>
                  <Select 
                    value={newMap.type}
                    onValueChange={(v) => setNewMap({ ...newMap, type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Genetic">Genetic</SelectItem>
                      <SelectItem value="Physical">Physical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Unit</Label>
                  <Select 
                    value={newMap.unit}
                    onValueChange={(v) => setNewMap({ ...newMap, unit: v })}
                  >
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
                <Input 
                  placeholder="Rice" 
                  value={newMap.commonCropName}
                  onChange={(e) => setNewMap({ ...newMap, commonCropName: e.target.value })}
                />
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
                placeholder="Search maps by crop..."
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
                <SelectItem value="Genetic">Genetic</SelectItem>
                <SelectItem value="Physical">Physical</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{maps.length}</div>
            <p className="text-sm text-muted-foreground">Total Maps</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{geneticMaps}</div>
            <p className="text-sm text-muted-foreground">Genetic Maps</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{(totalMarkers / 1000).toFixed(1)}K</div>
            <p className="text-sm text-muted-foreground">Total Markers</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{uniqueCrops}</div>
            <p className="text-sm text-muted-foreground">Crops</p>
          </CardContent>
        </Card>
      </div>

      {error ? (
        <Card>
          <CardContent className="py-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                <span>Failed to load genome maps. {(error as Error).message}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ['brapi-maps'] })}
                  className="ml-4"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      ) : isLoading ? (
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
                  <Badge variant={map.type === 'Genetic' ? 'default' : 'secondary'}>
                    {map.type}
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
                    <p className="font-semibold">{map.markerCount?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Unit</p>
                    <p className="font-semibold">{map.unit}</p>
                  </div>
                </div>
                {map.comments && (
                  <p className="text-xs text-muted-foreground mb-2">{map.comments}</p>
                )}
                {map.publishedDate && (
                  <p className="text-xs text-muted-foreground">Published: {map.publishedDate}</p>
                )}
                <div className="flex gap-2 mt-4">
                  <Button size="sm" variant="outline" onClick={() => toast.info(`View markers for ${map.mapName}`)}>View Markers</Button>
                  <Button size="sm" variant="outline" onClick={() => toast.success('Export started')}>Export</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

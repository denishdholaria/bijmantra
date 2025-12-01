/**
 * Plates Page - BrAPI Genotyping Module
 * Sample plate management for genotyping
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

interface Plate {
  plateDbId: string
  plateName: string
  plateFormat: string
  sampleCount: number
  sampleType: string
  studyDbId?: string
  clientPlateBarcode?: string
  created?: string
}

const mockPlates: Plate[] = [
  { plateDbId: 'plate001', plateName: 'RICE_GBS_PLATE_001', plateFormat: '96-well', sampleCount: 94, sampleType: 'DNA', studyDbId: 'study001', clientPlateBarcode: 'BC001234', created: '2024-01-10' },
  { plateDbId: 'plate002', plateName: 'RICE_GBS_PLATE_002', plateFormat: '96-well', sampleCount: 96, sampleType: 'DNA', studyDbId: 'study001', clientPlateBarcode: 'BC001235', created: '2024-01-10' },
  { plateDbId: 'plate003', plateName: 'WHEAT_SNP_PLATE_001', plateFormat: '384-well', sampleCount: 380, sampleType: 'DNA', studyDbId: 'study002', clientPlateBarcode: 'BC002001', created: '2024-01-25' },
  { plateDbId: 'plate004', plateName: 'MAIZE_WGS_PLATE_001', plateFormat: '96-well', sampleCount: 48, sampleType: 'DNA', studyDbId: 'study003', clientPlateBarcode: 'BC003001', created: '2024-02-15' },
]

export function Plates() {
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [selectedPlate, setSelectedPlate] = useState<Plate | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['plates', search],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockPlates
      if (search) {
        filtered = filtered.filter(p => 
          p.plateName.toLowerCase().includes(search.toLowerCase()) ||
          p.clientPlateBarcode?.toLowerCase().includes(search.toLowerCase())
        )
      }
      return { result: { data: filtered } }
    },
  })

  const plates = data?.result?.data || []

  const handleCreate = () => {
    toast.success('Plate created (demo)')
    setIsCreateOpen(false)
  }

  // Generate plate visualization
  const PlateVisualization = ({ plate }: { plate: Plate }) => {
    const rows = plate.plateFormat === '384-well' ? 16 : 8
    const cols = plate.plateFormat === '384-well' ? 24 : 12
    const rowLabels = 'ABCDEFGHIJKLMNOP'.slice(0, rows).split('')
    
    return (
      <div className="overflow-x-auto">
        <div className="inline-block">
          <div className="flex">
            <div className="w-6"></div>
            {Array.from({ length: cols }, (_, i) => (
              <div key={i} className="w-6 text-center text-xs text-muted-foreground">
                {i + 1}
              </div>
            ))}
          </div>
          {rowLabels.map((row, rowIdx) => (
            <div key={row} className="flex">
              <div className="w-6 text-xs text-muted-foreground flex items-center justify-center">
                {row}
              </div>
              {Array.from({ length: cols }, (_, colIdx) => {
                const wellIndex = rowIdx * cols + colIdx
                const hasSample = wellIndex < plate.sampleCount
                return (
                  <div
                    key={colIdx}
                    className={`w-5 h-5 m-0.5 rounded-full border ${
                      hasSample 
                        ? 'bg-green-500 border-green-600' 
                        : 'bg-gray-100 border-gray-200'
                    }`}
                    title={`${row}${String(colIdx + 1).padStart(2, '0')}`}
                  />
                )
              })}
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Sample Plates</h1>
          <p className="text-muted-foreground mt-1">Manage genotyping sample plates</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>🧫 New Plate</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Plate</DialogTitle>
              <DialogDescription>Register a new sample plate</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Plate Name</Label>
                <Input placeholder="RICE_GBS_PLATE_001" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Plate Format</Label>
                  <Select defaultValue="96-well">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="96-well">96-well</SelectItem>
                      <SelectItem value="384-well">384-well</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Sample Type</Label>
                  <Select defaultValue="DNA">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DNA">DNA</SelectItem>
                      <SelectItem value="RNA">RNA</SelectItem>
                      <SelectItem value="Tissue">Tissue</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Barcode</Label>
                <Input placeholder="BC001234" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Create Plate</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Input
            placeholder="Search plates by name or barcode..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-md"
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockPlates.length}</div>
            <p className="text-sm text-muted-foreground">Total Plates</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockPlates.reduce((a, p) => a + p.sampleCount, 0)}</div>
            <p className="text-sm text-muted-foreground">Total Samples</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockPlates.filter(p => p.plateFormat === '96-well').length}</div>
            <p className="text-sm text-muted-foreground">96-well Plates</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockPlates.filter(p => p.plateFormat === '384-well').length}</div>
            <p className="text-sm text-muted-foreground">384-well Plates</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map(i => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {plates.map((plate) => (
            <Card key={plate.plateDbId} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{plate.plateName}</CardTitle>
                    <CardDescription>{plate.clientPlateBarcode}</CardDescription>
                  </div>
                  <Badge>{plate.plateFormat}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Samples</p>
                    <p className="font-semibold">{plate.sampleCount}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Type</p>
                    <p className="font-semibold">{plate.sampleType}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Created</p>
                    <p className="font-semibold">{plate.created}</p>
                  </div>
                </div>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => setSelectedPlate(plate)}>
                      View Plate Layout
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>{plate.plateName}</DialogTitle>
                      <DialogDescription>
                        {plate.sampleCount} samples in {plate.plateFormat} format
                      </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                      <PlateVisualization plate={plate} />
                    </div>
                    <div className="flex gap-2 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full bg-green-500"></div>
                        <span>Sample present</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full bg-gray-100 border"></div>
                        <span>Empty well</span>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

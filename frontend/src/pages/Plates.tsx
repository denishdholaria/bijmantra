/**
 * Plates Page - BrAPI Genotyping Module
 * Sample plate management for genotyping
 * Connected to BrAPI v2.1 /brapi/v2/plates endpoint
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
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface Plate {
  plateDbId: string
  plateName: string
  plateFormat: string
  sampleType: string
  studyDbId?: string
  clientPlateBarcode?: string
  plateBarcode?: string
  samples?: Array<{ sampleDbId: string; well: string; row: string; column: number }>
  additionalInfo?: { submissionDate?: string }
}

export function Plates() {
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [selectedPlate, setSelectedPlate] = useState<Plate | null>(null)
  const [newPlate, setNewPlate] = useState({
    plateName: '',
    plateFormat: 'PLATE_96',
    sampleType: 'DNA',
    plateBarcode: '',
  })
  const queryClient = useQueryClient()

  // Fetch plates from BrAPI endpoint
  const { data, isLoading, error } = useQuery({
    queryKey: ['brapi-plates', search],
    queryFn: () => apiClient.getPlates({
      plateName: search || undefined,
      pageSize: 100,
    }),
  })

  // Create plate mutation
  const createMutation = useMutation({
    mutationFn: (plateData: typeof newPlate) => apiClient.createPlates([{
      plateName: plateData.plateName,
      plateFormat: plateData.plateFormat,
      sampleType: plateData.sampleType,
      plateBarcode: plateData.plateBarcode,
      samples: [],
    }]),
    onSuccess: () => {
      toast.success('Plate created successfully')
      setIsCreateOpen(false)
      setNewPlate({ plateName: '', plateFormat: 'PLATE_96', sampleType: 'DNA', plateBarcode: '' })
      queryClient.invalidateQueries({ queryKey: ['brapi-plates'] })
    },
    onError: () => toast.error('Failed to create plate'),
  })

  const plates: Plate[] = data?.result?.data || []
  const totalSamples = plates.reduce((a, p) => a + (p.samples?.length || 0), 0)
  const plate96Count = plates.filter(p => p.plateFormat === 'PLATE_96').length
  const plate384Count = plates.filter(p => p.plateFormat === 'PLATE_384').length

  const handleCreate = () => {
    if (!newPlate.plateName) {
      toast.error('Plate name is required')
      return
    }
    createMutation.mutate(newPlate)
  }

  // Generate plate visualization
  const PlateVisualization = ({ plate }: { plate: Plate }) => {
    const is384 = plate.plateFormat === 'PLATE_384' || plate.plateFormat === '384-well'
    const rows = is384 ? 16 : 8
    const cols = is384 ? 24 : 12
    const rowLabels = 'ABCDEFGHIJKLMNOP'.slice(0, rows).split('')
    const sampleCount = plate.samples?.length || 0
    
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
                const hasSample = wellIndex < sampleCount
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
          <p className="text-muted-foreground mt-1">Manage genotyping sample plates (BrAPI v2.1)</p>
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
                <Input 
                  placeholder="RICE_GBS_PLATE_001" 
                  value={newPlate.plateName}
                  onChange={(e) => setNewPlate({ ...newPlate, plateName: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Plate Format</Label>
                  <Select 
                    value={newPlate.plateFormat} 
                    onValueChange={(v) => setNewPlate({ ...newPlate, plateFormat: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PLATE_96">96-well</SelectItem>
                      <SelectItem value="PLATE_384">384-well</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Sample Type</Label>
                  <Select 
                    value={newPlate.sampleType}
                    onValueChange={(v) => setNewPlate({ ...newPlate, sampleType: v })}
                  >
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
                <Input 
                  placeholder="BC001234" 
                  value={newPlate.plateBarcode}
                  onChange={(e) => setNewPlate({ ...newPlate, plateBarcode: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Plate'}
              </Button>
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
            <div className="text-2xl font-bold">{plates.length}</div>
            <p className="text-sm text-muted-foreground">Total Plates</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{totalSamples}</div>
            <p className="text-sm text-muted-foreground">Total Samples</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{plate96Count}</div>
            <p className="text-sm text-muted-foreground">96-well Plates</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{plate384Count}</div>
            <p className="text-sm text-muted-foreground">384-well Plates</p>
          </CardContent>
        </Card>
      </div>

      {error ? (
        <Card><CardContent className="py-12 text-center"><p className="text-red-500">Error loading plates: {(error as Error).message}</p></CardContent></Card>
      ) : isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map(i => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      ) : plates.length === 0 ? (
        <Card><CardContent className="py-12 text-center"><p className="text-muted-foreground">No plates found</p></CardContent></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {plates.map((plate) => (
            <Card key={plate.plateDbId} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{plate.plateName}</CardTitle>
                    <CardDescription>{plate.plateBarcode || plate.clientPlateBarcode}</CardDescription>
                  </div>
                  <Badge>{plate.plateFormat === 'PLATE_384' ? '384-well' : '96-well'}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Samples</p>
                    <p className="font-semibold">{plate.samples?.length || 0}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Type</p>
                    <p className="font-semibold">{plate.sampleType}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Submitted</p>
                    <p className="font-semibold">{plate.additionalInfo?.submissionDate || 'N/A'}</p>
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
                        {plate.samples?.length || 0} samples in {plate.plateFormat === 'PLATE_384' ? '384-well' : '96-well'} format
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

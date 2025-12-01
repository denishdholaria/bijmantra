/**
 * Common Crop Names Page - BrAPI Core Module
 * Manage crop names used in the system
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
import { toast } from 'sonner'

interface CropName {
  commonCropName: string
  scientificName?: string
  germplasmCount: number
  programCount: number
  icon: string
}

const mockCrops: CropName[] = [
  { commonCropName: 'Rice', scientificName: 'Oryza sativa', germplasmCount: 1250, programCount: 3, icon: '🌾' },
  { commonCropName: 'Wheat', scientificName: 'Triticum aestivum', germplasmCount: 890, programCount: 2, icon: '🌾' },
  { commonCropName: 'Maize', scientificName: 'Zea mays', germplasmCount: 720, programCount: 2, icon: '🌽' },
  { commonCropName: 'Soybean', scientificName: 'Glycine max', germplasmCount: 450, programCount: 1, icon: '🫘' },
  { commonCropName: 'Tomato', scientificName: 'Solanum lycopersicum', germplasmCount: 320, programCount: 1, icon: '🍅' },
  { commonCropName: 'Potato', scientificName: 'Solanum tuberosum', germplasmCount: 280, programCount: 1, icon: '🥔' },
]

export function CommonCropNames() {
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['commonCropNames', search],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 300))
      let filtered = mockCrops
      if (search) {
        filtered = filtered.filter(c => 
          c.commonCropName.toLowerCase().includes(search.toLowerCase()) ||
          c.scientificName?.toLowerCase().includes(search.toLowerCase())
        )
      }
      return { result: { data: filtered } }
    },
  })

  const crops = data?.result?.data || []

  const handleCreate = () => {
    toast.success('Crop added (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Common Crop Names</h1>
          <p className="text-muted-foreground mt-1">Crops managed in the system</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>🌱 Add Crop</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Crop</DialogTitle>
              <DialogDescription>Register a new crop in the system</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Common Name</Label>
                <Input placeholder="Rice" />
              </div>
              <div className="space-y-2">
                <Label>Scientific Name</Label>
                <Input placeholder="Oryza sativa" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Add Crop</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Input
            placeholder="Search crops..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-md"
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockCrops.length}</div>
            <p className="text-sm text-muted-foreground">Crops</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockCrops.reduce((a, c) => a + c.germplasmCount, 0).toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">Total Germplasm</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockCrops.reduce((a, c) => a + c.programCount, 0)}</div>
            <p className="text-sm text-muted-foreground">Programs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{Math.round(mockCrops.reduce((a, c) => a + c.germplasmCount, 0) / mockCrops.length)}</div>
            <p className="text-sm text-muted-foreground">Avg per Crop</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
      ) : crops.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No crops found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {crops.map((crop) => (
            <Card key={crop.commonCropName} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="pt-6 text-center">
                <div className="text-4xl mb-2">{crop.icon}</div>
                <h3 className="font-semibold text-lg">{crop.commonCropName}</h3>
                {crop.scientificName && (
                  <p className="text-sm text-muted-foreground italic">{crop.scientificName}</p>
                )}
                <div className="flex justify-center gap-4 mt-4 text-sm">
                  <div>
                    <Badge variant="secondary">{crop.germplasmCount} germplasm</Badge>
                  </div>
                </div>
                <div className="mt-2">
                  <Badge variant="outline">{crop.programCount} programs</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

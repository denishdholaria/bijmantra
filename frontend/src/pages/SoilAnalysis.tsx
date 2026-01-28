/**
 * Soil Analysis Page
 * Track and analyze soil test results - connected to real API
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, Beaker, Leaf, RefreshCw } from 'lucide-react'

const optimalRanges = {
  ph: { min: 6.0, max: 7.0, unit: '', label: 'pH' },
  organic_matter: { min: 3.0, max: 5.0, unit: '%', label: 'OM' },
  nitrogen_ppm: { min: 40, max: 60, unit: 'ppm', label: 'N' },
  phosphorus_ppm: { min: 25, max: 50, unit: 'ppm', label: 'P' },
  potassium_ppm: { min: 150, max: 250, unit: 'ppm', label: 'K' },
}

export function SoilAnalysis() {
  const [showCreate, setShowCreate] = useState(false)
  const [selectedField, setSelectedField] = useState<string>('')
  const [newProfile, setNewProfile] = useState({
    field_id: '',
    depth_cm: 30,
    texture: 'loam',
    ph: 6.5,
    organic_matter: 3.0,
    nitrogen_ppm: 45,
    phosphorus_ppm: 30,
    potassium_ppm: 180,
  })
  const queryClient = useQueryClient()

  // Fetch fields for dropdown
  const { data: fieldsData } = useQuery({
    queryKey: ['fields'],
    queryFn: () => apiClient.fieldMapService.getFields(),
  })

  // Fetch soil profiles
  const { data: profiles, isLoading, error, refetch } = useQuery({
    queryKey: ['soil-profiles', selectedField],
    queryFn: () => apiClient.fieldEnvironmentService.getSoilProfiles(selectedField || undefined),
  })

  // Fetch soil textures
  const { data: texturesData } = useQuery({
    queryKey: ['soil-textures'],
    queryFn: () => apiClient.fieldEnvironmentService.getSoilTextures(),
  })

  const createMutation = useMutation({
    mutationFn: () => apiClient.fieldEnvironmentService.createSoilProfile(newProfile),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['soil-profiles'] })
      toast.success('Soil profile created!')
      setShowCreate(false)
      setNewProfile({
        field_id: '',
        depth_cm: 30,
        texture: 'loam',
        ph: 6.5,
        organic_matter: 3.0,
        nitrogen_ppm: 45,
        phosphorus_ppm: 30,
        potassium_ppm: 180,
      })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create profile'),
  })

  const fields = fieldsData || []
  const textures = texturesData?.soil_textures || [
    { value: 'sand', name: 'Sand' },
    { value: 'loamy_sand', name: 'Loamy Sand' },
    { value: 'sandy_loam', name: 'Sandy Loam' },
    { value: 'loam', name: 'Loam' },
    { value: 'silt_loam', name: 'Silt Loam' },
    { value: 'clay_loam', name: 'Clay Loam' },
    { value: 'clay', name: 'Clay' },
  ]

  const getValueStatus = (value: number, param: keyof typeof optimalRanges) => {
    const range = optimalRanges[param]
    if (value < range.min) return { status: 'low', color: 'text-red-600', bg: 'bg-red-50' }
    if (value > range.max) return { status: 'high', color: 'text-orange-600', bg: 'bg-orange-50' }
    return { status: 'optimal', color: 'text-green-600', bg: 'bg-green-50' }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Beaker className="h-8 w-8 text-primary" />
            Soil Analysis
          </h1>
          <p className="text-muted-foreground mt-1">Track and analyze soil test results</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedField || "__all__"} onValueChange={(v) => setSelectedField(v === "__all__" ? "" : v)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Fields" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">All Fields</SelectItem>
              {fields.map((field: any) => (
                <SelectItem key={field.id} value={field.id}>{field.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" aria-label="Refresh soil data" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Sample</Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>New Soil Sample</DialogTitle>
                <DialogDescription>Record a new soil analysis result</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Field</Label>
                  <Select value={newProfile.field_id} onValueChange={(v) => setNewProfile(p => ({ ...p, field_id: v }))}>
                    <SelectTrigger><SelectValue placeholder="Select field..." /></SelectTrigger>
                    <SelectContent>
                      {fields.map((field: any) => (
                        <SelectItem key={field.id} value={field.id}>{field.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Depth (cm)</Label>
                    <Input type="number" value={newProfile.depth_cm} onChange={(e) => setNewProfile(p => ({ ...p, depth_cm: Number(e.target.value) }))} />
                  </div>
                  <div className="space-y-2">
                    <Label>Texture</Label>
                    <Select value={newProfile.texture} onValueChange={(v) => setNewProfile(p => ({ ...p, texture: v }))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {textures.map((t: any) => (
                          <SelectItem key={t.value} value={t.value}>{t.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>pH</Label>
                    <Input type="number" step="0.1" value={newProfile.ph} onChange={(e) => setNewProfile(p => ({ ...p, ph: Number(e.target.value) }))} />
                  </div>
                  <div className="space-y-2">
                    <Label>Organic Matter (%)</Label>
                    <Input type="number" step="0.1" value={newProfile.organic_matter} onChange={(e) => setNewProfile(p => ({ ...p, organic_matter: Number(e.target.value) }))} />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>N (ppm)</Label>
                    <Input type="number" value={newProfile.nitrogen_ppm} onChange={(e) => setNewProfile(p => ({ ...p, nitrogen_ppm: Number(e.target.value) }))} />
                  </div>
                  <div className="space-y-2">
                    <Label>P (ppm)</Label>
                    <Input type="number" value={newProfile.phosphorus_ppm} onChange={(e) => setNewProfile(p => ({ ...p, phosphorus_ppm: Number(e.target.value) }))} />
                  </div>
                  <div className="space-y-2">
                    <Label>K (ppm)</Label>
                    <Input type="number" value={newProfile.potassium_ppm} onChange={(e) => setNewProfile(p => ({ ...p, potassium_ppm: Number(e.target.value) }))} />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button onClick={() => createMutation.mutate()} disabled={!newProfile.field_id || createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Sample'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center gap-2">
            Failed to load soil profiles. {error instanceof Error ? error.message : 'Please try again.'}
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Optimal Ranges Reference */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Leaf className="h-4 w-4" />
            Optimal Ranges
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div><span className="font-medium">pH:</span> 6.0-7.0</div>
            <div><span className="font-medium">OM:</span> 3-5%</div>
            <div><span className="font-medium">N:</span> 40-60 ppm</div>
            <div><span className="font-medium">P:</span> 25-50 ppm</div>
            <div><span className="font-medium">K:</span> 150-250 ppm</div>
          </div>
        </CardContent>
      </Card>

      {/* Samples */}
      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      ) : profiles && profiles.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {profiles.map((sample: any) => {
            const field = fields.find((f: any) => f.id === sample.field_id)
            return (
              <Card key={sample.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{field?.name || sample.field_id}</CardTitle>
                      <CardDescription>
                        {sample.id} • {formatDate(sample.sample_date)} • {sample.depth_cm}cm depth
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="capitalize">{sample.texture.replace('_', ' ')}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-5 gap-2">
                    {(['ph', 'organic_matter', 'nitrogen_ppm', 'phosphorus_ppm', 'potassium_ppm'] as const).map((param) => {
                      const value = sample[param]
                      const { status, color, bg } = getValueStatus(value, param)
                      const range = optimalRanges[param]
                      
                      return (
                        <div key={param} className={`text-center p-2 rounded-lg ${bg}`}>
                          <p className="text-xs text-muted-foreground">{range.label}</p>
                          <p className={`text-lg font-bold ${color}`}>
                            {typeof value === 'number' ? value.toFixed(param === 'ph' ? 1 : 0) : value}
                          </p>
                          <p className="text-xs text-muted-foreground">{range.unit}</p>
                          <Badge variant="outline" className={`text-xs mt-1 ${color}`}>{status}</Badge>
                        </div>
                      )
                    })}
                  </div>
                  {sample.cec && (
                    <p className="text-xs text-muted-foreground mt-3">CEC: {sample.cec} meq/100g</p>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <Beaker className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Soil Samples</h3>
            <p className="text-muted-foreground mb-4">Start by adding your first soil analysis</p>
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-2" />Add Sample
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

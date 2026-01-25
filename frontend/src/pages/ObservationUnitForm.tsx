/**
 * Observation Unit Form - Create/Edit observation units
 * BrAPI v2.1 Phenotyping Module
 */

import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, Link, useParams } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { useActiveWorkspace } from '@/store/workspaceStore'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'

interface UnitFormData {
  observationUnitName: string
  observationUnitType: string
  studyDbId: string
  germplasmDbId: string
  positionCoordinateX: string
  positionCoordinateY: string
  positionCoordinateXType: string
  positionCoordinateYType: string
  entryType: string
  plotNumber: string
  blockNumber: string
  replicate: string
}

export function ObservationUnitForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const activeWorkspace = useActiveWorkspace()
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<UnitFormData>()

  if (!activeWorkspace) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Select a Workspace</h2>
          <p className="text-muted-foreground">Please select a workspace to create observation units.</p>
        </div>
      </div>
    )
  }

  const { data: studiesData } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.getStudies(0, 200),
  })

  const { data: germplasmData } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.getGermplasm(0, 200),
  })

  const studies = studiesData?.result?.data || []
  const germplasm = germplasmData?.result?.data || []

  const mutation = useMutation({
    mutationFn: (data: UnitFormData) => {
      const payload = [{
        observationUnitName: data.observationUnitName,
        observationUnitType: data.observationUnitType || 'PLOT',
        studyDbId: data.studyDbId || undefined,
        germplasmDbId: data.germplasmDbId || undefined,
        observationUnitPosition: {
          positionCoordinateX: data.positionCoordinateX || undefined,
          positionCoordinateY: data.positionCoordinateY || undefined,
          positionCoordinateXType: data.positionCoordinateXType || 'GRID_COL',
          positionCoordinateYType: data.positionCoordinateYType || 'GRID_ROW',
          entryType: data.entryType || undefined,
        },
        observationUnitPUI: undefined,
      }]
      return apiClient.createObservationUnits(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['observationunits'] })
      toast.success('Observation unit created!')
      navigate('/observationunits')
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to create unit')
    },
  })

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild aria-label="Back to observation units"><Link to="/observationunits">←</Link></Button>
            <div>
              <CardTitle>{isEdit ? 'Edit Observation Unit' : 'Create Observation Unit'}</CardTitle>
              <CardDescription>Plot, plant, or sample (BrAPI v2.1)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="observationUnitName">Unit Name *</Label>
                <Input id="observationUnitName" {...register('observationUnitName', { required: 'Required' })} placeholder="e.g., PLOT-001" />
                {errors.observationUnitName && <p className="text-sm text-red-600">{errors.observationUnitName.message}</p>}
              </div>
              <div className="space-y-2">
                <Label>Unit Type</Label>
                <Select value={watch('observationUnitType')} onValueChange={(v) => setValue('observationUnitType', v)}>
                  <SelectTrigger><SelectValue placeholder="Select type..." /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PLOT">Plot</SelectItem>
                    <SelectItem value="PLANT">Plant</SelectItem>
                    <SelectItem value="SAMPLE">Sample</SelectItem>
                    <SelectItem value="POT">Pot</SelectItem>
                    <SelectItem value="BLOCK">Block</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Study *</Label>
                <Select value={watch('studyDbId')} onValueChange={(v) => setValue('studyDbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select study..." /></SelectTrigger>
                  <SelectContent>
                    {studies.map((s: any) => (
                      <SelectItem key={s.studyDbId} value={s.studyDbId}>{s.studyName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Germplasm</Label>
                <Select value={watch('germplasmDbId')} onValueChange={(v) => setValue('germplasmDbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select germplasm..." /></SelectTrigger>
                  <SelectContent>
                    {germplasm.map((g: any) => (
                      <SelectItem key={g.germplasmDbId} value={g.germplasmDbId}>{g.germplasmName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-semibold mb-3">Position</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="positionCoordinateX">X (Column)</Label>
                  <Input id="positionCoordinateX" {...register('positionCoordinateX')} placeholder="1" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="positionCoordinateY">Y (Row)</Label>
                  <Input id="positionCoordinateY" {...register('positionCoordinateY')} placeholder="1" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="plotNumber">Plot #</Label>
                  <Input id="plotNumber" {...register('plotNumber')} placeholder="1" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="blockNumber">Block #</Label>
                  <Input id="blockNumber" {...register('blockNumber')} placeholder="1" />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Entry Type</Label>
              <Select value={watch('entryType')} onValueChange={(v) => setValue('entryType', v)}>
                <SelectTrigger><SelectValue placeholder="Select entry type..." /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="TEST">Test Entry</SelectItem>
                  <SelectItem value="CHECK">Check Entry</SelectItem>
                  <SelectItem value="FILLER">Filler</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? '🌿 Creating...' : '🌿 Create Unit'}
              </Button>
              <Button variant="outline" asChild><Link to="/observationunits">Cancel</Link></Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

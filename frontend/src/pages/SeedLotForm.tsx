/**
 * Seed Lot Form - Create/Edit seed lot
 * BrAPI v2.1 Germplasm Module
 */

import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, Link, useParams } from 'react-router-dom'
import { useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'

interface SeedLotFormData {
  seedLotName: string
  seedLotDescription: string
  germplasmDbId: string
  locationDbId: string
  programDbId: string
  amount: string
  units: string
  storageLocation: string
  sourceCollection: string
  createdDate: string
}

export function SeedLotForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<SeedLotFormData>()

  const { data: germplasmData } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.germplasmService.getGermplasm(0, 200),
  })

  const { data: locationsData } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.locationService.getLocations(0, 200),
  })

  const { data: programsData } = useQuery({
    queryKey: ['programs'],
    queryFn: () => apiClient.programService.getPrograms(0, 200),
  })

  const { data: existingData } = useQuery({
    queryKey: ['seedlot', id],
    queryFn: () => apiClient.seedLotService.getSeedLot(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existingData?.result) {
      const lot = existingData.result
      reset({
        seedLotName: lot.seedLotName || '',
        seedLotDescription: lot.seedLotDescription || '',
        germplasmDbId: lot.germplasmDbId || '',
        locationDbId: lot.locationDbId || '',
        programDbId: lot.programDbId || '',
        amount: lot.amount?.toString() || '',
        units: lot.units || '',
        storageLocation: lot.storageLocation || '',
        sourceCollection: lot.sourceCollection || '',
        createdDate: lot.createdDate?.split('T')[0] || '',
      })
    }
  }, [existingData, reset])

  const germplasm = germplasmData?.result?.data || []
  const locations = locationsData?.result?.data || []
  const programs = programsData?.result?.data || []

  const mutation = useMutation({
    mutationFn: (data: SeedLotFormData) => {
      const payload = {
        seedLotName: data.seedLotName,
        seedLotDescription: data.seedLotDescription || undefined,
        germplasmDbId: data.germplasmDbId || undefined,
        locationDbId: data.locationDbId || undefined,
        programDbId: data.programDbId || undefined,
        amount: data.amount ? parseFloat(data.amount) : undefined,
        units: data.units || undefined,
        storageLocation: data.storageLocation || undefined,
        sourceCollection: data.sourceCollection || undefined,
        createdDate: data.createdDate || undefined,
      }
      return isEdit 
        ? apiClient.seedLotService.updateSeedLot(id!, payload)
        : apiClient.seedLotService.createSeedLot(payload)
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['seedlots'] })
      toast.success(isEdit ? 'Seed lot updated!' : 'Seed lot created!')
      const lotId = response.result?.seedLotDbId || id
      navigate(lotId ? `/seedlots/${lotId}` : '/seedlots')
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to save seed lot')
    },
  })

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild aria-label="Back to seed lots"><Link to="/seedlots">←</Link></Button>
            <div>
              <CardTitle>{isEdit ? 'Edit Seed Lot' : 'Create Seed Lot'}</CardTitle>
              <CardDescription>Manage seed inventory (BrAPI v2.1)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="seedLotName">Lot Name *</Label>
                <Input id="seedLotName" {...register('seedLotName', { required: 'Required' })} 
                  placeholder="e.g., LOT-2024-001" />
                {errors.seedLotName && <p className="text-sm text-red-600">{errors.seedLotName.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="createdDate">Created Date</Label>
                <Input id="createdDate" type="date" {...register('createdDate')} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="seedLotDescription">Description</Label>
              <Textarea id="seedLotDescription" {...register('seedLotDescription')} rows={2}
                placeholder="Notes about this seed lot..." />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Germplasm *</Label>
                <Select value={watch('germplasmDbId')} onValueChange={(v) => setValue('germplasmDbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select germplasm..." /></SelectTrigger>
                  <SelectContent>
                    {germplasm.map((g: any) => (
                      <SelectItem key={g.germplasmDbId} value={g.germplasmDbId}>{g.germplasmName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Program</Label>
                <Select value={watch('programDbId')} onValueChange={(v) => setValue('programDbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select program..." /></SelectTrigger>
                  <SelectContent>
                    {programs.map((p: any) => (
                      <SelectItem key={p.programDbId} value={p.programDbId}>{p.programName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="amount">Amount</Label>
                <Input id="amount" type="number" step="0.01" {...register('amount')} placeholder="1000" />
              </div>
              <div className="space-y-2">
                <Label>Units</Label>
                <Select value={watch('units')} onValueChange={(v) => setValue('units', v)}>
                  <SelectTrigger><SelectValue placeholder="Select units..." /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="seeds">Seeds</SelectItem>
                    <SelectItem value="g">Grams (g)</SelectItem>
                    <SelectItem value="kg">Kilograms (kg)</SelectItem>
                    <SelectItem value="packets">Packets</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Storage Location</Label>
                <Select value={watch('locationDbId')} onValueChange={(v) => setValue('locationDbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select location..." /></SelectTrigger>
                  <SelectContent>
                    {locations.map((l: any) => (
                      <SelectItem key={l.locationDbId} value={l.locationDbId}>{l.locationName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="storageLocation">Storage Details</Label>
                <Input id="storageLocation" {...register('storageLocation')} placeholder="e.g., Cold Room A, Shelf 3" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sourceCollection">Source Collection</Label>
                <Input id="sourceCollection" {...register('sourceCollection')} placeholder="e.g., Field harvest 2024" />
              </div>
            </div>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? '📦 Saving...' : isEdit ? '📦 Update Seed Lot' : '📦 Create Seed Lot'}
              </Button>
              <Button variant="outline" asChild><Link to="/seedlots">Cancel</Link></Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

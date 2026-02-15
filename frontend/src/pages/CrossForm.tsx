/**
 * Cross Form - Create/Edit breeding cross
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

interface CrossFormData {
  crossName: string
  crossType: string
  parent1DbId: string
  parent2DbId: string
  crossingProjectDbId: string
  plannedCrossDbId: string
  pollinationTimeStamp: string
  crossAttributes: string
}

export function CrossForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<CrossFormData>()

  const { data: germplasmData } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.germplasmService.getGermplasm(0, 200),
  })

  const { data: existingData } = useQuery({
    queryKey: ['cross', id],
    queryFn: () => apiClient.crossService.getCross(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existingData?.result) {
      const c = existingData.result
      reset({
        crossName: c.crossName || '',
        crossType: c.crossType || '',
        parent1DbId: c.parent1DbId || '',
        parent2DbId: c.parent2DbId || '',
        crossingProjectDbId: c.crossingProjectDbId || '',
        pollinationTimeStamp: c.pollinationTimeStamp?.split('T')[0] || '',
        crossAttributes: JSON.stringify(c.crossAttributes || {}, null, 2),
      })
    }
  }, [existingData, reset])

  const germplasm = germplasmData?.result?.data || []

  const mutation = useMutation({
    mutationFn: (data: CrossFormData) => {
      const payload = {
        crossName: data.crossName,
        crossType: data.crossType || undefined,
        parent1DbId: data.parent1DbId || undefined,
        parent2DbId: data.parent2DbId || undefined,
        crossingProjectDbId: data.crossingProjectDbId || undefined,
        pollinationTimeStamp: data.pollinationTimeStamp || undefined,
        crossAttributes: data.crossAttributes ? JSON.parse(data.crossAttributes) : undefined,
      }
      return isEdit ? apiClient.crossService.updateCross(id!, payload) : apiClient.crossService.createCross(payload)
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['crosses'] })
      toast.success(isEdit ? 'Cross updated!' : 'Cross created!')
      const crossId = response.result?.crossDbId || id
      navigate(crossId ? `/crosses/${crossId}` : '/crosses')
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to save cross')
    },
  })

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild aria-label="Back to crosses"><Link to="/crosses">←</Link></Button>
            <div>
              <CardTitle>{isEdit ? 'Edit Cross' : 'Create Cross'}</CardTitle>
              <CardDescription>Breeding cross (BrAPI v2.1)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="crossName">Cross Name *</Label>
                <Input id="crossName" {...register('crossName', { required: 'Required' })} placeholder="e.g., CROSS-2025-001" />
                {errors.crossName && <p className="text-sm text-red-600">{errors.crossName.message}</p>}
              </div>
              <div className="space-y-2">
                <Label>Cross Type</Label>
                <Select value={watch('crossType')} onValueChange={(v) => setValue('crossType', v)}>
                  <SelectTrigger><SelectValue placeholder="Select type..." /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BIPARENTAL">Biparental</SelectItem>
                    <SelectItem value="SELF">Self</SelectItem>
                    <SelectItem value="OPEN_POLLINATED">Open Pollinated</SelectItem>
                    <SelectItem value="BACKCROSS">Backcross</SelectItem>
                    <SelectItem value="DOUBLE_HAPLOID">Double Haploid</SelectItem>
                    <SelectItem value="POLYCROSS">Polycross</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Parent 1 (Female ♀) *</Label>
                <Select value={watch('parent1DbId')} onValueChange={(v) => setValue('parent1DbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select female parent..." /></SelectTrigger>
                  <SelectContent>
                    {germplasm.map((g: any) => (
                      <SelectItem key={g.germplasmDbId} value={g.germplasmDbId}>{g.germplasmName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Parent 2 (Male ♂)</Label>
                <Select value={watch('parent2DbId')} onValueChange={(v) => setValue('parent2DbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select male parent..." /></SelectTrigger>
                  <SelectContent>
                    {germplasm.map((g: any) => (
                      <SelectItem key={g.germplasmDbId} value={g.germplasmDbId}>{g.germplasmName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pollinationTimeStamp">Pollination Date</Label>
              <Input id="pollinationTimeStamp" type="date" {...register('pollinationTimeStamp')} />
            </div>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? '🧬 Saving...' : isEdit ? '🧬 Update Cross' : '🧬 Create Cross'}
              </Button>
              <Button variant="outline" asChild><Link to="/crosses">Cancel</Link></Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

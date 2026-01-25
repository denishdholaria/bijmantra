/**
 * Trait Edit Page - Wrapper for TraitForm in edit mode
 * BrAPI v2.1 Phenotyping Module
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'

interface VariableFormData {
  observationVariableName: string
  traitName: string
  traitDescription: string
  traitClass: string
  methodName: string
  methodDescription: string
  methodClass: string
  formula: string
  scaleName: string
  dataType: string
  validValueMin: string
  validValueMax: string
  decimalPlaces: string
  ontologyName: string
  ontologyDbId: string
}

export function TraitEdit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<VariableFormData>()

  const { data, isLoading } = useQuery({
    queryKey: ['variable', id],
    queryFn: () => apiClient.getObservationVariable(id!),
    enabled: !!id,
  })

  useEffect(() => {
    if (data?.result) {
      const v = data.result
      reset({
        observationVariableName: v.observationVariableName || '',
        traitName: v.trait?.traitName || '',
        traitDescription: v.trait?.traitDescription || '',
        traitClass: v.trait?.traitClass || '',
        methodName: v.method?.methodName || '',
        methodDescription: v.method?.methodDescription || '',
        methodClass: v.method?.methodClass || '',
        formula: v.method?.formula || '',
        scaleName: v.scale?.scaleName || '',
        dataType: v.scale?.dataType || '',
        validValueMin: v.scale?.validValues?.min?.toString() || '',
        validValueMax: v.scale?.validValues?.max?.toString() || '',
        decimalPlaces: v.scale?.decimalPlaces?.toString() || '',
        ontologyDbId: v.ontologyReference?.ontologyDbId || '',
        ontologyName: v.ontologyReference?.ontologyName || '',
      })
    }
  }, [data, reset])

  const mutation = useMutation({
    mutationFn: (formData: VariableFormData) => {
      const payload = {
        observationVariableName: formData.observationVariableName,
        trait: {
          traitName: formData.traitName,
          traitDescription: formData.traitDescription || undefined,
          traitClass: formData.traitClass || undefined,
        },
        method: {
          methodName: formData.methodName || formData.traitName + ' method',
          methodDescription: formData.methodDescription || undefined,
          methodClass: formData.methodClass || undefined,
          formula: formData.formula || undefined,
        },
        scale: {
          scaleName: formData.scaleName || 'Numeric',
          dataType: formData.dataType || 'Numerical',
          validValues: formData.validValueMin || formData.validValueMax ? {
            min: formData.validValueMin ? parseFloat(formData.validValueMin) : undefined,
            max: formData.validValueMax ? parseFloat(formData.validValueMax) : undefined,
          } : undefined,
          decimalPlaces: formData.decimalPlaces ? parseInt(formData.decimalPlaces) : undefined,
        },
        ontologyReference: formData.ontologyDbId ? {
          ontologyDbId: formData.ontologyDbId,
          ontologyName: formData.ontologyName || undefined,
        } : undefined,
      }
      return apiClient.updateObservationVariable(id!, payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['variables'] })
      queryClient.invalidateQueries({ queryKey: ['variable', id] })
      toast.success('Variable updated!')
      navigate(`/traits/${id}`)
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to update variable')
    },
  })

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild aria-label="Back to trait"><Link to={`/traits/${id}`}>←</Link></Button>
            <div>
              <CardTitle>Edit Observation Variable</CardTitle>
              <CardDescription>Update trait, method, and scale (BrAPI v2.1)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="observationVariableName">Variable Name *</Label>
              <Input id="observationVariableName" {...register('observationVariableName', { required: 'Required' })} />
              {errors.observationVariableName && <p className="text-sm text-red-600">{errors.observationVariableName.message}</p>}
            </div>

            <Tabs defaultValue="trait" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="trait">Trait</TabsTrigger>
                <TabsTrigger value="method">Method</TabsTrigger>
                <TabsTrigger value="scale">Scale</TabsTrigger>
                <TabsTrigger value="ontology">Ontology</TabsTrigger>
              </TabsList>

              <TabsContent value="trait" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="traitName">Trait Name *</Label>
                  <Input id="traitName" {...register('traitName', { required: 'Required' })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="traitDescription">Trait Description</Label>
                  <Textarea id="traitDescription" {...register('traitDescription')} rows={3} />
                </div>
                <div className="space-y-2">
                  <Label>Trait Class</Label>
                  <Select value={watch('traitClass')} onValueChange={(v) => setValue('traitClass', v)}>
                    <SelectTrigger><SelectValue placeholder="Select trait class" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Morphological">Morphological</SelectItem>
                      <SelectItem value="Phenological">Phenological</SelectItem>
                      <SelectItem value="Agronomic">Agronomic</SelectItem>
                      <SelectItem value="Physiological">Physiological</SelectItem>
                      <SelectItem value="Biochemical">Biochemical</SelectItem>
                      <SelectItem value="Quality">Quality</SelectItem>
                      <SelectItem value="Stress">Stress</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              <TabsContent value="method" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="methodName">Method Name</Label>
                  <Input id="methodName" {...register('methodName')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="methodDescription">Method Description</Label>
                  <Textarea id="methodDescription" {...register('methodDescription')} rows={3} />
                </div>
                <div className="space-y-2">
                  <Label>Method Class</Label>
                  <Select value={watch('methodClass')} onValueChange={(v) => setValue('methodClass', v)}>
                    <SelectTrigger><SelectValue placeholder="Select method class" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Measurement">Measurement</SelectItem>
                      <SelectItem value="Counting">Counting</SelectItem>
                      <SelectItem value="Estimation">Estimation</SelectItem>
                      <SelectItem value="Computation">Computation</SelectItem>
                      <SelectItem value="Observation">Observation</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="formula">Formula</Label>
                  <Input id="formula" {...register('formula')} />
                </div>
              </TabsContent>

              <TabsContent value="scale" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="scaleName">Scale Name</Label>
                    <Input id="scaleName" {...register('scaleName')} />
                  </div>
                  <div className="space-y-2">
                    <Label>Data Type</Label>
                    <Select value={watch('dataType')} onValueChange={(v) => setValue('dataType', v)}>
                      <SelectTrigger><SelectValue placeholder="Select data type" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Numerical">Numerical</SelectItem>
                        <SelectItem value="Ordinal">Ordinal</SelectItem>
                        <SelectItem value="Nominal">Nominal</SelectItem>
                        <SelectItem value="Date">Date</SelectItem>
                        <SelectItem value="Text">Text</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="validValueMin">Min Value</Label>
                    <Input id="validValueMin" type="number" step="any" {...register('validValueMin')} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="validValueMax">Max Value</Label>
                    <Input id="validValueMax" type="number" step="any" {...register('validValueMax')} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="decimalPlaces">Decimal Places</Label>
                    <Input id="decimalPlaces" type="number" {...register('decimalPlaces')} />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="ontology" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="ontologyDbId">Ontology Term ID</Label>
                    <Input id="ontologyDbId" {...register('ontologyDbId')} placeholder="e.g., CO_321:0000020" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ontologyName">Ontology Name</Label>
                    <Input id="ontologyName" {...register('ontologyName')} />
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? '📊 Saving...' : '📊 Update Variable'}
              </Button>
              <Button variant="outline" asChild><Link to={`/traits/${id}`}>Cancel</Link></Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

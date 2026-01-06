/**
 * Observation Variable Form - Create new trait/variable
 * BrAPI v2.1 Phenotyping Module
 */

import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

interface VariableFormData {
  observationVariableName: string
  // Trait
  traitName: string
  traitDescription: string
  traitClass: string
  // Method
  methodName: string
  methodDescription: string
  methodClass: string
  formula: string
  // Scale
  scaleName: string
  dataType: string
  validValueMin: string
  validValueMax: string
  decimalPlaces: string
  // Ontology
  ontologyName: string
  ontologyDbId: string
}

export function TraitForm() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<VariableFormData>()

  const mutation = useMutation({
    mutationFn: (data: VariableFormData) => {
      const payload = {
        observationVariableName: data.observationVariableName,
        trait: {
          traitName: data.traitName,
          traitDescription: data.traitDescription || undefined,
          traitClass: data.traitClass || undefined,
        },
        method: {
          methodName: data.methodName || data.traitName + ' method',
          methodDescription: data.methodDescription || undefined,
          methodClass: data.methodClass || undefined,
          formula: data.formula || undefined,
        },
        scale: {
          scaleName: data.scaleName || 'Numeric',
          dataType: data.dataType || 'Numerical',
          validValues: data.validValueMin || data.validValueMax ? {
            min: data.validValueMin ? parseFloat(data.validValueMin) : undefined,
            max: data.validValueMax ? parseFloat(data.validValueMax) : undefined,
          } : undefined,
          decimalPlaces: data.decimalPlaces ? parseInt(data.decimalPlaces) : undefined,
        },
        ontologyReference: data.ontologyDbId ? {
          ontologyDbId: data.ontologyDbId,
          ontologyName: data.ontologyName || undefined,
        } : undefined,
      }
      return apiClient.createObservationVariable([payload])
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['variables'] })
      toast.success('Observation variable created!')
      const id = response.result?.data?.[0]?.observationVariableDbId
      navigate(id ? `/traits/${id}` : '/traits')
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to create variable')
    },
  })

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild><Link to="/traits">←</Link></Button>
            <div>
              <CardTitle>Create Observation Variable</CardTitle>
              <CardDescription>Define a trait with measurement method and scale (BrAPI v2.1)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="observationVariableName">Variable Name *</Label>
              <Input id="observationVariableName" {...register('observationVariableName', { required: 'Required' })} 
                placeholder="e.g., Plant_Height_cm, Grain_Yield_kg_ha" />
              {errors.observationVariableName && <p className="text-sm text-red-600">{errors.observationVariableName.message}</p>}
              <p className="text-xs text-muted-foreground">MIAPPE: Variable ID - Format: trait_method_scale</p>
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
                  <Input id="traitName" {...register('traitName', { required: 'Required' })} placeholder="e.g., Plant Height" />
                  {errors.traitName && <p className="text-sm text-red-600">{errors.traitName.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="traitDescription">Trait Description</Label>
                  <Textarea id="traitDescription" {...register('traitDescription')} rows={3} 
                    placeholder="The height of the plant from ground to the tip of the main stem" />
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
                  <Input id="methodName" {...register('methodName')} placeholder="e.g., Ruler measurement" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="methodDescription">Method Description</Label>
                  <Textarea id="methodDescription" {...register('methodDescription')} rows={3} 
                    placeholder="Measure from soil surface to tip of main stem using a ruler" />
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
                  <Label htmlFor="formula">Formula (if computed)</Label>
                  <Input id="formula" {...register('formula')} placeholder="e.g., (a]b)/c" />
                </div>
              </TabsContent>

              <TabsContent value="scale" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="scaleName">Scale Name</Label>
                    <Input id="scaleName" {...register('scaleName')} placeholder="e.g., Centimeters" />
                  </div>
                  <div className="space-y-2">
                    <Label>Data Type</Label>
                    <Select value={watch('dataType')} onValueChange={(v) => setValue('dataType', v)}>
                      <SelectTrigger><SelectValue placeholder="Select data type" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Numerical">Numerical</SelectItem>
                        <SelectItem value="Ordinal">Ordinal</SelectItem>
                        <SelectItem value="Nominal">Nominal (Categorical)</SelectItem>
                        <SelectItem value="Date">Date</SelectItem>
                        <SelectItem value="Text">Text</SelectItem>
                        <SelectItem value="Duration">Duration</SelectItem>
                        <SelectItem value="Code">Code</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="validValueMin">Min Value</Label>
                    <Input id="validValueMin" type="number" step="any" {...register('validValueMin')} placeholder="0" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="validValueMax">Max Value</Label>
                    <Input id="validValueMax" type="number" step="any" {...register('validValueMax')} placeholder="300" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="decimalPlaces">Decimal Places</Label>
                    <Input id="decimalPlaces" type="number" {...register('decimalPlaces')} placeholder="2" />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="ontology" className="space-y-4 mt-4">
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    Link to Crop Ontology (CO) or other ontology for standardized trait definitions.
                    Browse ontologies at <a href="https://cropontology.org" target="_blank" rel="noopener" className="text-primary hover:underline">cropontology.org</a>
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="ontologyDbId">Ontology Term ID</Label>
                    <Input id="ontologyDbId" {...register('ontologyDbId')} placeholder="e.g., CO_321:0000020" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ontologyName">Ontology Name</Label>
                    <Input id="ontologyName" {...register('ontologyName')} placeholder="e.g., Crop Ontology for Rice" />
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? '📊 Creating...' : '📊 Create Variable'}
              </Button>
              <Button variant="outline" asChild><Link to="/traits">Cancel</Link></Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

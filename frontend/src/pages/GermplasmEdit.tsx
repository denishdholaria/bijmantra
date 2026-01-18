/**
 * Germplasm Edit Page
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'

interface GermplasmFormData {
  germplasmName: string
  accessionNumber: string
  germplasmPUI: string
  commonCropName: string
  genus: string
  species: string
  subtaxa: string
  biologicalStatusOfAccessionCode: string
  countryOfOriginCode: string
  instituteCode: string
  instituteName: string
  pedigree: string
  seedSource: string
  acquisitionDate: string
  defaultDisplayName: string
  documentationURL: string
}

export function GermplasmEdit() {
  const { germplasmDbId } = useParams<{ germplasmDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<GermplasmFormData>()

  const { data, isLoading } = useQuery({
    queryKey: ['germplasm', germplasmDbId],
    queryFn: () => apiClient.getGermplasmById(germplasmDbId!),
    enabled: !!germplasmDbId,
  })

  useEffect(() => {
    if (data?.result) {
      const g = data.result
      reset({
        germplasmName: g.germplasmName || '',
        accessionNumber: g.accessionNumber || '',
        germplasmPUI: g.germplasmPUI || '',
        commonCropName: g.commonCropName || '',
        genus: g.genus || '',
        species: g.species || '',
        subtaxa: g.subtaxa || '',
        biologicalStatusOfAccessionCode: g.biologicalStatusOfAccessionCode?.toString() || '',
        countryOfOriginCode: g.countryOfOriginCode || '',
        instituteCode: g.instituteCode || '',
        instituteName: g.instituteName || '',
        pedigree: g.pedigree || '',
        seedSource: g.seedSource || '',
        acquisitionDate: g.acquisitionDate?.split('T')[0] || '',
        defaultDisplayName: g.defaultDisplayName || '',
        documentationURL: g.documentationURL || '',
      })
    }
  }, [data, reset])

  const mutation = useMutation({
    mutationFn: (formData: GermplasmFormData) => {
      const payload = {
        germplasmName: formData.germplasmName,
        accessionNumber: formData.accessionNumber || undefined,
        germplasmPUI: formData.germplasmPUI || undefined,
        commonCropName: formData.commonCropName || undefined,
        genus: formData.genus || undefined,
        species: formData.species || undefined,
        subtaxa: formData.subtaxa || undefined,
        biologicalStatusOfAccessionCode: formData.biologicalStatusOfAccessionCode ? parseInt(formData.biologicalStatusOfAccessionCode) : undefined,
        countryOfOriginCode: formData.countryOfOriginCode || undefined,
        instituteCode: formData.instituteCode || undefined,
        instituteName: formData.instituteName || undefined,
        pedigree: formData.pedigree || undefined,
        seedSource: formData.seedSource || undefined,
        acquisitionDate: formData.acquisitionDate || undefined,
        defaultDisplayName: formData.defaultDisplayName || undefined,
        documentationURL: formData.documentationURL || undefined,
      }
      return apiClient.updateGermplasm(germplasmDbId!, payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['germplasm'] })
      toast.success('Germplasm updated!')
      navigate(`/germplasm/${germplasmDbId}`)
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to update')
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
            <Button variant="ghost" size="icon" asChild aria-label="Back to germplasm"><Link to={`/germplasm/${germplasmDbId}`}>←</Link></Button>
            <div>
              <CardTitle>Edit Germplasm</CardTitle>
              <CardDescription>Update germplasm entry (MCPD compliant)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-6">
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="taxonomy">Taxonomy</TabsTrigger>
                <TabsTrigger value="origin">Origin</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="germplasmName">Germplasm Name *</Label>
                    <Input id="germplasmName" {...register('germplasmName', { required: 'Required' })} />
                    {errors.germplasmName && <p className="text-sm text-red-600">{errors.germplasmName.message}</p>}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="accessionNumber">Accession Number</Label>
                    <Input id="accessionNumber" {...register('accessionNumber')} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="germplasmPUI">Germplasm PUI</Label>
                    <Input id="germplasmPUI" {...register('germplasmPUI')} placeholder="doi:10.xxx/xxx" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="commonCropName">Common Crop Name</Label>
                    <Input id="commonCropName" {...register('commonCropName')} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pedigree">Pedigree</Label>
                  <Textarea id="pedigree" {...register('pedigree')} rows={2} />
                </div>
              </TabsContent>

              <TabsContent value="taxonomy" className="space-y-4 mt-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="genus">Genus</Label>
                    <Input id="genus" {...register('genus')} className="italic" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="species">Species</Label>
                    <Input id="species" {...register('species')} className="italic" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="subtaxa">Subtaxa</Label>
                    <Input id="subtaxa" {...register('subtaxa')} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Biological Status (MCPD)</Label>
                  <Select value={watch('biologicalStatusOfAccessionCode')} onValueChange={(v) => setValue('biologicalStatusOfAccessionCode', v)}>
                    <SelectTrigger><SelectValue placeholder="Select status..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="100">100 - Wild</SelectItem>
                      <SelectItem value="200">200 - Weedy</SelectItem>
                      <SelectItem value="300">300 - Traditional cultivar</SelectItem>
                      <SelectItem value="400">400 - Breeding material</SelectItem>
                      <SelectItem value="500">500 - Advanced cultivar</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              <TabsContent value="origin" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="countryOfOriginCode">Country of Origin (ISO)</Label>
                    <Input id="countryOfOriginCode" {...register('countryOfOriginCode')} placeholder="e.g., USA, NLD" maxLength={3} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="instituteCode">Institute Code (FAO)</Label>
                    <Input id="instituteCode" {...register('instituteCode')} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="instituteName">Institute Name</Label>
                    <Input id="instituteName" {...register('instituteName')} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="acquisitionDate">Acquisition Date</Label>
                    <Input id="acquisitionDate" type="date" {...register('acquisitionDate')} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="seedSource">Seed Source</Label>
                  <Input id="seedSource" {...register('seedSource')} />
                </div>
              </TabsContent>
            </Tabs>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? '🌱 Saving...' : '🌱 Update Germplasm'}
              </Button>
              <Button variant="outline" asChild><Link to={`/germplasm/${germplasmDbId}`}>Cancel</Link></Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

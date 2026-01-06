/**
 * Germplasm Form - Create new germplasm entry
 * BrAPI v2.1 Compliant
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

interface GermplasmFormData {
  // Required fields per BrAPI v2.1
  germplasmName: string
  commonCropName: string
  germplasmPUI: string
  // Optional fields
  accessionNumber: string
  genus: string
  species: string
  subtaxa: string
  pedigree: string
  seedSource: string
  seedSourceDescription: string
  biologicalStatusOfAccessionCode: string
  countryOfOriginCode: string
  instituteCode: string
  instituteName: string
  acquisitionDate: string
  collection: string
  breedingMethodName: string
  defaultDisplayName: string
  documentationURL: string
}

export function GermplasmForm() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<GermplasmFormData>()

  const mutation = useMutation({
    mutationFn: (data: GermplasmFormData) => {
      // Build BrAPI compliant payload
      const payload = {
        germplasmName: data.germplasmName,
        commonCropName: data.commonCropName,
        germplasmPUI: data.germplasmPUI || `urn:bijmantra:germplasm:${Date.now()}`,
        accessionNumber: data.accessionNumber || undefined,
        genus: data.genus || undefined,
        species: data.species || undefined,
        subtaxa: data.subtaxa || undefined,
        pedigree: data.pedigree || undefined,
        seedSource: data.seedSource || undefined,
        seedSourceDescription: data.seedSourceDescription || undefined,
        biologicalStatusOfAccessionCode: data.biologicalStatusOfAccessionCode || undefined,
        countryOfOriginCode: data.countryOfOriginCode || undefined,
        instituteCode: data.instituteCode || undefined,
        instituteName: data.instituteName || undefined,
        acquisitionDate: data.acquisitionDate || undefined,
        collection: data.collection || undefined,
        breedingMethodName: data.breedingMethodName || undefined,
        defaultDisplayName: data.defaultDisplayName || data.germplasmName,
        documentationURL: data.documentationURL || undefined,
      }
      return apiClient.createGermplasm([payload])
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['germplasm'] })
      toast.success('Germplasm created successfully!')
      const id = response.result?.data?.[0]?.germplasmDbId
      navigate(id ? `/germplasm/${id}` : '/germplasm')
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to create germplasm')
    },
  })

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild>
              <Link to="/germplasm">←</Link>
            </Button>
            <div>
              <CardTitle>Add New Germplasm</CardTitle>
              <CardDescription>Register a new genetic material entry (BrAPI v2.1 compliant)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="taxonomy">Taxonomy</TabsTrigger>
                <TabsTrigger value="origin">Origin</TabsTrigger>
                <TabsTrigger value="breeding">Breeding</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="germplasmName">Germplasm Name *</Label>
                    <Input id="germplasmName" {...register('germplasmName', { required: 'Name is required' })} placeholder="e.g., IR64, Nipponbare" />
                    {errors.germplasmName && <p className="text-sm text-red-600">{errors.germplasmName.message}</p>}
                    <p className="text-xs text-muted-foreground">MCPD: ACCENAME - Primary name for this germplasm</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="commonCropName">Common Crop Name *</Label>
                    <Input id="commonCropName" {...register('commonCropName', { required: 'Crop name is required' })} placeholder="e.g., Rice, Wheat, Maize" />
                    {errors.commonCropName && <p className="text-sm text-red-600">{errors.commonCropName.message}</p>}
                    <p className="text-xs text-muted-foreground">MCPD: CROPNAME - Common name of the crop</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="accessionNumber">Accession Number</Label>
                    <Input id="accessionNumber" {...register('accessionNumber')} placeholder="e.g., IRGC 117265" />
                    <p className="text-xs text-muted-foreground">MCPD: ACCENUMB - Unique identifier within genebank</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="germplasmPUI">Permanent Unique Identifier (PUI)</Label>
                    <Input id="germplasmPUI" {...register('germplasmPUI')} placeholder="e.g., doi:10.18730/..." />
                    <p className="text-xs text-muted-foreground">MCPD: PUID - DOI or persistent identifier (auto-generated if empty)</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="defaultDisplayName">Display Name</Label>
                    <Input id="defaultDisplayName" {...register('defaultDisplayName')} placeholder="Human readable name" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="collection">Collection/Panel</Label>
                    <Input id="collection" {...register('collection')} placeholder="e.g., 3K Rice Genome Panel" />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="taxonomy" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="genus">Genus</Label>
                    <Input id="genus" {...register('genus')} placeholder="e.g., Oryza" className="italic" />
                    <p className="text-xs text-muted-foreground">MCPD: GENUS - Initial uppercase</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="species">Species</Label>
                    <Input id="species" {...register('species')} placeholder="e.g., sativa" className="italic" />
                    <p className="text-xs text-muted-foreground">MCPD: SPECIES - Lowercase</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="subtaxa">Subtaxa</Label>
                    <Input id="subtaxa" {...register('subtaxa')} placeholder="e.g., subsp. indica" />
                    <p className="text-xs text-muted-foreground">MCPD: SUBTAXA - Subspecies, variety, etc.</p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="origin" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="countryOfOriginCode">Country of Origin (ISO 3166-1)</Label>
                    <Input id="countryOfOriginCode" {...register('countryOfOriginCode')} placeholder="e.g., PHL, IND, USA" maxLength={3} />
                    <p className="text-xs text-muted-foreground">MCPD: ORIGCTY - 3-letter ISO code</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="acquisitionDate">Acquisition Date</Label>
                    <Input id="acquisitionDate" type="date" {...register('acquisitionDate')} />
                    <p className="text-xs text-muted-foreground">MCPD: ACQDATE - Date entered collection</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="instituteCode">Institute Code (FAO WIEWS)</Label>
                    <Input id="instituteCode" {...register('instituteCode')} placeholder="e.g., PHL001" />
                    <p className="text-xs text-muted-foreground">MCPD: INSTCODE - FAO WIEWS code</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="instituteName">Institute Name</Label>
                    <Input id="instituteName" {...register('instituteName')} placeholder="e.g., International Rice Research Institute" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="seedSource">Seed Source</Label>
                  <Input id="seedSource" {...register('seedSource')} placeholder="e.g., IRRI:IRGC 117265" />
                  <p className="text-xs text-muted-foreground">MIAPPE: Material source ID - Repository:Accession format</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="seedSourceDescription">Seed Source Description</Label>
                  <Textarea id="seedSourceDescription" {...register('seedSourceDescription')} rows={2} placeholder="Description of the material source..." />
                </div>
              </TabsContent>

              <TabsContent value="breeding" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Biological Status</Label>
                  <Select value={watch('biologicalStatusOfAccessionCode')} onValueChange={(v) => setValue('biologicalStatusOfAccessionCode', v)}>
                    <SelectTrigger><SelectValue placeholder="Select biological status (MCPD SAMPSTAT)" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="100">100 - Wild</SelectItem>
                      <SelectItem value="110">110 - Natural</SelectItem>
                      <SelectItem value="120">120 - Semi-natural/wild</SelectItem>
                      <SelectItem value="200">200 - Weedy</SelectItem>
                      <SelectItem value="300">300 - Traditional cultivar/landrace</SelectItem>
                      <SelectItem value="400">400 - Breeding/research material</SelectItem>
                      <SelectItem value="410">410 - Breeder's line</SelectItem>
                      <SelectItem value="411">411 - Synthetic population</SelectItem>
                      <SelectItem value="412">412 - Hybrid</SelectItem>
                      <SelectItem value="413">413 - Founder stock/base population</SelectItem>
                      <SelectItem value="414">414 - Inbred line (parent of hybrid)</SelectItem>
                      <SelectItem value="415">415 - Segregating population</SelectItem>
                      <SelectItem value="420">420 - Genetic stock</SelectItem>
                      <SelectItem value="500">500 - Advanced/improved cultivar</SelectItem>
                      <SelectItem value="600">600 - GMO</SelectItem>
                      <SelectItem value="999">999 - Other</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">MCPD: SAMPSTAT - Biological status of accession</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pedigree">Pedigree</Label>
                  <Textarea id="pedigree" {...register('pedigree')} rows={3} placeholder="e.g., IR8/TN1//IR20 or 'selection from Irene'" />
                  <p className="text-xs text-muted-foreground">MCPD: ANCEST - Cross name and selection history</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="breedingMethodName">Breeding Method</Label>
                  <Input id="breedingMethodName" {...register('breedingMethodName')} placeholder="e.g., Single seed descent, Backcross" />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="documentationURL">Documentation URL</Label>
                  <Input id="documentationURL" type="url" {...register('documentationURL')} placeholder="https://..." />
                </div>
              </TabsContent>
            </Tabs>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? '🌱 Creating...' : '🌱 Create Germplasm'}
              </Button>
              <Button variant="outline" asChild>
                <Link to="/germplasm">Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

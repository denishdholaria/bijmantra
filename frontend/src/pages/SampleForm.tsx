/**
 * Sample Form Page - BrAPI Genotyping Module
 * Create/Edit genotyping samples
 */
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

export function SampleForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEdit = Boolean(id)

  const [formData, setFormData] = useState({
    sampleName: '',
    sampleType: 'DNA',
    germplasmDbId: '',
    observationUnitDbId: '',
    plateDbId: '',
    plateIndex: '',
    concentration: '',
    volume: '',
    sampleDescription: '',
    tissueType: '',
    sampleTimestamp: new Date().toISOString().split('T')[0],
  })

  // Load existing sample for edit
  useQuery({
    queryKey: ['sample', id],
    queryFn: () => apiClient.sampleService.getSample(id!),
    enabled: isEdit,
    // @ts-ignore
    onSuccess: (data: any) => {
      const sample = data.result
      setFormData({
        sampleName: sample.sampleName || '',
        sampleType: sample.sampleType || 'DNA',
        germplasmDbId: sample.germplasmDbId || '',
        observationUnitDbId: sample.observationUnitDbId || '',
        plateDbId: sample.plateDbId || '',
        plateIndex: sample.plateIndex || '',
        concentration: sample.concentration || '',
        volume: sample.volume || '',
        sampleDescription: sample.sampleDescription || '',
        tissueType: sample.tissueType || '',
        sampleTimestamp: sample.sampleTimestamp?.split('T')[0] || '',
      })
    },
  })

  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      // Demo - would call API
      await new Promise(r => setTimeout(r, 500))
      return { result: { sampleDbId: id || 'new-sample-id' } }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] })
      toast.success(isEdit ? 'Sample updated' : 'Sample created')
      navigate('/samples')
    },
    onError: () => {
      toast.error('Failed to save sample')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.sampleName) {
      toast.error('Sample name is required')
      return
    }
    mutation.mutate(formData)
  }

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">
          {isEdit ? 'Edit Sample' : 'New Sample'}
        </h1>
        <p className="text-muted-foreground mt-1">
          {isEdit ? 'Update sample information' : 'Register a new genotyping sample'}
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Sample Information</CardTitle>
            <CardDescription>Basic sample details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sampleName">Sample Name *</Label>
                <Input
                  id="sampleName"
                  value={formData.sampleName}
                  onChange={(e) => handleChange('sampleName', e.target.value)}
                  placeholder="SAMPLE_001"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sampleType">Sample Type</Label>
                <Select value={formData.sampleType} onValueChange={(v) => handleChange('sampleType', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DNA">DNA</SelectItem>
                    <SelectItem value="RNA">RNA</SelectItem>
                    <SelectItem value="Tissue">Tissue</SelectItem>
                    <SelectItem value="Seed">Seed</SelectItem>
                    <SelectItem value="Leaf">Leaf</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="tissueType">Tissue Type</Label>
                <Input
                  id="tissueType"
                  value={formData.tissueType}
                  onChange={(e) => handleChange('tissueType', e.target.value)}
                  placeholder="Young leaf"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sampleTimestamp">Collection Date</Label>
                <Input
                  id="sampleTimestamp"
                  type="date"
                  value={formData.sampleTimestamp}
                  onChange={(e) => handleChange('sampleTimestamp', e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="sampleDescription">Description</Label>
              <Textarea
                id="sampleDescription"
                value={formData.sampleDescription}
                onChange={(e) => handleChange('sampleDescription', e.target.value)}
                placeholder="Sample description..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Linkages</CardTitle>
            <CardDescription>Connect to germplasm and observation units</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="germplasmDbId">Germplasm ID</Label>
                <Input
                  id="germplasmDbId"
                  value={formData.germplasmDbId}
                  onChange={(e) => handleChange('germplasmDbId', e.target.value)}
                  placeholder="germplasm-001"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="observationUnitDbId">Observation Unit ID</Label>
                <Input
                  id="observationUnitDbId"
                  value={formData.observationUnitDbId}
                  onChange={(e) => handleChange('observationUnitDbId', e.target.value)}
                  placeholder="ou-001"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Plate Information</CardTitle>
            <CardDescription>Sample plate location and quantity</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="plateDbId">Plate ID</Label>
                <Input
                  id="plateDbId"
                  value={formData.plateDbId}
                  onChange={(e) => handleChange('plateDbId', e.target.value)}
                  placeholder="PLATE_001"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="plateIndex">Well Position</Label>
                <Input
                  id="plateIndex"
                  value={formData.plateIndex}
                  onChange={(e) => handleChange('plateIndex', e.target.value)}
                  placeholder="A01"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="concentration">Concentration (ng/µL)</Label>
                <Input
                  id="concentration"
                  type="number"
                  step="0.1"
                  value={formData.concentration}
                  onChange={(e) => handleChange('concentration', e.target.value)}
                  placeholder="50.0"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="volume">Volume (µL)</Label>
                <Input
                  id="volume"
                  type="number"
                  step="0.1"
                  value={formData.volume}
                  onChange={(e) => handleChange('volume', e.target.value)}
                  placeholder="100.0"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-4 mt-6">
          <Button type="button" variant="outline" onClick={() => navigate('/samples')} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending} className="flex-1">
            {mutation.isPending ? 'Saving...' : isEdit ? 'Update Sample' : 'Create Sample'}
          </Button>
        </div>
      </form>
    </div>
  )
}

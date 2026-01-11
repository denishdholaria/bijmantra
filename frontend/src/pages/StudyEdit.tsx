/**
 * Study Edit Page
 */

import { useForm } from 'react-hook-form'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface StudyFormData {
  studyName: string
  studyDescription: string
  trialDbId: string
  locationDbId: string
  startDate: string
  endDate: string
}

export function StudyEdit() {
  const { studyDbId } = useParams<{ studyDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['study', studyDbId],
    queryFn: () => apiClient.getStudy(studyDbId!),
    enabled: !!studyDbId,
  })

  const { data: trialsData } = useQuery({
    queryKey: ['trials'],
    queryFn: () => apiClient.getTrials(0, 100),
  })

  const { data: locationsData } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.getLocations(0, 100),
  })

  const study = data?.result
  const trials = trialsData?.result?.data || []
  const locations = locationsData?.result?.data || []

  const { register, handleSubmit, setValue, watch } = useForm<StudyFormData>({
    values: study ? {
      studyName: study.studyName || '',
      studyDescription: study.studyDescription || '',
      trialDbId: study.trialDbId || '',
      locationDbId: study.locationDbId || '',
      startDate: study.startDate || '',
      endDate: study.endDate || '',
    } : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: (data: StudyFormData) => apiClient.updateStudy(studyDbId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      queryClient.invalidateQueries({ queryKey: ['study', studyDbId] })
      navigate(`/studies/${studyDbId}`)
    },
  })

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!study) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold mb-2">Study Not Found</h2>
            <Button asChild><Link to="/studies">← Back to Studies</Link></Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild aria-label="Back to study">
              <Link to={`/studies/${studyDbId}`}>←</Link>
            </Button>
            <div>
              <CardTitle>Edit Study</CardTitle>
              <CardDescription>Update study information</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((data) => updateMutation.mutate(data))} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="studyName">Study Name *</Label>
              <Input id="studyName" {...register('studyName', { required: true })} placeholder="e.g., Yield Trial 2025" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="studyDescription">Description</Label>
              <Textarea id="studyDescription" {...register('studyDescription')} rows={4} placeholder="Study description..." />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Trial</Label>
                <Select value={watch('trialDbId')} onValueChange={(v) => setValue('trialDbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select trial" /></SelectTrigger>
                  <SelectContent>
                    {trials.map((t: any) => (
                      <SelectItem key={t.trialDbId} value={t.trialDbId}>{t.trialName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Location</Label>
                <Select value={watch('locationDbId')} onValueChange={(v) => setValue('locationDbId', v)}>
                  <SelectTrigger><SelectValue placeholder="Select location" /></SelectTrigger>
                  <SelectContent>
                    {locations.map((l: any) => (
                      <SelectItem key={l.locationDbId} value={l.locationDbId}>{l.locationName}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="startDate">Start Date</Label>
                <Input id="startDate" type="date" {...register('startDate')} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="endDate">End Date</Label>
                <Input id="endDate" type="date" {...register('endDate')} />
              </div>
            </div>

            {updateMutation.isError && (
              <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg">
                <p className="text-sm text-red-800">❌ {updateMutation.error instanceof Error ? updateMutation.error.message : 'Failed to update'}</p>
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={updateMutation.isPending} className="flex-1">
                {updateMutation.isPending ? '💾 Saving...' : '💾 Save Changes'}
              </Button>
              <Button variant="outline" asChild>
                <Link to={`/studies/${studyDbId}`}>Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

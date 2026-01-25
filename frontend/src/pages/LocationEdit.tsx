/**
 * Location Edit Page
 */

import { useForm } from 'react-hook-form'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface LocationFormData {
  locationName: string
  locationType: string
  countryName: string
  countryCode: string
  latitude: string
  longitude: string
  altitude: string
}

export function LocationEdit() {
  const { locationDbId } = useParams<{ locationDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['location', locationDbId],
    queryFn: () => apiClient.getLocation(locationDbId!),
    enabled: !!locationDbId,
  })

  const location = data?.result
  const coords = location?.coordinates?.geometry?.coordinates

  const { register, handleSubmit, setValue, watch } = useForm<LocationFormData>({
    values: location ? {
      locationName: location.locationName || '',
      locationType: location.locationType || '',
      countryName: location.countryName || '',
      countryCode: location.countryCode || '',
      latitude: coords?.[1]?.toString() || '',
      longitude: coords?.[0]?.toString() || '',
      altitude: location.altitude?.toString() || '',
    } : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: (data: any) => apiClient.updateLocation(locationDbId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
      queryClient.invalidateQueries({ queryKey: ['location', locationDbId] })
      navigate(`/locations/${locationDbId}`)
    },
  })

  const onSubmit = (data: LocationFormData) => {
    const locationData: any = {
      locationName: data.locationName,
      locationType: data.locationType || undefined,
      countryName: data.countryName || undefined,
      countryCode: data.countryCode || undefined,
    }

    if (data.latitude && data.longitude) {
      locationData.coordinates = {
        geometry: {
          type: 'Point',
          coordinates: [parseFloat(data.longitude), parseFloat(data.latitude)]
        },
        type: 'Feature'
      }
    }

    if (data.altitude) {
      locationData.altitude = parseFloat(data.altitude)
    }

    updateMutation.mutate(locationData)
  }

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!location) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-6xl mb-4">📍</div>
            <h2 className="text-2xl font-bold mb-2">Location Not Found</h2>
            <Button asChild><Link to="/locations">← Back to Locations</Link></Button>
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
            <Button variant="ghost" size="icon" asChild aria-label="Back to location">
              <Link to={`/locations/${locationDbId}`}>←</Link>
            </Button>
            <div>
              <CardTitle>Edit Location</CardTitle>
              <CardDescription>Update location information</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="locationName">Location Name *</Label>
              <Input id="locationName" {...register('locationName', { required: true })} placeholder="e.g., North Field Station" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="locationType">Location Type</Label>
              <Select value={watch('locationType')} onValueChange={(v) => setValue('locationType', v)}>
                <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Field">Field</SelectItem>
                  <SelectItem value="Greenhouse">Greenhouse</SelectItem>
                  <SelectItem value="Laboratory">Laboratory</SelectItem>
                  <SelectItem value="Storage">Storage</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="countryName">Country</Label>
                <Input id="countryName" {...register('countryName')} placeholder="e.g., United States" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="countryCode">Country Code</Label>
                <Input id="countryCode" {...register('countryCode')} placeholder="e.g., USA" maxLength={3} />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="latitude">Latitude</Label>
                <Input id="latitude" type="number" step="any" {...register('latitude')} placeholder="40.7128" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="longitude">Longitude</Label>
                <Input id="longitude" type="number" step="any" {...register('longitude')} placeholder="-74.0060" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="altitude">Altitude (m)</Label>
                <Input id="altitude" type="number" step="any" {...register('altitude')} placeholder="10" />
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
                <Link to={`/locations/${locationDbId}`}>Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Location Detail Page
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

export function LocationDetail() {
  const { locationDbId } = useParams<{ locationDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['location', locationDbId],
    queryFn: () => apiClient.locationService.getLocation(locationDbId!),
    enabled: !!locationDbId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.locationService.deleteLocation(locationDbId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
      navigate('/locations')
    },
  })

  const location = data?.result

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2"><Skeleton className="h-64 w-full" /></div>
          <div><Skeleton className="h-48 w-full" /></div>
        </div>
      </div>
    )
  }

  if (error || !location) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-6xl mb-4">📍</div>
            <h2 className="text-2xl font-bold mb-2">Location Not Found</h2>
            <p className="text-muted-foreground mb-6">
              {error instanceof Error ? error.message : 'The location does not exist.'}
            </p>
            <Button asChild><Link to="/locations">← Back to Locations</Link></Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const coords = location.coordinates?.geometry?.coordinates
  const hasCoords = coords && coords.length >= 2

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label="Back to locations">
            <Link to="/locations">←</Link>
          </Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">{location.locationName}</h1>
            <div className="flex gap-2 mt-1">
              {location.locationType && <Badge variant="secondary">{location.locationType}</Badge>}
              {location.countryName && <Badge variant="outline">{location.countryName}</Badge>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild><Link to={`/locations/${locationDbId}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDeleteDialog(true)}>🗑️ Delete</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Map Preview */}
          {hasCoords && (
            <Card>
              <CardHeader><CardTitle>📍 Location Map</CardTitle></CardHeader>
              <CardContent>
                <div className="aspect-video bg-muted rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-4xl mb-2">🗺️</p>
                    <p className="text-muted-foreground">Lat: {coords[1].toFixed(6)}</p>
                    <p className="text-muted-foreground">Lng: {coords[0].toFixed(6)}</p>
                    <a 
                      href={`https://www.google.com/maps?q=${coords[1]},${coords[0]}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline mt-2 inline-block"
                    >
                      Open in Google Maps →
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Additional Info */}
          {location.additionalInfo && Object.keys(location.additionalInfo).length > 0 && (
            <Card>
              <CardHeader><CardTitle>ℹ️ Additional Information</CardTitle></CardHeader>
              <CardContent>
                <dl className="space-y-3">
                  {Object.entries(location.additionalInfo).map(([key, value]) => (
                    <div key={key}>
                      <dt className="text-sm font-semibold text-muted-foreground">{key}</dt>
                      <dd className="mt-1">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Location Details</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div>
                <dt className="text-sm font-semibold text-muted-foreground">Location ID</dt>
                <dd className="font-mono text-sm bg-muted px-2 py-1 rounded mt-1">{location.locationDbId}</dd>
              </div>
              {location.locationType && (
                <div>
                  <dt className="text-sm font-semibold text-muted-foreground">Type</dt>
                  <dd className="mt-1">{location.locationType}</dd>
                </div>
              )}
              {location.countryName && (
                <div>
                  <dt className="text-sm font-semibold text-muted-foreground">Country</dt>
                  <dd className="mt-1">{location.countryName} {location.countryCode && `(${location.countryCode})`}</dd>
                </div>
              )}
              {location.altitude && (
                <div>
                  <dt className="text-sm font-semibold text-muted-foreground">Altitude</dt>
                  <dd className="mt-1">{location.altitude}m</dd>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full" asChild>
                <Link to={`/studies/new?locationId=${locationDbId}`}>📊 Create Study Here</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Location"
        message={`Are you sure you want to delete "${location.locationName}"?`}
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

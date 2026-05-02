import { RefreshCw, MapPin, Radio } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { useSensorLocations } from './hooks/useSensorLocations';
import type { SensorLocation } from './types';

interface SensorLocationListProps {
  selectedLocationId?: string | null;
  onSelectLocation?: (location: SensorLocation) => void;
}

function getStatusTone(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === 'online') {
    return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300';
  }
  if (normalized === 'warning') {
    return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300';
  }
  return 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300';
}

export function SensorLocationList({
  selectedLocationId,
  onSelectLocation,
}: SensorLocationListProps) {
  const locationQuery = useSensorLocations();
  const locations = locationQuery.data ?? [];

  if (locationQuery.isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-44" />
          <Skeleton className="h-4 w-72" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-20 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (locationQuery.isError) {
    return (
      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle>Unable to load sensor locations</CardTitle>
          <CardDescription>
            {locationQuery.error instanceof Error
              ? locationQuery.error.message
              : 'The location request failed.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => locationQuery.refetch()}>Retry Locations</Button>
        </CardContent>
      </Card>
    );
  }

  if (locations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No sensor locations found</CardTitle>
          <CardDescription>
            This organization does not currently have registered sensor devices with visible locations.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="gap-3">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle>Sensor Locations</CardTitle>
            <CardDescription>
              Select a location to inspect its latest environmental series.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            onClick={() => locationQuery.refetch()}
            disabled={locationQuery.isFetching}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${locationQuery.isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {locations.map((location) => {
          const isSelected = location.id === selectedLocationId;
          return (
            <button
              key={location.id}
              type="button"
              onClick={() => onSelectLocation?.(location)}
              aria-label={`Select sensor location ${location.name}`}
              aria-pressed={isSelected}
              className={`w-full rounded-lg border p-4 text-left transition-colors hover:bg-muted/40 ${
                isSelected ? 'border-primary bg-primary/5' : 'border-border'
              }`}
            >
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{location.name}</h3>
                    <Badge className={getStatusTone(location.status)}>{location.status}</Badge>
                  </div>
                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {location.locationLabel}
                    </span>
                    <span className="flex items-center gap-1">
                      <Radio className="h-4 w-4" />
                      {location.sensorCount} sensor{location.sensorCount === 1 ? '' : 's'}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Coordinates:{' '}
                    {location.coordinates
                      ? `${location.coordinates.latitude.toFixed(4)}, ${location.coordinates.longitude.toFixed(4)}`
                      : 'Not available'}
                  </p>
                </div>
                <div className="text-sm text-muted-foreground">
                  <div>Type: {location.type}</div>
                  <div>Battery: {location.battery ?? 'n/a'}%</div>
                  <div>Signal: {location.signal ?? 'n/a'}%</div>
                </div>
              </div>
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { SensorLocation } from './types';

interface LocationMapProps {
  location: SensorLocation | null;
}

function projectLongitude(longitude: number) {
  return ((longitude + 180) / 360) * 100;
}

function projectLatitude(latitude: number) {
  return ((90 - latitude) / 180) * 60;
}

export function LocationMap({ location }: LocationMapProps) {
  if (!location) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Location Map</CardTitle>
          <CardDescription>Select a location to show its mapped position.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!location.coordinates) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Location Map</CardTitle>
          <CardDescription>
            Coordinate data is not available for this sensor location, so the map is intentionally hidden.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const markerX = projectLongitude(location.coordinates.longitude);
  const markerY = projectLatitude(location.coordinates.latitude);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Location Map</CardTitle>
        <CardDescription>
          {location.name} · {location.coordinates.latitude.toFixed(4)}, {location.coordinates.longitude.toFixed(4)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-lg border bg-muted/20 p-4">
          <svg
            viewBox="0 0 100 60"
            className="h-64 w-full rounded-md bg-[radial-gradient(circle_at_top_right,hsl(var(--chart-2)/0.15),transparent_30%),linear-gradient(180deg,hsl(var(--muted)/0.7),hsl(var(--background)))]"
            role="img"
            aria-label={`Map of ${location.name}`}
          >
            <rect x="8" y="10" width="84" height="40" rx="8" fill="transparent" stroke="hsl(var(--border))" />
            <line x1="50" x2="50" y1="10" y2="50" stroke="hsl(var(--border))" strokeDasharray="2 2" />
            <line x1="8" x2="92" y1="30" y2="30" stroke="hsl(var(--border))" strokeDasharray="2 2" />
            <circle cx={markerX} cy={markerY} r="2.5" fill="hsl(var(--chart-1))" />
            <text x={Math.min(markerX + 3, 84)} y={Math.max(markerY - 3, 8)} fontSize="4" fill="currentColor">
              {location.name}
            </text>
          </svg>
        </div>
      </CardContent>
    </Card>
  );
}

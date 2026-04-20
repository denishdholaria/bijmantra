import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function WeatherStationDetail({ stationId }: { stationId: number }) {
  const { data: station, isLoading } = useQuery({
    queryKey: ['weather-station', stationId],
    queryFn: () => apiClient.weatherService.getWeatherStation(stationId),
  });

  if (isLoading) return <div>Loading...</div>;
  if (!station) return <div>Not found</div>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{station.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="font-semibold">Coordinates</p>
            <p>{station.latitude}, {station.longitude}</p>
          </div>
          <div>
            <p className="font-semibold">Provider</p>
            <p>{station.provider || '-'}</p>
          </div>
          <div>
            <p className="font-semibold">Status</p>
            <p>{station.status}</p>
          </div>
          <div>
             <p className="font-semibold">Elevation</p>
             <p>{station.elevation || '-'} m</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

import { WeatherStationList } from '@/components/weather/WeatherStationList';

export function WeatherStationManagement() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Weather Stations</h1>
        <p className="text-muted-foreground">
          Manage physical and virtual weather stations for data collection.
        </p>
      </div>
      <WeatherStationList />
    </div>
  );
}

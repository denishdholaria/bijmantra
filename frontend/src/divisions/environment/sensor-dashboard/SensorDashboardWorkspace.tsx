import { startTransition, useState } from 'react';
import { LocationMap } from './LocationMap';
import { SensorDataChart } from './SensorDataChart';
import { SensorLocationList } from './SensorLocationList';
import type { SensorLocation } from './types';

export function SensorDashboardWorkspace() {
  const [selectedLocation, setSelectedLocation] = useState<SensorLocation | null>(null);

  const handleSelectLocation = (location: SensorLocation) => {
    startTransition(() => {
      setSelectedLocation(location);
    });
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
      <SensorLocationList
        selectedLocationId={selectedLocation?.id ?? null}
        onSelectLocation={handleSelectLocation}
      />
      <div className="space-y-6">
        <SensorDataChart
          locationId={selectedLocation?.id ?? null}
          locationName={selectedLocation?.name}
        />
        <LocationMap location={selectedLocation} />
      </div>
    </div>
  );
}

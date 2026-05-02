import { useQuery } from '@tanstack/react-query';
import { sensorDashboardService } from '../services/sensorDashboardService';
import type { SensorTimeRange } from '../types';

export function useSensorData(locationId: string | null, range: SensorTimeRange) {
  return useQuery({
    queryKey: ['environment', 'sensor-dashboard', 'series', locationId, range],
    queryFn: () => sensorDashboardService.getSensorSeries(locationId as string, range),
    enabled: Boolean(locationId),
  });
}

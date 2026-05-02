import { useQuery } from '@tanstack/react-query';
import { sensorDashboardService } from '../services/sensorDashboardService';

export function useSensorLocations() {
  return useQuery({
    queryKey: ['environment', 'sensor-dashboard', 'locations'],
    queryFn: () => sensorDashboardService.getLocations(),
  });
}

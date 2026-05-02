import { useQuery } from '@tanstack/react-query';
import { crossPlanningService } from '../services/crossPlanningService';

export function useCrossPlans(page = 0, pageSize = 20) {
  return useQuery({
    queryKey: ['breeding', 'cross-planning', 'plans', page, pageSize],
    queryFn: () => crossPlanningService.getCrossPlans(page, pageSize),
  });
}

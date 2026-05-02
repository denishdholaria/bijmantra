import { useQuery } from '@tanstack/react-query';
import { crossPlanningService } from '../services/crossPlanningService';

export function usePedigree(germplasmId: string | null, maxGenerations = 5) {
  return useQuery({
    queryKey: ['breeding', 'cross-planning', 'pedigree', germplasmId, maxGenerations],
    queryFn: () => crossPlanningService.getPedigreeTree(germplasmId as string, maxGenerations),
    enabled: Boolean(germplasmId),
  });
}

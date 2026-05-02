import { useMutation, useQueryClient } from '@tanstack/react-query';
import { crossPlanningService } from '../services/crossPlanningService';
import type { CrossPlanFormValues } from '../types';

export function useCreateCrossPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (values: CrossPlanFormValues) => crossPlanningService.createCrossPlan(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['breeding', 'cross-planning', 'plans'] });
    },
  });
}

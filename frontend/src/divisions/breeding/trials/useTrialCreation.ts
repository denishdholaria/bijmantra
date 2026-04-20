/**
 * useTrialCreation Hook
 * State management for trial creation workflow
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { trialService } from '../services/trialService';
import type { TrialFormData, TrialCreationState } from './types';

export function useTrialCreation() {
  const queryClient = useQueryClient();
  const [state, setState] = useState<TrialCreationState>({
    isLoading: false,
    isEmpty: true,
    error: null,
    success: false,
  });

  const createMutation = useMutation({
    mutationFn: (data: TrialFormData) => trialService.createTrial(data),
    onMutate: () => {
      setState({
        isLoading: true,
        isEmpty: false,
        error: null,
        success: false,
      });
    },
    onSuccess: (data) => {
      setState({
        isLoading: false,
        isEmpty: false,
        error: null,
        success: true,
        createdTrialId: data.trialDbId,
      });
      // Invalidate trials list to refresh
      queryClient.invalidateQueries({ queryKey: ['trials'] });
    },
    onError: (error: Error) => {
      setState({
        isLoading: false,
        isEmpty: false,
        error: error.message || 'Failed to create trial',
        success: false,
      });
    },
  });

  const createTrial = (data: TrialFormData) => {
    createMutation.mutate(data);
  };

  const resetState = () => {
    setState({
      isLoading: false,
      isEmpty: true,
      error: null,
      success: false,
    });
  };

  return {
    ...state,
    createTrial,
    resetState,
  };
}

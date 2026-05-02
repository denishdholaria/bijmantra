/**
 * Custom hook for breeding cross management
 */

import { useState, useEffect } from 'react';
import { crossManagementService } from './crossManagementService';
import type { CrossManagementState, CrossFilter } from './types';

export function useCrossManagement(initialFilter: CrossFilter = {}) {
  const [state, setState] = useState<CrossManagementState>({
    crosses: [],
    loading: false,
    error: null,
    filter: initialFilter,
  });

  const loadCrosses = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const crosses = await crossManagementService.fetchCrosses(state.filter);
      setState(prev => ({ ...prev, crosses, loading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load crosses',
      }));
    }
  };

  const updateFilter = (filter: Partial<CrossFilter>) => {
    setState(prev => ({ ...prev, filter: { ...prev.filter, ...filter } }));
  };

  useEffect(() => {
    loadCrosses();
  }, [state.filter]);

  return {
    ...state,
    updateFilter,
    reload: loadCrosses,
  };
}

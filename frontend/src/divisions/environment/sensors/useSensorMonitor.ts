/**
 * Custom hook for environmental sensor monitoring
 */

import { useState, useEffect } from 'react';
import { sensorMonitorService } from './sensorMonitorService';
import type { SensorMonitorState, SensorFilter } from './types';

export function useSensorMonitor(initialFilter: SensorFilter = {}) {
  const [state, setState] = useState<SensorMonitorState>({
    readings: [],
    loading: false,
    error: null,
    filter: initialFilter,
  });

  const loadReadings = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const readings = await sensorMonitorService.fetchReadings(state.filter);
      setState(prev => ({ ...prev, readings, loading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load sensor readings',
      }));
    }
  };

  const updateFilter = (filter: Partial<SensorFilter>) => {
    setState(prev => ({ ...prev, filter: { ...prev.filter, ...filter } }));
  };

  useEffect(() => {
    loadReadings();
  }, [state.filter]);

  return {
    ...state,
    updateFilter,
    reload: loadReadings,
  };
}

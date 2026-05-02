/**
 * Tests for useSensorMonitor hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useSensorMonitor } from './useSensorMonitor';
import { sensorMonitorService } from './sensorMonitorService';

vi.mock('./sensorMonitorService', () => ({
  sensorMonitorService: {
    fetchReadings: vi.fn(),
    getLatestReading: vi.fn(),
  },
}));

describe('useSensorMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads sensor readings on mount', async () => {
    const mockReadings = [
      { 
        id: '1', 
        sensorId: 'S001', 
        sensorType: 'temperature' as const, 
        value: 22.5, 
        unit: '°C', 
        timestamp: new Date(), 
        location: 'Greenhouse A', 
        quality: 'good' as const 
      },
    ];
    (sensorMonitorService.fetchReadings as any).mockResolvedValue(mockReadings);

    const { result } = renderHook(() => useSensorMonitor());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.readings).toEqual(mockReadings);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch errors', async () => {
    (sensorMonitorService.fetchReadings as any).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useSensorMonitor());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.readings).toEqual([]);
  });
});

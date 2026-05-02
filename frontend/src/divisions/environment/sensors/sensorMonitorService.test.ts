/**
 * Tests for sensorMonitorService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sensorMonitorService } from './sensorMonitorService';

global.fetch = vi.fn();

describe('sensorMonitorService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches sensor readings with filters', async () => {
    const mockReadings = [
      { 
        id: '1', 
        sensorId: 'S001', 
        sensorType: 'temperature', 
        value: 22.5, 
        unit: '°C', 
        timestamp: new Date(), 
        location: 'Greenhouse A', 
        quality: 'good' 
      },
    ];
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockReadings,
    });

    const result = await sensorMonitorService.fetchReadings({ sensorId: 'S001', sensorType: 'temperature' });

    expect(result).toEqual(mockReadings);
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('sensor_id=S001'));
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('sensor_type=temperature'));
  });

  it('throws error on failed fetch', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: false,
    });

    await expect(sensorMonitorService.fetchReadings({})).rejects.toThrow('Failed to fetch sensor readings');
  });

  it('fetches latest reading for a sensor', async () => {
    const mockReading = { 
      id: '1', 
      sensorId: 'S001', 
      sensorType: 'temperature', 
      value: 22.5, 
      unit: '°C', 
      timestamp: new Date(), 
      location: 'Greenhouse A', 
      quality: 'good' 
    };
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockReading,
    });

    const result = await sensorMonitorService.getLatestReading('S001');

    expect(result).toEqual(mockReading);
    expect(global.fetch).toHaveBeenCalledWith('/api/v2/environment/sensors/S001/latest');
  });
});

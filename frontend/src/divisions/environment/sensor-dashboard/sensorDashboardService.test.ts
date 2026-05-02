import { beforeEach, describe, expect, it, vi } from 'vitest';
import { sensorDashboardService } from './services/sensorDashboardService';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: mockGet,
  },
}));

describe('sensorDashboardService', () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it('aggregates supported sensor readings into sorted chart points', async () => {
    mockGet.mockResolvedValue({
      readings: [
        {
          id: 'r1',
          device_id: 'device-1',
          sensor: 'temperature',
          value: 28.4,
          unit: 'C',
          timestamp: '2026-04-20T06:00:00Z',
        },
        {
          id: 'r2',
          device_id: 'device-1',
          sensor: 'humidity',
          value: 61,
          unit: '%',
          timestamp: '2026-04-20T06:15:00Z',
        },
        {
          id: 'r3',
          device_id: 'device-1',
          sensor: 'rainfall',
          value: 4.2,
          unit: 'mm',
          timestamp: '2026-04-20T06:30:00Z',
        },
        {
          id: 'r4',
          device_id: 'device-1',
          sensor: 'temperature',
          value: 29.1,
          unit: 'C',
          timestamp: '2026-04-21T06:00:00Z',
        },
        {
          id: 'r5',
          device_id: 'device-1',
          sensor: 'soil_moisture',
          value: 18,
          unit: '%',
          timestamp: '2026-04-21T06:30:00Z',
        },
      ],
    });

    const result = await sensorDashboardService.getSensorSeries('device-1', '30d');

    expect(mockGet).toHaveBeenCalledWith(expect.stringContaining('/api/v2/sensors/readings?'));
    expect(mockGet).toHaveBeenCalledWith(expect.stringContaining('device_id=device-1'));
    expect(result.points).toEqual([
      {
        timestamp: '2026-04-20',
        temperature: 28.4,
        humidity: 61,
        rainfall: 4.2,
      },
      {
        timestamp: '2026-04-21',
        temperature: 29.1,
        humidity: null,
        rainfall: null,
      },
    ]);
    expect(result.latestReadings).toHaveLength(4);
  });
});

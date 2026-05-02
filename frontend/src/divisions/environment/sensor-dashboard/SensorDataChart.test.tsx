import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SensorDataChart } from './SensorDataChart';
import * as sensorDataHookModule from './hooks/useSensorData';

vi.mock('./hooks/useSensorData');
vi.mock('recharts', () => {
  const Mock = ({ children }: { children?: ReactNode }) => <div>{children}</div>;

  return {
    ResponsiveContainer: Mock,
    LineChart: Mock,
    CartesianGrid: Mock,
    Legend: Mock,
    Line: Mock,
    Tooltip: Mock,
    XAxis: Mock,
    YAxis: Mock,
  };
});

describe('SensorDataChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('switches time ranges and reruns the chart query with the selected range', () => {
    vi.mocked(sensorDataHookModule.useSensorData).mockImplementation((locationId, range) => ({
      isLoading: false,
      isError: false,
      data: {
        locationId: locationId ?? 'device-1',
        range,
        points:
          range === '7d'
            ? [
                {
                  timestamp: '2026-04-22',
                  temperature: 28,
                  humidity: 60,
                  rainfall: 0,
                },
              ]
            : [
                {
                  timestamp: '2026-04-20',
                  temperature: 27,
                  humidity: 58,
                  rainfall: 1,
                },
                {
                  timestamp: '2026-04-21',
                  temperature: 28,
                  humidity: 60,
                  rainfall: 0,
                },
              ],
        latestReadings: [],
      },
      error: null,
    } as unknown as ReturnType<typeof sensorDataHookModule.useSensorData>));

    render(<SensorDataChart locationId="device-1" locationName="North Field" />);

    expect(screen.getByText('Rendering 2 chart points for the selected range.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '7 days' }));

    expect(vi.mocked(sensorDataHookModule.useSensorData)).toHaveBeenLastCalledWith('device-1', '7d');
    expect(screen.getByText('Rendering 1 chart point for the selected range.')).toBeInTheDocument();
  });
});

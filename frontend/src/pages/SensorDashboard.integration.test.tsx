import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SensorDashboard } from './SensorDashboard';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: mockGet,
  },
}));
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

function renderWorkflow() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <SensorDashboard />
    </QueryClientProvider>
  );
}

describe('SensorDashboard integration', () => {
  beforeEach(() => {
    mockGet.mockReset();

    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === '/api/v2/sensors/devices') {
        return Promise.resolve({
          devices: [
            {
              device_id: 'device-1',
              name: 'North Field',
              device_type: 'weather-station',
              location: 'Block A',
              sensors: ['temperature', 'humidity', 'rainfall'],
              status: 'online',
              battery: 91,
              signal: 76,
              last_seen: '2026-04-22T09:00:00Z',
              coordinates: {
                latitude: 12.9716,
                longitude: 77.5946,
              },
            },
          ],
        });
      }

      if (endpoint.startsWith('/api/v2/sensors/readings?') && endpoint.includes('device_id=device-1')) {
        return Promise.resolve({
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
              timestamp: '2026-04-21T06:30:00Z',
            },
          ],
        });
      }

      throw new Error(`Unhandled endpoint: ${endpoint}`);
    });
  });

  it('selects a location and renders the corresponding chart and map', async () => {
    renderWorkflow();

    fireEvent.click(
      await screen.findByRole('button', { name: 'Select sensor location North Field' })
    );

    expect(await screen.findByText('Rendering 2 chart points for the selected range.')).toBeInTheDocument();
    expect(screen.getByText('North Field · 12.9716, 77.5946')).toBeInTheDocument();
    expect(screen.getByLabelText('Map of North Field')).toBeInTheDocument();
  });
});

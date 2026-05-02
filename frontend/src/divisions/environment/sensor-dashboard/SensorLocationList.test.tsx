import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SensorLocationList } from './SensorLocationList';
import * as sensorLocationsHookModule from './hooks/useSensorLocations';

vi.mock('./hooks/useSensorLocations');

describe('SensorLocationList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders available locations and reports the selected location', () => {
    const onSelectLocation = vi.fn();

    vi.mocked(sensorLocationsHookModule.useSensorLocations).mockReturnValue({
      isLoading: false,
      isError: false,
      isFetching: false,
      data: [
        {
          id: 'device-1',
          name: 'North Field',
          type: 'weather-station',
          locationLabel: 'Block A',
          sensorCount: 3,
          sensors: ['temperature', 'humidity', 'rainfall'],
          status: 'online',
          battery: 91,
          signal: 76,
          lastSeen: '2026-04-22T09:00:00Z',
          coordinates: {
            latitude: 12.9716,
            longitude: 77.5946,
          },
        },
      ],
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof sensorLocationsHookModule.useSensorLocations>);

    render(<SensorLocationList onSelectLocation={onSelectLocation} />);

    expect(screen.getByText('North Field')).toBeInTheDocument();
    expect(screen.getByText('Coordinates: 12.9716, 77.5946')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Select sensor location North Field' }));

    expect(onSelectLocation).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'device-1',
        name: 'North Field',
      })
    );
  });
});

import { render, screen } from '@testing-library/react';
import { WeatherStationList } from '@/components/weather/WeatherStationList';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect } from 'vitest';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    weatherService: {
      listWeatherStations: vi.fn().mockResolvedValue([
        {
          id: 1,
          name: 'Test Station',
          latitude: 10,
          longitude: 20,
          provider: 'TestProvider',
          status: 'active',
        },
      ]),
      deleteWeatherStation: vi.fn(),
    },
  },
}));

const queryClient = new QueryClient();

describe('WeatherStationList', () => {
  it('renders weather stations', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <WeatherStationList />
      </QueryClientProvider>
    );

    expect(await screen.findByText('Test Station')).toBeInTheDocument();
    expect(screen.getByText('10, 20')).toBeInTheDocument();
    expect(screen.getByText('TestProvider')).toBeInTheDocument();
  });
});

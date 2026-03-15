import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { LiveSensorTelemetryChart } from './LiveSensorTelemetryChart';

// Mock EChartsWrapper to avoid canvas issues in JSDOM
vi.mock('@/components/charts/EChartsWrapper', () => ({
  EChartsWrapper: React.forwardRef(() => <div data-testid="mock-echarts" />),
  default: React.forwardRef(() => <div data-testid="mock-echarts" />),
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  Play: () => <div data-testid="play-icon" />,
  Pause: () => <div data-testid="pause-icon" />,
  Activity: () => <div data-testid="activity-icon" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
}));

describe('LiveSensorTelemetryChart', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('renders with default props', () => {
    render(<LiveSensorTelemetryChart sensorId="sensor-123" />);

    expect(screen.getByText('Sensor Telemetry')).toBeDefined();
    expect(screen.getByText('Sensor ID: sensor-123')).toBeDefined();
    expect(screen.getByText('LIVE')).toBeDefined();
    expect(screen.getByTestId('mock-echarts')).toBeDefined();
  });

  it('displays the provided title and description', () => {
    render(
      <LiveSensorTelemetryChart
        sensorId="sensor-123"
        title="Custom Title"
        description="Custom Description"
      />
    );

    expect(screen.getByText('Custom Title')).toBeDefined();
    expect(screen.getByText('Custom Description')).toBeDefined();
  });

  it('starts simulating data when simulate={true}', async () => {
    render(
      <LiveSensorTelemetryChart
        sensorId="sensor-123"
        simulate={true}
        updateInterval={100}
      />
    );

    // Initially buffer is 0
    expect(screen.getByText(/Buffer: 0 \/ 100 points/)).toBeDefined();

    // Advance time
    await act(async () => {
      vi.advanceTimersByTime(150);
    });

    // Buffer should be 1
    expect(screen.getByText(/Buffer: 1 \/ 100 points/)).toBeDefined();

    // Advance time again
    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    // Buffer should be 2
    expect(screen.getByText(/Buffer: 2 \/ 100 points/)).toBeDefined();
  });

  it('stops simulating data when paused', async () => {
    const { getByRole } = render(
      <LiveSensorTelemetryChart
        sensorId="sensor-123"
        simulate={true}
        updateInterval={100}
      />
    );

    // Initially buffer is 0
    expect(screen.getByText(/Buffer: 0 \/ 100 points/)).toBeDefined();

    // Pause the chart
    const pauseButton = screen.getByRole('button', { name: /Pause/i });
    await act(async () => {
      pauseButton.click();
    });

    // Advance time
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    // Buffer should still be 0 because it's paused
    expect(screen.getByText(/Buffer: 0 \/ 100 points/)).toBeDefined();
  });

  it('resets data when reset button is clicked', async () => {
    render(
      <LiveSensorTelemetryChart
        sensorId="sensor-123"
        simulate={true}
        updateInterval={100}
      />
    );

    // Advance time to get some data
    await act(async () => {
      vi.advanceTimersByTime(250);
    });

    expect(screen.queryByText(/Buffer: [1-9]/)).toBeDefined();

    // Click reset
    const resetButton = screen.getByRole('button', { name: /Reset/i });
    await act(async () => {
      resetButton.click();
    });

    // Buffer should be 0
    expect(screen.getByText(/Buffer: 0 \/ 100 points/)).toBeDefined();
  });
});

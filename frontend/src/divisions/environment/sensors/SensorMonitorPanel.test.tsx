/**
 * Tests for SensorMonitorPanel component
 * @vitest-environment jsdom
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SensorMonitorPanel } from './SensorMonitorPanel';
import { useSensorMonitor } from './useSensorMonitor';

vi.mock('./useSensorMonitor', () => ({
  useSensorMonitor: vi.fn(),
}));

describe('SensorMonitorPanel', () => {
  it('renders loading state', () => {
    (useSensorMonitor as any).mockReturnValue({
      readings: [],
      loading: true,
      error: null,
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<SensorMonitorPanel />);
    expect(screen.getByText('Loading sensor data...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    (useSensorMonitor as any).mockReturnValue({
      readings: [],
      loading: false,
      error: 'Failed to load',
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<SensorMonitorPanel />);
    expect(screen.getByText('Error: Failed to load')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    (useSensorMonitor as any).mockReturnValue({
      readings: [],
      loading: false,
      error: null,
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<SensorMonitorPanel />);
    expect(screen.getByText('No sensor readings found')).toBeInTheDocument();
  });
});

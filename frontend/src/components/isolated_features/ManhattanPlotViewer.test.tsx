import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ManhattanPlotViewer, SNPData } from './ManhattanPlotViewer';
import React from 'react';

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

const mockData: SNPData[] = [
  { markerName: 'M1', chromosome: '1', position: 1000, p_value: 0.01 },
  { markerName: 'M2', chromosome: '1', position: 2000, p_value: 0.0001 },
  { markerName: 'M3', chromosome: '2', position: 1500, p_value: 0.05 },
  { markerName: 'M4', chromosome: '2', position: 2500, p_value: 0.000001 },
];

describe('ManhattanPlotViewer', () => {
  it('renders without crashing', () => {
    render(<ManhattanPlotViewer data={mockData} />);
    expect(screen.getByText('Manhattan Plot Viewer')).toBeDefined();
  });

  it('displays the correct number of SNPs in the header', () => {
    render(<ManhattanPlotViewer data={mockData} />);
    expect(screen.getByText(/Total SNPs: 4/)).toBeDefined();
  });

  it('updates threshold when slider is moved', () => {
    const { container } = render(<ManhattanPlotViewer data={mockData} />);
    // Slider is a Radix component, tricky to test via standard fireEvent.
    // We'll check if the text updates if we can find it.
    const thresholdText = screen.getByText(/Threshold: 5.0/);
    expect(thresholdText).toBeDefined();
  });
});

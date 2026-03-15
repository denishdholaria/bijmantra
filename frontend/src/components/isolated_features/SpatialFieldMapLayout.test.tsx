import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SpatialFieldMapLayout } from './SpatialFieldMapLayout';
import { generateMockLayout } from './SpatialFieldMapLayout.mocks';

// Mock useFieldMode hook
vi.mock('@/hooks/useFieldMode', () => ({
  useFieldMode: () => ({
    isFieldMode: false,
    triggerHaptic: vi.fn(),
  }),
}));

describe('SpatialFieldMapLayout', () => {
  const mockLayout = generateMockLayout(5, 5);

  it('renders the study name and plot counts', () => {
    render(<SpatialFieldMapLayout layout={mockLayout} />);
    expect(screen.getByText(/Mock Field Trial 2026/i)).toBeDefined();
    expect(screen.getByText(/5 Rows x 5 Columns/i)).toBeDefined();
    expect(screen.getByText(/25 Total Plots/i)).toBeDefined();
  });

  it('renders all plots in the grid', () => {
    render(<SpatialFieldMapLayout layout={mockLayout} />);
    // Check for some plot numbers (e.g., 1A, 2B, etc.)
    expect(screen.getByText('1A')).toBeDefined();
    expect(screen.getByText('5E')).toBeDefined();
  });

  it('updates search query and filters plots visually', () => {
    render(<SpatialFieldMapLayout layout={mockLayout} />);
    const searchInput = screen.getByPlaceholderText(/Search plots.../i);

    fireEvent.change(searchInput, { target: { value: '1A' } });

    // 1A should still be fully opaque, while others might be dimmed
    const plot1A = screen.getByText('1A');
    expect(plot1A.className).not.toContain('opacity-20');
  });

  it('toggles plot selection on click', () => {
    const onPlotSelect = vi.fn();
    render(<SpatialFieldMapLayout layout={mockLayout} onPlotSelect={onPlotSelect} />);

    const plot1A = screen.getByText('1A');
    fireEvent.click(plot1A);

    expect(onPlotSelect).toHaveBeenCalledWith(expect.objectContaining({
      plotNumber: '1A'
    }));

    expect(screen.getByText(/1 plots selected/i)).toBeDefined();
  });

  it('shows the legend by default', () => {
    render(<SpatialFieldMapLayout layout={mockLayout} />);
    expect(screen.getByText(/Legend:/i)).toBeDefined();
    expect(screen.getByText(/Pending/i)).toBeDefined();
    expect(screen.getByText(/Complete/i)).toBeDefined();
  });

  it('renders REEVU AI Insights panel', () => {
    render(<SpatialFieldMapLayout layout={mockLayout} />);
    expect(screen.getByText(/REEVU AI Insights/i)).toBeDefined();
  });
});

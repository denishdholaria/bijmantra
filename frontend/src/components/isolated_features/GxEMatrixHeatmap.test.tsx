import { render, screen } from '@testing-library/react';
import { GxEMatrixHeatmap, generateMockGxEData } from './GxEMatrixHeatmap';
import { describe, it, expect, vi } from 'vitest';

// Mock useTheme hook
vi.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({ isDark: false }),
}));

// Mock EChartsWrapper to avoid canvas issues in JSDOM
vi.mock('@/components/charts/EChartsWrapper', () => ({
  EChartsWrapper: () => <div data-testid="echarts-mock" />,
}));

describe('GxEMatrixHeatmap', () => {
  it('renders loading state', () => {
    render(<GxEMatrixHeatmap isLoading={true} />);
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders empty state when no data provided', () => {
    render(<GxEMatrixHeatmap data={undefined} />);
    expect(screen.getByText(/No data available/i)).toBeInTheDocument();
  });

  it('renders with mock data', () => {
    const mockData = generateMockGxEData(5, 3);
    render(<GxEMatrixHeatmap data={mockData} title="Test Heatmap" />);

    expect(screen.getByText('Test Heatmap')).toBeInTheDocument();
    expect(screen.getByText('REEVU Aligned')).toBeInTheDocument();
    expect(screen.getByTestId('echarts-mock')).toBeInTheDocument();
  });
});

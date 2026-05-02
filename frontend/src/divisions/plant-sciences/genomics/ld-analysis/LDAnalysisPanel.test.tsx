/**
 * LDAnalysisPanel Unit Tests
 * Tests all four workflow states: loading, empty, error, success
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { LDAnalysisPanel } from './LDAnalysisPanel';
import * as useLDAnalysisModule from './useLDAnalysis';

// Mock the useLDAnalysis hook
vi.mock('./useLDAnalysis');

// Mock recharts to avoid rendering issues in tests
vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
}));

describe('LDAnalysisPanel', () => {
  const mockUpdate = vi.fn();
  const mockRunAnalysis = vi.fn();

  const defaultMockState = {
    isProcessing: false,
    useServer: true,
    serverVariantSetId: '',
    analysisMessage: null,
    nSamples: 200,
    nMarkers: 50,
    ldThreshold: 0.2,
    ldPairs: [],
    hweTests: [],
    ldMatrix: [],
    decayData: [],
    highLDPairs: [],
    hweViolations: [],
    wasmReady: true,
    wasmVersion: '1.0.0',
    syntheticPreviewAvailable: false,
    update: mockUpdate,
    runAnalysis: mockRunAnalysis,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should display loading spinner when isProcessing is true', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        isProcessing: true,
      });

      render(<LDAnalysisPanel />);

      const runButton = screen.getByRole('button', { name: /analyzing/i });
      expect(runButton).toBeInTheDocument();
      expect(runButton).toBeDisabled();
      expect(runButton).toHaveTextContent('Analyzing...');
    });

    it('should disable parameter inputs during processing', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        isProcessing: true,
        useServer: true,
      });

      render(<LDAnalysisPanel />);

      const samplesInput = screen.getByLabelText(/number of samples/i);
      const markersInput = screen.getByLabelText(/number of markers/i);
      
      expect(samplesInput).toBeDisabled();
      expect(markersInput).toBeDisabled();
    });
  });

  describe('Empty State', () => {
    it('should display "Run analysis" prompt when no data is available', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        ldPairs: [],
        ldMatrix: [],
        decayData: [],
        hweTests: [],
      });

      render(<LDAnalysisPanel />);

      const runButton = screen.getByRole('button', { name: /run analysis/i });
      expect(runButton).toBeInTheDocument();
      expect(runButton).not.toBeDisabled();
    });

    it('should show empty state messages in result tabs', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        ldMatrix: [],
        decayData: [],
      });

      render(<LDAnalysisPanel />);

      // Check LD Matrix tab
      const matrixTab = screen.getByRole('tab', { name: /ld matrix/i });
      fireEvent.click(matrixTab);
      
      expect(screen.getByText(/run analysis to generate ld matrix/i)).toBeInTheDocument();

      // Check LD Decay tab
      const decayTab = screen.getByRole('tab', { name: /ld decay/i });
      fireEvent.click(decayTab);
      
      expect(screen.getByText(/run analysis to see ld decay pattern/i)).toBeInTheDocument();
    });

    it('should display zero counts in summary cards when no data', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        nMarkers: 0,
        highLDPairs: [],
        hweViolations: [],
        ldPairs: [],
      });

      render(<LDAnalysisPanel />);

      expect(screen.getByText('0')).toBeInTheDocument(); // Markers count
    });
  });

  describe('Error State', () => {
    it('should display error message in amber alert when analysisMessage is set', () => {
      const errorMessage = 'No usable genotype calls were available for this variant set.';
      
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        analysisMessage: errorMessage,
      });

      render(<LDAnalysisPanel />);

      const alert = screen.getByText(errorMessage);
      expect(alert).toBeInTheDocument();
      expect(alert.parentElement).toHaveClass('border-amber-300');
    });

    it('should display validation error when variant set ID is missing', () => {
      const validationError = 'Enter a variant set ID to run server-side LD analysis.';
      
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        analysisMessage: validationError,
        useServer: true,
        serverVariantSetId: '',
      });

      render(<LDAnalysisPanel />);

      expect(screen.getByText(validationError)).toBeInTheDocument();
    });

    it('should not display alert when analysisMessage is null', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        analysisMessage: null,
      });

      render(<LDAnalysisPanel />);

      const alerts = document.querySelectorAll('.border-amber-300');
      expect(alerts.length).toBe(0);
    });
  });

  describe('Success State', () => {
    const mockLDPairs = [
      { marker1: 'M1', marker2: 'M2', distance: 10, r2: 0.85, dPrime: 0.92 },
      { marker1: 'M2', marker2: 'M3', distance: 20, r2: 0.65, dPrime: 0.81 },
      { marker1: 'M3', marker2: 'M4', distance: 30, r2: 0.45, dPrime: 0.67 },
    ];

    const mockHWETests = [
      { marker: 'M1', chiSquared: 0.5, pValue: 0.78, observedHet: 0.48, expectedHet: 0.50, inEquilibrium: true },
      { marker: 'M2', chiSquared: 5.2, pValue: 0.02, observedHet: 0.35, expectedHet: 0.50, inEquilibrium: false },
    ];

    const mockLDMatrix = [
      [1.0, 0.85, 0.65],
      [0.85, 1.0, 0.75],
      [0.65, 0.75, 1.0],
    ];

    const mockDecayData = [
      { distance: 0, mean_r2: 0.85, pair_count: 10 },
      { distance: 10, mean_r2: 0.65, pair_count: 15 },
      { distance: 20, mean_r2: 0.45, pair_count: 20 },
    ];

    it('should display LD heatmap when ldMatrix has data', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        ldMatrix: mockLDMatrix,
      });

      render(<LDAnalysisPanel />);

      const matrixTab = screen.getByRole('tab', { name: /ld matrix/i });
      fireEvent.click(matrixTab);

      // Check that heatmap is rendered (grid of colored cells)
      const heatmapCells = document.querySelectorAll('.w-3.h-3.rounded-sm');
      expect(heatmapCells.length).toBeGreaterThan(0);
    });

    it('should display LD decay chart when decayData has data', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        decayData: mockDecayData,
      });

      render(<LDAnalysisPanel />);

      const decayTab = screen.getByRole('tab', { name: /ld decay/i });
      fireEvent.click(decayTab);

      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      expect(screen.getByText(/based on 45 pairwise comparisons/i)).toBeInTheDocument();
    });

    it('should display LD pairs table with correct data', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        ldPairs: mockLDPairs,
      });

      render(<LDAnalysisPanel />);

      // LD Pairs tab is default
      expect(screen.getByText('M1')).toBeInTheDocument();
      expect(screen.getByText('M2')).toBeInTheDocument();
      expect(screen.getByText('0.850')).toBeInTheDocument();
      expect(screen.getByText('0.920')).toBeInTheDocument();
    });

    it('should display HWE tests table with violations highlighted', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        hweTests: mockHWETests,
        hweViolations: [mockHWETests[1]],
      });

      render(<LDAnalysisPanel />);

      const hweTab = screen.getByRole('tab', { name: /hwe tests/i });
      fireEvent.click(hweTab);

      expect(screen.getByText('M1')).toBeInTheDocument();
      expect(screen.getByText('M2')).toBeInTheDocument();
      expect(screen.getByText('In HWE')).toBeInTheDocument();
      expect(screen.getByText('Deviation')).toBeInTheDocument();
    });

    it('should display correct summary statistics', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        nMarkers: 50,
        highLDPairs: [mockLDPairs[0]],
        hweViolations: [mockHWETests[1]],
        ldPairs: mockLDPairs,
      });

      render(<LDAnalysisPanel />);

      expect(screen.getByText('50')).toBeInTheDocument(); // Markers
      expect(screen.getByText('1')).toBeInTheDocument(); // High LD Pairs and HWE Violations
      
      // Mean r² calculation: (0.85 + 0.65 + 0.45) / 3 = 0.650
      expect(screen.getByText('0.650')).toBeInTheDocument();
    });

    it('should show high LD badge for pairs above threshold', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        ldPairs: mockLDPairs,
        ldThreshold: 0.5,
      });

      render(<LDAnalysisPanel />);

      const highLDBadges = screen.getAllByText('High LD');
      const lowLDBadges = screen.getAllByText('Low LD');
      
      expect(highLDBadges.length).toBe(2); // r2 >= 0.5: 0.85 and 0.65
      expect(lowLDBadges.length).toBe(1); // r2 < 0.5: 0.45
    });
  });

  describe('User Interactions', () => {
    it('should call update when parameter inputs change', async () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        useServer: false,
        syntheticPreviewAvailable: true,
      });

      render(<LDAnalysisPanel />);

      const samplesInput = screen.getByLabelText(/number of samples/i);
      fireEvent.change(samplesInput, { target: { value: '300' } });

      await waitFor(() => {
        expect(mockUpdate).toHaveBeenCalledWith({ nSamples: 300 });
      });
    });

    it('should call update when LD threshold slider changes', async () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
      });

      render(<LDAnalysisPanel />);

      const slider = screen.getByRole('slider');
      fireEvent.click(slider);

      // Slider interaction will trigger update
      expect(mockUpdate).toHaveBeenCalled();
    });

    it('should call runAnalysis when Run Analysis button is clicked', async () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
      });

      render(<LDAnalysisPanel />);

      const runButton = screen.getByRole('button', { name: /run analysis/i });
      fireEvent.click(runButton);

      expect(mockRunAnalysis).toHaveBeenCalledTimes(1);
    });

    it('should call update when server mode switch is toggled', async () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        useServer: false,
        syntheticPreviewAvailable: true,
      });

      render(<LDAnalysisPanel />);

      const serverSwitch = screen.getByRole('switch', { name: /server-side/i });
      fireEvent.click(serverSwitch);

      expect(mockUpdate).toHaveBeenCalledWith({ useServer: true });
    });

    it('should call update when variant set ID input changes', async () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        useServer: true,
      });

      render(<LDAnalysisPanel />);

      const variantSetInput = screen.getByLabelText(/variant set id/i);
      fireEvent.change(variantSetInput, { target: { value: 'VS123' } });

      await waitFor(() => {
        expect(mockUpdate).toHaveBeenCalled();
      });
    });
  });

  describe('Component Rendering', () => {
    it('should render main title and description', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
      });

      render(<LDAnalysisPanel />);

      expect(screen.getByText('Linkage Disequilibrium Analysis')).toBeInTheDocument();
      expect(screen.getByText(/LD decay, r² calculation, and Hardy-Weinberg equilibrium testing/i)).toBeInTheDocument();
    });

    it('should render all four summary cards', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
      });

      render(<LDAnalysisPanel />);

      expect(screen.getByText('Markers')).toBeInTheDocument();
      expect(screen.getByText('High LD Pairs')).toBeInTheDocument();
      expect(screen.getByText('HWE Violations')).toBeInTheDocument();
      expect(screen.getByText('Mean r²')).toBeInTheDocument();
    });

    it('should render all four result tabs', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
      });

      render(<LDAnalysisPanel />);

      expect(screen.getByRole('tab', { name: /ld pairs/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /ld matrix/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /hwe tests/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /ld decay/i })).toBeInTheDocument();
    });

    it('should show WebAssembly ready badge when wasm is loaded', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        wasmReady: true,
        wasmVersion: '1.2.3',
      });

      render(<LDAnalysisPanel />);

      expect(screen.getByText(/⚡ WebAssembly v1.2.3/i)).toBeInTheDocument();
    });

    it('should show loading badge when wasm is not ready', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        wasmReady: false,
      });

      render(<LDAnalysisPanel />);

      expect(screen.getByText(/loading\.\.\./i)).toBeInTheDocument();
    });

    it('should hide server mode switch in production builds', () => {
      vi.mocked(useLDAnalysisModule.useLDAnalysis).mockReturnValue({
        ...defaultMockState,
        syntheticPreviewAvailable: false,
      });

      render(<LDAnalysisPanel />);

      expect(screen.queryByRole('switch', { name: /server-side/i })).not.toBeInTheDocument();
      expect(screen.getByText(/production builds run against stored variant sets only/i)).toBeInTheDocument();
    });
  });
});

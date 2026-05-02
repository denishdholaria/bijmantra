/**
 * useLDAnalysis Hook Unit Tests
 * Tests state management and orchestration logic
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useLDAnalysis } from './useLDAnalysis';
import { LDAnalysisService } from './ldAnalysisService';
import * as wasmHooks from '@/wasm/hooks';

// Mock dependencies
vi.mock('./ldAnalysisService');
vi.mock('@/wasm/hooks');

describe('useLDAnalysis', () => {
  const mockWasm = {
    calculate_ld_pair: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default WASM mock
    vi.mocked(wasmHooks.useWasm).mockReturnValue({
      isReady: true,
      version: '1.0.0',
      wasm: mockWasm,
    });

    // Mock import.meta.env
    vi.stubGlobal('import', {
      meta: {
        env: {
          DEV: true,
        },
      },
    });
  });

  describe('Initial State', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useLDAnalysis());

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.useServer).toBe(true);
      expect(result.current.serverVariantSetId).toBe('');
      expect(result.current.analysisMessage).toBeNull();
      expect(result.current.nSamples).toBe(200);
      expect(result.current.nMarkers).toBe(50);
      expect(result.current.ldThreshold).toBe(0.2);
      expect(result.current.ldPairs).toEqual([]);
      expect(result.current.hweTests).toEqual([]);
      expect(result.current.ldMatrix).toEqual([]);
      expect(result.current.decayData).toEqual([]);
    });

    it('should expose WASM status', () => {
      const { result } = renderHook(() => useLDAnalysis());

      expect(result.current.wasmReady).toBe(true);
      expect(result.current.wasmVersion).toBe('1.0.0');
    });

    it('should indicate synthetic preview availability in dev mode', () => {
      const { result } = renderHook(() => useLDAnalysis());

      expect(result.current.syntheticPreviewAvailable).toBe(true);
    });
  });

  describe('State Updates', () => {
    it('should update state with partial updates', () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ nSamples: 300 });
      });

      expect(result.current.nSamples).toBe(300);
      expect(result.current.nMarkers).toBe(50); // Other state unchanged
    });

    it('should update multiple fields at once', () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ 
          nSamples: 400, 
          nMarkers: 100,
          ldThreshold: 0.5 
        });
      });

      expect(result.current.nSamples).toBe(400);
      expect(result.current.nMarkers).toBe(100);
      expect(result.current.ldThreshold).toBe(0.5);
    });

    it('should toggle server mode', () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ useServer: false });
      });

      expect(result.current.useServer).toBe(false);
    });

    it('should update variant set ID', () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      expect(result.current.serverVariantSetId).toBe('VS123');
    });
  });

  describe('Server-Side Analysis', () => {
    const mockLDResult = {
      pairs: [
        { marker1: 'M1', marker2: 'M2', distance: 10, r2: 0.85, dPrime: 0.92 },
        { marker1: 'M2', marker2: 'M3', distance: 20, r2: 0.65, dPrime: 0.81 },
      ],
      markerCount: 50,
      sampleCount: 200,
      meanR2: 0.75,
    };

    const mockDecayData = {
      decay_curve: [
        { distance: 0, mean_r2: 0.85, pair_count: 10 },
        { distance: 10, mean_r2: 0.65, pair_count: 15 },
      ],
    };

    const mockMatrixData = {
      markers: ['M1', 'M2', 'M3'],
      matrix: [
        [1.0, 0.85, 0.65],
        [0.85, 1.0, 0.75],
        [0.65, 0.75, 1.0],
      ],
      region: 'region1',
    };

    beforeEach(() => {
      vi.mocked(LDAnalysisService.calculateLD).mockResolvedValue(mockLDResult);
      vi.mocked(LDAnalysisService.fetchDecay).mockResolvedValue(mockDecayData);
      vi.mocked(LDAnalysisService.fetchMatrix).mockResolvedValue(mockMatrixData);
    });

    it('should validate variant set ID before running server analysis', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.analysisMessage).toBe('Enter a variant set ID to run server-side LD analysis.');
      expect(LDAnalysisService.calculateLD).not.toHaveBeenCalled();
    });

    it('should run server-side analysis with valid variant set ID', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(LDAnalysisService.calculateLD).toHaveBeenCalledWith('VS123');
      expect(result.current.ldPairs).toEqual(mockLDResult.pairs);
      expect(result.current.nMarkers).toBe(50);
      expect(result.current.nSamples).toBe(200);
    });

    it('should fetch decay data after successful LD calculation', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(LDAnalysisService.fetchDecay).toHaveBeenCalledWith('VS123');
      expect(result.current.decayData).toEqual(mockDecayData.decay_curve);
    });

    it('should fetch matrix data after successful LD calculation', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(LDAnalysisService.fetchMatrix).toHaveBeenCalledWith('VS123');
      expect(result.current.ldMatrix).toEqual(mockMatrixData.matrix);
    });

    it('should handle empty genotype data gracefully', async () => {
      vi.mocked(LDAnalysisService.calculateLD).mockResolvedValue({
        pairs: [],
        markerCount: 0,
        sampleCount: 0,
        meanR2: 0,
      });

      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.analysisMessage).toBe('No usable genotype calls were available for this variant set.');
    });

    it('should handle decay fetch failure gracefully', async () => {
      vi.mocked(LDAnalysisService.fetchDecay).mockRejectedValue(new Error('Decay fetch failed'));

      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.decayData).toEqual([]);
      expect(result.current.ldPairs).toEqual(mockLDResult.pairs); // Main data still loaded
    });

    it('should handle matrix fetch failure gracefully', async () => {
      vi.mocked(LDAnalysisService.fetchMatrix).mockRejectedValue(new Error('Matrix fetch failed'));

      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.ldMatrix).toEqual([]);
      expect(result.current.ldPairs).toEqual(mockLDResult.pairs); // Main data still loaded
    });

    it('should set isProcessing during analysis', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      // Start analysis
      const analysisPromise = result.current.runAnalysis();

      // Wait for state to update
      await waitFor(() => {
        expect(result.current.isProcessing).toBe(true);
      });

      await act(async () => {
        await analysisPromise;
      });

      // Should be done after completion
      expect(result.current.isProcessing).toBe(false);
    });

    it('should clear analysis message before running', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      await act(async () => {
        result.current.update({ 
          serverVariantSetId: 'VS123',
          analysisMessage: 'Previous error'
        });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      // Message should be cleared on success
      expect(result.current.analysisMessage).toBeNull();
    });

    it('should handle API errors', async () => {
      vi.mocked(LDAnalysisService.calculateLD).mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ serverVariantSetId: 'VS123' });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.analysisMessage).toBe('API Error');
      expect(result.current.ldPairs).toEqual([]);
    });
  });

  describe('Client-Side Analysis', () => {
    beforeEach(() => {
      mockWasm.calculate_ld_pair.mockReturnValue({
        r2: 0.75,
        d_prime: 0.85,
      });
    });

    it('should validate synthetic preview availability', async () => {
      vi.stubGlobal('import', {
        meta: {
          env: {
            DEV: false, // Production mode
          },
        },
      });

      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ useServer: false });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.analysisMessage).toBe('Local synthetic LD preview is only available in development builds.');
    });

    it('should generate synthetic LD data in dev mode', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ 
          useServer: false,
          nSamples: 100,
          nMarkers: 10
        });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.ldPairs.length).toBeGreaterThan(0);
      expect(result.current.ldMatrix.length).toBe(10);
      expect(result.current.decayData.length).toBeGreaterThan(0);
      expect(result.current.hweTests.length).toBeGreaterThan(0);
    });

    it('should use WASM for LD calculation when available', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ 
          useServer: false,
          nSamples: 50,
          nMarkers: 5
        });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(mockWasm.calculate_ld_pair).toHaveBeenCalled();
    });

    it('should fallback to JS calculation when WASM fails', async () => {
      mockWasm.calculate_ld_pair.mockImplementation(() => {
        throw new Error('WASM error');
      });

      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ 
          useServer: false,
          nSamples: 50,
          nMarkers: 5
        });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      // Should still produce results using JS fallback
      expect(result.current.ldPairs.length).toBeGreaterThan(0);
    });

    it('should calculate HWE tests for client-side analysis', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ 
          useServer: false,
          nSamples: 100,
          nMarkers: 10
        });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.hweTests.length).toBeGreaterThan(0);
      expect(result.current.hweTests[0]).toHaveProperty('marker');
      expect(result.current.hweTests[0]).toHaveProperty('chiSquared');
      expect(result.current.hweTests[0]).toHaveProperty('pValue');
      expect(result.current.hweTests[0]).toHaveProperty('inEquilibrium');
    });

    it('should calculate decay curve for client-side analysis', async () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({ 
          useServer: false,
          nSamples: 100,
          nMarkers: 20
        });
      });

      await act(async () => {
        await result.current.runAnalysis();
      });

      expect(result.current.decayData.length).toBeGreaterThan(0);
      expect(result.current.decayData[0]).toHaveProperty('distance');
      expect(result.current.decayData[0]).toHaveProperty('mean_r2');
      expect(result.current.decayData[0]).toHaveProperty('pair_count');
    });
  });

  describe('Computed Properties', () => {
    it('should compute high LD pairs based on threshold', () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({
          ldThreshold: 0.5,
          ldPairs: [
            { marker1: 'M1', marker2: 'M2', distance: 10, r2: 0.85, dPrime: 0.92 },
            { marker1: 'M2', marker2: 'M3', distance: 20, r2: 0.45, dPrime: 0.67 },
            { marker1: 'M3', marker2: 'M4', distance: 30, r2: 0.65, dPrime: 0.81 },
          ],
        });
      });

      expect(result.current.highLDPairs).toHaveLength(2);
      expect(result.current.highLDPairs[0].r2).toBeGreaterThanOrEqual(0.5);
    });

    it('should compute HWE violations', () => {
      const { result } = renderHook(() => useLDAnalysis());

      act(() => {
        result.current.update({
          hweTests: [
            { marker: 'M1', chiSquared: 0.5, pValue: 0.78, observedHet: 0.48, expectedHet: 0.50, inEquilibrium: true },
            { marker: 'M2', chiSquared: 5.2, pValue: 0.02, observedHet: 0.35, expectedHet: 0.50, inEquilibrium: false },
            { marker: 'M3', chiSquared: 6.1, pValue: 0.01, observedHet: 0.30, expectedHet: 0.50, inEquilibrium: false },
          ],
        });
      });

      expect(result.current.hweViolations).toHaveLength(2);
      expect(result.current.hweViolations.every(t => !t.inEquilibrium)).toBe(true);
    });
  });
});

/**
 * LDAnalysisService Unit Tests
 * Tests API client integration for LD analysis endpoints
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LDAnalysisService } from './ldAnalysisService';
import { apiClient } from '@/lib/api-client';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('LDAnalysisService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('calculateLD', () => {
    const mockApiResponse = {
      pairs: [
        { marker1: 'M1', marker2: 'M2', distance: 10, r2: 0.85, d_prime: 0.92 },
        { marker1: 'M2', marker2: 'M3', distance: 20, r2: 0.65, d_prime: 0.81 },
        { marker1: 'M3', marker2: 'M4', distance: 30, r2: 0.45, d_prime: 0.67 },
      ],
      marker_count: 50,
      sample_count: 200,
      mean_r2: 0.65,
    };

    it('should call the calculate endpoint with correct parameters', async () => {
      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse);

      await LDAnalysisService.calculateLD('VS123', 50);

      expect(apiClient.post).toHaveBeenCalledWith('/api/v2/ld/calculate', {
        window_size: 50,
        variant_set_id: 'VS123',
      });
    });

    it('should use default window size if not provided', async () => {
      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse);

      await LDAnalysisService.calculateLD('VS123');

      expect(apiClient.post).toHaveBeenCalledWith('/api/v2/ld/calculate', {
        window_size: 50,
        variant_set_id: 'VS123',
      });
    });

    it('should transform API response to expected format', async () => {
      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse);

      const result = await LDAnalysisService.calculateLD('VS123');

      expect(result).toEqual({
        pairs: [
          { marker1: 'M1', marker2: 'M2', distance: 10, r2: 0.85, dPrime: 0.92 },
          { marker1: 'M2', marker2: 'M3', distance: 20, r2: 0.65, dPrime: 0.81 },
          { marker1: 'M3', marker2: 'M4', distance: 30, r2: 0.45, dPrime: 0.67 },
        ],
        markerCount: 50,
        sampleCount: 200,
        meanR2: 0.65,
      });
    });

    it('should calculate dPrime from r2 when not provided', async () => {
      const responseWithoutDPrime = {
        ...mockApiResponse,
        pairs: [
          { marker1: 'M1', marker2: 'M2', distance: 10, r2: 0.64 }, // sqrt(0.64) = 0.8
        ],
      };

      vi.mocked(apiClient.post).mockResolvedValue(responseWithoutDPrime);

      const result = await LDAnalysisService.calculateLD('VS123');

      expect(result.pairs[0].dPrime).toBe(0.8);
    });

    it('should handle empty pairs array', async () => {
      const emptyResponse = {
        pairs: [],
        marker_count: 0,
        sample_count: 0,
        mean_r2: 0,
      };

      vi.mocked(apiClient.post).mockResolvedValue(emptyResponse);

      const result = await LDAnalysisService.calculateLD('VS123');

      expect(result.pairs).toEqual([]);
      expect(result.markerCount).toBe(0);
      expect(result.sampleCount).toBe(0);
    });

    it('should propagate API errors', async () => {
      const error = new Error('API Error');
      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(LDAnalysisService.calculateLD('VS123')).rejects.toThrow('API Error');
    });
  });

  describe('fetchDecay', () => {
    const mockDecayResponse = {
      decay_curve: [
        { distance: 0, mean_r2: 0.85, pair_count: 10 },
        { distance: 1000, mean_r2: 0.65, pair_count: 15 },
        { distance: 2000, mean_r2: 0.45, pair_count: 20 },
      ],
    };

    it('should call the decay endpoint with correct parameters', async () => {
      vi.mocked(apiClient.post).mockResolvedValue(mockDecayResponse);

      await LDAnalysisService.fetchDecay('VS123', 100000, 1000);

      expect(apiClient.post).toHaveBeenCalledWith('/api/v2/ld/decay', {
        max_distance: 100000,
        bin_size: 1000,
        variant_set_id: 'VS123',
      });
    });

    it('should use default parameters if not provided', async () => {
      vi.mocked(apiClient.post).mockResolvedValue(mockDecayResponse);

      await LDAnalysisService.fetchDecay('VS123');

      expect(apiClient.post).toHaveBeenCalledWith('/api/v2/ld/decay', {
        max_distance: 100000,
        bin_size: 1000,
        variant_set_id: 'VS123',
      });
    });

    it('should return decay curve data', async () => {
      vi.mocked(apiClient.post).mockResolvedValue(mockDecayResponse);

      const result = await LDAnalysisService.fetchDecay('VS123');

      expect(result).toEqual(mockDecayResponse);
      expect(result.decay_curve).toHaveLength(3);
      expect(result.decay_curve[0]).toHaveProperty('distance');
      expect(result.decay_curve[0]).toHaveProperty('mean_r2');
      expect(result.decay_curve[0]).toHaveProperty('pair_count');
    });

    it('should handle empty decay curve', async () => {
      const emptyResponse = { decay_curve: [] };
      vi.mocked(apiClient.post).mockResolvedValue(emptyResponse);

      const result = await LDAnalysisService.fetchDecay('VS123');

      expect(result.decay_curve).toEqual([]);
    });

    it('should propagate API errors', async () => {
      const error = new Error('Decay fetch failed');
      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(LDAnalysisService.fetchDecay('VS123')).rejects.toThrow('Decay fetch failed');
    });
  });

  describe('fetchMatrix', () => {
    const mockMatrixResponse = {
      markers: ['M1', 'M2', 'M3'],
      matrix: [
        [1.0, 0.85, 0.65],
        [0.85, 1.0, 0.75],
        [0.65, 0.75, 1.0],
      ],
      region: 'region1',
    };

    it('should call the matrix endpoint with correct parameters', async () => {
      vi.mocked(apiClient.get).mockResolvedValue(mockMatrixResponse);

      await LDAnalysisService.fetchMatrix('VS123', 'chr1');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v2/ld/matrix/chr1?variant_set_id=VS123'
      );
    });

    it('should use default region if not provided', async () => {
      vi.mocked(apiClient.get).mockResolvedValue(mockMatrixResponse);

      await LDAnalysisService.fetchMatrix('VS123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v2/ld/matrix/region1?variant_set_id=VS123'
      );
    });

    it('should URL encode variant set ID', async () => {
      vi.mocked(apiClient.get).mockResolvedValue(mockMatrixResponse);

      await LDAnalysisService.fetchMatrix('VS 123 / Test', 'region1');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v2/ld/matrix/region1?variant_set_id=VS%20123%20%2F%20Test'
      );
    });

    it('should return matrix data', async () => {
      vi.mocked(apiClient.get).mockResolvedValue(mockMatrixResponse);

      const result = await LDAnalysisService.fetchMatrix('VS123');

      expect(result).toEqual(mockMatrixResponse);
      expect(result.markers).toHaveLength(3);
      expect(result.matrix).toHaveLength(3);
      expect(result.matrix[0]).toHaveLength(3);
    });

    it('should handle empty matrix', async () => {
      const emptyResponse = {
        markers: [],
        matrix: [],
        region: 'region1',
      };
      vi.mocked(apiClient.get).mockResolvedValue(emptyResponse);

      const result = await LDAnalysisService.fetchMatrix('VS123');

      expect(result.markers).toEqual([]);
      expect(result.matrix).toEqual([]);
    });

    it('should propagate API errors', async () => {
      const error = new Error('Matrix fetch failed');
      vi.mocked(apiClient.get).mockRejectedValue(error);

      await expect(LDAnalysisService.fetchMatrix('VS123')).rejects.toThrow('Matrix fetch failed');
    });
  });

  describe('Integration', () => {
    it('should handle network errors gracefully', async () => {
      const networkError = new Error('Network error');
      vi.mocked(apiClient.post).mockRejectedValue(networkError);

      await expect(LDAnalysisService.calculateLD('VS123')).rejects.toThrow('Network error');
    });

    it('should handle malformed responses', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        // Missing required fields
        pairs: null,
      });

      await expect(async () => {
        const result = await LDAnalysisService.calculateLD('VS123');
        // Should fail when trying to map over null
        result.pairs.map(p => p);
      }).rejects.toThrow();
    });

    it('should handle timeout errors', async () => {
      const timeoutError = new Error('Request timeout');
      vi.mocked(apiClient.post).mockRejectedValue(timeoutError);

      await expect(LDAnalysisService.calculateLD('VS123')).rejects.toThrow('Request timeout');
    });
  });
});

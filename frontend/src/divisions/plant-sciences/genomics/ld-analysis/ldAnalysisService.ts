/**
 * LD Analysis Service
 * API client for Linkage Disequilibrium analysis endpoints
 */

import { apiClient } from '@/lib/api-client';
import type { LDCalculateResponse, LDDecayResponse, LDMatrixResponse, MarkerPair } from './types';

export class LDAnalysisService {
  /**
   * Run server-side LD calculation for a variant set
   */
  static async calculateLD(variantSetId: string, windowSize = 50): Promise<{
    pairs: MarkerPair[];
    markerCount: number;
    sampleCount: number;
    meanR2: number;
  }> {
    const response = await apiClient.post('/api/v2/ld/calculate', {
      window_size: windowSize,
      variant_set_id: variantSetId,
    }) as unknown as LDCalculateResponse;

    const pairs: MarkerPair[] = response.pairs.map((p) => ({
      marker1: p.marker1,
      marker2: p.marker2,
      distance: p.distance,
      r2: p.r2,
      dPrime: p.d_prime || Math.sqrt(p.r2),
    }));

    return {
      pairs,
      markerCount: response.marker_count,
      sampleCount: response.sample_count,
      meanR2: response.mean_r2,
    };
  }

  /**
   * Fetch LD decay curve for a variant set
   */
  static async fetchDecay(variantSetId: string, maxDistance = 100000, binSize = 1000): Promise<LDDecayResponse> {
    return await apiClient.post('/api/v2/ld/decay', {
      max_distance: maxDistance,
      bin_size: binSize,
      variant_set_id: variantSetId,
    }) as unknown as LDDecayResponse;
  }

  /**
   * Fetch LD matrix for a genomic region
   */
  static async fetchMatrix(variantSetId: string, region = 'region1'): Promise<LDMatrixResponse> {
    return await apiClient.get(
      `/api/v2/ld/matrix/${region}?variant_set_id=${encodeURIComponent(variantSetId)}`
    ) as unknown as LDMatrixResponse;
  }
}

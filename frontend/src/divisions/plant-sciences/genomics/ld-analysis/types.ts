/**
 * LD Analysis Types
 * Shared interfaces for Linkage Disequilibrium analysis workflows
 */

export interface MarkerPair {
  marker1: string;
  marker2: string;
  distance: number;
  r2: number;
  dPrime: number;
}

export interface HWETest {
  marker: string;
  chiSquared: number;
  pValue: number;
  observedHet: number;
  expectedHet: number;
  inEquilibrium: boolean;
}

export interface LDDecayPoint {
  distance: number;
  mean_r2: number;
  pair_count: number;
}

export interface LDCalculateResponse {
  pairs: Array<{
    marker1: string;
    marker2: string;
    distance: number;
    r2: number;
    d_prime?: number;
  }>;
  marker_count: number;
  sample_count: number;
  mean_r2: number;
}

export interface LDDecayResponse {
  decay_curve: LDDecayPoint[];
}

export interface LDMatrixResponse {
  markers: string[];
  matrix: number[][];
  region: string;
}

export interface LDAnalysisState {
  isProcessing: boolean;
  useServer: boolean;
  serverVariantSetId: string;
  analysisMessage: string | null;
  nSamples: number;
  nMarkers: number;
  ldThreshold: number;
  ldPairs: MarkerPair[];
  hweTests: HWETest[];
  ldMatrix: number[][];
  decayData: LDDecayPoint[];
}

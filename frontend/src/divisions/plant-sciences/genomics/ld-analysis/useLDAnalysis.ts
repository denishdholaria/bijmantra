/**
 * useLDAnalysis Hook
 * State management and orchestration for LD Analysis workflows
 */

import { useState, useCallback } from 'react';
import { useWasm } from '@/wasm/hooks';
import { LDAnalysisService } from './ldAnalysisService';
import type { MarkerPair, HWETest, LDDecayPoint, LDAnalysisState } from './types';

function generateLDData(nSamples: number, nMarkers: number) {
  const genotypes: number[][] = [];
  const marker0: number[] = [];
  for (let i = 0; i < nSamples; i++) {
    const r = Math.random();
    marker0.push(r < 0.25 ? 0 : r < 0.75 ? 1 : 2);
  }
  genotypes.push(marker0);

  for (let m = 1; m < nMarkers; m++) {
    const marker: number[] = [];
    const ldStrength = Math.exp(-m * 0.1);
    for (let i = 0; i < nSamples; i++) {
      if (Math.random() < ldStrength) {
        marker.push(genotypes[m - 1][i]);
      } else {
        const r = Math.random();
        marker.push(r < 0.25 ? 0 : r < 0.75 ? 1 : 2);
      }
    }
    genotypes.push(marker);
  }
  return genotypes;
}

export function useLDAnalysis() {
  const { isReady, version, wasm } = useWasm();
  const syntheticPreviewAvailable = import.meta.env.DEV;

  const [state, setState] = useState<LDAnalysisState>({
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
  });

  const update = useCallback((partial: Partial<LDAnalysisState>) => {
    setState((prev) => ({ ...prev, ...partial }));
  }, []);

  const runAnalysis = useCallback(async () => {
    update({ isProcessing: true, analysisMessage: null });
    try {
      if (state.useServer) {
        const variantSetId = state.serverVariantSetId.trim();
        if (!variantSetId) {
          update({ isProcessing: false, analysisMessage: 'Enter a variant set ID to run server-side LD analysis.' });
          return;
        }

        const result = await LDAnalysisService.calculateLD(variantSetId);
        update({
          ldPairs: result.pairs,
          nMarkers: result.markerCount,
          nSamples: result.sampleCount,
        });

        try {
          const decayRes = await LDAnalysisService.fetchDecay(variantSetId);
          update({ decayData: decayRes.decay_curve });
        } catch {
          update({ decayData: [] });
        }

        try {
          const matrixRes = await LDAnalysisService.fetchMatrix(variantSetId);
          update({ ldMatrix: matrixRes.matrix });
        } catch {
          update({ ldMatrix: [] });
        }

        update({ hweTests: [] });
        if (result.sampleCount < 1 || result.pairs.length === 0) {
          update({ analysisMessage: 'No usable genotype calls were available for this variant set.' });
        }
      } else {
        if (!syntheticPreviewAvailable) {
          update({ isProcessing: false, analysisMessage: 'Local synthetic LD preview is only available in development builds.' });
          return;
        }

        const genotypes = generateLDData(state.nSamples, state.nMarkers);
        const pairs: MarkerPair[] = [];
        const matrix: number[][] = Array(state.nMarkers).fill(null).map(() => Array(state.nMarkers).fill(0));

        for (let i = 0; i < state.nMarkers; i++) {
          matrix[i][i] = 1.0;
          for (let j = i + 1; j < Math.min(i + 10, state.nMarkers); j++) {
            let r2 = 0;
            let dPrime = 0;
            let calculated = false;

            if (isReady && wasm) {
              try {
                const g1 = new Int32Array(genotypes[i]);
                const g2 = new Int32Array(genotypes[j]);
                const res = wasm.calculate_ld_pair(g1, g2);
                const result = res as unknown as { r2: number; d_prime: number };
                if (typeof result.r2 === 'number') {
                  r2 = result.r2;
                  dPrime = result.d_prime;
                  calculated = true;
                }
              } catch {
                // WASM failed, fallback to JS
              }
            }

            if (!calculated) {
              const g1 = genotypes[i];
              const g2 = genotypes[j];
              let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
              for (let k = 0; k < state.nSamples; k++) {
                sumX += g1[k]; sumY += g2[k]; sumXY += g1[k] * g2[k];
                sumX2 += g1[k] * g1[k]; sumY2 += g2[k] * g2[k];
              }
              const n = state.nSamples;
              const varX = sumX2 / n - (sumX / n) ** 2;
              const varY = sumY2 / n - (sumY / n) ** 2;
              const covXY = sumXY / n - (sumX / n) * (sumY / n);
              r2 = varX > 0 && varY > 0 ? (covXY ** 2) / (varX * varY) : 0;
              dPrime = Math.sqrt(r2);
            }

            matrix[i][j] = r2;
            matrix[j][i] = r2;
            pairs.push({ marker1: `M${i + 1}`, marker2: `M${j + 1}`, distance: (j - i) * 10, r2, dPrime });
          }
        }

        update({ ldPairs: pairs.sort((a, b) => b.r2 - a.r2), ldMatrix: matrix });

        // Client-side decay data
        const bins: Record<number, { sum: number; count: number }> = {};
        pairs.forEach((p) => {
          const bin = Math.floor(p.distance / 10) * 10;
          if (!bins[bin]) bins[bin] = { sum: 0, count: 0 };
          bins[bin].sum += p.r2;
          bins[bin].count++;
        });
        const clientDecay = Object.keys(bins)
          .sort((a, b) => Number(a) - Number(b))
          .map((d) => ({
            distance: Number(d),
            mean_r2: bins[Number(d)].sum / bins[Number(d)].count,
            pair_count: bins[Number(d)].count,
          }));
        update({ decayData: clientDecay });

        // HWE Analysis
        const tests: HWETest[] = [];
        for (let m = 0; m < Math.min(state.nMarkers, 20); m++) {
          const geno = genotypes[m];
          let nAA = 0, nAB = 0, nBB = 0;
          for (const g of geno) { if (g === 0) nAA++; else if (g === 1) nAB++; else nBB++; }
          const n = nAA + nAB + nBB;
          const p = (2 * nAA + nAB) / (2 * n);
          const q = 1 - p;
          const expAA = p * p * n; const expAB = 2 * p * q * n; const expBB = q * q * n;
          const chi2 = (expAA > 0 ? (nAA - expAA) ** 2 / expAA : 0) +
                       (expAB > 0 ? (nAB - expAB) ** 2 / expAB : 0) +
                       (expBB > 0 ? (nBB - expBB) ** 2 / expBB : 0);
          const pValue = Math.exp(-chi2 / 2);
          tests.push({
            marker: `M${m + 1}`, chiSquared: chi2, pValue,
            observedHet: nAB / n, expectedHet: 2 * p * q,
            inEquilibrium: pValue > 0.05,
          });
        }
        update({ hweTests: tests });
      }
    } catch (e) {
      update({
        ldPairs: [], ldMatrix: [], decayData: [], hweTests: [],
        analysisMessage: e instanceof Error ? e.message : 'LD analysis failed.',
      });
    } finally {
      update({ isProcessing: false });
    }
  }, [state.useServer, state.serverVariantSetId, state.nSamples, state.nMarkers, isReady, wasm, syntheticPreviewAvailable, update]);

  const highLDPairs = state.ldPairs.filter((p) => p.r2 >= state.ldThreshold);
  const hweViolations = state.hweTests.filter((t) => !t.inEquilibrium);

  return {
    ...state,
    update,
    runAnalysis,
    highLDPairs,
    hweViolations,
    wasmReady: isReady,
    wasmVersion: version,
    syntheticPreviewAvailable,
  };
}

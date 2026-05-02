// React hooks for Bijmantra Genomics WASM module

import { useState, useEffect, useCallback } from 'react';
import { initWasm, getWasm } from './index';
import type {
  GRMResult,
  BLUPResult,
  GBLUPResult,
  DiversityMetrics,
  PCAResult,
  FstResult,
  HeritabilityResult,
  SelectionIndexResult,
  LDResult,
  HWEResult,
  AMMIResult,
} from './types';

/**
 * Hook to initialize and access WASM module
 */
export function useWasm() {
  const [isLoading, setIsLoading] = useState(true);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [version, setVersion] = useState<string>('');

  useEffect(() => {
    initWasm()
      .then((wasm) => {
        setIsReady(wasm.is_wasm_ready());
        setVersion(wasm.get_version());
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err);
        setIsLoading(false);
      });
  }, []);

  return { isLoading, isReady, error, version, wasm: getWasm() };
}

/**
 * Hook for calculating Genomic Relationship Matrix
 */
export function useGRM() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<GRMResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (genotypes: number[], nSamples: number, nMarkers: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const genoArray = new Int32Array(genotypes);
        const grm = wasm.calculate_grm(genoArray, nSamples, nMarkers);
        setResult(grm);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for BLUP estimation
 */
export function useBLUP() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<BLUPResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (phenotypes: number[], relationshipMatrix: number[], nIndividuals: number, heritability: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const phenoArray = new Float64Array(phenotypes);
        const relArray = new Float64Array(relationshipMatrix);
        const blup = wasm.estimate_blup(phenoArray, relArray, nIndividuals, heritability);
        setResult(blup);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for GBLUP estimation
 */
export function useGBLUP() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<GBLUPResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (phenotypes: number[], grm: number[], nIndividuals: number, heritability: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const phenoArray = new Float64Array(phenotypes);
        const grmArray = new Float64Array(grm);
        const gblup = wasm.estimate_gblup(phenoArray, grmArray, nIndividuals, heritability);
        setResult(gblup);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for genetic diversity calculation
 */
export function useDiversity() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<DiversityMetrics | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (genotypes: number[], nSamples: number, nMarkers: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const genoArray = new Int32Array(genotypes);
        const diversity = wasm.calculate_diversity(genoArray, nSamples, nMarkers);
        setResult(diversity);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for PCA calculation
 */
export function usePCA() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<PCAResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (genotypes: number[], nSamples: number, nMarkers: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const genoArray = new Int32Array(genotypes);
        const pca = wasm.calculate_pca(genoArray, nSamples, nMarkers);
        setResult(pca);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for Fst calculation
 */
export function useFst() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<FstResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (genotypes: number[], populationIds: number[], nSamples: number, nMarkers: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const genoArray = new Int32Array(genotypes);
        const popArray = new Int32Array(populationIds);
        const fst = wasm.calculate_fst(genoArray, popArray, nSamples, nMarkers);
        setResult(fst);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for heritability estimation
 */
export function useHeritability() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<HeritabilityResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (phenotypes: number[], grm: number[], nIndividuals: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const phenoArray = new Float64Array(phenotypes);
        const grmArray = new Float64Array(grm);
        const h2 = wasm.estimate_heritability(phenoArray, grmArray, nIndividuals);
        setResult(h2);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for selection index calculation
 */
export function useSelectionIndex() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<SelectionIndexResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (traitValues: number[], economicWeights: number[], nIndividuals: number, nTraits: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const traitArray = new Float64Array(traitValues);
        const weightArray = new Float64Array(economicWeights);
        const index = wasm.calculate_selection_index(traitArray, weightArray, nIndividuals, nTraits);
        setResult(index);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for LD calculation
 */
export function useLD() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<LDResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (geno1: number[], geno2: number[]) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const g1 = new Int32Array(geno1);
        const g2 = new Int32Array(geno2);
        const ld = wasm.calculate_ld_pair(g1, g2);
        setResult(ld);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for HWE test
 */
export function useHWE() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<HWEResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (genotypes: number[]) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const genoArray = new Int32Array(genotypes);
        const hwe = wasm.test_hwe(genoArray);
        setResult(hwe);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

/**
 * Hook for AMMI analysis
 */
export function useAMMI() {
  const { wasm, isReady } = useWasm();
  const [result, setResult] = useState<AMMIResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const calculate = useCallback(
    (phenotypes: number[], nGenotypes: number, nEnvironments: number) => {
      if (!wasm || !isReady) {
        setError(new Error('WASM not ready'));
        return;
      }

      setIsCalculating(true);
      setError(null);

      try {
        const phenoArray = new Float64Array(phenotypes);
        const ammi = wasm.calculate_ammi(phenoArray, nGenotypes, nEnvironments);
        setResult(ammi);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsCalculating(false);
      }
    },
    [wasm, isReady]
  );

  return { calculate, result, isCalculating, error };
}

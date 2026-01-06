// Bijmantra Genomics WASM Module Loader
// High-performance genomic computations using Rust/WebAssembly

import type { BijmantraGenomicsWasm } from './types';

let wasmModule: BijmantraGenomicsWasm | null = null;
let initPromise: Promise<BijmantraGenomicsWasm> | null = null;

/**
 * Initialize the WASM module
 * Call this once at app startup or before first use
 */
export async function initWasm(): Promise<BijmantraGenomicsWasm> {
  if (wasmModule) {
    return wasmModule;
  }

  if (initPromise) {
    return initPromise;
  }

  initPromise = (async () => {
    try {
      // Dynamic import of WASM module
      const wasm = await import('./pkg/bijmantra_genomics');
      await wasm.default();
      
      wasmModule = wasm as unknown as BijmantraGenomicsWasm;
      console.log('🦀 Bijmantra Genomics WASM loaded, version:', wasm.get_version());
      
      return wasmModule;
    } catch (error) {
      console.warn('⚠️ WASM module not available, using JavaScript fallback');
      // Return a mock module that throws helpful errors
      return createFallbackModule();
    }
  })();

  return initPromise;
}

/**
 * Get the WASM module (must call initWasm first)
 */
export function getWasm(): BijmantraGenomicsWasm | null {
  return wasmModule;
}

/**
 * Check if WASM is available and loaded
 */
export function isWasmReady(): boolean {
  return wasmModule !== null && wasmModule.is_wasm_ready();
}

/**
 * Create a fallback module for when WASM is not available
 */
function createFallbackModule(): BijmantraGenomicsWasm {
  const notAvailable = () => {
    throw new Error('WASM module not available. Build with: cd rust && ./build.sh');
  };

  return {
    get_version: () => 'fallback-0.0.0',
    is_wasm_ready: () => false,
    calculate_allele_frequencies: notAvailable,
    calculate_ld_pair: notAvailable,
    calculate_ld_matrix: notAvailable,
    test_hwe: notAvailable,
    filter_by_maf: notAvailable,
    impute_missing_mean: notAvailable,
    calculate_grm: notAvailable,
    calculate_a_matrix: notAvailable,
    calculate_kinship: notAvailable,
    calculate_ibs_matrix: notAvailable,
    calculate_eigenvalues: notAvailable,
    estimate_blup: notAvailable,
    estimate_gblup: notAvailable,
    calculate_selection_index: notAvailable,
    calculate_genetic_correlations: notAvailable,
    estimate_heritability: notAvailable,
    calculate_diversity: notAvailable,
    calculate_fst: notAvailable,
    calculate_genetic_distance: notAvailable,
    calculate_pca: notAvailable,
    calculate_ammi: notAvailable,
  };
}

// Re-export types
export * from './types';

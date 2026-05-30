// Bijmantra Genomics WASM Module Loader
// High-performance genomic computations using Rust/WebAssembly

import { loadWasmModule } from './loader';
import type { BijmantraGenomicsWasm } from './types';

let wasmModule: BijmantraGenomicsWasm | null = null;
let initPromise: Promise<BijmantraGenomicsWasm> | null = null;
let wasmLoadError: Error | null = null;

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
      const wasm = await loadWasmModule();
      await wasm.default();
      
      wasmModule = wasm as unknown as BijmantraGenomicsWasm;
      console.log('🦀 Bijmantra Genomics WASM loaded, version:', wasm.get_version());
      
      return wasmModule;
    } catch (err) {
      // Log the real error BEFORE falling back, so it appears in DevTools
      console.error('⚠️ WASM module failed to load:', err);
      console.warn('⚠️ WASM module not available, using JavaScript fallback — run `make wasm` to rebuild');
      // Store the error so useWasm() can expose it to the UI
      wasmLoadError = err instanceof Error ? err : new Error(String(err));
      // Cache the fallback so getWasm() returns it and subsequent calls skip re-loading
      wasmModule = createFallbackModule();
      return wasmModule;
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
 * Get the WASM load error, if any (set when initWasm() falls back to the fallback module)
 */
export function getWasmLoadError(): Error | null {
  return wasmLoadError;
}

/**
 * Create a fallback module for when WASM is not available
 */
function createFallbackModule(): BijmantraGenomicsWasm {
  const notAvailable = () => {
    throw new Error('WASM module not available. Run `make wasm` in the project root to rebuild.');
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
    needleman_wunsch: notAvailable,
    smith_waterman: notAvailable,
    search_motif: notAvailable,
    calculate_grm: notAvailable,
    calculate_a_matrix: notAvailable,
    calculate_kinship: notAvailable,
    calculate_ibs_matrix: notAvailable,
    calculate_g_matrix: notAvailable,
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

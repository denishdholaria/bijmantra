import { initWasm } from '@/wasm';
import type { BijmantraGenomicsWasm } from '@/wasm/types';

export class GenomicsEngine {
  private wasmModule: BijmantraGenomicsWasm | null = null;
  private initPromise: Promise<BijmantraGenomicsWasm> | null = null;

  async initialize(): Promise<BijmantraGenomicsWasm> {
    if (this.wasmModule) {
      return this.wasmModule;
    }

    if (!this.initPromise) {
      this.initPromise = initWasm();
    }

    this.wasmModule = await this.initPromise;
    return this.wasmModule;
  }

  calculateGMatrix(markers: Uint8Array, nMarkers: number, nIndividuals: number): Float32Array {
    if (!this.wasmModule) {
      throw new Error('GenomicsEngine not initialized. Call initialize() first.');
    }

    return this.wasmModule.calculate_g_matrix(markers, nMarkers, nIndividuals);
  }
}

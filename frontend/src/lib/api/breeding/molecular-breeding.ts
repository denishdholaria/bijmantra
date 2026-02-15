import { ApiClientCore } from "../core/client";

export class MolecularBreedingService {
  constructor(private client: ApiClientCore) {}

  async getHaplotypeBlocks(chromosome?: string) {
    const query = chromosome ? `?chromosome=${chromosome}` : "";
    return this.client.get<{ data: any[] }>(
      `/api/v2/molecular-breeding/haplotypes/blocks${query}`
    );
  }

  async getBlockHaplotypes(blockId: string) {
    return this.client.get<{ data: any[] }>(
      `/api/v2/molecular-breeding/haplotypes/blocks/${blockId}`
    );
  }

  async getHaplotypeDiversity() {
    return this.client.get<{ data: any }>(
      "/api/v2/molecular-breeding/haplotypes/diversity"
    );
  }

  async getHaplotypeStatistics() {
    return this.client.get<{ data: any }>(
      "/api/v2/molecular-breeding/haplotypes/statistics"
    );
  }

  /**
   * Calculate LD from genotype data.
   * POST /api/v2/gwas/ld
   */
  async calculateLD(data: {
    genotypes: number[][];
    positions: number[];
    chromosome?: string;
  }) {
    return this.client.post<{ data: any }>("/api/v2/gwas/ld", data);
  }

  /**
   * LD-based pruning.
   * POST /api/v2/gwas/ld/pruning
   */
  async ldPruning(data: {
    genotypes: number[][];
    positions: number[];
    r2_threshold?: number;
    window_size?: number;
  }) {
    return this.client.post<{ data: any }>("/api/v2/gwas/ld/pruning", data);
  }

  /**
   * @deprecated - Use calculateLD() instead. Kept for backward-compat during migration.
   */
  async getLDDemoData() {
    console.warn("[DEPRECATED] getLDDemoData() calls deleted endpoint. Use calculateLD().");
    return { data: null };
  }

  async getSchemes() {
    return this.client.get<{ data: any[] }>(
      "/api/v2/molecular-breeding/schemes"
    );
  }

  async getLines() {
    return this.client.get<{ data: any[] }>(
      "/api/v2/molecular-breeding/lines"
    );
  }

  async getStatistics() {
    return this.client.get<{ data: any }>(
      "/api/v2/molecular-breeding/statistics"
    );
  }
}

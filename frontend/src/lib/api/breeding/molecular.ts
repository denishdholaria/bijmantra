import { ApiClientCore } from "../core/client";

export interface LDPair {
  marker1: string;
  marker2: string;
  chromosome: string;
  distance: number;
  r2: number;
  dprime: number;
}

export interface LDDecayPoint {
  distance: number;
  mean_r2: number;
  n_pairs: number;
}

export interface LDChromosomeStat {
  chromosome: string;
  mean_r2: number;
  n_pairs: number;
}

export interface LDData {
  n_markers: number;
  n_pairs: number;
  n_high_ld: number;
  mean_r2: number;
  ld_decay_distance: number;
  pairs: LDPair[];
  decay_curve: LDDecayPoint[];
  chromosome_stats: LDChromosomeStat[];
}

export class MolecularBreedingService {
  constructor(private client: ApiClientCore) {}

  // ============================================
  // MOLECULAR BREEDING SCHEMES
  // ============================================

  async getSchemes(params?: { scheme_type?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.scheme_type)
      searchParams.append("scheme_type", params.scheme_type);
    if (params?.status) searchParams.append("status", params.status);
    return this.client.get<any>(
      `/api/v2/molecular-breeding/schemes?${searchParams}`
    );
  }

  async getScheme(schemeId: string) {
    return this.client.get<any>(`/api/v2/molecular-breeding/schemes/${schemeId}`);
  }

  async getLines(params?: {
    scheme_id?: string;
    foreground_status?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.scheme_id) searchParams.append("scheme_id", params.scheme_id);
    if (params?.foreground_status)
      searchParams.append("foreground_status", params.foreground_status);
    return this.client.get<any>(
      `/api/v2/molecular-breeding/lines?${searchParams}`
    );
  }

  async getStatistics() {
    return this.client.get<any>("/api/v2/molecular-breeding/statistics");
  }

  async getPyramiding(schemeId: string) {
    return this.client.get<any>(
      `/api/v2/molecular-breeding/pyramiding/${schemeId}`
    );
  }

  // ============================================
  // HAPLOTYPE ANALYSIS
  // ============================================

  async getHaplotypeBlocks(chromosome?: string, minLength?: number) {
    const params = new URLSearchParams();
    if (chromosome) params.append("chromosome", chromosome);
    if (minLength) params.append("min_length", String(minLength));
    return this.client.get<any>(`/api/v2/haplotype/blocks?${params}`);
  }

  async getHaplotypeBlock(blockId: string) {
    return this.client.get<any>(`/api/v2/haplotype/blocks/${blockId}`);
  }

  async getBlockHaplotypes(blockId: string) {
    return this.client.get<any>(
      `/api/v2/haplotype/blocks/${blockId}/haplotypes`
    );
  }

  async getHaplotypeAssociations(trait?: string, chromosome?: string) {
    const params = new URLSearchParams();
    if (trait) params.append("trait", trait);
    if (chromosome) params.append("chromosome", chromosome);
    return this.client.get<any>(`/api/v2/haplotype/associations?${params}`);
  }

  async getFavorableHaplotypes(trait?: string) {
    const params = trait ? `?trait=${encodeURIComponent(trait)}` : "";
    return this.client.get<any>(`/api/v2/haplotype/favorable${params}`);
  }

  async getHaplotypeDiversity() {
    return this.client.get<any>("/api/v2/haplotype/diversity");
  }

  async getHaplotypeStatistics() {
    return this.client.get<any>("/api/v2/haplotype/statistics");
  }

  async getHaplotypeTraits() {
    return this.client.get<any>("/api/v2/haplotype/traits");
  }

  // ============================================
  // LINKAGE DISEQUILIBRIUM (LD)
  // ============================================



  async getLDDemoData() {
    return this.client.get<any>("/api/v2/gwas/ld/demo");
  }

  async calculateLD(data: {
    genotypes: number[][];
    positions: number[];
    chromosome?: string;
  }) {
    return this.client.post<any>("/api/v2/gwas/ld", data);
  }

  async ldPruning(data: {
    genotypes: number[][];
    positions: number[];
    r2_threshold?: number;
    window_size?: number;
  }) {
    return this.client.post<any>("/api/v2/gwas/ld/pruning", data);
  }
}

import { ApiClientCore } from "../core/client";

export interface Population {
  id: string;
  name: string;
  size: number;
  region: string;
  crop?: string;
  admixture?: number[];
}

export interface StructureAnalysis {
  populations: Array<{
    population_id: string;
    population_name: string;
    sample_size: number;
    proportions: Array<{ cluster: number; proportion: number }>;
  }>;
  delta_k_analysis: Array<{ k: number; delta_k: number }>;
  optimal_k: number;
}

export interface PCAResult {
  samples: Array<{
    sample_id: string;
    population_name: string;
    pc1: number;
    pc2: number;
    pc3?: number;
  }>;
  variance_explained: Array<{
    pc: string;
    variance: number;
    cumulative?: number;
  }>;
}

export interface FstAnalysis {
  pairwise: Array<{
    population1_name: string;
    population2_name: string;
    fst: number;
    differentiation: string;
    nm: number;
  }>;
  global_statistics: {
    global_fst: string;
    mean_he: string;
    mean_ho: string;
    mean_fis: string;
  };
  interpretation: {
    fst_ranges: Array<{ range: string; level: string }>;
  };
}

export interface MigrationAnalysis {
  migrations: Array<{
    from_population_name: string;
    to_population_name: string;
    nm: number;
    gene_flow: string;
  }>;
  interpretation: { description: string };
}

export interface PopulationSummary {
  total_populations: number;
  total_samples: number;
  mean_expected_heterozygosity: number;
  global_fst: number;
  mean_allelic_richness: number;
}

export class PopulationGeneticsService {
  constructor(private client: ApiClientCore) {}

  async getPopulations(
    crop?: string,
    region?: string,
  ): Promise<{ populations: Population[] }> {
    const params = new URLSearchParams();
    if (crop) params.append("crop", crop);
    if (region) params.append("region", region);
    const query = params.toString() ? `?${params}` : "";
    return this.client.request<{ populations: Population[] }>(
      `/api/v2/population-genetics/populations${query}`
    );
  }

  async getPopulation(populationId: string): Promise<Population> {
    return this.client.request<Population>(
      `/api/v2/population-genetics/populations/${populationId}`
    );
  }

  async getStructure(
    k: number = 3,
    populationIds?: string[],
  ): Promise<StructureAnalysis> {
    const params = new URLSearchParams({ k: String(k) });
    if (populationIds?.length)
      params.append("population_ids", populationIds.join(","));
    return this.client.request<StructureAnalysis>(
      `/api/v2/population-genetics/structure?${params}`
    );
  }

  async getPCA(populationIds?: string[]): Promise<PCAResult> {
    const params = populationIds?.length
      ? `?population_ids=${populationIds.join(",")}`
      : "";
    return this.client.request<PCAResult>(
      `/api/v2/population-genetics/pca${params}`
    );
  }

  async getFst(populationIds?: string[]): Promise<FstAnalysis> {
    const params = populationIds?.length
      ? `?population_ids=${populationIds.join(",")}`
      : "";
    return this.client.request<FstAnalysis>(
      `/api/v2/population-genetics/fst${params}`
    );
  }

  async getMigration(populationIds?: string[]): Promise<MigrationAnalysis> {
    const params = populationIds?.length
      ? `?population_ids=${populationIds.join(",")}`
      : "";
    return this.client.request<MigrationAnalysis>(
      `/api/v2/population-genetics/migration${params}`
    );
  }

  async getSummary(): Promise<PopulationSummary> {
    return this.client.request<PopulationSummary>(
      "/api/v2/population-genetics/summary"
    );
  }

  async getHardyWeinberg(populationId: string): Promise<any> {
    return this.client.request<any>(
      `/api/v2/population-genetics/hardy-weinberg/${populationId}`
    );
  }
}

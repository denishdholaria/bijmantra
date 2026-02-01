import { ApiClientCore } from "../core/client";

export interface StressType {
  stress_id: string;
  name: string;
  category: string;
  description: string;
}

export interface ToleranceGene {
  gene_id: string;
  name: string;
  stress_id: string;
  mechanism: string;
  crop: string;
  chromosome?: string;
  markers?: string[];
}

export interface StressIndices {
  SSI: number;
  STI: number;
  YSI: number;
  GMP: number;
  MP: number;
  TOL: number;
  HM: number;
}

export class AbioticStressService {
  constructor(private client: ApiClientCore) {}
  async getStressTypes(params?: {
    category?: string;
    search?: string;
  }): Promise<{ data: StressType[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set("category", params.category);
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    return this.client.get<{ data: StressType[]; total: number }>(
      `/api/v2/abiotic/stress-types${query ? `?${query}` : ""}`
    );
  }

  async getStressType(stressId: string): Promise<StressType> {
    return this.client.get<StressType>(`/api/v2/abiotic/stress-types/${stressId}`);
  }

  async getGenes(params?: {
    stress_id?: string;
    crop?: string;
    search?: string;
  }): Promise<{ data: ToleranceGene[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.stress_id) searchParams.set("stress_id", params.stress_id);
    if (params?.crop) searchParams.set("crop", params.crop);
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    return this.client.get<{ data: ToleranceGene[]; total: number }>(
      `/api/v2/abiotic/genes${query ? `?${query}` : ""}`
    );
  }

  async getGene(geneId: string): Promise<ToleranceGene> {
    return this.client.get<ToleranceGene>(`/api/v2/abiotic/genes/${geneId}`);
  }

  async getCategories(): Promise<{ categories: string[] }> {
    return this.client.get<{ categories: string[] }>("/api/v2/abiotic/categories");
  }

  async getCrops(): Promise<{ crops: string[] }> {
    return this.client.get<{ crops: string[] }>("/api/v2/abiotic/crops");
  }

  async getStatistics(): Promise<{
    totalStressTypes: number;
    totalGenes: number;
    totalCategories: number;
    masReadyGenes: number;
    stressesByCategory: Record<string, number>;
    genesByStress: Record<string, number>;
  }> {
    return this.client.get<{
      totalStressTypes: number;
      totalGenes: number;
      totalCategories: number;
      masReadyGenes: number;
      stressesByCategory: Record<string, number>;
      genesByStress: Record<string, number>;
    }>("/api/v2/abiotic/statistics");
  }

  async calculateIndices(
    controlYield: number,
    stressYield: number,
  ): Promise<{
    data: {
      indices: StressIndices;
      interpretation: Record<string, string>;
      recommendation: string;
    };
  }> {
    return this.client.post<{
      data: {
        indices: StressIndices;
        interpretation: Record<string, string>;
        recommendation: string;
      };
    }>("/api/v2/abiotic/calculate/indices", {
      control_yield: controlYield,
      stress_yield: stressYield,
    });
  }

  async getScreeningProtocols(): Promise<{
    protocols: Array<{
      stress: string;
      method: string;
      stages: string[];
      duration: string;
      indicators: string[];
    }>;
  }> {
    return this.client.get<{
      protocols: Array<{
        stress: string;
        method: string;
        stages: string[];
        duration: string;
        indicators: string[];
      }>;
    }>("/api/v2/abiotic/screening-protocols");
  }
}

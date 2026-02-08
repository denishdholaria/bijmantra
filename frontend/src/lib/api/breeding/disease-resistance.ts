import { ApiClientCore } from "../core/client";

export interface Disease {
  id: string;
  name: string;
  pathogen: string;
  pathogen_type: string;
  crop: string;
  symptoms: string;
  severity_scale: string[];
}

export interface ResistanceGene {
  id: string;
  gene_name: string;
  disease_id: string;
  disease_name?: string;
  chromosome?: string;
  resistance_type: string;
  source_germplasm?: string;
  markers?: string[];
}

export interface PyramidingStrategy {
  id: string;
  name: string;
  disease: string;
  genes: string[];
  description: string;
  status: string;
  warning?: string;
}

export class DiseaseResistanceService {
  constructor(private client: ApiClientCore) {}
  async getDiseases(params?: {
    crop?: string;
    pathogen_type?: string;
    search?: string;
  }): Promise<{ diseases: Disease[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.set("crop", params.crop);
    if (params?.pathogen_type)
      searchParams.set("pathogen_type", params.pathogen_type);
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    return this.client.get<{ diseases: Disease[]; total: number }>(`/api/v2/disease/diseases${query ? `?${query}` : ""}`);
  }

  async getDisease(id: string) {
    return this.client.get<{ data: Disease }>(`/api/v2/disease/${id}`);
  }

  async getGenes(params?: {
    disease_id?: string;
    resistance_type?: string;
    search?: string;
  }): Promise<{ genes: ResistanceGene[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.disease_id) searchParams.set("disease_id", params.disease_id);
    if (params?.resistance_type)
      searchParams.set("resistance_type", params.resistance_type);
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    return this.client.get<{ genes: ResistanceGene[]; total: number }>(
      `/api/v2/disease/genes${query ? `?${query}` : ""}`
    );
  }

  async getGene(geneId: string): Promise<ResistanceGene> {
    return this.client.get<ResistanceGene>(`/api/v2/disease/genes/${geneId}`);
  }

  async getCrops(): Promise<{ crops: string[] }> {
    return this.client.get<{ crops: string[] }>("/api/v2/disease/crops");
  }

  async getPathogenTypes(): Promise<{ pathogenTypes: string[] }> {
    return this.client.get<{ pathogenTypes: string[] }>("/api/v2/disease/pathogen-types");
  }

  async getResistanceTypes(): Promise<{ resistanceTypes: string[] }> {
    return this.client.get<{ resistanceTypes: string[] }>("/api/v2/disease/resistance-types");
  }

  async getStatistics(): Promise<{
    totalDiseases: number;
    totalGenes: number;
    totalCrops: number;
    masReadyGenes: number;
    diseasesByCrop: Record<string, number>;
    genesByResistanceType: Record<string, number>;
  }> {
    return this.client.get<{
      totalDiseases: number;
      totalGenes: number;
      totalCrops: number;
      masReadyGenes: number;
      diseasesByCrop: Record<string, number>;
      genesByResistanceType: Record<string, number>;
    }>("/api/v2/disease/statistics");
  }

  async getPyramidingStrategies(): Promise<{
    strategies: PyramidingStrategy[];
  }> {
    return this.client.get<{ strategies: PyramidingStrategy[] }>(
      "/api/v2/disease/pyramiding-strategies"
    );
  }
}

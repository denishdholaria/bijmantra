import { ApiClientCore } from "../core/client";

export interface BreedingValueIndividual {
  id: string;
  name: string;
  ebv: number;
  accuracy: number;
  rank?: number;
}

export interface BLUPResult {
  individuals: BreedingValueIndividual[];
  heritability: number;
  genetic_variance: number;
  residual_variance: number;
  mean: number;
}

export interface CrossPredictionResult {
  parent1: string;
  parent2: string;
  predicted_mean: number;
  predicted_variance: number;
  probability_superior: number;
}

export interface BreedingValueEntry {
  id: string;
  name: string;
  ebv: number;
  accuracy: number;
  rank: number;
  parent_mean?: number;
  mendelian_sampling?: number;
}

export interface BreedingValueAnalysis {
  id: string;
  trait: string;
  method: string;
  heritability: number;
  genetic_variance: number;
  mean: number;
  breeding_values: BreedingValueEntry[];
}


export interface EstimateFromDbRequest {
  study_db_ids: string[];
  trait_db_id: string;
}

export class BreedingValueService {
  constructor(private client: ApiClientCore) {}
  // Calculator Methods
  async getIndividuals(trait?: string): Promise<{ data: BreedingValueIndividual[] }> {
    const query = trait ? `?trait=${trait}` : "";
    return this.client.get<{ data: BreedingValueIndividual[] }>(`/api/v2/breeding-value/individuals${query}`);
  }

  async runBLUP(params: {
    trait: string;
    pedigree_data?: any;
  }): Promise<BLUPResult> {
    return this.client.post<BLUPResult>("/api/v2/breeding-value/blup", params);
  }

  async runGBLUP(params: {
    trait: string;
    marker_data?: any;
  }): Promise<BLUPResult> {
    return this.client.post<BLUPResult>("/api/v2/breeding-value/gblup", params);
  }

  async predictCross(params: {
    parent1: string;
    parent2: string;
    trait: string;
  }): Promise<CrossPredictionResult> {
    return this.client.post<CrossPredictionResult>("/api/v2/breeding-value/predict-cross", params);
  }

  async getTraits(): Promise<{
    data: Array<{ id: string; name: string; unit?: string }>;
  }> {
    return this.client.get("/api/v2/breeding-value/traits");
  }

  async getAnalysesOld(): Promise<{
    data: Array<{
      id: string;
      trait: string;
      method: string;
      created_at: string;
      n_entries: number;
    }>;
  }> {
    return this.client.get("/api/v2/breeding-value/analyses");
  }

  async getAnalysisOld(
    analysisId: string,
  ): Promise<BLUPResult & { id: string; trait: string; method: string }> {
    return this.client.get(`/api/v2/breeding-value/analyses/${analysisId}`);
  }

  // Values API Methods (Newer? v2?)
  async listAnalyses(): Promise<{
    data: Array<{
      id: string;
      trait: string;
      method: string;
      n_individuals: number;
      created_at: string;
    }>;
  }> {
    return this.client.get("/api/v2/breeding-value/analyses");
  }

  async getAnalysis(
    analysisId: string,
  ): Promise<{ data: BreedingValueAnalysis | null }> {
    return this.client.get<{ data: BreedingValueAnalysis | null }>(`/api/v2/breeding-value/analyses/${analysisId}`);
  }

  async getMethods(): Promise<{
    data: Array<{ id: string; name: string; description: string }>;
  }> {
    return this.client.get("/api/v2/breeding-value/methods");
  }

  async estimateBLUP(data: {
    phenotypes: Array<{ id: string; value: number }>;
    trait?: string;
    heritability?: number;
    pedigree?: Array<{ id: string; sire?: string; dam?: string }>;
    fixed_effects?: string[];
  }): Promise<any> {
    return this.client.post("/api/v2/breeding-value/blup", data);
  }

  async estimateGBLUP(data: {
    phenotypes: Array<{ id: string; value: number }>;
    markers: Array<{ id: string; markers: number[] }>;
    trait?: string;
    heritability?: number;
  }): Promise<any> {
    return this.client.post("/api/v2/breeding-value/gblup", data);
  }

  async predictCrossValue(data: {
    parent1_ebv: number;
    parent2_ebv: number;
    trait_mean: number;
    heritability?: number;
  }): Promise<any> {
    return this.client.post("/api/v2/breeding-value/predict-cross", data);
  }

  async rankCandidates(data: {
    breeding_values: Array<{ id: string; ebv: number; [key: string]: any }>;
    selection_intensity?: number;
    ebv_key?: string;
  }): Promise<any> {
    return this.client.post("/api/v2/breeding-value/rank", data);
  }

  async estimateFromDb(data: EstimateFromDbRequest): Promise<any> {
    return this.client.post<any>("/api/v2/breeding-value/estimate-from-db", data);
  }
}

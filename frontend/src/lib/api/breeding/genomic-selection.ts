import { ApiClientCore } from "../core/client";

export interface GSModel {
  id: string;
  name: string;
  method: string;
  trait: string;
  accuracy: number;
  heritability: number;
  markers: number;
  status: "trained" | "training" | "pending";
  created_at?: string;
}

export interface GEBVPrediction {
  germplasm_id: string;
  germplasm_name: string;
  gebv: number;
  reliability: number;
  rank: number;
  selected: boolean;
}

export interface SelectionResponse {
  expected_response: number;
  response_percent: number;
  selection_differential: number;
  selection_intensity: number;
  accuracy: number;
  genetic_variance: number;
}

export interface GSMethod {
  id: string;
  name: string;
  description: string;
  category?: string;
}

export interface GSSummary {
  trained_models: number;
  average_accuracy: number;
  total_predictions: number;
  selected_candidates: number;
  traits_covered: string[];
}

export class GenomicSelectionService {
  constructor(private client: ApiClientCore) {}

  async getModels(params?: { trait?: string; method?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.trait) searchParams.set("trait", params.trait);
    if (params?.method) searchParams.set("method", params.method);
    if (params?.status) searchParams.set("status", params.status);
    const query = searchParams.toString();
    return this.client.get<{ models: GSModel[]; total: number }>(
      `/api/v2/genomic-selection/models${query ? `?${query}` : ""}`
    );
  }

  async getModel(modelId: string) {
    return this.client.get<GSModel>(
      `/api/v2/genomic-selection/models/${modelId}`
    );
  }

  async getPredictions(
    modelId: string,
    params?: {
      min_gebv?: number;
      min_reliability?: number;
      selected_only?: boolean;
    }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.min_gebv)
      searchParams.set("min_gebv", params.min_gebv.toString());
    if (params?.min_reliability)
      searchParams.set("min_reliability", params.min_reliability.toString());
    if (params?.selected_only) searchParams.set("selected_only", "true");
    const query = searchParams.toString();
    return this.client.get<{ predictions: GEBVPrediction[]; total: number }>(
      `/api/v2/genomic-selection/models/${modelId}/predictions${
        query ? `?${query}` : ""
      }`
    );
  }

  async getSelectionResponse(modelId: string, selectionIntensity?: number) {
    const query = selectionIntensity
      ? `?selection_intensity=${selectionIntensity}`
      : "";
    return this.client.get<SelectionResponse>(
      `/api/v2/genomic-selection/models/${modelId}/selection-response${query}`
    );
  }

  async getYieldPredictions(environment?: string) {
    const query = environment ? `?environment=${environment}` : "";
    return this.client.get<{ predictions: any[]; total: number }>(
      `/api/v2/genomic-selection/yield-predictions${query}`
    );
  }

  async getCrossPrediction(parent1Id: string, parent2Id: string) {
    return this.client.get<any>(
      `/api/v2/genomic-selection/cross-prediction?parent1_id=${parent1Id}&parent2_id=${parent2Id}`
    );
  }

  async getModelComparison() {
    return this.client.get<{ comparison: any[] }>(
      "/api/v2/genomic-selection/comparison"
    );
  }

  async getSummary() {
    return this.client.get<GSSummary>("/api/v2/genomic-selection/summary");
  }

  async getMethods() {
    return this.client.get<{ methods: GSMethod[] }>(
      "/api/v2/genomic-selection/methods"
    );
  }

  async getTraits() {
    return this.client.get<{ traits: string[] }>(
      "/api/v2/genomic-selection/traits"
    );
  }
}

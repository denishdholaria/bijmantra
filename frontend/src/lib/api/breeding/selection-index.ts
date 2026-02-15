import { ApiClientCore } from "../core/client";

export class SelectionIndexService {
  constructor(private client: ApiClientCore) {}

  async getSelectionMethods() {
    return this.client.get<{ status: string; data: any[] }>(
      "/api/v2/selection/methods"
    );
  }

  async getDefaultWeights() {
    return this.client.get<{ status: string; data: Record<string, number> }>(
      "/api/v2/selection/default-weights"
    );
  }

  async calculateSmithHazel(data: {
    phenotypic_values: Array<Record<string, any>>;
    trait_names: string[];
    economic_weights: number[];
    heritabilities: number[];
  }) {
    return this.client.post<{ status: string; data: any }>(
      "/api/v2/selection/smith-hazel",
      data
    );
  }

  async calculateBaseIndex(data: {
    phenotypic_values: Array<Record<string, any>>;
    trait_names: string[];
    weights: number[];
  }) {
    return this.client.post<{ status: string; data: any }>(
      "/api/v2/selection/base-index",
      data
    );
  }

  async calculateDesiredGains(data: {
    phenotypic_values: Array<Record<string, any>>;
    trait_names: string[];
    desired_gains: number[];
    heritabilities: number[];
  }) {
    return this.client.post<{ status: string; data: any }>(
      "/api/v2/selection/desired-gains",
      data
    );
  }

  async calculateIndependentCulling(data: {
    phenotypic_values: Array<Record<string, any>>;
    trait_names: string[];
    thresholds: number[];
    threshold_types: string[];
  }) {
    return this.client.post<{ status: string; data: any }>(
      "/api/v2/selection/independent-culling",
      data
    );
  }

  async predictSelectionResponse(data: {
    selection_intensity: number;
    heritability: number;
    phenotypic_std: number;
  }) {
    return this.client.post<{ status: string; data: any }>(
      "/api/v2/selection/predict-response",
      data
    );
  }
}

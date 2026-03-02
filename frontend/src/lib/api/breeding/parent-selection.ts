import { ApiClientCore } from "../core/client";

export interface Parent {
  id: string;
  name: string;
  type: "elite" | "donor" | "landrace";
  traits: string[];
  gebv: number;
  heterosis_potential: number;
  pedigree: string;
  markers?: Record<string, boolean>;
  agronomic_data?: {
    yield_potential: number;
    days_to_maturity: number;
    plant_height: number;
  };
}

export interface CrossPrediction {
  parent1: { id: string; name: string; type: string };
  parent2: { id: string; name: string; type: string };
  expected_gebv: number;
  heterosis: number;
  genetic_distance: number;
  success_probability: number;
  combined_traits: string[];
  recommendation: string;
}

export interface CrossRecommendation {
  cross: string;
  parent1_id: string;
  parent2_id: string;
  score: number;
  reason: string;
  expected_gebv: number;
  heterosis: number;
  combined_traits: string[];
}

export class ParentSelectionService {
  constructor(private client: ApiClientCore) {}

  async getParents(params?: {
    type?: string;
    trait?: string;
    search?: string;
    page?: number;
    pageSize?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.type) queryParams.append("type", params.type);
    if (params?.trait) queryParams.append("trait", params.trait);
    if (params?.search) queryParams.append("search", params.search);
    if (params?.page) queryParams.append("page", String(params.page));
    if (params?.pageSize)
      queryParams.append("pageSize", String(params.pageSize));
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{ data: Parent[]; total: number }>(
      `/api/v2/parent-selection/parents${query}`
    );
  }

  async getParent(parentId: string) {
    return this.client.get<{ data: Parent }>(
      `/api/v2/parent-selection/parents/${parentId}`
    );
  }

  async getRecommendations(params?: {
    limit?: number;
    trait?: string;
    type?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append("limit", String(params.limit));
    if (params?.trait) queryParams.append("trait", params.trait);
    if (params?.type) queryParams.append("type", params.type);
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{ data: CrossRecommendation[] }>(
      `/api/v2/parent-selection/recommendations${query}`
    );
  }

  async predictCross(parent1Id: string, parent2Id: string) {
    return this.client.get<{ data: CrossPrediction }>(
      `/api/v2/parent-selection/predict-cross?parent1_id=${parent1Id}&parent2_id=${parent2Id}`
    );
  }

  async createCrossPlan(data: {
    parent1_id: string;
    parent2_id: string;
    name?: string;
    notes?: string;
  }) {
    return this.client.post<{ data: any }>(
      "/api/v2/parent-selection/cross-plans",
      data
    );
  }

  async export(parentIds?: string[], format: "csv" | "json" = "csv") {
    return this.client.post<Blob>("/api/v2/parent-selection/export", {
      parent_ids: parentIds,
      format,
    });
  }
}

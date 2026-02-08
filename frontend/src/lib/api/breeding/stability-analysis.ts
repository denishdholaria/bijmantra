import { ApiClientCore } from "../core/client";

export interface StabilityVariety {
  id: string;
  name: string;
  mean_yield: number;
  rank: number;
  bi: number;
  s2di: number;
  sigma2i: number;
  wi: number;
  pi: number;
  asv: number;
  stability_rank: number;
  recommendation: "wide" | "favorable" | "unfavorable" | "specific";
  environments_tested: number;
  years_tested: number;
}

export interface StabilityMethod {
  id: string;
  name: string;
  year: number;
  type: string;
  description: string;
  interpretation: Record<string, string>;
}

export class StabilityAnalysisService {
  constructor(private client: ApiClientCore) {}

  async getVarieties(params?: {
    recommendation?: string;
    min_yield?: number;
    sort_by?: string;
  }): Promise<{
    success: boolean;
    count: number;
    varieties: StabilityVariety[];
  }> {
    const searchParams = new URLSearchParams();
    if (params?.recommendation)
      searchParams.append("recommendation", params.recommendation);
    if (params?.min_yield)
      searchParams.append("min_yield", params.min_yield.toString());
    if (params?.sort_by) searchParams.append("sort_by", params.sort_by);
    const query = searchParams.toString();
    return this.client.request<{
      success: boolean;
      count: number;
      varieties: StabilityVariety[];
    }>(`/api/v2/stability/varieties${query ? `?${query}` : ""}`);
  }

  async getVariety(
    varietyId: string,
  ): Promise<
    { success: boolean } & StabilityVariety & {
        interpretation: Record<string, string>;
      }
  > {
    return this.client.request<
      { success: boolean } & StabilityVariety & {
        interpretation: Record<string, string>;
      }
    >(`/api/v2/stability/varieties/${varietyId}`);
  }

  async analyze(params: {
    variety_ids: string[];
    methods?: string[];
  }): Promise<{
    success: boolean;
    methods_used: string[];
    variety_count: number;
    results: any[];
  }> {
    return this.client.request<{
      success: boolean;
      methods_used: string[];
      variety_count: number;
      results: any[];
    }>("/api/v2/stability/analyze", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async getMethods(): Promise<{
    success: boolean;
    methods: StabilityMethod[];
  }> {
    return this.client.request<{
      success: boolean;
      methods: StabilityMethod[];
    }>("/api/v2/stability/methods");
  }

  async getRecommendations(): Promise<{
    success: boolean;
    recommendations: Record<
      string,
      {
        description: string;
        criteria: string;
        varieties: Array<{ id: string; name: string; mean_yield: number }>;
      }
    >;
  }> {
    return this.client.request<{
      success: boolean;
      recommendations: Record<
        string,
        {
          description: string;
          criteria: string;
          varieties: Array<{ id: string; name: string; mean_yield: number }>;
        }
      >;
    }>("/api/v2/stability/recommendations");
  }

  async getComparison(): Promise<{
    success: boolean;
    comparison: any[];
    correlation_matrix: Record<string, Record<string, number>>;
  }> {
    return this.client.request<{
      success: boolean;
      comparison: any[];
      correlation_matrix: Record<string, Record<string, number>>;
    }>("/api/v2/stability/comparison");
  }

  async getStatistics(): Promise<{
    success: boolean;
    statistics: Record<string, number>;
  }> {
    return this.client.request<{
      success: boolean;
      statistics: Record<string, number>;
    }>("/api/v2/stability/statistics");
  }
}

import { ApiClientCore } from "../core/client";

export class StatisticsService {
  constructor(private client: ApiClientCore) {}

  async getTrials() {
    return this.client.get<{ trials: any[]; total: number }>(
      "/api/v2/statistics/trials"
    );
  }

  async getTraits() {
    return this.client.get<{ traits: any[]; total: number }>(
      "/api/v2/statistics/traits"
    );
  }

  async getOverview(trialId?: string) {
    const query = trialId ? `?trial_id=${trialId}` : "";
    return this.client.get<{
      trial_id: string;
      trial_name: string;
      traits_analyzed: number;
      total_observations: number;
      genotypes: number;
      replications: number;
      locations: number;
      missing_data_pct: number;
      data_quality_score: number;
    }>(`/api/v2/statistics/overview${query}`);
  }

  async getSummary(params?: {
    trial_id?: string;
    trait_ids?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.trial_id) searchParams.append("trial_id", params.trial_id);
    if (params?.trait_ids) searchParams.append("trait_ids", params.trait_ids);
    const query = searchParams.toString();
    return this.client.get<{
      trial_id: string;
      trial_name: string;
      stats: any[];
      total_traits: number;
    }>(`/api/v2/statistics/summary${query ? `?${query}` : ""}`);
  }

  async getCorrelations(params?: {
    trial_id?: string;
    trait_ids?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.trial_id) searchParams.append("trial_id", params.trial_id);
    if (params?.trait_ids) searchParams.append("trait_ids", params.trait_ids);
    const query = searchParams.toString();
    return this.client.get<{
      trial_id: string;
      correlations: any[];
      total: number;
    }>(`/api/v2/statistics/correlations${query ? `?${query}` : ""}`);
  }

  async getDistribution(
    traitId: string,
    params?: { trial_id?: string; bins?: number },
  ) {
    const searchParams = new URLSearchParams({ trait_id: traitId });
    if (params?.trial_id) searchParams.append("trial_id", params.trial_id);
    if (params?.bins) searchParams.append("bins", String(params.bins));
    return this.client.get<{
      trait_id: string;
      trait_name: string;
      unit: string;
      histogram: any[];
      summary: any;
      n: number;
    }>(`/api/v2/statistics/distribution?${searchParams}`);
  }

  async getAnova(traitId: string, trialId?: string) {
    const searchParams = new URLSearchParams({ trait_id: traitId });
    if (trialId) searchParams.append("trial_id", trialId);
    return this.client.get<{
      trait_id: string;
      trait_name: string;
      sources: any[];
      total_df: number;
      cv_percent: number;
      heritability: number;
      lsd_5pct: number;
    }>(`/api/v2/statistics/anova?${searchParams}`);
  }
}

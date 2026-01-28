import { ApiClientCore } from "../core/client";
import {
  AnalyticsSummary,
  CorrelationMatrix,
  GeneticGainData,
  HeritabilityData,
  QuickInsight,
  SelectionResponseData,
} from "./types";

export interface AnalyticsResponse {
  genetic_gain: GeneticGainData[];
  heritabilities: HeritabilityData[];
  selection_response: SelectionResponseData[];
  correlations: CorrelationMatrix;
  summary: AnalyticsSummary;
  insights: QuickInsight[];
}

export class AnalyticsService {
  constructor(private client: ApiClientCore) {}

  async getAnalytics(params?: {
    program_id?: string;
    crop?: string;
    year?: number;
  }) {
    const query = new URLSearchParams();
    if (params?.program_id) query.append("program_id", params.program_id);
    if (params?.crop) query.append("crop", params.crop);
    if (params?.year) query.append("year", String(params.year));
    const queryString = query.toString() ? `?${query}` : "";
    return this.client.get<AnalyticsResponse>(`/api/v2/analytics${queryString}`);
  }

  async getSummary() {
    return this.client.get<AnalyticsSummary>("/api/v2/analytics/summary");
  }

  async getGeneticGain(programId?: string) {
    const query = programId ? `?program_id=${programId}` : "";
    return this.client.get<{ data: GeneticGainData[] }>(
      `/api/v2/analytics/genetic-gain${query}`
    );
  }

  async getHeritabilities(trialId?: string) {
    const query = trialId ? `?trial_id=${trialId}` : "";
    return this.client.get<{ data: HeritabilityData[] }>(
      `/api/v2/analytics/heritabilities${query}`
    );
  }

  async getCorrelations(traitIds?: string[]) {
    const query = traitIds?.length ? `?trait_ids=${traitIds.join(",")}` : "";
    return this.client.get<{ data: CorrelationMatrix }>(
      `/api/v2/analytics/correlations${query}`
    );
  }

  async getSelectionResponse(programId?: string) {
    const query = programId ? `?program_id=${programId}` : "";
    return this.client.get<{ data: SelectionResponseData[] }>(
      `/api/v2/analytics/selection-response${query}`
    );
  }

  async getInsights() {
    return this.client.get<{ insights: QuickInsight[] }>(
      "/api/v2/analytics/insights"
    );
  }

  async computeGBLUP(params: { trait_id: string; population_id?: string }) {
    const query = new URLSearchParams({ trait_id: params.trait_id });
    if (params.population_id) {
      query.append("population_id", params.population_id);
    }
    return this.client.post<{ job_id: string; status: string }>(
      `/api/v2/analytics/compute/gblup?${query}`,
      {}
    );
  }

  async getComputeJob(jobId: string) {
    return this.client.get<{
      job_id: string;
      status: string;
      progress?: number;
      result?: any;
    }>(`/api/v2/analytics/compute/${jobId}`);
  }

  async getVeenaSummary() {
    return this.client.get<{
      summary: string;
      key_metrics?: Record<string, string>;
    }>("/api/v2/analytics/veena-summary");
  }
}

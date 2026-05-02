import { ApiClientCore } from "../core/client";

export interface TrialInfo {
  trialDbId: string;
  trialName: string;
  programDbId: string;
  programName: string;
  startDate: string;
  endDate: string;
  locations: number;
  entries: number;
  traits: number;
  observations: number;
  completionRate: number;
  leadScientist: string;
}

export interface TopPerformer {
  rank: number;
  germplasmDbId: string;
  germplasmName: string;
  yield_value: number;
  change_percent: string;
  traits: string[];
}

export interface TraitSummaryItem {
  trait: string;
  mean: number;
  cv: number;
  lsd: number;
  fValue: number;
  significance: string;
}

export interface LocationPerformance {
  locationDbId: string;
  locationName: string;
  entries: number;
  meanYield: number;
  cv: number;
  completionRate: number;
}

export interface TrialStatistics {
  grand_mean: number;
  overall_cv: number;
  heritability: number;
  genetic_variance: number;
  error_variance: number;
  lsd_5_percent: number;
  selection_intensity: number;
  expected_gain: number;
  anova?: any;
}

export class TrialSummaryService {
  constructor(private client: ApiClientCore) {}

  async getTrials(params?: { program_id?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.set("program_id", params.program_id);
    if (params?.status) searchParams.set("status", params.status);
    const query = searchParams.toString();
    return this.client.get<{ data: TrialInfo[]; total: number }>(
      `/api/v2/trial-summary/trials${query ? `?${query}` : ""}`
    );
  }

  async getTrial(trialId: string) {
    return this.client.get<{ data: TrialInfo }>(
      `/api/v2/trial-summary/trials/${trialId}`
    );
  }

  async getSummary(trialId: string) {
    return this.client.get<{
      trial: TrialInfo;
      topPerformers: TopPerformer[];
      traitSummary: TraitSummaryItem[];
      locationPerformance: LocationPerformance[];
      statistics: TrialStatistics;
    }>(`/api/v2/trial-summary/trials/${trialId}/summary`);
  }

  async getTopPerformers(
    trialId: string,
    params?: { limit?: number; trait?: string }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.trait) searchParams.set("trait", params.trait);
    const query = searchParams.toString();
    return this.client.get<{ data: TopPerformer[]; trait: string }>(
      `/api/v2/trial-summary/trials/${trialId}/top-performers${
        query ? `?${query}` : ""
      }`
    );
  }

  async getTraitSummary(trialId: string) {
    return this.client.get<{ data: TraitSummaryItem[] }>(
      `/api/v2/trial-summary/trials/${trialId}/traits`
    );
  }

  async getLocationPerformance(trialId: string) {
    return this.client.get<{ data: LocationPerformance[] }>(
      `/api/v2/trial-summary/trials/${trialId}/locations`
    );
  }

  async getStatistics(trialId: string) {
    return this.client.get<TrialStatistics>(
      `/api/v2/trial-summary/trials/${trialId}/statistics`
    );
  }

  async exportSummary(
    trialId: string,
    format: string = "pdf",
    sections?: string[]
  ) {
    const searchParams = new URLSearchParams();
    searchParams.set("format", format);
    if (sections) searchParams.set("sections", sections.join(","));
    return this.client.post<any>(
      `/api/v2/trial-summary/trials/${trialId}/export?${searchParams}`,
      {}
    );
  }
}

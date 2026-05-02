import { ApiClientCore } from "../core/client";

export interface PlannedTrial {
  id: string;
  name: string;
  type: string;
  season: string;
  year: number;
  locations: string[];
  entries: number;
  reps: number;
  design: string;
  status: string;
  progress: number;
  startDate: string;
  endDate?: string;
  totalPlots: number;
  crop?: string;
  objectives?: string;
}

export interface TrialType {
  value: string;
  label: string;
  description?: string;
}

export interface TrialDesign {
  value: string;
  label: string;
}

export class TrialPlanningService {
  constructor(private client: ApiClientCore) {}

  async getTrials(params?: {
    status?: string;
    type?: string;
    search?: string;
    year?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.type) searchParams.set("type", params.type);
    if (params?.search) searchParams.set("search", params.search);
    if (params?.year) searchParams.set("year", params.year.toString());
    const query = searchParams.toString();
    return this.client.get<PlannedTrial[]>(
      `/api/v2/trial-planning/trials${query ? `?${query}` : ""}`
    );
  }

  async getTrial(trialId: string) {
    return this.client.get<PlannedTrial>(
      `/api/v2/trial-planning/trials/${trialId}`
    );
  }

  async createTrial(data: {
    name: string;
    type: string;
    season: string;
    locations: string[];
    entries: number;
    reps: number;
    design: string;
    startDate: string;
    endDate?: string;
    crop?: string;
    objectives?: string;
  }) {
    return this.client.post<PlannedTrial>("/api/v2/trial-planning/trials", data);
  }

  async updateTrial(trialId: string, data: Partial<PlannedTrial>) {
    return this.client.patch<PlannedTrial>(
      `/api/v2/trial-planning/trials/${trialId}`,
      data
    );
  }

  async deleteTrial(trialId: string) {
    return this.client.delete<{ success: boolean }>(
      `/api/v2/trial-planning/trials/${trialId}`
    );
  }

  async approveTrial(trialId: string, approvedBy: string) {
    return this.client.post<PlannedTrial>(
      `/api/v2/trial-planning/trials/${trialId}/approve?approved_by=${encodeURIComponent(
        approvedBy
      )}`,
      {}
    );
  }

  async startTrial(trialId: string) {
    return this.client.post<PlannedTrial>(
      `/api/v2/trial-planning/trials/${trialId}/start`,
      {}
    );
  }

  async completeTrial(trialId: string) {
    return this.client.post<PlannedTrial>(
      `/api/v2/trial-planning/trials/${trialId}/complete`,
      {}
    );
  }

  async cancelTrial(trialId: string, reason: string) {
    return this.client.post<PlannedTrial>(
      `/api/v2/trial-planning/trials/${trialId}/cancel?reason=${encodeURIComponent(
        reason
      )}`,
      {}
    );
  }

  async getStatistics() {
    return this.client.get<{
      totalTrials: number;
      planning: number;
      approved: number;
      active: number;
      completed: number;
      cancelled: number;
      totalPlots: number;
    }>("/api/v2/trial-planning/statistics");
  }

  async getTimeline(year?: number) {
    const query = year ? `?year=${year}` : "";
    return this.client.get<PlannedTrial[]>(
      `/api/v2/trial-planning/timeline${query}`
    );
  }

  async getTypes() {
    return this.client.get<TrialType[]>("/api/v2/trial-planning/types");
  }

  async getSeasons() {
    return this.client.get<string[]>("/api/v2/trial-planning/seasons");
  }
}

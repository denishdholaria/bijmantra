import { ApiClientCore } from "../core/client";

export interface RankedEntry {
  id: string;
  entry_id: string;
  name: string;
  rank: number;
  previous_rank: number;
  yield: number;
  gebv: number;
  traits: string[];
  score: number;
  program_name?: string;
  trial_name?: string;
  generation?: string;
}

export interface RankingStatistics {
  total_entries: number;
  avg_score: number;
  avg_yield: number;
  avg_gebv: number;
  top_performer: string | null;
  most_improved: { name: string; improvement: number } | null;
}

export interface RankingProgram {
  id: string;
  name: string;
}

export interface RankingTrial {
  id: string;
  name: string;
  program_id: string;
}

export class PerformanceRankingService {
  constructor(private client: ApiClientCore) {}

  async getRankings(params?: {
    program_id?: string;
    trial_id?: string;
    sort_by?: string;
    limit?: number;
    search?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.set("program_id", params.program_id);
    if (params?.trial_id) searchParams.set("trial_id", params.trial_id);
    if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    return this.client.get<{ status: string; data: RankedEntry[]; count: number }>(
      `/api/v2/performance-ranking/rankings${query ? `?${query}` : ""}`
    );
  }

  async getTopPerformers(params?: {
    program_id?: string;
    trial_id?: string;
    limit?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.set("program_id", params.program_id);
    if (params?.trial_id) searchParams.set("trial_id", params.trial_id);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    const query = searchParams.toString();
    return this.client.get<{ status: string; data: RankedEntry[]; count: number }>(
      `/api/v2/performance-ranking/top-performers${query ? `?${query}` : ""}`
    );
  }

  async getStatistics(params?: { program_id?: string; trial_id?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.set("program_id", params.program_id);
    if (params?.trial_id) searchParams.set("trial_id", params.trial_id);
    const query = searchParams.toString();
    return this.client.get<{ status: string; data: RankingStatistics }>(
      `/api/v2/performance-ranking/statistics${query ? `?${query}` : ""}`
    );
  }

  async getEntry(entryId: string) {
    return this.client.get<{ status: string; data: RankedEntry }>(
      `/api/v2/performance-ranking/entries/${entryId}`
    );
  }

  async compareEntries(entryIds: string[]) {
    return this.client.post<{ status: string; data: any }>(
      "/api/v2/performance-ranking/compare",
      { entry_ids: entryIds }
    );
  }

  async getPrograms() {
    return this.client.get<{ status: string; data: RankingProgram[] }>(
      "/api/v2/performance-ranking/programs"
    );
  }

  async getTrials(programId?: string) {
    const query = programId ? `?program_id=${programId}` : "";
    return this.client.get<{ status: string; data: RankingTrial[] }>(
      `/api/v2/performance-ranking/trials${query}`
    );
  }
}

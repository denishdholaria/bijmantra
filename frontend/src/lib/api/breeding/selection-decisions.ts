import { ApiClientCore } from "../core/client";

export interface SelectionCandidate {
  id: string;
  name: string;
  germplasm_id?: string;
  program_id?: string;
  program_name?: string;
  generation?: string;
  gebv: number;
  yield_estimate?: number;
  traits: string[];
  pedigree?: string;
  trial_id?: string;
  trial_name?: string;
  location?: string;
  decision?: "advance" | "reject" | "hold" | null;
  decision_notes?: string;
  decision_date?: string;
}

export interface SelectionStatistics {
  total_candidates: number;
  advanced: number;
  rejected: number;
  on_hold: number;
  pending: number;
  selection_rate: number;
  avg_gebv_advanced?: number;
  avg_gebv_rejected?: number;
}

export interface SelectionProgram {
  id: string;
  name: string;
}

export interface SelectionTrial {
  id: string;
  name: string;
}

export class SelectionDecisionsService {
  constructor(private client: ApiClientCore) {}

  async getCandidates(params?: {
    program_id?: string;
    trial_id?: string;
    status?: string;
    search?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.set("program_id", params.program_id);
    if (params?.trial_id) searchParams.set("trial_id", params.trial_id);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.search) searchParams.set("search", params.search);
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.pageSize)
      searchParams.set("pageSize", params.pageSize.toString());
    const query = searchParams.toString();
    return this.client.get<{
      status: string;
      data: SelectionCandidate[];
      count: number;
    }>(`/api/v2/selection-decisions/candidates${query ? `?${query}` : ""}`);
  }

  async getCandidate(candidateId: string) {
    return this.client.get<{ status: string; data: SelectionCandidate }>(
      `/api/v2/selection-decisions/candidates/${candidateId}`
    );
  }

  async makeDecision(
    candidateId: string,
    decision: "advance" | "reject" | "hold",
    notes?: string
  ) {
    return this.client.post<{ status: string; data: SelectionCandidate }>(
      `/api/v2/selection-decisions/candidates/${candidateId}/decision`,
      { decision, notes }
    );
  }

  async recordBulkDecisions(
    decisions: Array<{
      candidate_id: string;
      decision: string;
      notes?: string;
    }>
  ) {
    return this.client.post<{ successful: number; failed: number }>(
      "/api/v2/selection-decisions/candidates/bulk-decision",
      { decisions }
    );
  }

  async getStatistics(params?: { program_id?: string; trial_id?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.set("program_id", params.program_id);
    if (params?.trial_id) searchParams.set("trial_id", params.trial_id);
    const query = searchParams.toString();
    return this.client.get<{ status: string; data: SelectionStatistics }>(
      `/api/v2/selection-decisions/statistics${query ? `?${query}` : ""}`
    );
  }

  async getPrograms() {
    return this.client.get<{ status: string; data: SelectionProgram[] }>(
      "/api/v2/selection-decisions/programs"
    );
  }

  async getTrials(programId?: string) {
    const query = programId ? `?program_id=${programId}` : "";
    return this.client.get<{ status: string; data: SelectionTrial[] }>(
      `/api/v2/selection-decisions/trials${query}`
    );
  }
}

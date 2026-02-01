import { ApiClientCore } from "../core/client";

export interface PipelineStage {
  id: string;
  name: string;
  order: number;
  description: string;
}

export interface PipelineEntry {
  id: string;
  name: string;
  pedigree: string;
  current_stage: string;
  program_id: string;
  program_name: string;
  crop: string;
  year: number;
  status: "active" | "released" | "dropped";
  traits: string[];
  notes: string;
  created_at: string;
  updated_at: string;
  stage_history: Array<{
    stage: string;
    date: string;
    decision: string;
    notes?: string;
  }>;
}

export interface PipelineStatistics {
  total_entries: number;
  active: number;
  released: number;
  dropped: number;
  stage_counts: Record<string, number>;
  crop_counts: Record<string, number>;
  avg_years_to_release: number;
  crops: string[];
}

export class BreedingPipelineService {
  constructor(private client: ApiClientCore) {}

  async getStages() {
    return this.client.get<{ data: PipelineStage[] }>(
      "/api/v2/breeding-pipeline/stages"
    );
  }

  async getEntries(params?: {
    stage?: string;
    crop?: string;
    program_id?: string;
    status?: string;
    year?: number;
    search?: string;
    limit?: number;
    offset?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.stage) queryParams.append("stage", params.stage);
    if (params?.crop) queryParams.append("crop", params.crop);
    if (params?.program_id) queryParams.append("program_id", params.program_id);
    if (params?.status) queryParams.append("status", params.status);
    if (params?.year) queryParams.append("year", String(params.year));
    if (params?.search) queryParams.append("search", params.search);
    if (params?.limit) queryParams.append("limit", String(params.limit));
    if (params?.offset) queryParams.append("offset", String(params.offset));
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{ data: PipelineEntry[]; total: number }>(
      `/api/v2/breeding-pipeline${query}`
    );
  }

  async getEntry(entryId: string) {
    return this.client.get<{ data: PipelineEntry }>(
      `/api/v2/breeding-pipeline/${entryId}`
    );
  }

  async getStatistics(params?: { program_id?: string; crop?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.program_id) queryParams.append("program_id", params.program_id);
    if (params?.crop) queryParams.append("crop", params.crop);
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{ data: PipelineStatistics }>(
      `/api/v2/breeding-pipeline/statistics${query}`
    );
  }

  async getStageSummary() {
    return this.client.get<{
      data: Array<{
        stage_id: string;
        stage_name: string;
        order: number;
        count: number;
        entries: Array<{ id: string; name: string; crop: string }>;
      }>;
    }>("/api/v2/breeding-pipeline/stage-summary");
  }

  async getCrops() {
    return this.client.get<{ data: string[] }>(
      "/api/v2/breeding-pipeline/crops"
    );
  }


  async advanceStage(
    entryId: string,
    decision: string,
    notes?: string
  ): Promise<{ success: boolean; message: string }> {
    return this.client.post<{ success: boolean; message: string }>(
      `/api/v2/breeding-pipeline/${entryId}/stage`,
      { decision, notes }
    );
  }

  async getPrograms() {
    return this.client.get<{ data: Array<{ id: string; name: string }> }>(
      "/api/v2/breeding-pipeline/programs"
    );
  }
}

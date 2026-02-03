import { ApiClientCore } from "../core/client";

export class PhenologyService {
  constructor(private client: ApiClientCore) {}
  async getPhenologyGrowthStages(crop?: string) {
    const query = crop ? `?crop=${crop}` : "";
    return this.client.request<{ stages: any[] }>(`/api/v2/phenology/stages${query}`);
  }

  async getPhenologyStats(studyId?: string) {
    const query = studyId ? `?study_id=${studyId}` : "";
    return this.client.request<{
      total_records: number;
      by_stage: Record<string, number>;
      by_crop: Record<string, number>;
      avg_days_to_maturity: number;
    }>(`/api/v2/phenology/stats${query}`);
  }

  async getPhenologyRecords(params?: {
    study_id?: string;
    crop?: string;
    min_stage?: number;
    max_stage?: number;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.study_id) searchParams.append("study_id", params.study_id);
    if (params?.crop) searchParams.append("crop", params.crop);
    if (params?.min_stage !== undefined)
      searchParams.append("min_stage", String(params.min_stage));
    if (params?.max_stage !== undefined)
      searchParams.append("max_stage", String(params.max_stage));
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.offset) searchParams.append("offset", String(params.offset));
    const query = searchParams.toString();
    return this.client.request<{ records: any[]; total: number }>(
      `/api/v2/phenology/records${query ? `?${query}` : ""}`,
    );
  }

  async getPhenologyRecord(recordId: string) {
    return this.client.request<any>(`/api/v2/phenology/records/${recordId}`);
  }

  async createPhenologyRecord(data: {
    germplasm_id?: string;
    germplasm_name: string;
    study_id: string;
    plot_id: string;
    sowing_date: string;
    current_stage?: number;
    expected_maturity?: number;
    crop?: string;
  }) {
    return this.client.request<any>("/api/v2/phenology/records", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updatePhenologyRecord(
    recordId: string,
    data: { current_stage?: number; expected_maturity?: number },
  ) {
    return this.client.request<any>(`/api/v2/phenology/records/${recordId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async recordPhenologyObservation(
    recordId: string,
    data: { stage: number; date?: string; notes?: string },
  ) {
    return this.client.request<any>(
      `/api/v2/phenology/records/${recordId}/observations`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );
  }

  async getPhenologyObservations(recordId: string) {
    return this.client.request<{ observations: any[]; total: number }>(
      `/api/v2/phenology/records/${recordId}/observations`,
    );
  }
}

import { ApiClientCore } from "../core/client";

export class QuickEntryService {
  constructor(private client: ApiClientCore) {}
  async getQuickEntryStats() {
    return this.client.request<{
      total_entries: number;
      by_type: Record<string, number>;
      recent_by_type: Record<string, number>;
    }>("/api/v2/quick-entry/stats");
  }

  async getQuickEntryRecent() {
    return this.client.request<{ activity: any[] }>("/api/v2/quick-entry/recent");
  }

  async getQuickEntryOptions(optionType: string) {
    return this.client.request<{ options: any[]; type: string }>(
      `/api/v2/quick-entry/options/${optionType}`,
    );
  }

  async getQuickEntries(params?: {
    entry_type?: string;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.entry_type)
      searchParams.append("entry_type", params.entry_type);
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.offset) searchParams.append("offset", String(params.offset));
    const query = searchParams.toString();
    return this.client.request<{ entries: any[]; total: number }>(
      `/api/v2/quick-entry/entries${query ? `?${query}` : ""}`,
    );
  }

  async createQuickGermplasm(data: {
    germplasm_name: string;
    accession_number?: string;
    species?: string;
    country_of_origin?: string;
    pedigree?: string;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/quick-entry/germplasm", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async createQuickObservation(data: {
    study_id: string;
    observation_unit_id: string;
    trait: string;
    value: number;
    unit?: string;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/quick-entry/observation", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async createQuickCross(data: {
    female_parent: string;
    male_parent: string;
    cross_date?: string;
    seeds_obtained?: number;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/quick-entry/cross", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async createQuickTrial(data: {
    trial_name: string;
    program_id?: string;
    start_date?: string;
    end_date?: string;
    location?: string;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/quick-entry/trial", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteQuickEntry(entryId: string) {
    return this.client.request<{ success: boolean }>(
      `/api/v2/quick-entry/entries/${entryId}`,
      {
        method: "DELETE",
      },
    );
  }
}

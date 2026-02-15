import { ApiClientCore } from "../core/client";

export interface NurseryBatch {
  nursery_id: string;
  name: string;
  nursery_type: string;
  season: string;
  year: number;
  location: string;
  status: string;
  sowing_date?: string;
  harvest_date?: string;
  entry_count: number;
  notes: string;
}

export interface NurseryEntry {
  entry_id: string;
  nursery_id: string;
  genotype_id: string;
  genotype_name: string;
  pedigree: string;
  source_nursery: string;
  selection_decision?: string;
  selection_notes?: string;
  seed_harvested: number;
}

export class NurseryManagementService {
  constructor(private client: ApiClientCore) {}
  async getNurseries(params?: {
    year?: number;
    nursery_type?: string;
    status?: string;
  }): Promise<{ success: boolean; count: number; nurseries: NurseryBatch[] }> {
    const searchParams = new URLSearchParams();
    if (params?.year) searchParams.append("year", params.year.toString());
    if (params?.nursery_type)
      searchParams.append("nursery_type", params.nursery_type);
    if (params?.status) searchParams.append("status", params.status);
    const query = searchParams.toString();
    return this.client.get<{ success: boolean; count: number; nurseries: NurseryBatch[] }>(
      `/api/v2/nursery/nurseries${query ? `?${query}` : ""}`
    );
  }

  async getNursery(
    nurseryId: string,
  ): Promise<
    { success: boolean } & NurseryBatch & { entries: NurseryEntry[] }
  > {
    return this.client.get<{ success: boolean } & NurseryBatch & { entries: NurseryEntry[] }>(
      `/api/v2/nursery/nurseries/${nurseryId}`
    );
  }

  async createNursery(data: {
    name: string;
    nursery_type: string;
    season: string;
    year: number;
    location: string;
    sowing_date?: string;
    notes?: string;
  }): Promise<{ success: boolean; message: string } & NurseryBatch> {
    return this.client.post<{ success: boolean; message: string } & NurseryBatch>(
      "/api/v2/nursery/nurseries",
      data
    );
  }

  async addEntry(
    nurseryId: string,
    data: {
      genotype_id: string;
      genotype_name: string;
      pedigree?: string;
      source_nursery?: string;
    },
  ): Promise<{ success: boolean; message: string } & NurseryEntry> {
    return this.client.post<{ success: boolean; message: string } & NurseryEntry>(
      `/api/v2/nursery/nurseries/${nurseryId}/entries`,
      data
    );
  }

  async bulkAddEntries(
    nurseryId: string,
    entries: Array<{
      genotype_id: string;
      genotype_name: string;
      pedigree?: string;
      source_nursery?: string;
    }>,
  ): Promise<{ success: boolean; nursery_id: string; entries_added: number }> {
    return this.client.post<{ success: boolean; nursery_id: string; entries_added: number }>(
      `/api/v2/nursery/nurseries/${nurseryId}/entries/bulk`,
      { entries }
    );
  }

  async recordSelection(
    entryId: string,
    data: { decision: string; notes?: string; seed_harvested?: number },
  ): Promise<{ success: boolean; message: string } & NurseryEntry> {
    return this.client.post<{ success: boolean; message: string } & NurseryEntry>(
      `/api/v2/nursery/entries/${entryId}/selection`,
      data
    );
  }

  async advanceSelections(
    sourceNurseryId: string,
    targetNurseryId: string,
  ): Promise<{ success: boolean; message: string; entries_advanced: number }> {
    return this.client.post<{ success: boolean; message: string; entries_advanced: number }>(
      "/api/v2/nursery/advance",
      {
        source_nursery_id: sourceNurseryId,
        target_nursery_id: targetNurseryId,
      }
    );
  }

  async updateStatus(
    nurseryId: string,
    data: { status: string; harvest_date?: string },
  ): Promise<{ success: boolean; message: string } & NurseryBatch> {
    return this.client.patch<{ success: boolean; message: string } & NurseryBatch>(
      `/api/v2/nursery/nurseries/${nurseryId}/status`,
      data
    );
  }

  async getSummary(
    nurseryId: string,
  ): Promise<{
    success: boolean;
    nursery_id: string;
    total_entries: number;
    by_decision: Record<string, number>;
    selection_rate: number;
  }> {
    return this.client.get<{
      success: boolean;
      nursery_id: string;
      total_entries: number;
      by_decision: Record<string, number>;
      selection_rate: number;
    }>(`/api/v2/nursery/nurseries/${nurseryId}/summary`);
  }

  async getTypes(): Promise<{
    types: Array<{ id: string; name: string; description: string }>;
  }> {
    return this.client.get<{ types: Array<{ id: string; name: string; description: string }> }>(
      "/api/v2/nursery/types"
    );
  }
}

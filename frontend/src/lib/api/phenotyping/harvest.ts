import { ApiClientCore } from "../core/client";

export interface HarvestPlan {
  id: string;
  study_id: string;
  study_name: string;
  planned_date: string;
  status: "planned" | "in_progress" | "completed" | "cancelled";
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface HarvestRecord {
  id: string;
  plan_id: string;
  plot_id: string;
  germplasm_name: string;
  harvest_date: string;
  wet_weight: number;
  dry_weight?: number;
  moisture_content?: number;
  quality_grade?: string;
  storage_unit?: string;
  notes?: string;
  grain_yield?: number;
}

export interface StorageUnit {
  id: string;
  name: string;
  type: string;
  capacity: number;
  current_stock: number;
  temperature?: number;
  humidity?: number;
  location?: string;
}

export interface HarvestStats {
  total_harvested_kg: number;
  avg_moisture: number;
  total_capacity: number;
  total_stock: number;
  records_count: number;
  plans_count: number;
}

export class HarvestService {
  constructor(private client: ApiClientCore) {}

  async getPlans(params?: { status?: string; study_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append("status", params.status);
    if (params?.study_id) queryParams.append("study_id", params.study_id);
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{ plans: HarvestPlan[] }>(
      `/api/v2/harvest/plans${query}`
    );
  }

  async getPlan(planId: string) {
    return this.client.get<{ plan: HarvestPlan }>(
      `/api/v2/harvest/plans/${planId}`
    );
  }

  async createPlan(data: {
    study_id: string;
    planned_date: string;
    notes?: string;
  }) {
    return this.client.post<{ plan: HarvestPlan }>(
      "/api/v2/harvest/plans",
      data
    );
  }

  async updatePlan(planId: string, data: Partial<HarvestPlan>) {
    return this.client.patch<{ plan: HarvestPlan }>(
      `/api/v2/harvest/plans/${planId}`,
      data
    );
  }

  async deletePlan(planId: string) {
    return this.client.delete<void>(`/api/v2/harvest/plans/${planId}`);
  }

  async getRecords(params?: { plan_id?: string; plot_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.plan_id) queryParams.append("plan_id", params.plan_id);
    if (params?.plot_id) queryParams.append("plot_id", params.plot_id);
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{ records: HarvestRecord[] }>(
      `/api/v2/harvest/records${query}`
    );
  }

  async getRecord(recordId: string) {
    return this.client.get<{ record: HarvestRecord }>(
      `/api/v2/harvest/records/${recordId}`
    );
  }

  async createRecord(data: {
    plan_id: string;
    plot_id: string;
    germplasm_name?: string;
    wet_weight: number;
    moisture_content?: number;
    quality_grade?: string;
    storage_unit?: string;
    notes?: string;
  }) {
    return this.client.post<{ record: HarvestRecord }>("/api/v2/harvest/records", {
      ...data,
      harvest_date: new Date().toISOString().split("T")[0],
    });
  }

  async updateRecord(recordId: string, data: Partial<HarvestRecord>) {
    return this.client.patch<{ record: HarvestRecord }>(
      `/api/v2/harvest/records/${recordId}`,
      data
    );
  }

  async deleteRecord(recordId: string) {
    return this.client.delete<void>(`/api/v2/harvest/records/${recordId}`);
  }

  async getStorage() {
    return this.client.get<{ units: StorageUnit[] }>("/api/v2/harvest/storage");
  }

  async getStorageUnit(unitId: string) {
    return this.client.get<{ unit: StorageUnit }>(
      `/api/v2/harvest/storage/${unitId}`
    );
  }

  async updateStorageUnit(unitId: string, data: Partial<StorageUnit>) {
    return this.client.patch<{ unit: StorageUnit }>(
      `/api/v2/harvest/storage/${unitId}`,
      data
    );
  }

  async getStats() {
    return this.client.get<{ data: HarvestStats }>("/api/v2/harvest/stats");
  }

  // Aliases for compatibility with HarvestLog.tsx
  async getHarvestRecords(params?: { search?: string; quality?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append("search", params.search);
    if (params?.quality) queryParams.append("quality", params.quality);
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<HarvestRecord[]>(
      `/api/v2/harvest/records${query}`
    );
  }

  async getHarvestSummary() {
    return this.client.get<{
      total_records: number;
      avg_yield: number;
      total_dry_weight: number;
      grade_a_count: number;
      grade_a_percent: number;
      avg_moisture: number;
    }>("/api/v2/harvest/summary");
  }

  async createHarvestRecord(data: any) {
    return this.createRecord(data);
  }
}

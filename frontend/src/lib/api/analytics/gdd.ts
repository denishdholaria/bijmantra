import { ApiClientCore } from "../core/client";

export interface GDDLog {
  id: string;
  organization_id: string;
  field_id?: string;
  crop_name: string;
  planting_date: string;
  log_date: string;
  daily_gdd: number;
  cumulative_gdd: number;
  base_temperature: number;
  growth_stage?: string;
}

export interface GDDPrediction {
  id: string;
  field_id: string;
  crop_name: string;
  prediction_date: string;
  target_stage: string;
  predicted_date: string;
  predicted_gdd: number;
  confidence: number;
}

export class GDDService {
  constructor(private client: ApiClientCore) {}

  async calculate(params: {
    tmax: number;
    tmin: number;
    tbase?: number;
    method?: string;
  }) {
    const query = new URLSearchParams({
      tmax: String(params.tmax),
      tmin: String(params.tmin),
      tbase: String(params.tbase || 10),
      method: params.method || "standard",
    }).toString();
    return this.client.post<any>(`/api/v2/gdd/calculate?${query}`, {});
  }

  async predictGrowthStages(params: {
    crop_name: string;
    cumulative_gdd: number;
    planting_date: string;
    current_date?: string;
  }) {
    const query = new URLSearchParams({
      crop_name: params.crop_name,
      cumulative_gdd: String(params.cumulative_gdd),
      planting_date: params.planting_date,
      ...(params.current_date ? { current_date: params.current_date } : {}),
    }).toString();
    return this.client.post<any>(
      `/api/v2/gdd/predict/growth-stages?${query}`,
      {}
    );
  }

  async getFieldSummary(fieldId: string) {
    return this.client.get<any>(`/api/v2/gdd/field/${fieldId}/summary`);
  }

  async getFieldHistory(fieldId: string, startDate: string, endDate: string) {
    const query = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
    }).toString();
    return this.client.get<any>(
      `/api/v2/gdd/field/${fieldId}/history?${query}`
    );
  }

  async getFieldPredictions(fieldId: string) {
    return this.client.get<any>(`/api/v2/gdd/field/${fieldId}/predictions`);
  }

  async createFieldPrediction(fieldId: string, data: any) {
    return this.client.post<any>(`/api/v2/gdd/field/${fieldId}/predict`, data);
  }
}

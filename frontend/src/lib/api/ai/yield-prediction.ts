import { ApiClientCore } from "../core/client";

export interface YieldPredictionRecord {
  id: string;
  organization_id: number;
  field_id: number;
  trial_id?: number;
  crop_name: string;
  variety?: string;
  season: string;
  predicted_yield: number;
  yield_unit: string;
  prediction_date: string;
  lower_bound?: number;
  upper_bound?: number;
  confidence_level: number;
  model_name: string;
  model_version?: string;
  prediction_method?: string;
  weather_factors?: Record<string, any>;
  soil_factors?: Record<string, any>;
  management_factors?: Record<string, any>;
  actual_yield?: number;
  prediction_error?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface YieldPredictionCreate {
  field_id: number;
  trial_id?: number;
  crop_name: string;
  variety?: string;
  season: string;
  predicted_yield: number;
  yield_unit?: string;
  prediction_date: string;
  lower_bound?: number;
  upper_bound?: number;
  confidence_level?: number;
  model_name: string;
  model_version?: string;
  prediction_method?: string;
  weather_factors?: Record<string, any>;
  soil_factors?: Record<string, any>;
  management_factors?: Record<string, any>;
  actual_yield?: number;
  prediction_error?: number;
  notes?: string;
}

export class YieldPredictionService {
  constructor(private client: ApiClientCore) {}

  async list(skip = 0, limit = 100): Promise<YieldPredictionRecord[]> {
    return this.client.get<YieldPredictionRecord[]>(
      `/api/v2/future/yield-prediction?skip=${skip}&limit=${limit}`
    );
  }

  async get(id: number): Promise<YieldPredictionRecord> {
    return this.client.get<YieldPredictionRecord>(
      `/api/v2/future/yield-prediction/${id}`
    );
  }

  async create(data: YieldPredictionCreate): Promise<YieldPredictionRecord> {
    return this.client.post<YieldPredictionRecord>(
      "/api/v2/future/yield-prediction",
      data
    );
  }

  async delete(id: number): Promise<void> {
    return this.client.delete<void>(`/api/v2/future/yield-prediction/${id}`);
  }

  async getByField(fieldId: number): Promise<YieldPredictionRecord[]> {
    return this.client.get<YieldPredictionRecord[]>(
      `/api/v2/future/yield-prediction/field/${fieldId}`
    );
  }

  async getLatestByField(fieldId: number): Promise<YieldPredictionRecord> {
    return this.client.get<YieldPredictionRecord>(
      `/api/v2/future/yield-prediction/field/${fieldId}/latest`
    );
  }

  async getByTrial(trialId: number): Promise<YieldPredictionRecord[]> {
    return this.client.get<YieldPredictionRecord[]>(
      `/api/v2/future/yield-prediction/trial/${trialId}`
    );
  }
}

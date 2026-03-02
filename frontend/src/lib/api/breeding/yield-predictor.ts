import { ApiClientCore } from "../core/client";

export interface YieldPrediction {
  germplasm_id: string;
  germplasm_name: string;
  predicted_yield: number;
  confidence_low: number;
  confidence_high: number;
  environment: string;
  model_accuracy?: number;
}

export interface EnvironmentalFactor {
  name: string;
  value: number;
  unit: string;
  optimal: [number, number];
  impact: "positive" | "negative" | "neutral";
}

export class YieldPredictorService {
  constructor(private client: ApiClientCore) {}

  async getPredictions(params?: {
    environment?: string;
    model?: string;
  }): Promise<{
    predictions: YieldPrediction[];
    model_accuracy: number;
    avg_yield: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.environment && params.environment !== "all")
      queryParams.append("environment", params.environment);
    if (params?.model) queryParams.append("model", params.model);
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.request<{
      predictions: YieldPrediction[];
      model_accuracy: number;
      avg_yield: number;
    }>(`/api/v2/genomic-selection/yield-predictions${query}`);
  }

  async runPrediction(params: {
    germplasm_ids?: string[];
    environment?: string;
    model?: string;
  }): Promise<{ predictions: YieldPrediction[]; job_id: string }> {
    return this.client.request<{
      predictions: YieldPrediction[];
      job_id: string;
    }>("/api/v2/genomic-selection/yield-predictions/run", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async getScenarioAnalysis(params: {
    ndvi: number;
    rainfall: number;
    temperature: number;
    soil_moisture?: number;
  }): Promise<{
    predicted_yield: number;
    confidence_interval: [number, number];
    factors: EnvironmentalFactor[];
  }> {
    return this.client.request<{
      predicted_yield: number;
      confidence_interval: [number, number];
      factors: EnvironmentalFactor[];
    }>("/api/v2/genomic-selection/scenario-analysis", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async getEnvironmentalFactors(
    locationId?: string,
  ): Promise<{ factors: EnvironmentalFactor[] }> {
    const query = locationId ? `?location_id=${locationId}` : "";
    return this.client.request<{ factors: EnvironmentalFactor[] }>(
      `/api/v2/genomic-selection/environmental-factors${query}`,
    );
  }

  async getModels(): Promise<{
    models: Array<{
      id: string;
      name: string;
      accuracy: number;
      description: string;
    }>;
  }> {
    return this.client.request<{
      models: Array<{
        id: string;
        name: string;
        accuracy: number;
        description: string;
      }>;
    }>("/api/v2/genomic-selection/models");
  }
}

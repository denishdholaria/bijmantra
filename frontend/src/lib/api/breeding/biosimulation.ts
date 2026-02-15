import { ApiClientCore } from "../core/client";

export interface DailyWeatherData {
  date: string;
  t_max: number;
  t_min: number;
  par: number; // Photosynthetically Active Radiation
}

export interface SimulationRequest {
  crop_model_id: number;
  location_id: number;
  start_date: string; // ISO Date
  daily_weather_data: DailyWeatherData[];
}

export interface SimulationResponse {
  run_id: number;
  predicted_flowering_date: string | null;
  predicted_maturity_date: string | null;
  predicted_yield: number | null;
  status: string;
}

export interface CropModelCreate {
  name: string;
  crop_name: string;
  description?: string;
  base_temp?: number;
  gdd_flowering?: number;
  gdd_maturity?: number;
  rue?: number;
}

export class BiosimulationService {
  constructor(private client: ApiClientCore) {}

  async runSimulation(data: SimulationRequest) {
    return this.client.request<SimulationResponse>(
      "/api/v2/biosimulation/run",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );
  }

  async createCropModel(data: CropModelCreate) {
    return this.client.request<{ id: number; name: string }>(
      "/api/v2/biosimulation/models",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );
  }

  async getCropModels() {
    return this.client.request<
      { id: number; name: string; crop_name: string }[]
    >("/api/v2/biosimulation/models", {
      method: "GET",
    });
  }
}

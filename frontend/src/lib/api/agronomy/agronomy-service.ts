
import { ApiClientCore } from "../core/client";

export interface FertilizerRequest {
  crop: string;
  area: number;
  target_yield: number;
  soil_n: number;
  soil_p: number;
  soil_k: number;
}

export interface FertilizerResponse {
  urea: number;
  dap: number;
  mop: number;
  nitrogen_needed: number;
  phosphorus_needed: number;
  potassium_needed: number;
  total_cost: number;
}

export class AgronomyService {
  constructor(private client: ApiClientCore) {}

  async calculateFertilizer(data: FertilizerRequest) {
    return this.client.post<FertilizerResponse>(
      `/api/v2/agronomy/fertilizer/calculate`,
      data
    );
  }

  async getSupportedCrops() {
    return this.client.get<{ crops: string[] }>(
      `/api/v2/agronomy/fertilizer/crops`
    );
  }
}

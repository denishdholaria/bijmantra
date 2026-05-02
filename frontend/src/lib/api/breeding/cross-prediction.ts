import { ApiClientCore } from "../core/client";

export class CrossPredictionService {
  constructor(private client: ApiClientCore) {}

  async predictById(data: {
    parent1_id: string;
    parent2_id: string;
    trait_name?: string;
    selection_intensity?: number;
  }) {
    return this.client.post<any>("/api/v2/crosses/predict-by-id", data);
  }

  async predict(data: any) {
    return this.client.post<any>("/api/v2/crosses/predict", data);
  }

  async rank(data: any) {
    return this.client.post<any>("/api/v2/crosses/rank", data);
  }
}

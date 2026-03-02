
import { ApiClientCore } from "../core/client";

export class DUSService {
  constructor(private client: ApiClientCore) {}

  async getCrops() {
    return this.client.get<{ crops: any[]; total: number }>(
      "/api/v2/dus/crops"
    );
  }

  async getCropTemplate(cropCode: string) {
    return this.client.get<any>(`/api/v2/dus/crops/${cropCode}`);
  }

  async getTrials(params?: { crop_code?: string; year?: string; status?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.crop_code && params.crop_code !== 'all') queryParams.append("crop_code", params.crop_code);
    if (params?.year && params.year !== 'all') queryParams.append("year", params.year);
    if (params?.status) queryParams.append("status", params.status);
    
    return this.client.get<{ trials: any[]; total: number }>(
      `/api/v2/dus/trials?${queryParams.toString()}`
    );
  }

  async createTrial(data: {
    crop_code: string;
    trial_name: string;
    year: number;
    location: string;
    sample_size: number;
    notes?: string;
  }) {
    return this.client.post<any>("/api/v2/dus/trials", data);
  }

  async getTrial(trialId: string) {
    return this.client.get<any>(`/api/v2/dus/trials/${trialId}`);
  }

  async addTrialEntry(
    trialId: string,
    data: {
      variety_name: string;
      is_candidate: boolean;
      is_reference: boolean;
      breeder?: string;
      origin?: string;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/dus/trials/${trialId}/entries`,
      data
    );
  }

  async recordScore(
    trialId: string,
    entryId: string,
    data: {
      character_id: string;
      value: any;
      notes?: string;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/dus/trials/${trialId}/entries/${entryId}/scores`,
      data
    );
  }

  async analyzeDistinctness(trialId: string, entryId: string) {
    return this.client.get<any>(
      `/api/v2/dus/trials/${trialId}/distinctness/${entryId}`
    );
  }

  async generateReport(trialId: string, entryId: string) {
    return this.client.get<any>(
      `/api/v2/dus/trials/${trialId}/report/${entryId}`
    );
  }
}

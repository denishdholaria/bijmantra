import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class TrialService {
  constructor(private client: ApiClientCore) {}

  async getTrials(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/trials?page=${page}&pageSize=${pageSize}`
    );
  }

  async getTrial(trialDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/trials/${trialDbId}`);
  }

  async createTrial(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/trials", data);
  }

  async updateTrial(trialDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/trials/${trialDbId}`,
      data
    );
  }

  async deleteTrial(trialDbId: string) {
    return this.client.delete(`/brapi/v2/trials/${trialDbId}`);
  }
}

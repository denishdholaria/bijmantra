import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class SampleService {
  constructor(private client: ApiClientCore) {}

  async getSamples(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/samples?page=${page}&pageSize=${pageSize}`
    );
  }

  async getSample(sampleDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/samples/${sampleDbId}`);
  }

  async createSample(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/samples", data);
  }

  async deleteSample(sampleDbId: string) {
    return this.client.delete(`/brapi/v2/samples/${sampleDbId}`);
  }
}

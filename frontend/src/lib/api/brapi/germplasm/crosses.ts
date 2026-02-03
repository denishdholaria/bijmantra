import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class CrossService {
  constructor(private client: ApiClientCore) {}

  async getCrossStats() {
    return this.client.get<BrAPIResponse<any>>("/brapi/v2/crosses/stats");
  }

  async getCrosses(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/crosses?page=${page}&pageSize=${pageSize}`
    );
  }

  async getCross(crossDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/crosses/${crossDbId}`);
  }

  async createCross(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/crosses", data);
  }

  async updateCross(crossDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/crosses/${crossDbId}`,
      data
    );
  }

  async deleteCross(crossDbId: string) {
    return this.client.delete(`/brapi/v2/crosses/${crossDbId}`);
  }

  // Pedigree
  async getPedigree(germplasmDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/germplasm/${germplasmDbId}/pedigree`
    );
  }

  // Progeny
  async getProgeny(germplasmDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/germplasm/${germplasmDbId}/progeny`
    );
  }

  // Cross Planning
  async getPlannedCrosses(params?: any) {
    const queryParams = new URLSearchParams(params).toString();
    return this.client.get<BrAPIListResponse<any>>(`/brapi/v2/planned-crosses?${queryParams}`);
  }

  async createPlannedCross(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/planned-crosses", data);
  }

  async updatePlannedCrossStatus(crossId: string, status: string) {
    return this.client.put<BrAPIResponse<any>>(`/brapi/v2/planned-crosses/${crossId}/status`, { status });
  }

  async getCrossingPlannerStats() {
    return this.client.get<BrAPIResponse<any>>("/brapi/v2/planned-crosses/stats");
  }

  async getCrossingPlannerGermplasm() {
    return this.client.get<BrAPIListResponse<any>>("/brapi/v2/planned-crosses/germplasm");
  }
}

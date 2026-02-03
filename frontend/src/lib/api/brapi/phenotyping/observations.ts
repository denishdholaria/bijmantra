import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class ObservationService {
  constructor(private client: ApiClientCore) {}

  async getObservationVariables(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/variables?page=${page}&pageSize=${pageSize}`
    );
  }

  async getObservations(studyDbId?: string, page = 0, pageSize = 100) {
    const params = new URLSearchParams({
      page: String(page),
      pageSize: String(pageSize),
    });
    if (studyDbId) params.append("studyDbId", studyDbId);
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/observations?${params}`
    );
  }

  async createObservations(data: any[]) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/observations", data);
  }

  async getObservationVariable(observationVariableDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/variables/${observationVariableDbId}`
    );
  }

  async createObservationVariable(data: any[]) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/variables", data);
  }

  async updateObservationVariable(observationVariableDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/variables/${observationVariableDbId}`,
      data
    );
  }

  async deleteObservationVariable(observationVariableDbId: string) {
    return this.client.delete(`/brapi/v2/variables/${observationVariableDbId}`);
  }

  async getObservationUnits(studyDbId?: string, page = 0, pageSize = 100) {
    const params = new URLSearchParams({
      page: String(page),
      pageSize: String(pageSize),
    });
    if (studyDbId) params.append("studyDbId", studyDbId);
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/observationunits?${params}`
    );
  }

  async createObservationUnits(data: any[]) {
    return this.client.post<BrAPIResponse<any>>(
      "/brapi/v2/observationunits",
      data
    );
  }

  async searchObservations(searchRequest: any) {
    return this.client.post<BrAPIListResponse<any>>(
      "/brapi/v2/search/observations",
      searchRequest
    );
  }
}

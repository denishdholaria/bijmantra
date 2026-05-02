import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class StudyService {
  constructor(private client: ApiClientCore) {}

  async getStudies(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/studies?page=${page}&pageSize=${pageSize}`
    );
  }

  async getStudy(studyDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/studies/${studyDbId}`);
  }

  async createStudy(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/studies", data);
  }

  async updateStudy(studyDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/studies/${studyDbId}`,
      data
    );
  }

  async deleteStudy(studyDbId: string) {
    return this.client.delete(`/brapi/v2/studies/${studyDbId}`);
  }
}

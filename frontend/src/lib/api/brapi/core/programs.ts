import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class ProgramService {
  constructor(private client: ApiClientCore) {}

  async getPrograms(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/programs?page=${page}&pageSize=${pageSize}`
    );
  }

  async getProgram(programDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/programs/${programDbId}`
    );
  }

  async createProgram(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/programs", data);
  }

  async updateProgram(programDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/programs/${programDbId}`,
      data
    );
  }

  async deleteProgram(programDbId: string) {
    return this.client.delete(`/brapi/v2/programs/${programDbId}`);
  }
}

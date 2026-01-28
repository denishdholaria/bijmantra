import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class ListService {
  constructor(private client: ApiClientCore) {}

  async getLists(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/lists?page=${page}&pageSize=${pageSize}`
    );
  }

  async getList(listDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/lists/${listDbId}`);
  }

  async createList(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/lists", data);
  }

  async deleteList(listDbId: string) {
    return this.client.delete(`/brapi/v2/lists/${listDbId}`);
  }
}

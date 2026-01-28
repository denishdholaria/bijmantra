import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class GermplasmService {
  constructor(private client: ApiClientCore) {}

  async getGermplasm(page = 0, pageSize = 100, search?: string) {
    const params = new URLSearchParams({
      page: String(page),
      pageSize: String(pageSize),
    });
    if (search) params.append("germplasmName", search);
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/germplasm?${params}`
    );
  }

  async getGermplasmById(germplasmDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/germplasm/${germplasmDbId}`
    );
  }

  async createGermplasm(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/germplasm", data);
  }

  async updateGermplasm(germplasmDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/germplasm/${germplasmDbId}`,
      data
    );
  }

  async deleteGermplasm(germplasmDbId: string) {
    return this.client.delete(`/brapi/v2/germplasm/${germplasmDbId}`);
  }
}

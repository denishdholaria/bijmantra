import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class SeedLotService {
  constructor(private client: ApiClientCore) {}

  async getSeedLots(germplasmDbId?: string, page = 0, pageSize = 100) {
    const params = new URLSearchParams({
      page: String(page),
      pageSize: String(pageSize),
    });
    if (germplasmDbId) params.append("germplasmDbId", germplasmDbId);
    return this.client.get<BrAPIListResponse<any>>(`/brapi/v2/seedlots?${params}`);
  }

  async createSeedLot(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/seedlots", data);
  }

  async getSeedLot(seedLotDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/seedlots/${seedLotDbId}`);
  }

  async updateSeedLot(seedLotDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/seedlots/${seedLotDbId}`,
      data
    );
  }

  async deleteSeedLot(seedLotDbId: string) {
    return this.client.delete(`/brapi/v2/seedlots/${seedLotDbId}`);
  }

  async getSeedlotTransactionsById(seedLotDbId: string, params?: any) {
    const queryParams = new URLSearchParams(params).toString();
    return this.client.get<BrAPIListResponse<any>>(`/brapi/v2/seedlots/${seedLotDbId}/transactions?${queryParams}`);
  }

  async createSeedlotTransaction(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/seedlots/transactions", data);
  }
}

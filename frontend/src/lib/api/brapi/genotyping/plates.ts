import { ApiClientCore } from "../../core/client";
import { BrAPIListResponse, BrAPIResponse } from "../../core/types";

export class PlatesService {
  constructor(private client: ApiClientCore) {}

  async getPlates(params?: {
    plateBarcode?: string;
    plateName?: string;
    sampleDbId?: string;
    studyDbId?: string;
    trialDbId?: string;
    programDbId?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.plateBarcode)
      searchParams.append("plateBarcode", params.plateBarcode);
    if (params?.plateName) searchParams.append("plateName", params.plateName);
    if (params?.sampleDbId)
      searchParams.append("sampleDbId", params.sampleDbId);
    if (params?.studyDbId) searchParams.append("studyDbId", params.studyDbId);
    if (params?.trialDbId) searchParams.append("trialDbId", params.trialDbId);
    if (params?.programDbId)
      searchParams.append("programDbId", params.programDbId);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/plates?${searchParams}`
    );
  }

  async getPlate(plateDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/plates/${plateDbId}`);
  }

  async createPlates(plates: any[]) {
    return this.client.post<BrAPIListResponse<any>>("/brapi/v2/plates", plates);
  }

  async updatePlates(plates: any[]) {
    return this.client.put<BrAPIListResponse<any>>("/brapi/v2/plates", plates);
  }

  async deletePlate(plateDbId: string) {
    return this.client.delete<any>(`/brapi/v2/plates/${plateDbId}`);
  }

  // Vendor Orders
  async getVendorOrders(params?: any) {
    const queryParams = new URLSearchParams(params).toString();
    return this.client.get<BrAPIListResponse<any>>(`/brapi/v2/vendor/orders?${queryParams}`);
  }

  async createVendorOrder(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/vendor/orders", data);
  }

  async updateVendorOrderStatus(orderId: string, status: string) {
    return this.client.put<BrAPIResponse<any>>(`/brapi/v2/vendor/orders/${orderId}/status`, { status });
  }
}

import { ApiClientCore } from "../../core/client";
import { BrAPIListResponse, BrAPIResponse } from "../../core/types";

export class ScalesService {
  constructor(private client: ApiClientCore) {}

  async getScales(params?: {
    scaleDbId?: string;
    scaleName?: string;
    dataType?: string;
    ontologyDbId?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.scaleDbId) searchParams.append("scaleDbId", params.scaleDbId);
    if (params?.scaleName) searchParams.append("scaleName", params.scaleName);
    if (params?.dataType) searchParams.append("dataType", params.dataType);
    if (params?.ontologyDbId)
      searchParams.append("ontologyDbId", params.ontologyDbId);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/scales?${searchParams}`
    );
  }

  async getScale(scaleDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/scales/${scaleDbId}`);
  }

  async createScales(scales: any[]) {
    return this.client.post<BrAPIListResponse<any>>("/brapi/v2/scales", scales);
  }

  async updateScale(scaleDbId: string, scale: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/scales/${scaleDbId}`,
      scale
    );
  }

  async deleteScale(scaleDbId: string) {
    return this.client.delete<any>(`/brapi/v2/scales/${scaleDbId}`);
  }
}

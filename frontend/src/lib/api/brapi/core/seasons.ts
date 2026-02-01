import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class SeasonService {
  constructor(private client: ApiClientCore) {}

  async getSeasons(page = 0, pageSize = 100, year?: number) {
    const params = new URLSearchParams({
      page: String(page),
      pageSize: String(pageSize),
    });
    if (year) params.append("year", String(year));
    return this.client.get<BrAPIListResponse<any>>(`/brapi/v2/seasons?${params}`);
  }

  async getSeason(seasonDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/seasons/${seasonDbId}`);
  }

  async createSeason(data: { seasonName: string; year?: number }) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/seasons", data);
  }

  async updateSeason(
    seasonDbId: string,
    data: { seasonName?: string; year?: number }
  ) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/seasons/${seasonDbId}`,
      data
    );
  }

  async deleteSeason(seasonDbId: string) {
    return this.client.delete(`/brapi/v2/seasons/${seasonDbId}`);
  }
}

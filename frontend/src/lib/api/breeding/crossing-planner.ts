import { ApiClientCore } from "../core/client";

export class CrossingPlannerService {
  constructor(private client: ApiClientCore) {}

  async getPlannedCrosses(params?: {
    status?: string;
    priority?: string;
    season?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append("status", params.status);
    if (params?.priority) searchParams.append("priority", params.priority);
    if (params?.season) searchParams.append("season", params.season);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<any>(`/api/v2/crossing-planner?${searchParams}`);
  }

  async createPlannedCross(data: {
    femaleParentId: string;
    maleParentId: string;
    objective?: string;
    priority?: string;
    targetDate?: string;
    expectedProgeny?: number;
  }) {
    return this.client.post<any>("/api/v2/crossing-planner", data);
  }

  async updatePlannedCrossStatus(
    crossId: string,
    status: string,
    actualProgeny?: number,
  ) {
    return this.client.put<any>(`/api/v2/crossing-planner/${crossId}/status`, {
      status,
      actualProgeny,
    });
  }

  async deletePlannedCross(crossId: string) {
    return this.client.delete<any>(`/api/v2/crossing-planner/${crossId}`);
  }

  async getCrossingPlannerStats() {
    return this.client.get<any>("/api/v2/crossing-planner/statistics");
  }

  async getCrossingPlannerGermplasm(search?: string) {
    const params = search ? `?search=${encodeURIComponent(search)}` : "";
    return this.client.get<any>(`/api/v2/crossing-planner/germplasm${params}`);
  }
}

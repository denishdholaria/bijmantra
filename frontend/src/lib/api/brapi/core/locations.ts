import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class LocationService {
  constructor(private client: ApiClientCore) {}

  async getLocations(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/locations?page=${page}&pageSize=${pageSize}`
    );
  }

  async getLocation(locationDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/locations/${locationDbId}`
    );
  }

  async createLocation(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/locations", data);
  }

  async updateLocation(locationDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/locations/${locationDbId}`,
      data
    );
  }

  async deleteLocation(locationDbId: string) {
    return this.client.delete(`/brapi/v2/locations/${locationDbId}`);
  }
}

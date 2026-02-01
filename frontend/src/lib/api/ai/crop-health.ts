import { ApiClientCore } from "../core/client";

export class CropHealthService {
  constructor(private client: ApiClientCore) {}

  async getHealthStatus(locationId: string) {
    return this.client.get<any>(
      `/api/v2/crop-health/status?location_id=${locationId}`
    );
  }

  async getTrends(days?: number) {
    const query = days ? `?days=${days}` : "";
    return this.client.get<{
      status: string;
      data: any[];
      period_days: number;
    }>(`/api/v2/crop-health/trends${query}`);
  }

  async getLocations() {
    return this.client.get<{ status: string; data: string[]; count: number }>(
      "/api/v2/crop-health/locations"
    );
  }

  async getCrops() {
    return this.client.get<{ status: string; data: string[]; count: number }>(
      "/api/v2/crop-health/crops"
    );
  }

  async getTrials(params?: { location?: string; crop?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.location) searchParams.set("location", params.location);
    if (params?.crop) searchParams.set("crop", params.crop);
    const query = searchParams.toString();
    return this.client.get<{ data: any[] }>(`/api/v2/crop-health/trials${query ? `?${query}` : ""}`);
  }

  async getAlerts(params?: { acknowledged?: boolean }) {
    const searchParams = new URLSearchParams();
    if (params?.acknowledged !== undefined) searchParams.set("acknowledged", String(params.acknowledged));
    const query = searchParams.toString();
    return this.client.get<{ data: any[] }>(`/api/v2/crop-health/alerts${query ? `?${query}` : ""}`);
  }

  async getSummary() {
    return this.client.get<any>("/api/v2/crop-health/summary");
  }

  async acknowledgeAlert(alertId: string) {
    return this.client.post<any>(
      `/api/v2/crop-health/alerts/${alertId}/acknowledge`,
      {}
    );
  }
}

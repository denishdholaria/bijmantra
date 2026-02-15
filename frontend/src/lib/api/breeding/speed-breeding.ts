import { ApiClientCore } from "../core/client";

export class SpeedBreedingService {
  constructor(private client: ApiClientCore) {}

  async getSpeedBreedingProtocols(params?: { crop?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append("crop", params.crop);
    return this.client.get<any[]>(
      `/api/v2/speed-breeding/protocols?${searchParams}`
    );
  }

  async getSpeedBreedingBatches() {
    return this.client.get<any[]>("/api/v2/speed-breeding/batches");
  }

  async getSpeedBreedingChambers() {
    return this.client.get<any[]>("/api/v2/speed-breeding/chambers");
  }

  async getSpeedBreedingStatistics() {
    return this.client.get<{
      active_batches: number;
      total_entries: number;
      avg_generations_per_year: number;
      chambers_in_use: number;
    }>("/api/v2/speed-breeding/statistics");
  }
}

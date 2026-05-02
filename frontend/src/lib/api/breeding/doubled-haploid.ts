import { ApiClientCore } from "../core/client";

export class DoubledHaploidService {
  constructor(private client: ApiClientCore) {}

  async getProtocols(params?: { crop?: string; method?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append("crop", params.crop);
    if (params?.method) searchParams.append("method", params.method);
    return this.client.get<any[]>(
      `/api/v2/doubled-haploid/protocols?${searchParams}`
    );
  }

  async getBatches() {
    return this.client.get<any[]>("/api/v2/doubled-haploid/batches");
  }

  async getStatistics() {
    return this.client.get<{
      total_protocols: number;
      active_batches: number;
      total_dh_lines_produced: number;
      avg_efficiency: number;
    }>("/api/v2/doubled-haploid/statistics");
  }
}

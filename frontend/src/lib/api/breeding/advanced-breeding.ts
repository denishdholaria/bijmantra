import { ApiClientCore } from "../core/client";

export class AdvancedBreedingService {
  constructor(private client: ApiClientCore) {}

  // ============================================
  // SPEED BREEDING
  // ============================================

  async getSpeedBreedingProtocols(params?: { crop?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append("crop", params.crop);
    if (params?.status) searchParams.append("status", params.status);
    return this.client.get<any>(
      `/api/v2/speed-breeding/protocols?${searchParams}`
    );
  }

  async getSpeedBreedingProtocol(protocolId: string) {
    return this.client.get<any>(`/api/v2/speed-breeding/protocols/${protocolId}`);
  }

  async getSpeedBreedingBatches(params?: {
    protocol_id?: string;
    status?: string;
    chamber?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.protocol_id)
      searchParams.append("protocol_id", params.protocol_id);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.chamber) searchParams.append("chamber", params.chamber);
    return this.client.get<any>(`/api/v2/speed-breeding/batches?${searchParams}`);
  }

  async getSpeedBreedingBatch(batchId: string) {
    return this.client.get<any>(`/api/v2/speed-breeding/batches/${batchId}`);
  }

  async calculateSpeedBreedingTimeline(
    protocolId: string,
    targetGeneration: string,
    startDate?: string
  ) {
    return this.client.post<any>("/api/v2/speed-breeding/timeline", {
      protocol_id: protocolId,
      target_generation: targetGeneration,
      start_date: startDate,
    });
  }

  async getSpeedBreedingChambers() {
    return this.client.get<any>("/api/v2/speed-breeding/chambers");
  }

  async getSpeedBreedingStatistics() {
    return this.client.get<any>("/api/v2/speed-breeding/statistics");
  }

  // ============================================
  // DOUBLED HAPLOID
  // ============================================

  async getDoubledHaploidProtocols(params?: {
    crop?: string;
    method?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append("crop", params.crop);
    if (params?.method) searchParams.append("method", params.method);
    return this.client.get<any>(
      `/api/v2/doubled-haploid/protocols?${searchParams}`
    );
  }

  async getDoubledHaploidProtocol(protocolId: string) {
    return this.client.get<any>(
      `/api/v2/doubled-haploid/protocols/${protocolId}`
    );
  }

  async getDoubledHaploidBatches(params?: {
    protocol_id?: string;
    status?: string;
    stage?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.protocol_id)
      searchParams.append("protocol_id", params.protocol_id);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.stage) searchParams.append("stage", params.stage);
    return this.client.get<any>(
      `/api/v2/doubled-haploid/batches?${searchParams}`
    );
  }

  async getDoubledHaploidBatch(batchId: string) {
    return this.client.get<any>(`/api/v2/doubled-haploid/batches/${batchId}`);
  }

  async calculateDoubledHaploidEfficiency(
    protocolId: string,
    data: {
      initial_explants: number;
      embryos?: number;
      green_plants?: number;
      doubled_haploids?: number;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/doubled-haploid/efficiency/${protocolId}`,
      data
    );
  }

  async getDoubledHaploidStatistics() {
    return this.client.get<any>("/api/v2/doubled-haploid/statistics");
  }

  async getDoubledHaploidLaboratories() {
    return this.client.get<any>("/api/v2/doubled-haploid/laboratories");
  }
}

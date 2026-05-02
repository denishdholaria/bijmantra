import { ApiClientCore } from "../core/client";

export interface Sample {
  id: string;
  sampleId: string;
  type: "leaf" | "seed" | "dna";
  source: string;
  status: "collected" | "processing" | "stored" | "shipped";
  location: string;
  collectedAt: string;
  processedAt?: string;
}

export class SampleTrackingService {
  constructor(private client: ApiClientCore) {}

  async getSamples(params?: {
    status?: string;
    type?: string;
    search?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.type) searchParams.set("type", params.type);
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    return this.client.get<{ data: Sample[]; total: number }>(
      `/api/v2/samples/tracking${query ? `?${query}` : ""}`
    );
  }

  async getSample(sampleId: string) {
    return this.client.get<{ data: Sample }>(
      `/api/v2/samples/tracking/${sampleId}`
    );
  }

  async createSample(data: Partial<Sample>) {
    return this.client.post<{ data: Sample }>("/api/v2/samples/tracking", data);
  }

  async updateSample(sampleId: string, data: Partial<Sample>) {
    return this.client.patch<{ data: Sample }>(
      `/api/v2/samples/tracking/${sampleId}`,
      data
    );
  }

  async getStats() {
    return this.client.get<{
      total: number;
      collected: number;
      processing: number;
      stored: number;
      shipped: number;
    }>("/api/v2/samples/tracking/stats");
  }

  async generateLabels(sampleIds: string[]) {
    return this.client.post<Blob>("/api/v2/samples/tracking/labels", {
      sample_ids: sampleIds,
    });
  }
}

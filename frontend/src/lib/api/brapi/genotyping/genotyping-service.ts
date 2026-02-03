import { ApiClientCore } from "../../core/client";

export class GenotypingService {
  constructor(private client: ApiClientCore) {}

  async getAlleleMatrix(params?: Record<string, any>) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.append(key, String(value));
      });
    }
    const query = searchParams.toString();
    return this.client.get<any>(`/api/v2/genotyping/allele-matrix${query ? `?${query}` : ""}`);
  }

  async getVariantSets(params?: Record<string, any>) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.append(key, String(value));
      });
    }
    const query = searchParams.toString();
    return this.client.get<any>(`/api/v2/genotyping/variant-sets${query ? `?${query}` : ""}`);
  }

  async getCalls(params?: Record<string, any>) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.append(key, String(value));
      });
    }
    const query = searchParams.toString();
    return this.client.get<any>(`/api/v2/genotyping/calls${query ? `?${query}` : ""}`);
  }

  async getCallSets(params?: Record<string, any>) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.append(key, String(value));
      });
    }
    const query = searchParams.toString();
    return this.client.get<any>(`/api/v2/genotyping/call-sets${query ? `?${query}` : ""}`);
  }

  async getGenotypingSummary() {
    return this.client.get<any>("/api/v2/genotyping/summary");
  }
}

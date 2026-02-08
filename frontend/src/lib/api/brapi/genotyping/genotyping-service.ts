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
    return this.client.get<any>(`/api/v2/genotyping/variantsets${query ? `?${query}` : ""}`);
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
    return this.client.get<any>(`/api/v2/genotyping/callsets${query ? `?${query}` : ""}`);
  }

  async getGenotypingSummary() {
    return this.client.get<any>("/api/v2/genotyping/summary");
  }

  /**
   * Import VCF file
   */
  async importVCF(formData: FormData) {
    return this.client.post<any>("/api/v2/genotyping/import", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  }
}

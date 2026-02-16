import { ApiClientCore } from "../core/client";

export interface SeedlingBatch {
  id: string;
  germplasm: string;
  sowingDate: string;
  expectedTransplant: string;
  quantity: number;
  germinated: number;
  healthy: number;
  status: "sowing" | "germinating" | "growing" | "ready" | "transplanted";
  location: string;
}

export interface SeedlingStats {
  total: number;
  sowing: number;
  growing: number;
  ready: number;
  totalSeedlings: number;
}

export class SeedlingBatchService {
  constructor(private client: ApiClientCore) {}
  async getBatches(params?: {
    status?: string;
    location?: string;
  }): Promise<{ success: boolean; count: number; batches: SeedlingBatch[] }> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append("status", params.status);
    if (params?.location) searchParams.append("location", params.location);
    const query = searchParams.toString();
    return this.client.get<{ success: boolean; count: number; batches: SeedlingBatch[] }>(
      `/api/v2/nursery-management/batches${query ? `?${query}` : ""}`
    );
  }

  async getBatch(
    batchId: string,
  ): Promise<{ success: boolean } & SeedlingBatch> {
    return this.client.get<{ success: boolean } & SeedlingBatch>(
      `/api/v2/nursery-management/batches/${batchId}`
    );
  }

  async createBatch(data: {
    germplasm: string;
    sowingDate: string;
    expectedTransplant: string;
    quantity: number;
    location: string;
  }): Promise<{ success: boolean; message: string } & SeedlingBatch> {
    return this.client.post<{ success: boolean; message: string } & SeedlingBatch>(
      "/api/v2/nursery-management/batches",
      data
    );
  }

  async updateBatchStatus(
    batchId: string,
    status: string,
  ): Promise<{ success: boolean; message: string }> {
    return this.client.patch<{ success: boolean; message: string }>(
      `/api/v2/nursery-management/batches/${batchId}/status`,
      { status }
    );
  }

  async updateBatchCounts(
    batchId: string,
    data: { germinated?: number; healthy?: number },
  ): Promise<{ success: boolean; message: string }> {
    return this.client.patch<{ success: boolean; message: string }>(
      `/api/v2/nursery-management/batches/${batchId}/counts`,
      data
    );
  }

  async deleteBatch(
    batchId: string,
  ): Promise<{ success: boolean; message: string }> {
    return this.client.delete<{ success: boolean; message: string }>(
      `/api/v2/nursery-management/batches/${batchId}`
    );
  }

  async getStats(): Promise<{ success: boolean } & SeedlingStats> {
    return this.client.get<{ success: boolean } & SeedlingStats>(
      "/api/v2/nursery-management/stats"
    );
  }

  async getLocations(): Promise<{ success: boolean; locations: string[] }> {
    return this.client.get<{ success: boolean; locations: string[] }>(
      "/api/v2/nursery-management/locations"
    );
  }

  async getGermplasmList(): Promise<{
    success: boolean;
    germplasm: Array<{ id: string; name: string }>;
  }> {
    return this.client.get<{ success: boolean; germplasm: Array<{ id: string; name: string }> }>(
      "/api/v2/nursery-management/germplasm"
    );
  }
}

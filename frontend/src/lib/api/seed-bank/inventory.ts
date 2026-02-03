import { ApiClientCore } from "../core/client";
import { SeedLot, ViabilityTest, SeedInventorySummary } from "./types";

export class InventoryService {
  constructor(private client: ApiClientCore) {}

  async getLots(params?: {
    species?: string;
    status?: string;
    storage_type?: string;
  }): Promise<{ success: boolean; count: number; lots: SeedLot[] }> {
    const searchParams = new URLSearchParams();
    if (params?.species) searchParams.append("species", params.species);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.storage_type)
      searchParams.append("storage_type", params.storage_type);
    const query = searchParams.toString();
    return this.client.get<{ success: boolean; count: number; lots: SeedLot[] }>(
      `/api/v2/seed-inventory/lots${query ? `?${query}` : ""}`
    );
  }

  async getLot(
    lotId: string,
  ): Promise<
    { success: boolean } & SeedLot & { viability_history: ViabilityTest[] }
  > {
    return this.client.get(
      `/api/v2/seed-inventory/lots/${lotId}`
    );
  }

  async registerLot(data: {
    accession_id: string;
    species: string;
    variety: string;
    harvest_date: string;
    quantity: number;
    storage_type: string;
    storage_location: string;
    initial_viability: number;
    notes?: string;
  }): Promise<{ success: boolean; message: string } & SeedLot> {
    return this.client.post(
      "/api/v2/seed-inventory/lots",
      data
    );
  }

  async recordViabilityTest(data: {
    lot_id: string;
    test_date: string;
    seeds_tested: number;
    seeds_germinated: number;
    test_method: string;
    tester: string;
    notes?: string;
  }): Promise<{ success: boolean; message: string } & ViabilityTest> {
    return this.client.post(
      "/api/v2/seed-inventory/viability",
      data
    );
  }

  async getViabilityHistory(
    lotId: string,
  ): Promise<{
    success: boolean;
    lot_id: string;
    test_count: number;
    tests: ViabilityTest[];
  }> {
    return this.client.get(
      `/api/v2/seed-inventory/viability/${lotId}`
    );
  }

  async createRequest(data: {
    lot_id: string;
    requester: string;
    institution: string;
    quantity: number;
    purpose?: string;
  }): Promise<{ success: boolean; message: string; request_id: string }> {
    return this.client.post(
      "/api/v2/seed-inventory/requests",
      data
    );
  }

  async approveRequest(
    requestId: string,
    quantityApproved: number,
  ): Promise<{ success: boolean; message: string }> {
    return this.client.post(
      `/api/v2/seed-inventory/requests/${requestId}/approve`,
      { quantity_approved: quantityApproved }
    );
  }

  async shipRequest(
    requestId: string,
  ): Promise<{ success: boolean; message: string }> {
    return this.client.post(
      `/api/v2/seed-inventory/requests/${requestId}/ship`,
      {}
    );
  }

  async getSummary(): Promise<SeedInventorySummary> {
    return this.client.get<SeedInventorySummary>("/api/v2/seed-inventory/summary");
  }

  async getAlerts(): Promise<{
    success: boolean;
    alert_count: number;
    alerts: Array<{
      type: string;
      lot_id: string;
      message: string;
      severity: string;
    }>;
  }> {
    return this.client.get("/api/v2/seed-inventory/alerts");
  }

  async getStorageTypes(): Promise<{
    storage_types: Array<{
      id: string;
      name: string;
      temperature: string;
      expected_viability: string;
      use_case: string;
    }>;
  }> {
    return this.client.get("/api/v2/seed-inventory/storage-types");
  }
}

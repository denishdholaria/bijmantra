import { ApiClientCore } from "../core/client";
import { BrAPIListResponse, BrAPIResponse } from "../core/types";

export class SeedOperationsService {
  constructor(private client: ApiClientCore) {}

  // Quality Control
  async getQCSamples(status?: string) {
    const query = status ? `?status=${status}` : "";
    return this.client.get<{ samples: any[] }>(`/api/v2/seed-operations/qc-samples${query}`);
  }

  async getQCCertificates() {
    return this.client.get<{ certificates: any[] }>("/api/v2/seed-operations/certificates");
  }

  async issueQCCertificate(data: any) {
    return this.client.post("/api/v2/seed-operations/certificates", data);
  }

  async getQCSummary() {
    return this.client.get<{ pending: number }>("/api/v2/seed-operations/qc-summary");
  }

  async getQCTestTypes() {
    return this.client.get<{ test_types: any[] }>("/api/v2/seed-operations/test-types");
  }

  async getQCSeedClasses() {
    return this.client.get<{ seed_classes: any[] }>("/api/v2/seed-operations/seed-classes");
  }

  async recordQCTest(data: any) {
    return this.client.post("/api/v2/seed-operations/test-results", data);
  }

  // Inventory
  async getSeedInventoryLots() {
    return this.client.get<{ success: boolean; lots: any[] }>("/api/v2/seed-operations/inventory");
  }

  async getSeedInventorySummary() {
    return this.client.get<{
      success: boolean;
      total_lots: number;
      total_quantity_g: number;
      by_status: { low_stock: number; active: number };
    }>("/api/v2/seed-operations/inventory/summary");
  }

  async getSeedInventoryAlerts() {
    return this.client.get<{ alert_count: number }>("/api/v2/seed-operations/inventory/alerts");
  }

  async registerSeedInventoryLot(data: any) {
    return this.client.post("/api/v2/seed-operations/inventory", data);
  }

  // Traceability
  async getTraceabilityStatistics() {
    return this.client.get<{ data: { active_lots: number; certified_lots: number } }>(
      "/api/v2/seed-operations/traceability/stats"
    );
  }
}

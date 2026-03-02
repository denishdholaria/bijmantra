import { ApiClientCore } from "../core/client";

export class TraceabilityService {
  constructor(private client: ApiClientCore) {}

  async getTraceabilityTransfers() {
    return this.client.get<{ status: string; data: any[]; count: number }>(
      "/api/v2/traceability/transfers"
    );
  }

  async getTraceabilityLots(
    crop?: string,
    varietyId?: string,
    seedClass?: string,
    status?: string
  ) {
    const params = new URLSearchParams();
    if (crop) params.append("crop", crop);
    if (varietyId) params.append("variety_id", varietyId);
    if (seedClass) params.append("seed_class", seedClass);
    if (status) params.append("status", status);
    return this.client.get<any>(`/api/v2/traceability/lots?${params}`);
  }

  async getTraceabilityLot(lotId: string) {
    return this.client.get<any>(`/api/v2/traceability/lots/${lotId}`);
  }

  async registerTraceabilityLot(data: {
    variety_id: string;
    variety_name: string;
    crop: string;
    seed_class: string;
    production_year: number;
    production_season: string;
    production_location: string;
    producer_id: string;
    producer_name: string;
    quantity_kg: number;
    parent_lot_id?: string;
    germination_percent?: number;
    purity_percent?: number;
    moisture_percent?: number;
  }) {
    return this.client.post<any>("/api/v2/traceability/lots", data);
  }

  async recordTraceabilityEvent(
    lotId: string,
    data: {
      event_type: string;
      details: Record<string, any>;
      operator_id?: string;
      operator_name?: string;
      location?: string;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/traceability/lots/${lotId}/events`,
      data
    );
  }

  async getLotHistory(lotId: string) {
    return this.client.get<any>(`/api/v2/traceability/lots/${lotId}/history`);
  }

  async addLotCertification(
    lotId: string,
    data: {
      cert_type: string;
      cert_number: string;
      issuing_authority: string;
      issue_date: string;
      expiry_date: string;
      test_results?: Record<string, any>;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/traceability/lots/${lotId}/certifications`,
      data
    );
  }

  async getLotCertifications(lotId: string) {
    return this.client.get<any>(
      `/api/v2/traceability/lots/${lotId}/certifications`
    );
  }

  async recordLotTransfer(
    lotId: string,
    data: {
      from_entity_id: string;
      from_entity_name: string;
      to_entity_id: string;
      to_entity_name: string;
      quantity_kg: number;
      transfer_type: string;
      price_per_kg?: number;
      invoice_number?: string;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/traceability/lots/${lotId}/transfers`,
      data
    );
  }

  async getLotTransfers(lotId: string) {
    return this.client.get<any>(`/api/v2/traceability/lots/${lotId}/transfers`);
  }

  async traceLotLineage(lotId: string) {
    return this.client.get<any>(`/api/v2/traceability/lots/${lotId}/lineage`);
  }

  async getLotDescendants(lotId: string) {
    return this.client.get<any>(
      `/api/v2/traceability/lots/${lotId}/descendants`
    );
  }

  async getLotQRData(lotId: string) {
    return this.client.get<any>(`/api/v2/traceability/lots/${lotId}/qr`);
  }

  async getTraceabilityEventTypes() {
    return this.client.get<any>("/api/v2/traceability/event-types");
  }

  async getTraceabilityStatistics() {
    return this.client.get<any>("/api/v2/traceability/statistics");
  }
}

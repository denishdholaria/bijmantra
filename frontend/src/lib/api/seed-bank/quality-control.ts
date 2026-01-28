import { ApiClientCore } from "../core/client";

export class QualityControlService {
  constructor(private client: ApiClientCore) {}

  async getQCSamples(status?: string, lotId?: string) {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (lotId) params.append("lot_id", lotId);
    return this.client.get<any>(`/api/v2/quality/samples?${params}`);
  }

  async getQCSample(sampleId: string) {
    return this.client.get<any>(`/api/v2/quality/samples/${sampleId}`);
  }

  async registerQCSample(data: {
    lot_id: string;
    variety: string;
    sample_date: string;
    sample_weight: number;
    source: string;
  }) {
    return this.client.post<any>("/api/v2/quality/samples", data);
  }

  async recordQCTest(data: {
    sample_id: string;
    test_type: string;
    result_value: number;
    tester: string;
    method: string;
    seed_class?: string;
    notes?: string;
  }) {
    return this.client.post<any>("/api/v2/quality/tests", data);
  }

  async issueQCCertificate(data: {
    sample_id: string;
    seed_class: string;
    valid_months?: number;
  }) {
    return this.client.post<any>("/api/v2/quality/certificates", data);
  }

  async getQCCertificates() {
    return this.client.get<{ certificates: any[] }>(
      "/api/v2/quality/certificates"
    );
  }

  async getQCStandards(seedClass: string = "certified") {
    return this.client.get<any>(
      `/api/v2/quality/standards?seed_class=${seedClass}`
    );
  }

  async getQCSummary() {
    return this.client.get<any>("/api/v2/quality/summary");
  }

  async getQCTestTypes() {
    return this.client.get<any>("/api/v2/quality/test-types");
  }

  async getQCSeedClasses() {
    return this.client.get<any>("/api/v2/quality/seed-classes");
  }
}

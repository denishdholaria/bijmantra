import { ApiClientCore } from "../core/client";

type QCSampleApiRecord = {
  sample_id: string;
  lot_id: string;
  variety: string;
  sample_date: string;
  sample_weight?: number;
  sample_weight_g?: number;
  source: string;
  status?: string;
  overall_status?: string;
  tests?: any[];
  test_count?: number;
};

type QCSummaryApiResponse = {
  total_samples?: number;
  pending?: number;
  passed?: number;
  failed?: number;
  pass_rate?: number;
  samples_by_status?: Record<string, number>;
};

const normalizeQCSampleStatus = (status?: string) => {
  if (status === 'passed' || status === 'failed' || status === 'pending') {
    return status;
  }

  return 'pending';
};

const normalizeQCSample = (sample: QCSampleApiRecord) => ({
  ...sample,
  sample_weight: sample.sample_weight ?? sample.sample_weight_g ?? 0,
  status: normalizeQCSampleStatus(sample.status ?? sample.overall_status),
  tests: Array.isArray(sample.tests) ? sample.tests : [],
});

const normalizeQCSummary = (summary: QCSummaryApiResponse) => {
  const byStatus = summary.samples_by_status ?? {};

  return {
    ...summary,
    total_samples: summary.total_samples ?? 0,
    pending: summary.pending ?? byStatus.pending ?? 0,
    passed: summary.passed ?? byStatus.passed ?? 0,
    failed: summary.failed ?? byStatus.failed ?? 0,
    pass_rate: summary.pass_rate,
  };
};

export class QualityControlService {
  constructor(private client: ApiClientCore) {}

  async getQCSamples(status?: string, lotId?: string) {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (lotId) params.append("lot_id", lotId);
    const response = await this.client.get<any>(`/api/v2/quality/samples?${params}`);
    return {
      ...response,
      samples: Array.isArray(response.samples)
        ? response.samples.map((sample: QCSampleApiRecord) => normalizeQCSample(sample))
        : [],
    };
  }

  async getQCSample(sampleId: string) {
    const response = await this.client.get<any>(`/api/v2/quality/samples/${sampleId}`);
    return normalizeQCSample(response);
  }

  async registerQCSample(data: {
    lot_id: string;
    variety: string;
    sample_date: string;
    sample_weight: number;
    source: string;
  }) {
    const response = await this.client.post<any>("/api/v2/quality/samples", data);
    return normalizeQCSample(response);
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
    const response = await this.client.get<QCSummaryApiResponse>("/api/v2/quality/summary");
    return normalizeQCSummary(response);
  }

  async getQCTestTypes() {
    return this.client.get<any>("/api/v2/quality/test-types");
  }

  async getQCSeedClasses() {
    return this.client.get<any>("/api/v2/quality/seed-classes");
  }
}

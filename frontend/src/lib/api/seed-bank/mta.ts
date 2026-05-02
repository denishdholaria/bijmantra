import { ApiClientCore } from "../core/client";

export interface MTAInstitutionInfo {
  institution: string;
  country: string;
  contact: string;
  email: string;
}

export interface MTABenefitSharingInfo {
  type: "none" | "monetary" | "non_monetary" | "both";
  details: string;
  royalty_rate?: number;
  milestones?: Array<Record<string, unknown>>;
}

export interface MTARecord {
  id: string;
  mta_number: string;
  type: "smta" | "institutional" | "research" | "commercial";
  status: "draft" | "pending_review" | "pending_signature" | "active" | "expired" | "terminated" | "rejected";
  provider: MTAInstitutionInfo;
  recipient: MTAInstitutionInfo;
  accessions: string[];
  accession_count: number;
  crops: string[];
  purpose: string;
  benefit_sharing: MTABenefitSharingInfo;
  created_date: string;
  signed_date?: string | null;
  effective_date?: string | null;
  expiry_date?: string | null;
  exchange_id?: string | null;
}

export interface MTATemplate {
  id: string;
  name: string;
  type: MTARecord["type"];
  description: string;
  version?: string;
  clause_count: number;
  benefit_sharing: MTABenefitSharingInfo["type"];
  duration_years: number | null;
  requires_approval: boolean;
}

export interface MTAStatistics {
  total: number;
  active: number;
  pending: number;
  institutions: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  total_accessions_under_mta: number;
}

export interface MTAComplianceResult {
  mta_id: string;
  mta_number: string;
  compliant: boolean;
  issues: string[];
  warnings: string[];
  checked_at: string;
}

export interface MTAListResponse {
  mtas: MTARecord[];
  count: number;
}

export interface MTATemplatesResponse {
  templates: MTATemplate[];
  types: string[];
}

export interface CreateMTAPayload {
  mta_type: MTARecord["type"];
  provider: MTAInstitutionInfo;
  recipient: MTAInstitutionInfo;
  accessions: string[];
  crops: string[];
  purpose: string;
  benefit_sharing?: MTABenefitSharingInfo;
  exchange_id?: string | null;
}

interface MTAActionResponse {
  message: string;
  mta: MTARecord;
}

export class MTAService {
  constructor(private client: ApiClientCore) {}

  async getMTAs(params: { mtaType?: string; status?: string; institution?: string } = {}) {
    const searchParams = new URLSearchParams();
    if (params.mtaType) searchParams.append("mta_type", params.mtaType);
    if (params.status) searchParams.append("status", params.status);
    if (params.institution) searchParams.append("institution", params.institution);

    const query = searchParams.toString();
    return this.client.get<MTAListResponse>(`/api/v2/mta${query ? `?${query}` : ""}`);
  }

  async getStatistics() {
    return this.client.get<MTAStatistics>("/api/v2/mta/statistics");
  }

  async getTemplates() {
    return this.client.get<MTATemplatesResponse>("/api/v2/mta/templates");
  }

  async createMTA(payload: CreateMTAPayload) {
    return this.client.post<MTAActionResponse>("/api/v2/mta", payload);
  }

  async submitMTA(mtaId: string) {
    return this.client.post<MTAActionResponse>(`/api/v2/mta/${mtaId}/submit`);
  }

  async approveMTA(mtaId: string, approver: string) {
    return this.client.post<MTAActionResponse>(`/api/v2/mta/${mtaId}/approve`, { approver });
  }

  async rejectMTA(mtaId: string, reason: string, rejector: string) {
    return this.client.post<MTAActionResponse>(`/api/v2/mta/${mtaId}/reject`, { reason, rejector });
  }

  async signMTA(mtaId: string, signatory: string) {
    return this.client.post<MTAActionResponse>(`/api/v2/mta/${mtaId}/sign`, { signatory });
  }

  async terminateMTA(mtaId: string, reason: string, terminator: string) {
    return this.client.post<MTAActionResponse>(`/api/v2/mta/${mtaId}/terminate`, { reason, terminator });
  }

  async getCompliance(mtaId: string) {
    return this.client.get<MTAComplianceResult>(`/api/v2/mta/${mtaId}/compliance`);
  }
}
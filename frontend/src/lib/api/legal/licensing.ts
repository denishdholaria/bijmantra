import { ApiClientCore } from "../core/client";

export class LicensingService {
  constructor(private client: ApiClientCore) {}

  // Varieties
  async registerVariety(data: {
    variety_name: string;
    crop: string;
    breeder_id: string;
    breeder_name: string;
    organization_id: string;
    organization_name: string;
    description: string;
    key_traits: string[];
    release_date?: string;
  }) {
    return this.client.post<any>("/api/v2/licensing/varieties", data);
  }

  async getLicensingVarieties(
    crop?: string,
    organizationId?: string,
    status?: string
  ) {
    const params = new URLSearchParams();
    if (crop) params.append("crop", crop);
    if (organizationId) params.append("organization_id", organizationId);
    if (status) params.append("status", status);
    return this.client.get<any>(`/api/v2/licensing/varieties?${params}`);
  }

  async getLicensingVariety(varietyId: string) {
    return this.client.get<any>(`/api/v2/licensing/varieties/${varietyId}`);
  }

  // Protections
  async fileProtection(data: {
    variety_id: string;
    protection_type: string;
    application_number: string;
    filing_date: string;
    territory: string[];
    authority: string;
  }) {
    return this.client.post<any>("/api/v2/licensing/protections", data);
  }

  async grantProtection(
    protectionId: string,
    data: {
      certificate_number: string;
      grant_date: string;
      expiry_date: string;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/licensing/protections/${protectionId}/grant`,
      data
    );
  }

  async getProtections(
    varietyId?: string,
    protectionType?: string,
    status?: string
  ) {
    const params = new URLSearchParams();
    if (varietyId) params.append("variety_id", varietyId);
    if (protectionType) params.append("protection_type", protectionType);
    if (status) params.append("status", status);
    return this.client.get<any>(`/api/v2/licensing/protections?${params}`);
  }

  async getProtection(protectionId: string) {
    return this.client.get<any>(`/api/v2/licensing/protections/${protectionId}`);
  }

  async createLicense(data: {
    variety_id: string;
    licensee_id: string;
    licensee_name: string;
    license_type: string;
    territory: string[];
    start_date: string;
    end_date: string;
    royalty_rate_percent: number;
    minimum_royalty?: number;
    upfront_fee?: number;
    terms?: string;
  }) {
    return this.client.post<any>("/api/v2/licensing/licenses", data);
  }

  async activateLicense(licenseId: string) {
    return this.client.put<any>(
      `/api/v2/licensing/licenses/${licenseId}/activate`,
      {}
    );
  }

  async terminateLicense(licenseId: string, reason: string) {
    return this.client.put<any>(
      `/api/v2/licensing/licenses/${licenseId}/terminate?reason=${encodeURIComponent(
        reason
      )}`,
      {}
    );
  }

  async getLicenses(
    varietyId?: string,
    licenseeId?: string,
    licenseType?: string,
    status?: string
  ) {
    const params = new URLSearchParams();
    if (varietyId) params.append("variety_id", varietyId);
    if (licenseeId) params.append("licensee_id", licenseeId);
    if (licenseType) params.append("license_type", licenseType);
    if (status) params.append("status", status);
    return this.client.get<any>(`/api/v2/licensing/licenses?${params}`);
  }

  async getLicense(licenseId: string) {
    return this.client.get<any>(`/api/v2/licensing/licenses/${licenseId}`);
  }

  async recordRoyalty(
    licenseId: string,
    data: {
      period_start: string;
      period_end: string;
      sales_quantity_kg: number;
      sales_value: number;
      royalty_amount: number;
      payment_status?: string;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/licensing/licenses/${licenseId}/royalties`,
      data
    );
  }

  async getVarietyRoyaltySummary(varietyId: string) {
    return this.client.get<any>(
      `/api/v2/licensing/varieties/${varietyId}/royalties`
    );
  }

  async getProtectionTypes() {
    return this.client.get<any>("/api/v2/licensing/protection-types");
  }

  async getLicenseTypes() {
    return this.client.get<any>("/api/v2/licensing/license-types");
  }

  async getLicensingStatistics() {
    return this.client.get<any>("/api/v2/licensing/statistics");
  }
}

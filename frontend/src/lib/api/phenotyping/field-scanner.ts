import { ApiClientCore } from "../core/client";

export class FieldScannerService {
  constructor(private client: ApiClientCore) {}

  async getFieldScans(params?: {
    study_id?: string;
    plot_id?: string;
    crop?: string;
    has_issues?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.study_id) searchParams.append("study_id", params.study_id);
    if (params?.plot_id) searchParams.append("plot_id", params.plot_id);
    if (params?.crop) searchParams.append("crop", params.crop);
    if (params?.has_issues !== undefined)
      searchParams.append("has_issues", String(params.has_issues));
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.offset) searchParams.append("offset", String(params.offset));
    const query = searchParams.toString();
    return this.client.get<{ scans: any[]; total: number }>(
      `/api/v2/field-scanner${query ? `?${query}` : ""}`
    );
  }

  async getStats(studyId?: string) {
    const query = studyId ? `?study_id=${studyId}` : "";
    return this.client.get<{
      total_scans: number;
      plots_scanned: number;
      healthy_plots: number;
      issues_found: number;
      diseases: Record<string, number>;
      stresses: Record<string, number>;
    }>(`/api/v2/field-scanner/stats${query}`);
  }

  async getScan(scanId: string) {
    return this.client.get<any>(`/api/v2/field-scanner/${scanId}`);
  }

  async createScan(data: {
    plot_id?: string;
    study_id?: string;
    crop?: string;
    location?: { lat: number; lng: number };
    results?: any[];
    thumbnail?: string;
    notes?: string;
  }) {
    return this.client.post<any>("/api/v2/field-scanner", data);
  }

  async updateScan(
    scanId: string,
    data: { plot_id?: string; notes?: string; results?: any[] }
  ) {
    return this.client.patch<any>(`/api/v2/field-scanner/${scanId}`, data);
  }

  async deleteScan(scanId: string) {
    return this.client.delete<any>(`/api/v2/field-scanner/${scanId}`);
  }

  async exportScans(format: 'json' | 'csv') {
    return this.client.get<{ data: any }>(`/api/v2/field-scanner/export?format=${format}`);
  }
}

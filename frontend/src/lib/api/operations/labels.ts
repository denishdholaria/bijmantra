import { ApiClientCore } from "../core/client";

export class LabelService {
  constructor(private client: ApiClientCore) {}
  async getLabelTemplates(labelType?: string) {
    const query = labelType ? `?label_type=${labelType}` : "";
    return this.client.request<{ templates: any[]; total: number }>(
      `/api/v2/labels/templates${query}`,
    );
  }

  async getLabelTemplate(templateId: string) {
    return this.client.request<any>(`/api/v2/labels/templates/${templateId}`);
  }

  async createLabelTemplate(data: {
    name: string;
    type?: string;
    size?: string;
    fields?: string[];
    barcode_type?: string;
  }) {
    return this.client.request<any>("/api/v2/labels/templates", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getLabelData(
    sourceType: string,
    params?: { study_id?: string; trial_id?: string; limit?: number },
  ) {
    const searchParams = new URLSearchParams({ source_type: sourceType });
    if (params?.study_id) searchParams.append("study_id", params.study_id);
    if (params?.trial_id) searchParams.append("trial_id", params.trial_id);
    if (params?.limit) searchParams.append("limit", String(params.limit));
    return this.client.request<{ data: any[]; total: number; source_type: string }>(
      `/api/v2/labels/data?${searchParams}`,
    );
  }

  async getLabelPrintJobs(status?: string, limit?: number) {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (limit) params.append("limit", String(limit));
    const query = params.toString();
    return this.client.request<{ jobs: any[]; total: number }>(
      `/api/v2/labels/jobs${query ? `?${query}` : ""}`,
    );
  }

  async createLabelPrintJob(data: {
    template_id: string;
    items: any[];
    copies?: number;
  }) {
    return this.client.request<any>("/api/v2/labels/jobs", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateLabelPrintJobStatus(jobId: string, status: string) {
    return this.client.request<any>(`/api/v2/labels/jobs/${jobId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  }

  async getLabelPrintingStats() {
    return this.client.request<{
      total_jobs: number;
      completed_jobs: number;
      pending_jobs: number;
      total_labels_printed: number;
      templates_count: number;
    }>("/api/v2/labels/stats");
  }
}

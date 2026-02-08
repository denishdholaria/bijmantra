import { ApiClientCore } from "../core/client";

export interface ReportTemplate {
  id: string;
  name: string;
  type: string;
  description?: string;
  category: string;
  parameters: Record<string, any>;
  formats: string[];
  last_generated?: string;
  generation_count: number;
}

export interface GeneratedReport {
  id: string;
  template_id: string;
  name: string;
  format: string;
  status: string;
  created_at: string;
  generated_at: string;
  generated_by: string;
  size_bytes: number;
  file_url?: string;
  download_url?: string;
}

export interface ReportSchedule {
  id: string;
  template_id: string;
  name: string;
  frequency: string;
  schedule: string;
  schedule_time: string;
  enabled: boolean;
  status: string;
  recipients: string[];
  last_run?: string;
  next_run?: string;
}

export interface ReportStats {
  total_templates: number;
  generated_reports: number;
  scheduled_reports: number;
  active_schedules: number;
  generated_today: number;
  storage_used_mb: number;
  storage_quota_mb: number;
}

export class ReportsService {
  constructor(private client: ApiClientCore) {}

  async getStats() {
    return this.client.get<ReportStats>("/api/v2/reports/stats");
  }

  async getTemplates() {
    return this.client.get<{ templates: ReportTemplate[] }>(
      "/api/v2/reports/templates"
    );
  }

  async generateReport(
    templateId: string,
    format: string = "pdf",
    params?: Record<string, any>
  ) {
    const query = new URLSearchParams({ template_id: templateId, format });
    return this.client.post<GeneratedReport>(
      `/api/v2/reports/generate?${query}`,
      params || {}
    );
  }

  async getGeneratedReports() {
    return this.client.get<{ reports: GeneratedReport[] }>(
      "/api/v2/reports/generated"
    );
  }

  async downloadReport(reportId: string) {
    return this.client.get<any>(`/api/v2/reports/download/${reportId}`);
  }

  async getSchedules() {
    return this.client.get<{ schedules: ReportSchedule[] }>(
      "/api/v2/reports/schedules"
    );
  }

  async createSchedule(
    templateId: string,
    frequency: string,
    name?: string
  ) {
    const params = new URLSearchParams({ template_id: templateId, frequency });
    if (name) params.append("name", name);
    return this.client.post<ReportSchedule>(
      `/api/v2/reports/schedules?${params}`,
      {}
    );
  }

  async toggleSchedule(scheduleId: string, enabled: boolean) {
    return this.client.patch<ReportSchedule>(
      `/api/v2/reports/schedules/${scheduleId}?enabled=${enabled}`,
      {}
    );
  }

  async runSchedule(scheduleId: string) {
    return this.client.post<GeneratedReport>(
      `/api/v2/reports/schedules/${scheduleId}/run`,
      {}
    );
  }

  async deleteSchedule(scheduleId: string) {
    return this.client.delete<void>(`/api/v2/reports/schedules/${scheduleId}`);
  }
}

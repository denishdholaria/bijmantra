import { ApiClientCore } from "../core/client";

export class SecurityService {
  constructor(private client: ApiClientCore) {}

  async getAuditEntries(params?: {
    limit?: number;
    category?: string;
    severity?: string;
    actor?: string;
    hours?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.category) searchParams.append("category", params.category);
    if (params?.severity) searchParams.append("severity", params.severity);
    if (params?.actor) searchParams.append("actor", params.actor);
    if (params?.hours) searchParams.append("hours", String(params.hours));
    return this.client.get<{ count: number; entries: any[] }>(
      `/api/v2/audit/security?${searchParams}`
    );
  }

  async getAuditStats(hours: number = 24) {
    return this.client.get<any>(`/api/v2/audit/security/stats?hours=${hours}`);
  }

  async searchAuditLogs(query: string, limit: number = 100) {
    return this.client.get<{ query: string; count: number; results: any[] }>(
      `/api/v2/audit/security/search?q=${encodeURIComponent(query)}&limit=${limit}`
    );
  }

  async getAuditByActor(actor: string, limit: number = 100) {
    return this.client.get<{ actor: string; count: number; entries: any[] }>(
      `/api/v2/audit/security/actor/${encodeURIComponent(actor)}?limit=${limit}`
    );
  }

  async getAuditByTarget(target: string, limit: number = 100) {
    return this.client.get<{ target: string; count: number; entries: any[] }>(
      `/api/v2/audit/security/target/${encodeURIComponent(target)}?limit=${limit}`
    );
  }

  async getFailedAuditActions(limit: number = 100) {
    return this.client.get<{ count: number; entries: any[] }>(
      `/api/v2/audit/security/failed?limit=${limit}`
    );
  }

  async exportAuditLogs(params: {
    start_date: string;
    end_date: string;
    format: "json" | "csv";
  }) {
    return this.client.post<{
      format: string;
      start_date: string;
      end_date: string;
      data: any;
    }>("/api/v2/audit/security/export", params);
  }

  async getAuditCategories() {
    return this.client.get<{ categories: Array<{ id: string; name: string }> }>(
      "/api/v2/audit/security/categories"
    );
  }

  async getAuditSeverities() {
    return this.client.get<{ severities: Array<{ id: string; name: string }> }>(
      "/api/v2/audit/security/severities"
    );
  }
}

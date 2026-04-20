import { ApiClientCore } from "../core/client";

export class DataValidationService {
  constructor(private client: ApiClientCore) {}

  async getIssues(params?: {
    type?: string;
    status?: string;
    entity_type?: string;
    rule_id?: string;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.type) searchParams.append("type", params.type);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.entity_type)
      searchParams.append("entity_type", params.entity_type);
    if (params?.rule_id) searchParams.append("rule_id", params.rule_id);
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.offset) searchParams.append("offset", String(params.offset));
    
    return this.client.get<{
      status: string;
      data: Array<{
        id: string;
        type: "error" | "warning" | "info";
        rule_id: string;
        field: string;
        record_id: string;
        entity_type: string;
        message: string;
        suggestion?: string;
        status: string;
        created_at: string;
      }>;
      total: number;
    }>(`/api/v2/data-validation?${searchParams}`);
  }

  async getStats() {
    return this.client.get<{
      status: string;
      data: {
        total_issues: number;
        open_issues: number;
        resolved_issues: number;
        ignored_issues: number;
        errors: number;
        warnings: number;
        info: number;
        data_quality_score: number;
        last_validation: string | null;
        records_validated: number;
        bySeverity?: {
          error: number;
          warning: number;
          info: number;
        };
      };
    }>("/api/v2/data-validation/stats");
  }

  async getSummary() {
    return this.getStats();
  }

  async getRules(enabled?: boolean) {
    const query = enabled !== undefined ? `?enabled=${enabled}` : "";
    return this.client.get<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        description: string;
        enabled: boolean;
        severity: string;
        entity_types: string[];
        issues_found: number;
      }>;
    }>(`/api/v2/data-validation/rules${query}`);
  }

  async updateRule(
    ruleId: string,
    data: { enabled?: boolean; severity?: string }
  ) {
    return this.client.patch<any>(
      `/api/v2/data-validation/rules/${ruleId}`,
      data
    );
  }

  async updateIssueStatus(
    issueId: string,
    data: { status: string; notes?: string }
  ) {
    return this.client.patch<any>(
      `/api/v2/data-validation/issues/${issueId}`,
      data
    );
  }

  async deleteIssue(issueId: string) {
    return this.client.delete<any>(`/api/v2/data-validation/issues/${issueId}`);
  }

  async runValidation(data?: { entity_types?: string[]; rule_ids?: string[] }) {
    return this.client.post<any>("/api/v2/data-validation/run", data || {});
  }

  async getValidationRuns(limit?: number) {
    const query = limit ? `?limit=${limit}` : "";
    return this.client.get<any>(`/api/v2/data-validation/runs${query}`);
  }

  async exportReport(format?: string) {
    const query = format ? `?format=${format}` : "";
    return this.client.get<any>(`/api/v2/data-validation/export${query}`);
  }

  // Compatibility methods for DataQuality.tsx
  async getQualityIssues(params?: any) {
    return this.getIssues({
      status: params?.status,
      entity_type: params?.entity,
      // map other params if needed
    });
  }

  async getQualityMetrics() {
    return this.client.get<any>("/api/v2/data-validation/metrics");
  }

  async getQualityScore() {
    return this.client.get<any>("/api/v2/data-validation/score");
  }

  async getDataQualityStatistics() {
    return this.getStats();
  }

  async runDataValidation() {
    return this.runValidation();
  }

  async resolveQualityIssue(id: string, user: string, notes: string) {
    return this.updateIssueStatus(id, { status: "resolved", notes });
  }

  async ignoreQualityIssue(id: string, notes: string) {
    return this.updateIssueStatus(id, { status: "ignored", notes });
  }
}

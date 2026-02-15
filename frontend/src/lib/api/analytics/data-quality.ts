import { ApiClientCore } from "../core/client";

export class DataQualityService {
  constructor(private client: ApiClientCore) {}

  async getQualityIssues(params?: {
    status?: string;
    severity?: string;
    entity?: string;
    issueType?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append("status", params.status);
    if (params?.severity) searchParams.append("severity", params.severity);
    if (params?.entity) searchParams.append("entity", params.entity);
    if (params?.issueType) searchParams.append("issueType", params.issueType);
    return this.client.get<any>(`/api/v2/data-quality/issues?${searchParams}`);
  }

  async getQualityIssue(issueId: string) {
    return this.client.get<any>(`/api/v2/data-quality/issues/${issueId}`);
  }

  async createQualityIssue(data: {
    entity: string;
    entityId: string;
    entityName: string;
    issueType: string;
    field: string;
    description: string;
    severity?: string;
  }) {
    return this.client.post<any>("/api/v2/data-quality/issues", data);
  }

  async resolveQualityIssue(
    issueId: string,
    resolvedBy: string,
    notes?: string,
  ) {
    return this.client.post<any>(`/api/v2/data-quality/issues/${issueId}/resolve`, {
      resolvedBy,
      notes,
    });
  }

  async ignoreQualityIssue(issueId: string, reason: string) {
    return this.client.post<any>(
      `/api/v2/data-quality/issues/${issueId}/ignore?reason=${encodeURIComponent(
        reason
      )}`,
      {}
    );
  }

  async reopenQualityIssue(issueId: string) {
    return this.client.post<any>(
      `/api/v2/data-quality/issues/${issueId}/reopen`,
      {}
    );
  }

  async getQualityMetrics() {
    return this.client.get<any>("/api/v2/data-quality/metrics");
  }

  async getQualityScore() {
    return this.client.get<any>("/api/v2/data-quality/score");
  }

  async runDataValidation(entity?: string) {
    return this.client.post<any>("/api/v2/data-quality/validate", { entity });
  }

  async getValidationHistory(limit?: number) {
    const params = limit ? `?limit=${limit}` : "";
    return this.client.get<any>(`/api/v2/data-quality/history${params}`);
  }

  async getQualityRules(entity?: string) {
    const params = entity ? `?entity=${entity}` : "";
    return this.client.get<any>(`/api/v2/data-quality/rules${params}`);
  }

  async createQualityRule(data: {
    entity: string;
    field: string;
    ruleType: string;
    ruleConfig?: Record<string, any>;
    severity?: string;
  }) {
    return this.client.post<any>("/api/v2/data-quality/rules", data);
  }

  async toggleQualityRule(ruleId: string, enabled: boolean) {
    return this.client.post<any>(`/api/v2/data-quality/rules/${ruleId}/toggle`, {
      enabled,
    });
  }

  async getDataQualityStatistics() {
    return this.client.get<any>("/api/v2/data-quality/statistics");
  }

  async getQualityIssueTypes() {
    return this.client.get<any>("/api/v2/data-quality/issue-types");
  }

  async getQualitySeverities() {
    return this.client.get<any>("/api/v2/data-quality/severities");
  }
}

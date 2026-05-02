import { ApiClientCore } from "../core/client";

export interface WorkflowStep {
  id: string;
  type: "trigger" | "action" | "condition";
  name: string;
  config: Record<string, string>;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  trigger: string;
  status: "active" | "paused" | "error";
  last_run: string;
  next_run: string;
  runs: number;
  success_rate: number;
  enabled: boolean;
  steps: WorkflowStep[];
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: "success" | "error" | "running";
  started_at: string;
  completed_at: string | null;
  duration: string;
  error?: string;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
}

export interface WorkflowStats {
  total_workflows: number;
  active_workflows: number;
  paused_workflows: number;
  error_workflows: number;
  total_runs: number;
  average_success_rate: number;
  time_saved_hours: number;
}

export class WorkflowService {
  constructor(private client: ApiClientCore) {}

  async listWorkflows(params?: { status?: string; enabled?: boolean }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append("status", params.status);
    if (params?.enabled !== undefined)
      searchParams.append("enabled", String(params.enabled));
    
    return this.client.get<{
      status: string;
      data: Workflow[];
      total: number;
    }>(`/api/v2/workflows?${searchParams}`);
  }

  async getStats() {
    return this.client.get<{ status: string; data: WorkflowStats }>(
      "/api/v2/workflows/stats"
    );
  }

  async getWorkflow(workflowId: string) {
    return this.client.get<{ status: string; data: Workflow }>(
      `/api/v2/workflows/${workflowId}`
    );
  }

  async createWorkflow(data: {
    name: string;
    description: string;
    trigger: string;
    steps: WorkflowStep[];
    enabled?: boolean;
  }) {
    return this.client.post<{
      status: string;
      data: Workflow;
      message: string;
    }>("/api/v2/workflows", data);
  }

  async updateWorkflow(
    workflowId: string,
    data: {
      name?: string;
      description?: string;
      trigger?: string;
      steps?: WorkflowStep[];
      enabled?: boolean;
    }
  ) {
    return this.client.patch<{
      status: string;
      data: Workflow;
      message: string;
    }>(`/api/v2/workflows/${workflowId}`, data);
  }

  async deleteWorkflow(workflowId: string) {
    return this.client.delete<{ status: string; message: string }>(
      `/api/v2/workflows/${workflowId}`
    );
  }

  async runWorkflow(workflowId: string) {
    return this.client.post<{
      status: string;
      data: WorkflowRun;
      message: string;
    }>(`/api/v2/workflows/${workflowId}/run`, {});
  }

  async toggleWorkflow(workflowId: string) {
    return this.client.post<{
      status: string;
      data: Workflow;
      message: string;
    }>(`/api/v2/workflows/${workflowId}/toggle`, {});
  }

  async getWorkflowRuns(params?: {
    workflow_id?: string;
    status?: string;
    limit?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.workflow_id)
      searchParams.append("workflow_id", params.workflow_id);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.limit) searchParams.append("limit", String(params.limit));
    
    return this.client.get<{
      status: string;
      data: WorkflowRun[];
      total: number;
    }>(`/api/v2/workflows/runs/history?${searchParams}`);
  }

  async listTemplates() {
    return this.client.get<{ status: string; data: WorkflowTemplate[] }>(
      "/api/v2/workflows/templates/list"
    );
  }

  async useTemplate(templateId: string, name: string) {
    return this.client.post<{
      status: string;
      data: Workflow;
      message: string;
    }>(
      `/api/v2/workflows/templates/${templateId}/use?name=${encodeURIComponent(
        name
      )}`,
      {}
    );
  }
}

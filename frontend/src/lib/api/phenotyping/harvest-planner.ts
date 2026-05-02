import { ApiClientCore } from "../core/client";

export interface HarvestTask {
  id: string;
  plot: string;
  germplasm: string;
  expectedDate: string;
  status: "pending" | "ready" | "harvested" | "processed";
  priority: "high" | "medium" | "low";
  notes: string;
  completed: boolean;
}

export class HarvestPlannerService {
  constructor(private client: ApiClientCore) {}

  async getTasks(params?: { status?: string; priority?: string; plot?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.priority) searchParams.set("priority", params.priority);
    if (params?.plot) searchParams.set("plot", params.plot);
    const query = searchParams.toString();
    return this.client.get<{ data: HarvestTask[]; total: number }>(
      `/api/v2/harvest/tasks${query ? `?${query}` : ""}`
    );
  }

  async getTask(taskId: string) {
    return this.client.get<{ data: HarvestTask }>(
      `/api/v2/harvest/tasks/${taskId}`
    );
  }

  async createTask(data: Partial<HarvestTask>) {
    return this.client.post<{ data: HarvestTask }>(
      "/api/v2/harvest/tasks",
      data
    );
  }

  async updateTask(taskId: string, data: Partial<HarvestTask>) {
    return this.client.patch<{ data: HarvestTask }>(
      `/api/v2/harvest/tasks/${taskId}`,
      data
    );
  }

  async getStats() {
    return this.client.get<{
      total: number;
      pending: number;
      ready: number;
      harvested: number;
      processed: number;
      progress: number;
    }>("/api/v2/harvest/stats");
  }
}

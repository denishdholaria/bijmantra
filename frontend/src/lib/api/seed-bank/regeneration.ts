import { ApiClientCore } from "../core/client";

export class RegenerationService {
  constructor(private client: ApiClientCore) {}

  async getRegenerationTasks(priority?: string, status?: string) {
    const params = new URLSearchParams();
    if (priority) params.append("priority", priority);
    if (status) params.append("status", status);
    return this.client.get<any[]>(
      `/api/v2/seed-bank/regeneration-tasks?${params}`
    );
  }

  async createRegenerationTask(data: any) {
    return this.client.post<any>("/api/v2/seed-bank/regeneration-tasks", data);
  }
}

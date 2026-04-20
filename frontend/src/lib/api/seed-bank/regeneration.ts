import { ApiClientCore } from "../core/client";

export interface SeedBankRegenerationTask {
  id: string;
  accession_id: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  target_quantity: number;
  planned_season?: string | null;
  status: 'planned' | 'in-progress' | 'harvested' | 'completed';
  harvested_quantity?: number | null;
  created_at: string;
}

export interface CreateSeedBankRegenerationTaskPayload {
  accession_id: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  target_quantity: number;
  planned_season?: string;
}

export class RegenerationService {
  constructor(private client: ApiClientCore) {}

  async getRegenerationTasks(priority?: string, status?: string) {
    const params = new URLSearchParams();
    if (priority) params.append("priority", priority);
    if (status) params.append("status", status);
    return this.client.get<SeedBankRegenerationTask[]>(
      `/api/v2/seed-bank/regeneration-tasks?${params}`
    );
  }

  async createRegenerationTask(data: CreateSeedBankRegenerationTaskPayload) {
    return this.client.post<SeedBankRegenerationTask>("/api/v2/seed-bank/regeneration-tasks", data);
  }
}

import { ApiClientCore } from "../core/client";

export class VaultService {
  constructor(private client: ApiClientCore) {}

  async getStats() {
    return this.client.get<{
      total_accessions: number;
      active_vaults: number;
      pending_viability: number;
      scheduled_regeneration: number;
    }>("/api/v2/seed-bank/stats");
  }

  async getVaults() {
    return this.client.get<any[]>("/api/v2/seed-bank/vaults");
  }

  async getVault(vaultId: string) {
    return this.client.get<any>(`/api/v2/seed-bank/vaults/${vaultId}`);
  }

  async createVault(data: any) {
    return this.client.post<any>("/api/v2/seed-bank/vaults", data);
  }

  async getVaultConditions() {
    return this.client.request<{ conditions: any[]; count: number }>("/api/v2/vault-sensors/conditions");
  }

  async getAlerts(limit: number = 50) {
    return this.client.get<{ alerts: any[]; count: number }>(`/api/v2/vault-sensors/alerts?limit=${limit}`);
  }

  async getStatistics() {
    return this.client.get<any>("/api/v2/vault-sensors/statistics");
  }

  async getReadings(params?: { hours?: number; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.hours !== undefined) {
      searchParams.set('hours', String(params.hours));
    }
    if (params?.limit !== undefined) {
      searchParams.set('limit', String(params.limit));
    }
    const query = searchParams.toString();
    return this.client.get<{ readings: any[]; count: number }>(`/api/v2/vault-sensors/readings${query ? `?${query}` : ''}`);
  }

  async acknowledgeAlert(alertId: string, user: string) {
    return this.client.post<{ success: boolean; alert: any }>(`/api/v2/vault-sensors/alerts/${alertId}/acknowledge`, { user });
  }
}

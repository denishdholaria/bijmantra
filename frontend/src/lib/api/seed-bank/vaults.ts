import { ApiClientCore } from "../core/client";

export class VaultService {
  constructor(private client: ApiClientCore) {}

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
}

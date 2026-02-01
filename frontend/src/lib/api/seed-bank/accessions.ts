import { ApiClientCore } from "../core/client";

export class AccessionService {
  constructor(private client: ApiClientCore) {}

  async getAccessions(
    page = 0,
    pageSize = 20,
    search?: string,
    status?: string,
    vaultId?: string
  ) {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (search) params.append("search", search);
    if (status) params.append("status", status);
    if (vaultId) params.append("vault_id", vaultId);

    return this.client.get<{ items: any[]; total: number }>(
      `/api/v2/seed-bank/accessions?${params}`
    );
  }

  async getAccession(accessionId: string) {
    return this.client.get<any>(`/api/v2/seed-bank/accessions/${accessionId}`);
  }

  async createAccession(data: any) {
    return this.client.post<any>("/api/v2/seed-bank/accessions", data);
  }

  async updateAccession(accessionId: string, data: any) {
    return this.client.put<any>(
      `/api/v2/seed-bank/accessions/${accessionId}`,
      data
    );
  }
}

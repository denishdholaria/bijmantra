import { ApiClientCore } from "../core/client";

export class ExchangeService {
  constructor(private client: ApiClientCore) {}

  async getExchanges(type?: string, status?: string) {
    const params = new URLSearchParams();
    if (type) params.append("type", type);
    if (status) params.append("status", status);
    return this.client.get<any[]>(`/api/v2/seed-bank/exchanges?${params}`);
  }

  async createExchange(data: any) {
    return this.client.post<any>("/api/v2/seed-bank/exchanges", data);
  }
}

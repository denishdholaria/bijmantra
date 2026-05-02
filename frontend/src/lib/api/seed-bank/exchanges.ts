import { ApiClientCore } from "../core/client";

export interface SeedBankExchange {
  id: string;
  request_number: string;
  type: 'incoming' | 'outgoing';
  institution_name: string;
  accession_count: number;
  status: 'pending' | 'approved' | 'shipped' | 'received' | 'rejected';
  request_date: string;
  smta: boolean;
}

export interface CreateSeedBankExchangePayload {
  type: 'incoming' | 'outgoing';
  institution_name: string;
  accession_ids: string[];
  smta: boolean;
  notes?: string;
}

export class ExchangeService {
  constructor(private client: ApiClientCore) {}

  async getExchanges(type?: string, status?: string) {
    const params = new URLSearchParams();
    if (type) params.append("type", type);
    if (status) params.append("status", status);
    return this.client.get<SeedBankExchange[]>(`/api/v2/seed-bank/exchanges?${params}`);
  }

  async createExchange(data: CreateSeedBankExchangePayload) {
    return this.client.post<SeedBankExchange>("/api/v2/seed-bank/exchanges", data);
  }
}

import { ApiClientCore } from "../core/client";

export interface SeedBankViabilityTest {
  id: string;
  batch_number: string;
  accession_id: string;
  test_date: string;
  seeds_tested: number;
  germinated: number;
  germination_rate: number;
  status: 'scheduled' | 'in-progress' | 'completed';
  created_at: string;
}

export interface CreateSeedBankViabilityTestPayload {
  accession_id: string;
  test_date: string;
  seeds_tested: number;
}

export class ViabilityService {
  constructor(private client: ApiClientCore) {}

  async getViabilityTests(status?: string, accessionId?: string) {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (accessionId) params.append("accession_id", accessionId);
    return this.client.get<SeedBankViabilityTest[]>(`/api/v2/seed-bank/viability-tests?${params}`);
  }

  async createViabilityTest(data: CreateSeedBankViabilityTestPayload) {
    return this.client.post<SeedBankViabilityTest>("/api/v2/seed-bank/viability-tests", data);
  }

  async recordViabilityTest(data: {
    lot_id: string;
    test_date: string;
    seeds_tested: number;
    seeds_germinated: number;
    test_method: string;
    tester: string;
    notes?: string;
  }) {
    return this.client.post<any>("/api/v2/seed-inventory/viability", data);
  }

  async getViabilityHistory(lotId: string) {
    return this.client.get<any>(`/api/v2/seed-inventory/viability/${lotId}`);
  }
}

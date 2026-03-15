import { ApiClientCore } from "../core/client";

export interface SeedBankAccession {
  id: string;
  accession_number: string;
  genus: string;
  species: string;
  subspecies?: string | null;
  common_name?: string | null;
  origin: string;
  collection_date?: string | null;
  collection_site?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  altitude?: number | null;
  vault_id?: string | null;
  seed_count: number;
  viability: number;
  status: 'active' | 'depleted' | 'regenerating';
  acquisition_type?: string | null;
  donor_institution?: string | null;
  mls: boolean;
  pedigree?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SeedBankAccessionListResponse {
  data: SeedBankAccession[];
  total: number;
  page: number;
  page_size: number;
}

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

    return this.client.get<SeedBankAccessionListResponse>(
      `/api/v2/seed-bank/accessions?${params}`
    );
  }

  async getAccession(accessionId: string) {
    return this.client.get<SeedBankAccession>(`/api/v2/seed-bank/accessions/${accessionId}`);
  }

  async createAccession(data: any) {
    return this.client.post<SeedBankAccession>("/api/v2/seed-bank/accessions", data);
  }

  async updateAccession(accessionId: string, data: any) {
    return this.client.patch<SeedBankAccession>(
      `/api/v2/seed-bank/accessions/${accessionId}`,
      data
    );
  }
}

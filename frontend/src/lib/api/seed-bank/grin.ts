import { ApiClientCore } from "../core/client";

export interface GRINSearchAccession {
  accession_number: string;
  genus: string;
  species: string;
  common_name?: string;
  country_code?: string;
  institute?: string;
  status?: string;
  available?: boolean;
}

export interface GenesysSearchAccession {
  accession_number: string;
  institute_code: string;
  genus: string;
  species: string;
  country?: string;
  available: boolean;
}

export interface GRINImportResult {
  success: boolean;
  imported_count: number;
  skipped_count: number;
  errors: string[];
}

export class GRINService {
  constructor(private client: ApiClientCore) {}

  async searchGrin(params: { genus?: string; species?: string; country?: string; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params.genus) searchParams.append("genus", params.genus);
    if (params.species) searchParams.append("species", params.species);
    if (params.country) searchParams.append("country", params.country);
    if (params.limit) searchParams.append("limit", String(params.limit));

    return this.client.get<GRINSearchAccession[]>(`/api/v2/grin/grin-global/search?${searchParams.toString()}`);
  }

  async searchGenesys(params: { genus?: string; species?: string; country?: string; availableOnly?: boolean; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params.genus) searchParams.append("genus", params.genus);
    if (params.species) searchParams.append("species", params.species);
    if (params.country) searchParams.append("country", params.country);
    if (params.availableOnly) searchParams.append("available_only", "true");
    if (params.limit) searchParams.append("limit", String(params.limit));

    return this.client.get<GenesysSearchAccession[]>(`/api/v2/grin/genesys/search?${searchParams.toString()}`);
  }

  async importFromGrin(accessionNumbers: string[]) {
    return this.client.post<GRINImportResult>("/api/v2/grin/import/grin-global", accessionNumbers);
  }

  async importFromGenesys(accessions: Array<{ institute_code?: string; accession_number?: string }>) {
    return this.client.post<GRINImportResult>("/api/v2/grin/import/genesys", accessions);
  }
}
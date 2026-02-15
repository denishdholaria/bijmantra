import { ApiClientCore } from "../core/client";

export interface GermplasmSearchResult {
  id: string;
  name: string;
  accession: string;
  species: string;
  subspecies?: string;
  origin: string;
  traits: string[];
  status: string;
  collection: string;
  year?: number;
}

export interface GermplasmSearchFilters {
  species: string[];
  origins: string[];
  collections: string[];
  traits: string[];
}

export class GermplasmSearchService {
  constructor(private client: ApiClientCore) {}

  async search(params: {
    query?: string;
    species?: string;
    origin?: string;
    collection?: string;
    trait?: string;
    page?: number;
    pageSize?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params.query) queryParams.append("query", params.query);
    if (params.species) queryParams.append("species", params.species);
    if (params.origin) queryParams.append("origin", params.origin);
    if (params.collection) queryParams.append("collection", params.collection);
    if (params.trait) queryParams.append("trait", params.trait);
    if (params.page) queryParams.append("page", String(params.page));
    if (params.pageSize)
      queryParams.append("pageSize", String(params.pageSize));
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{
      results: GermplasmSearchResult[];
      total: number;
    }>(`/api/v2/germplasm-search${query}`);
  }

  async getFilters() {
    return this.client.get<{ data: GermplasmSearchFilters }>(
      "/api/v2/germplasm-search/filters"
    );
  }

  async getById(id: string) {
    return this.client.get<{ data: GermplasmSearchResult }>(
      `/api/v2/germplasm-search/${id}`
    );
  }

  async addToList(germplasmIds: string[], listId: string) {
    return this.client.post<{ success: boolean }>(
      "/api/v2/germplasm-search/add-to-list",
      { germplasm_ids: germplasmIds, list_id: listId }
    );
  }

  async export(germplasmIds: string[], format: "csv" | "json" = "csv") {
    return this.client.post<Blob>("/api/v2/germplasm-search/export", {
      germplasm_ids: germplasmIds,
      format,
    });
  }

  async getStatistics() {
    return this.client.get<{
      total_germplasm: number;
      species_count: number;
      collection_count: number;
      trait_count: number;
    }>("/api/v2/germplasm-search/statistics");
  }
}

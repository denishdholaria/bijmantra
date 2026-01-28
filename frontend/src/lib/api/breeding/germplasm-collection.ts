import { ApiClientCore } from "../core/client";

export class GermplasmCollectionService {
  constructor(private client: ApiClientCore) {}

  async getCollections(params?: {
    type?: string;
    species?: string;
    curator?: string;
    search?: string;
    status?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.type) searchParams.append("type", params.type);
    if (params?.species) searchParams.append("species", params.species);
    if (params?.curator) searchParams.append("curator", params.curator);
    if (params?.search) searchParams.append("search", params.search);
    if (params?.status) searchParams.append("status", params.status);
    const query = searchParams.toString();
    return this.client.get<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        description: string;
        type: string;
        accession_count: number;
        species: string[];
        curator: string;
        updated_at: string;
        status: string;
      }>;
      count: number;
    }>(`/api/v2/collections${query ? `?${query}` : ""}`);
  }

  async getCollection(collectionId: string) {
    return this.client.get<any>(`/api/v2/collections/${collectionId}`);
  }

  async getStats() {
    return this.client.get<{
      status: string;
      data: {
        total_collections: number;
        total_accessions: number;
        unique_species: number;
        species_list: string[];
        unique_curators: number;
        by_type: Record<string, number>;
      };
    }>("/api/v2/collections/stats");
  }

  async getTypes() {
    return this.client.get<any>("/api/v2/collections/types");
  }

  async createCollection(data: {
    name: string;
    description?: string;
    type?: string;
    species?: string[];
    curator?: string;
  }) {
    return this.client.post<any>("/api/v2/collections", data);
  }

  async updateCollection(collectionId: string, data: Record<string, any>) {
    return this.client.patch<any>(`/api/v2/collections/${collectionId}`, data);
  }

  async deleteCollection(collectionId: string) {
    return this.client.delete<any>(`/api/v2/collections/${collectionId}`);
  }

  async addAccessions(collectionId: string, count: number) {
    return this.client.post<any>(
      `/api/v2/collections/${collectionId}/accessions`,
      { count }
    );
  }
}

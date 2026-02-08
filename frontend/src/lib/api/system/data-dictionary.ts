import { ApiClientCore } from "../core/client";

export class DataDictionaryService {
  constructor(private client: ApiClientCore) {}

  async getEntities() {
    return this.client.get<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        description: string;
        brapi_module: string;
        field_count: number;
        relationship_count: number;
      }>;
      count: number;
    }>("/api/v2/data-dictionary/entities");
  }

  async getEntity(entityId: string) {
    return this.client.get<{
      status: string;
      data: {
        id: string;
        name: string;
        description: string;
        brapi_module: string;
        fields: Array<{
          name: string;
          type: string;
          description: string;
          required: boolean;
          example: string;
          brapi_field?: string;
        }>;
        relationships: string[];
      };
    }>(`/api/v2/data-dictionary/entities/${entityId}`);
  }

  async searchFields(params?: { search?: string; entity?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append("search", params.search);
    if (params?.entity) searchParams.append("entity", params.entity);
    return this.client.get<any>(
      `/api/v2/data-dictionary/fields?${searchParams}`
    );
  }

  async getStats() {
    return this.client.get<any>("/api/v2/data-dictionary/stats");
  }

  async exportDictionary(format?: string) {
    const query = format ? `?format=${format}` : "";
    return this.client.get<any>(`/api/v2/data-dictionary/export${query}`);
  }
}

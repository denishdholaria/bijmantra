import { ApiClientCore } from "../core/client";

export interface ProgenyItem {
  germplasm_id: string;
  germplasm_name: string;
  parent_type: string;
  generation?: string;
  cross_year?: number;
}

export interface ProgenyEntry {
  id: string;
  germplasm_id: string;
  germplasm_name: string;
  parent_type: "FEMALE" | "MALE" | "SELF" | "POPULATION";
  species?: string;
  generation?: string;
  progeny: ProgenyItem[];
}

export interface ProgenyStatistics {
  total_parents: number;
  total_progeny: number;
  avg_offspring: number;
  max_offspring: number;
  max_offspring_parent: string | null;
  by_parent_type: Record<string, number>;
  by_species: Record<string, number>;
}

export class ProgenyService {
  constructor(private client: ApiClientCore) {}

  async getParents(params?: {
    search?: string;
    parent_type?: string;
    species?: string;
    page?: number;
    pageSize?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append("search", params.search);
    if (params?.parent_type)
      queryParams.append("parent_type", params.parent_type);
    if (params?.species) queryParams.append("species", params.species);
    if (params?.page) queryParams.append("page", String(params.page));
    if (params?.pageSize)
      queryParams.append("pageSize", String(params.pageSize));
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{ data: ProgenyEntry[]; total: number }>(
      `/api/v2/progeny/parents${query}`
    );
  }

  async getParent(parentId: string) {
    return this.client.get<{ data: ProgenyEntry }>(
      `/api/v2/progeny/parents/${parentId}`
    );
  }

  async getProgeny(germplasmId: string) {
    return this.client.get<{ data: ProgenyItem[] }>(
      `/api/v2/progeny/germplasm/${germplasmId}/progeny`
    );
  }

  async getStatistics() {
    return this.client.get<{ data: ProgenyStatistics }>(
      "/api/v2/progeny/statistics"
    );
  }

  async getLineageTree(germplasmId: string, depth?: number) {
    const query = depth ? `?depth=${depth}` : "";
    return this.client.get<{ data: any }>(
      `/api/v2/progeny/germplasm/${germplasmId}/lineage${query}`
    );
  }

  async export(parentIds?: string[], format: "csv" | "json" = "csv") {
    return this.client.post<Blob>("/api/v2/progeny/export", {
      parent_ids: parentIds,
      format,
    });
  }
}

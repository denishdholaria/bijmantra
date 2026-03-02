import { ApiClientCore } from "../core/client";

export interface ComparisonGermplasm {
  id: string;
  name: string;
  accession: string;
  species: string;
  origin: string;
  pedigree: string;
  traits: Record<string, number | string>;
  markers: Record<string, string>;
  status: "active" | "archived" | "candidate";
}

export interface ComparisonTrait {
  id: string;
  name: string;
  unit: string;
  type?: "numeric" | "categorical";
  optimal_range?: [number, number];
  higher_is_better: boolean;
  best?: { value: string | number; entry_id: string };
}

export interface ComparisonResult {
  entries: ComparisonGermplasm[];
  traits: ComparisonTrait[];
  markers?: Array<{ name: string; values: Record<string, boolean> }>;
  recommendations?: string[];
  summary?: {
    best_overall: string;
    recommendations: string[];
  };
}

export class GermplasmComparisonService {
  constructor(private client: ApiClientCore) {}

  async listGermplasm(params?: {
    search?: string;
    species?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set("search", params.search);
    if (params?.species) searchParams.set("species", params.species);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.skip) searchParams.set("skip", params.skip.toString());
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    const query = searchParams.toString();
    return this.client.get<{ data: ComparisonGermplasm[]; total: number }>(
      `/api/v2/germplasm-comparison/germplasm${query ? `?${query}` : ""}`
    );
  }

  async listTraits(params?: { category?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set("category", params.category);
    const query = searchParams.toString();
    return this.client.get<{ data: ComparisonTrait[] }>(
      `/api/v2/germplasm-comparison/traits${query ? `?${query}` : ""}`
    );
  }

  async getTraits(params?: { category?: string }) {
    return this.listTraits(params);
  }

  async compare(
    germplasmIds: string[],
    traitIds: string[] = []
  ) {
    return this.client.post<{ data: ComparisonResult }>(
      "/api/v2/germplasm-comparison/compare",
      { germplasm_ids: germplasmIds, trait_ids: traitIds }
    ).then(res => res.data);
  }

  async getMatrix(
    germplasmIds: string[],
    traitIds?: string[]
  ) {
    return this.client.post<{
      data: {
        matrix: Record<string, Record<string, number>>;
        traits: string[];
        germplasm: string[];
      };
    }>("/api/v2/germplasm-comparison/matrix", {
      germplasm_ids: germplasmIds,
      trait_ids: traitIds,
    });
  }

  async exportComparison(
    germplasmIds: string[],
    format: string = "csv"
  ) {
    return this.client.post<any>("/api/v2/germplasm-comparison/export", {
      germplasm_ids: germplasmIds,
      format,
    });
  }
}

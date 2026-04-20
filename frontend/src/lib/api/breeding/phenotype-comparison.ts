import { ApiClientCore } from "../core/client";

export interface PhenotypeGermplasm {
  germplasmDbId: string;
  germplasmName: string;
  defaultDisplayName?: string;
  species?: string;
  isCheck?: boolean;
}

export interface PhenotypeObservation {
  observationDbId: string;
  germplasmDbId: string;
  observationVariableName: string;
  observationVariableDbId: string;
  value: string;
}

export class PhenotypeComparisonService {
  constructor(private client: ApiClientCore) {}
  async getGermplasm(params?: {
    limit?: number;
    search?: string;
    species?: string;
  }): Promise<{ result: { data: PhenotypeGermplasm[] } }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.search) searchParams.set("search", params.search);
    if (params?.species) searchParams.set("species", params.species);
    const query = searchParams.toString();
    return this.client.get<{ result: { data: PhenotypeGermplasm[] } }>(
      `/api/v2/phenotype-comparison/germplasm${query ? `?${query}` : ""}`
    );
  }

  async getObservations(
    germplasmIds: string[],
    traits?: string[],
  ): Promise<{ result: { data: PhenotypeObservation[] } }> {
    return this.client.post<{ result: { data: PhenotypeObservation[] } }>(
      "/api/v2/phenotype-comparison/observations",
      { germplasm_ids: germplasmIds, traits }
    );
  }

  async getTraits(): Promise<{
    data: Array<{
      id: string;
      name: string;
      unit: string;
      higher_is_better: boolean;
    }>;
  }> {
    return this.client.get("/api/v2/phenotype-comparison/traits");
  }

  async compare(
    germplasmIds: string[],
    checkId?: string,
  ): Promise<{
    data: Array<{
      germplasm_id: string;
      germplasm_name: string;
      traits: Record<string, number>;
      vs_check?: Record<string, number>;
    }>;
    check_id: string;
    check_name: string;
  }> {
    return this.client.post("/api/v2/phenotype-comparison/compare", { germplasm_ids: germplasmIds, check_id: checkId });
  }

  async getStatistics(germplasmIds?: string[]): Promise<any> {
    const query = germplasmIds
      ? `?germplasm_ids=${germplasmIds.join(",")}`
      : "";
    return this.client.get(`/api/v2/phenotype-comparison/statistics${query}`);
  }
}

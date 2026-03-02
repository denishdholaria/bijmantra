import { ApiClientCore } from "../core/client";

export interface VarietyData {
  id: string;
  name: string;
  type: "check" | "test" | "elite";
  trials: number;
  locations: number;
  years: number[];
  avgYield: number;
  stability: number;
  traits: Record<string, number>;
}

export class VarietyComparisonService {
  constructor(private client: ApiClientCore) {}

  async getVarieties(params?: { type?: string; crop?: string; year?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.type) searchParams.set("type", params.type);
    if (params?.crop) searchParams.set("crop", params.crop);
    if (params?.year) searchParams.set("year", params.year.toString());
    const query = searchParams.toString();
    return this.client.get<{ data: VarietyData[]; total: number }>(
      `/api/v2/variety-comparison/varieties${query ? `?${query}` : ""}`
    );
  }

  async getVariety(varietyId: string) {
    return this.client.get<{ data: VarietyData }>(
      `/api/v2/variety-comparison/varieties/${varietyId}`
    );
  }

  async compare(varietyIds: string[], checkId?: string) {
    return this.client.post<{
      data: Array<{
        variety: VarietyData;
        vs_check: { yield_diff: number; yield_pct: number };
      }>;
      check: VarietyData;
    }>("/api/v2/variety-comparison/compare", {
      variety_ids: varietyIds,
      check_id: checkId,
    });
  }

  async getTraitComparison(varietyIds: string[], traits?: string[]) {
    return this.client.post<{
      data: Record<string, Record<string, number>>;
      traits: string[];
    }>("/api/v2/variety-comparison/traits", { variety_ids: varietyIds, traits });
  }
}

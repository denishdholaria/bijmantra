import { ApiClientCore } from "../core/client";

export interface MarkerRegisterRequest {
  marker_id: string;
  name: string;
  chromosome: string;
  position: number;
  marker_type?: string;
  target_allele: string;
  linked_trait: string;
  distance_to_qtl?: number;
}

export interface ForegroundRequest {
  individual_ids: string[];
  target_markers: string[];
}

export interface BackgroundRequest {
  individual_ids: string[];
  recurrent_parent_id: string;
  background_markers: string[];
}

export interface MABCRequest {
  individual_ids: string[];
  target_markers: string[];
  background_markers: string[];
  recurrent_parent_id: string;
  fg_weight?: number;
  bg_weight?: number;
  min_fg_score?: number;
  min_bg_score?: number;
  n_select?: number;
}

export class MarkerAssistedService {
  constructor(private client: ApiClientCore) {}

  async registerMarker(data: MarkerRegisterRequest) {
    return this.client.post<any>("/api/v2/mas/markers", data);
  }

  async listMarkers(params?: { chromosome?: string; trait?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.chromosome)
      searchParams.append("chromosome", params.chromosome);
    if (params?.trait) searchParams.append("trait", params.trait);
    return this.client.get<any>(`/api/v2/mas/markers?${searchParams}`);
  }

  async scoreGenotypes(data: {
    genotypes: {
      individual_id: string;
      marker_id: string;
      allele1: string;
      allele2: string;
    }[];
  }) {
    return this.client.post<any>("/api/v2/mas/score", data);
  }

  async foregroundSelection(data: ForegroundRequest) {
    return this.client.post<any>("/api/v2/mas/foreground", data);
  }

  async backgroundSelection(data: BackgroundRequest) {
    return this.client.post<any>("/api/v2/mas/background", data);
  }

  async mabcSelection(data: MABCRequest) {
    return this.client.post<any>("/api/v2/mas/mabc", data);
  }

  async getStats() {
    return this.client.get<any>("/api/v2/mas/stats");
  }
}

import { ApiClientCore } from "../core/client";

export interface TrialSite {
  id: string;
  name: string;
  location: string;
  country: string;
  coordinates: { lat: number; lng: number };
  trials: number;
  germplasm: number;
  status: "active" | "completed" | "planned";
  season: string;
  lead: string;
  region: string;
}

export interface TrialNetworkStats {
  total_sites: number;
  active_trials: number;
  countries: number;
  germplasm_entries: number;
  collaborators: number;
}

export interface SharedGermplasm {
  id: string;
  name: string;
  sites: number;
  performance: string;
  crop: string;
  type: string;
}

export interface PerformanceMetric {
  trait: string;
  mean: number;
  best: number;
  worst: number;
  cv: number;
  n_sites: number;
}

export class TrialNetworkService {
  constructor(private client: ApiClientCore) {}

  async getSites(params?: {
    season?: string;
    status?: string;
    country?: string;
    region?: string;
  }) {
    const query = new URLSearchParams();
    if (params?.season) query.append("season", params.season);
    if (params?.status) query.append("status", params.status);
    if (params?.country) query.append("country", params.country);
    if (params?.region) query.append("region", params.region);
    const queryStr = query.toString() ? `?${query}` : "";
    return this.client.get<{ sites: TrialSite[] }>(
      `/api/v2/trial-network/sites${queryStr}`
    );
  }

  async getSite(siteId: string) {
    return this.client.get<{ site: TrialSite }>(
      `/api/v2/trial-network/sites/${siteId}`
    );
  }

  async getStatistics(season?: string) {
    const query = season ? `?season=${season}` : "";
    return this.client.get<{ data: TrialNetworkStats }>(
      `/api/v2/trial-network/statistics${query}`
    );
  }

  async getSharedGermplasm(minSites?: number, crop?: string) {
    const params = new URLSearchParams();
    if (minSites) params.append("min_sites", String(minSites));
    if (crop) params.append("crop", crop);
    const query = params.toString() ? `?${params}` : "";
    return this.client.get<{ germplasm: SharedGermplasm[] }>(
      `/api/v2/trial-network/germplasm${query}`
    );
  }

  async getPerformance(trait?: string) {
    const query = trait ? `?trait=${trait}` : "";
    return this.client.get<{ performance: PerformanceMetric[] }>(
      `/api/v2/trial-network/performance${query}`
    );
  }

  async getSiteComparison(siteIds: string[]) {
    return this.client.get<{ data: any }>(
      `/api/v2/trial-network/compare?site_ids=${siteIds.join(",")}`
    );
  }

  async getCountries() {
    return this.client.get<{ countries: string[] }>(
      "/api/v2/trial-network/countries"
    );
  }

  async getSeasons() {
    return this.client.get<{ seasons: string[] }>(
      "/api/v2/trial-network/seasons"
    );
  }
}

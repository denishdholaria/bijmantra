import { ApiClientCore } from "../core/client";

export interface DiversityPopulation {
  id: string;
  name: string;
  size: number;
  region: string;
  crop?: string;
  metrics?: DiversityMetric[];
}

export interface DiversityMetric {
  name: string;
  value: number;
  unit?: string;
}

export interface DistanceMatrix {
  populations: string[];
  matrix: number[][];
}

export interface AMOVAResult {
  among_populations: number;
  among_individuals: number;
  within_individuals: number;
}

export interface AdmixtureResult {
  populations: Array<{
    id: string;
    name: string;
    proportions: number[];
  }>;
  k: number;
}

export interface PCAPoint {
  x: number;
  y: number;
  population: string;
  sample_id?: string;
}

export class GeneticDiversityService {
  constructor(private client: ApiClientCore) {}

  async getPopulations(params?: { crop?: string; region?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.crop) queryParams.append("crop", params.crop);
    if (params?.region) queryParams.append("region", params.region);
    const query = queryParams.toString() ? `?${queryParams}` : "";
    return this.client.get<{ data: DiversityPopulation[] }>(
      `/api/v2/genetic-diversity/populations${query}`
    );
  }

  async getPopulation(populationId: string) {
    return this.client.get<{ data: DiversityPopulation }>(
      `/api/v2/genetic-diversity/populations/${populationId}`
    );
  }

  async getMetrics(populationId: string) {
    return this.client.get<{
      data: { metrics: DiversityMetric[]; recommendations: string[] };
    }>(`/api/v2/genetic-diversity/populations/${populationId}/metrics`);
  }

  async getDistances(populationIds?: string[]) {
    const query = populationIds?.length
      ? `?population_ids=${populationIds.join(",")}`
      : "";
    return this.client.get<{ data: DistanceMatrix[] }>(
      `/api/v2/genetic-diversity/distances${query}`
    );
  }

  async getAMOVA(populationIds?: string[]) {
    const query = populationIds?.length
      ? `?population_ids=${populationIds.join(",")}`
      : "";
    return this.client.get<{ data: { variance_components: AMOVAResult } }>(
      `/api/v2/genetic-diversity/amova${query}`
    );
  }

  async getAdmixture(k?: number, populationIds?: string[]) {
    const params = new URLSearchParams();
    if (k) params.append("k", String(k));
    if (populationIds?.length)
      params.append("population_ids", populationIds.join(","));
    const query = params.toString() ? `?${params}` : "";
    return this.client.get<{ data: AdmixtureResult }>(
      `/api/v2/genetic-diversity/admixture${query}`
    );
  }

  async getPCA(populationIds?: string[]) {
    const query = populationIds?.length
      ? `?population_ids=${populationIds.join(",")}`
      : "";
    return this.client.get<{ data: { points: PCAPoint[] } }>(
      `/api/v2/genetic-diversity/pca${query}`
    );
  }

  async getSummary() {
    return this.client.get<{ data: any }>("/api/v2/genetic-diversity/summary");
  }
}

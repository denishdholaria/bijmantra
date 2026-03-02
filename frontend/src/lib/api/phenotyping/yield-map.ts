import { ApiClientCore } from "../core/client";

export interface YieldMapStudy {
  id: string;
  name: string;
  season: string;
  program_id: string;
  program_name: string;
  location: string;
  area_ha: number;
  total_plots: number;
  status: string;
  upload_date: string;
}

export interface YieldMapPlot {
  plot_id: string;
  plot_name: string;
  value: number;
  unit: string;
  coordinates: {
    geometry: {
      type: "Polygon";
      coordinates: number[][][];
    };
    positionCoordinateX: string;
    positionCoordinateY: string;
  };
  observations: Array<{
    observationVariableName: string;
    value: string;
  }>;
}

export class YieldMapService {
  constructor(private client: ApiClientCore) {}

  async getStudies(params?: {
    program_id?: string;
    season?: string;
    limit?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.set("program_id", params.program_id);
    if (params?.season) searchParams.set("season", params.season);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    const query = searchParams.toString();
    return this.client.get<{ result: { data: YieldMapStudy[] } }>(
      `/api/v2/yield-map/studies${query ? `?${query}` : ""}`
    );
  }

  async getFieldPlotData(params: { study_id: string; trait?: string }) {
    const searchParams = new URLSearchParams();
    if (params.trait) searchParams.set("trait", params.trait);
    const query = searchParams.toString();
    return this.client.get<{ result: { data: YieldMapPlot[] } }>(
      `/api/v2/yield-map/studies/${params.study_id}/plots${
        query ? `?${query}` : ""
      }`
    );
  }

  async getStats(studyId: string) {
    return this.client.get<{
      study_id: string;
      total_plots: number;
      min_yield: number;
      max_yield: number;
      avg_yield: number;
      std_yield: number;
      cv_percent: number;
    }>(`/api/v2/yield-map/studies/${studyId}/stats`);
  }

  async getTraits(studyId: string) {
    return this.client.get<{
      data: Array<{ id: string; name: string; unit: string }>;
    }>(`/api/v2/yield-map/studies/${studyId}/traits`);
  }

  async getSpatialAnalysis(studyId: string) {
    return this.client.get<any>(
      `/api/v2/yield-map/studies/${studyId}/spatial-analysis`
    );
  }
}

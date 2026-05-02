import { ApiClientCore } from "../core/client";

export interface SpatialField {
  field_id: string;
  name: string;
  location: string;
  latitude: number;
  longitude: number;
  area_ha: number;
  rows: number;
  columns: number;
  plot_size_m2: number;
  soil_type?: string;
  irrigation?: string;
}

export interface SpatialPlot {
  plot_id: string;
  row: number;
  column: number;
  x_m: number;
  y_m: number;
  center_lat: number;
  center_lon: number;
}

export interface DistanceResult {
  distance_m: number;
  distance_km: number;
}

export class SpatialService {
  constructor(private client: ApiClientCore) {}

  async getFields() {
    return this.client.get<{ data: SpatialField[]; count: number }>(
      "/api/v2/spatial/fields"
    );
  }

  async getField(fieldId: string) {
    return this.client.get<{ data: SpatialField }>(
      `/api/v2/spatial/fields/${fieldId}`
    );
  }

  async createField(data: {
    name: string;
    location: string;
    latitude: number;
    longitude: number;
    area_ha: number;
    rows: number;
    columns: number;
    plot_size_m2: number;
    soil_type?: string;
    irrigation?: string;
  }) {
    return this.client.post<{ data: SpatialField }>(
      "/api/v2/spatial/fields",
      data
    );
  }

  async getPlots(fieldId: string) {
    return this.client.get<{ data: SpatialPlot[]; count: number }>(
      `/api/v2/spatial/fields/${fieldId}/plots`
    );
  }

  async generatePlots(
    fieldId: string,
    params: {
      plot_width_m: number;
      plot_length_m: number;
      alley_width_m?: number;
      border_m?: number;
    }
  ) {
    return this.client.post<{ data: SpatialPlot[]; count: number }>(
      `/api/v2/spatial/fields/${fieldId}/plots`,
      params
    );
  }

  async calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ) {
    return this.client.post<{ data: DistanceResult }>(
      "/api/v2/spatial/calculate/distance",
      { lat1, lon1, lat2, lon2 }
    );
  }

  async analyzeAutocorrelation(
    values: any[],
    xKey?: string,
    yKey?: string,
    valueKey?: string
  ) {
    return this.client.post<{ data: any }>(
      "/api/v2/spatial/analyze/autocorrelation",
      {
        values,
        x_key: xKey,
        y_key: yKey,
        value_key: valueKey,
      }
    );
  }

  async analyzeMovingAverage(values: any[], windowSize?: number) {
    return this.client.post<{ data: any }>(
      "/api/v2/spatial/analyze/moving-average",
      { values, window_size: windowSize || 3 }
    );
  }

  async analyzeNearestNeighbor(points: any[], area?: number) {
    return this.client.post<{ data: any }>(
      "/api/v2/spatial/analyze/nearest-neighbor",
      { points, area }
    );
  }

  async analyzeRowColumnTrend(values: any[]) {
    return this.client.post<{ data: any }>(
      "/api/v2/spatial/analyze/row-column-trend",
      { values }
    );
  }

  async getStatistics() {
    return this.client.get<{ data: any }>("/api/v2/spatial/statistics");
  }

  async runSpATS(data: {
    field_id: string;
    trait: string;
    genotype_col: string;
    row_col: string;
    col_col: string;
    n_segments_row?: number;
    n_segments_col?: number;
  }) {
    return this.client.post<{
      success: boolean;
      job_id: string;
      results: {
        adjusted_means: Record<string, number>;
        heritability: number;
        spatial_trend: number[][]; // grid
      };
    }>("/api/v2/spatial/spats", data);
  }
}

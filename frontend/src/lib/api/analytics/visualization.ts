import { ApiClientCore } from "../core/client";

export interface ChartConfig {
  id: string;
  name: string;
  type: string;
  dataSource: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  isPublic: boolean;
  config: Record<string, any>;
}

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label?: string;
    data: any[];
    backgroundColor?: string | string[];
    borderColor?: string;
    fill?: boolean;
  }>;
  options: Record<string, any>;
}

export interface DataSourceInfo {
  id: string;
  name: string;
  type: string;
  recordCount: number;
  lastUpdated: string;
}

export interface ChartTypeInfo {
  id: string;
  name: string;
  icon: string;
  description: string;
}

export class DataVisualizationService {
  constructor(private client: ApiClientCore) {}

  async getCharts(params?: {
    type?: string;
    data_source?: string;
    search?: string;
    public_only?: boolean;
  }): Promise<{ data: ChartConfig[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.type) searchParams.set("type", params.type);
    if (params?.data_source)
      searchParams.set("data_source", params.data_source);
    if (params?.search) searchParams.set("search", params.search);
    if (params?.public_only) searchParams.set("public_only", "true");
    const query = searchParams.toString();
    return this.client.get<{ data: ChartConfig[]; total: number }>(
      `/api/v2/visualizations/charts${query ? `?${query}` : ""}`,
    );
  }

  async getChart(chartId: string): Promise<{ data: ChartConfig }> {
    return this.client.get<{ data: ChartConfig }>(`/api/v2/visualizations/charts/${chartId}`);
  }

  async createChart(data: Partial<ChartConfig>): Promise<any> {
    return this.client.post("/api/v2/visualizations/charts", data);
  }

  async updateChart(chartId: string, data: Partial<ChartConfig>): Promise<any> {
    return this.client.put(`/api/v2/visualizations/charts/${chartId}`, data);
  }

  async deleteChart(chartId: string): Promise<any> {
    return this.client.delete(`/api/v2/visualizations/charts/${chartId}`);
  }

  async getChartData(chartId: string, limit?: number): Promise<ChartData> {
    const query = limit ? `?limit=${limit}` : "";
    return this.client.get<ChartData>(`/api/v2/visualizations/charts/${chartId}/data${query}`);
  }

  async getDataSources(): Promise<{ data: DataSourceInfo[] }> {
    return this.client.get<{ data: DataSourceInfo[] }>("/api/v2/visualizations/data-sources");
  }

  async getChartTypes(): Promise<{ data: ChartTypeInfo[] }> {
    return this.client.get<{ data: ChartTypeInfo[] }>("/api/v2/visualizations/chart-types");
  }

  async getStatistics(): Promise<{
    total_charts: number;
    by_type: Record<string, number>;
    public_charts: number;
    private_charts: number;
    data_sources: number;
  }> {
    return this.client.get<{
      total_charts: number;
      by_type: Record<string, number>;
      public_charts: number;
      private_charts: number;
      data_sources: number;
    }>("/api/v2/visualizations/statistics");
  }

  async previewChart(params: {
    chart_type: string;
    data_source: string;
    x_axis?: string;
    y_axis?: string;
    group_by?: string;
  }): Promise<any> {
    const searchParams = new URLSearchParams();
    searchParams.set("chart_type", params.chart_type);
    searchParams.set("data_source", params.data_source);
    if (params.x_axis) searchParams.set("x_axis", params.x_axis);
    if (params.y_axis) searchParams.set("y_axis", params.y_axis);
    if (params.group_by) searchParams.set("group_by", params.group_by);
    return this.client.post(`/api/v2/visualizations/preview?${searchParams}`);
  }

  async exportChart(
    chartId: string,
    format: string = "png",
    width?: number,
    height?: number,
  ): Promise<any> {
    const searchParams = new URLSearchParams();
    searchParams.set("format", format);
    if (width) searchParams.set("width", width.toString());
    if (height) searchParams.set("height", height.toString());
    return this.client.post(`/api/v2/visualizations/charts/${chartId}/export?${searchParams}`);
  }
}

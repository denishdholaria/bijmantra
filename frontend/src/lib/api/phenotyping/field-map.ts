import { ApiClientCore } from "../core/client";

export interface Field {
  id: string;
  name: string;
  location: string;
  station: string;
  area: number;
  plots: number;
  status: string;
  soilType?: string;
  irrigationType?: string;
}

export interface Plot {
  id: string;
  plotNumber: number;
  status: string;
  row?: number;
  column?: number;
  entryId?: string;
  trialId?: string;
}

export class FieldMapService {
  constructor(private client: ApiClientCore) {}

  async getFields(params?: {
    station?: string;
    status?: string;
    search?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.station) searchParams.set("station", params.station);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    return this.client.get<Field[]>(
      `/api/v2/field-map/fields${query ? `?${query}` : ""}`
    );
  }

  async getField(fieldId: string) {
    return this.client.get<Field>(`/api/v2/field-map/fields/${fieldId}`);
  }

  async createField(data: {
    name: string;
    location: string;
    area: number;
    plots: number;
    soilType?: string;
    irrigationType?: string;
  }) {
    return this.client.post<Field>("/api/v2/field-map/fields", data);
  }

  async updateField(fieldId: string, data: Partial<Field>) {
    return this.client.patch<Field>(
      `/api/v2/field-map/fields/${fieldId}`,
      data
    );
  }

  async deleteField(fieldId: string) {
    return this.client.delete<{ success: boolean }>(
      `/api/v2/field-map/fields/${fieldId}`
    );
  }

  async getSummary() {
    return this.client.get<{
      totalFields: number;
      totalArea: number;
      totalPlots: number;
      activeFields: number;
    }>("/api/v2/field-map/summary");
  }

  async getStations() {
    return this.client.get<string[]>("/api/v2/field-map/stations");
  }

  async getStatuses() {
    return this.client.get<{
      fieldStatuses: string[];
      plotStatuses: string[];
    }>("/api/v2/field-map/statuses");
  }

  async getPlots(
    fieldId: string,
    params?: { status?: string; trial_id?: string }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.trial_id) searchParams.set("trial_id", params.trial_id);
    const query = searchParams.toString();
    return this.client.get<Plot[]>(
      `/api/v2/field-map/fields/${fieldId}/plots${query ? `?${query}` : ""}`
    );
  }

  async getPlot(fieldId: string, plotId: string) {
    return this.client.get<Plot>(
      `/api/v2/field-map/fields/${fieldId}/plots/${plotId}`
    );
  }

  async updatePlot(fieldId: string, plotId: string, data: Partial<Plot>) {
    return this.client.patch<Plot>(
      `/api/v2/field-map/fields/${fieldId}/plots/${plotId}`,
      data
    );
  }

  async deleteAttribute(attributeDbId: string) {
    return this.client.delete<void>(`/brapi/v2/attributes/${attributeDbId}`);
  }
}

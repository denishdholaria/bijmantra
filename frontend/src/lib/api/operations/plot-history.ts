import { ApiClientCore } from "../core/client";

export class PlotHistoryService {
  constructor(private client: ApiClientCore) {}
  async getPlotHistoryStats(fieldId?: string) {
    const query = fieldId ? `?field_id=${fieldId}` : "";
    return this.client.request<{
      total_plots: number;
      total_events: number;
      recent_events: number;
      by_event_type: Record<string, number>;
      by_field: Record<string, number>;
      active_plots: number;
    }>(`/api/v2/plot-history/stats${query}`);
  }

  async getPlotHistoryEventTypes() {
    return this.client.request<{ types: any[] }>("/api/v2/plot-history/event-types");
  }

  async getPlotHistoryFields() {
    return this.client.request<{ fields: any[] }>("/api/v2/plot-history/fields");
  }

  async getPlotHistoryPlots(params?: {
    field_id?: string;
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.field_id) searchParams.append("field_id", params.field_id);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.search) searchParams.append("search", params.search);
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.offset) searchParams.append("offset", String(params.offset));
    const query = searchParams.toString();
    return this.client.request<{ plots: any[]; total: number }>(
      `/api/v2/plot-history/plots${query ? `?${query}` : ""}`,
    );
  }

  async getPlotHistoryPlot(plotId: string) {
    return this.client.request<any>(`/api/v2/plot-history/plots/${plotId}`);
  }

  async getPlotHistoryEvents(
    plotId: string,
    params?: { event_type?: string; start_date?: string; end_date?: string },
  ) {
    const searchParams = new URLSearchParams();
    if (params?.event_type)
      searchParams.append("event_type", params.event_type);
    if (params?.start_date)
      searchParams.append("start_date", params.start_date);
    if (params?.end_date) searchParams.append("end_date", params.end_date);
    const query = searchParams.toString();
    return this.client.request<{ events: any[]; total: number }>(
      `/api/v2/plot-history/plots/${plotId}/events${query ? `?${query}` : ""}`,
    );
  }

  async createPlotHistoryEvent(
    plotId: string,
    data: {
      type: string;
      description: string;
      date?: string;
      value?: string;
      notes?: string;
      recorded_by?: string;
    },
  ) {
    return this.client.request<any>(`/api/v2/plot-history/plots/${plotId}/events`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updatePlotHistoryEvent(
    eventId: string,
    data: {
      type?: string;
      description?: string;
      date?: string;
      value?: string;
      notes?: string;
    },
  ) {
    return this.client.request<any>(`/api/v2/plot-history/events/${eventId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deletePlotHistoryEvent(eventId: string) {
    return this.client.request<{ success: boolean }>(
      `/api/v2/plot-history/events/${eventId}`,
      {
        method: "DELETE",
      },
    );
  }
}

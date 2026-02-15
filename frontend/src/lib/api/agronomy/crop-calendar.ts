import { ApiClientCore } from "../core/client";

export class CropCalendarService {
  constructor(private client: ApiClientCore) {}
  async getCropProfiles() {
    return this.client.request<{
      crops: Array<{
        crop_id: string;
        name: string;
        species: string;
        days_to_maturity: number;
        base_temperature: number;
        optimal_temp_min: number;
        optimal_temp_max: number;
        growth_stages: Record<string, number>;
      }>;
    }>("/api/v2/crop-calendar/crops");
  }

  async createCropProfile(data: {
    crop_id: string;
    name: string;
    species: string;
    days_to_maturity: number;
    base_temperature: number;
    optimal_temp_min: number;
    optimal_temp_max: number;
    growth_stages: Record<string, number>;
  }) {
    return this.client.request<any>("/api/v2/crop-calendar/crops", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getPlantingEvents(status?: string) {
    const params = status ? `?status=${status}` : "";
    return this.client.request<{
      events: Array<{
        event_id: string;
        crop_id: string;
        crop_name: string;
        trial_id: string;
        sowing_date: string;
        expected_harvest: string;
        location: string;
        area_hectares: number;
        notes: string;
        status: string;
      }>;
    }>(`/api/v2/crop-calendar/events${params}`);
  }

  async createPlantingEvent(data: {
    crop_id: string;
    trial_id?: string;
    sowing_date: string;
    location: string;
    area_hectares: number;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/crop-calendar/events", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getGrowthStage(eventId: string) {
    return this.client.request<{
      event_id: string;
      crop_name: string;
      current_stage: string;
      days_since_sowing: number;
      days_to_next_stage: number;
      next_stage: string;
      progress_percent: number;
    }>(`/api/v2/crop-calendar/growth-stage/${eventId}`);
  }

  async getUpcomingActivities(daysAhead: number = 30) {
    return this.client.request<{
      activities: Array<{
        activity_id: string;
        event_id: string;
        activity_type: string;
        scheduled_date: string;
        description: string;
        completed: boolean;
        completed_date?: string;
      }>;
    }>(`/api/v2/crop-calendar/activities?days_ahead=${daysAhead}`);
  }

  async completeActivity(activityId: string, notes?: string) {
    return this.client.request<any>(
      `/api/v2/crop-calendar/activities/${activityId}/complete`,
      {
        method: "POST",
        body: JSON.stringify({ notes: notes || "" }),
      },
    );
  }

  async calculateGDD(data: {
    crop_id: string;
    sowing_date: string;
    location_id?: string;
  }) {
    return this.client.request<{
      crop_id: string;
      accumulated_gdd: number;
      target_gdd: number;
      progress_percent: number;
      estimated_maturity: string;
    }>("/api/v2/crop-calendar/gdd", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getCalendarView(month?: number, year?: number) {
    const params = new URLSearchParams();
    if (month) params.append("month", month.toString());
    if (year) params.append("year", year.toString());
    const query = params.toString() ? `?${params}` : "";
    return this.client.request<{
      month: number;
      year: number;
      events: Array<{
        date: string;
        type: string;
        title: string;
        event_id?: string;
        activity_id?: string;
      }>;
    }>(`/api/v2/crop-calendar/view${query}`);
  }
}

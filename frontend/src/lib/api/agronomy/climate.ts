import { ApiClientCore } from "../core/client";

export class ClimateService {
  constructor(private client: ApiClientCore) {}
  async getClimateAnalysis(
    locationId: string,
    locationName: string,
    years: number = 30,
  ) {
    const params = new URLSearchParams({
      location_name: locationName,
      years: String(years),
    });
    return this.client.request<{
      location_id: string;
      location_name: string;
      analysis_period: string;
      indicators: Array<{
        name: string;
        current_value: number;
        historical_avg: number;
        change: number;
        change_percent: number;
        unit: string;
        trend: string;
      }>;
      recommendations: Array<{
        icon: string;
        title: string;
        description: string;
        priority: string;
      }>;
      generated_at: string;
    }>(`/api/v2/climate/analysis/${locationId}?${params}`);
  }

  async getDroughtMonitor(locationId: string, locationName: string) {
    const params = new URLSearchParams({
      location_name: locationName,
    });
    return this.client.request<{
      location_id: string;
      alert_active: boolean;
      alert_message: string | null;
      indicators: Array<{
        name: string;
        value: number;
        unit: string;
        status: string;
        trend: string;
      }>;
      regions: Array<{
        name: string;
        status: string;
        description: string;
        soil_moisture: number;
        days_since_rain: number;
      }>;
      recommendations: Array<{
        priority: string;
        action: string;
        impact: string;
      }>;
      generated_at: string;
    }>(`/api/v2/climate/drought/${locationId}?${params}`);
  }

  async getClimateTrends(
    locationId: string,
    locationName: string,
    parameter: string = "temperature",
    years: number = 30,
  ) {
    const params = new URLSearchParams({
      location_name: locationName,
      parameter,
      years: String(years),
    });
    return this.client.request<{
      location_id: string;
      location_name: string;
      parameter: string;
      period: string;
      data: Array<{
        year: number;
        value: number;
        unit: string;
        generated_at: string;
      }>;
      generated_at: string;
    }>(`/api/v2/climate/trends/${locationId}?${params}`);
  }
}

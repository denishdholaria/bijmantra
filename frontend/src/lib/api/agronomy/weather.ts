import { ApiClientCore } from "../core/client";

export class WeatherService {
  constructor(private client: ApiClientCore) {}
  async getWeatherForecast(
    locationId: string,
    locationName: string,
    days: number = 14,
    crop: string = "wheat",
  ) {
    const params = new URLSearchParams({
      location_name: locationName,
      days: String(days),
      crop,
    });
    return this.client.request<{
      location_id: string;
      location_name: string;
      generated_at: string;
      forecast_days: number;
      daily_forecast: Array<{
        date: string;
        location_id: string;
        location_name: string;
        temp_min: number;
        temp_max: number;
        temp_avg: number;
        humidity: number;
        precipitation: number;
        wind_speed: number;
        condition: string;
        uv_index: number;
        soil_moisture: number | null;
        solar_radiation: number | null;
        et0: number | null;
        soil_temperature: number | null;
        vapor_pressure_deficit: number | null;
      }>;
      impacts: Array<{
        date: string;
        event: string;
        probability: number;
        severity: string;
        affected_activities: string[];
        recommendation: string;
        details: string | null;
      }>;
      optimal_windows: Array<{
        activity: string;
        start: string;
        end: string;
        confidence: number;
        conditions: string;
      }>;
      gdd_forecast: Array<{
        location_id: string;
        date: string;
        gdd_daily: number;
        gdd_cumulative: number;
        base_temp: number;
        crop: string;
      }>;
      alerts: string[];
    }>(`/api/v2/weather/forecast/${locationId}?${params}`);
  }

  async getWeatherImpacts(
    locationId: string,
    locationName: string,
    days: number = 7,
  ) {
    const params = new URLSearchParams({
      location_name: locationName,
      days: String(days),
    });
    return this.client.request<{
      location_id: string;
      impacts: Array<{
        date: string;
        event: string;
        probability: number;
        severity: string;
        affected_activities: string[];
        recommendation: string;
      }>;
    }>(`/api/v2/weather/impacts/${locationId}?${params}`);
  }

  async getWeatherActivityWindows(
    locationId: string,
    locationName: string,
    activity: string,
    days: number = 14,
  ) {
    const params = new URLSearchParams({
      location_name: locationName,
      activity,
      days: String(days),
    });
    return this.client.request<{
      activity: string;
      windows: Array<{
        start: string;
        end: string;
        confidence: number;
        conditions: string;
      }>;
    }>(`/api/v2/weather/activity-windows/${locationId}?${params}`);
  }

  async getWeatherGDD(
    locationId: string,
    locationName: string,
    crop: string = "wheat",
    days: number = 14,
  ) {
    const params = new URLSearchParams({
      location_name: locationName,
      crop,
      days: String(days),
    });
    return this.client.request<{
      crop: string;
      base_temp: number;
      gdd_data: Array<{
        date: string;
        gdd_daily: number;
        gdd_cumulative: number;
      }>;
    }>(`/api/v2/weather/gdd/${locationId}?${params}`);
  }

  async getWeatherVeenaSummary(
    locationId: string,
    locationName: string,
    days: number = 7,
  ) {
    const params = new URLSearchParams({
      location_name: locationName,
      days: String(days),
    });
    return this.client.request<{
      location_id: string;
      location_name: string;
      summary: string;
    }>(`/api/v2/weather/veena/summary/${locationId}?${params}`);
  }

  async getWeatherAlerts(locationIds: string[], days: number = 7) {
    const params = new URLSearchParams({
      location_ids: locationIds.join(","),
      days: String(days),
    });
    return this.client.request<{
      alerts: Array<{
        location_id: string;
        alerts: string[];
      }>;
    }>(`/api/v2/weather/alerts?${params}`);
  }
}

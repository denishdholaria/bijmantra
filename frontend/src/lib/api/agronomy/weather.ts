import { ApiClientCore } from "../core/client";
import {
  WeatherStation, WeatherStationCreate, WeatherStationUpdate,
  ForecastData, ForecastDataCreate,
  HistoricalRecord, HistoricalRecordCreate,
  ClimateZone, ClimateZoneCreate,
  AlertSubscription, AlertSubscriptionCreate, AlertSubscriptionUpdate
} from "../../../types/weather";

export class WeatherService {
  constructor(private client: ApiClientCore) {}

  // ============ Existing Weather Intelligence Methods ============

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

  async getWeatherReevuSummary(
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

  /**
   * @deprecated Use `getWeatherReevuSummary()`.
   * Compatibility alias retained for one migration window.
   * TODO(reevu-migration): remove after downstream callsites fully switch to REEVU naming.
   */
  async getWeatherVeenaSummary(
    locationId: string,
    locationName: string,
    days: number = 7,
  ) {
    return this.getWeatherReevuSummary(locationId, locationName, days);
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

  // ============ Weather Station (CRUD) ============

  async listWeatherStations(skip: number = 0, limit: number = 100) {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    return this.client.request<WeatherStation[]>(`/api/v2/weather/stations?${params}`);
  }

  async createWeatherStation(station: WeatherStationCreate) {
    return this.client.request<WeatherStation>('/api/v2/weather/stations', {
      method: 'POST',
      body: JSON.stringify(station)
    });
  }

  async getWeatherStation(id: number) {
    return this.client.request<WeatherStation>(`/api/v2/weather/stations/${id}`);
  }

  async updateWeatherStation(id: number, station: WeatherStationUpdate) {
    return this.client.request<WeatherStation>(`/api/v2/weather/stations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(station)
    });
  }

  async deleteWeatherStation(id: number) {
    return this.client.request<WeatherStation>(`/api/v2/weather/stations/${id}`, {
      method: 'DELETE'
    });
  }

  // ============ Forecast Data (CRUD) ============

  async listForecastData(stationId?: number, skip: number = 0, limit: number = 100) {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (stationId) params.append('station_id', String(stationId));
    return this.client.request<ForecastData[]>(`/api/v2/weather/forecasts?${params}`);
  }

  async createForecastData(forecast: ForecastDataCreate) {
    return this.client.request<ForecastData>('/api/v2/weather/forecasts', {
      method: 'POST',
      body: JSON.stringify(forecast)
    });
  }

  async deleteForecastData(id: number) {
    return this.client.request<ForecastData>(`/api/v2/weather/forecasts/${id}`, {
      method: 'DELETE'
    });
  }

  // ============ Historical Record (CRUD) ============

  async listHistoricalRecords(stationId?: number, skip: number = 0, limit: number = 100) {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (stationId) params.append('station_id', String(stationId));
    return this.client.request<HistoricalRecord[]>(`/api/v2/weather/historical?${params}`);
  }

  async createHistoricalRecord(record: HistoricalRecordCreate) {
    return this.client.request<HistoricalRecord>('/api/v2/weather/historical', {
      method: 'POST',
      body: JSON.stringify(record)
    });
  }

  async deleteHistoricalRecord(id: number) {
    return this.client.request<HistoricalRecord>(`/api/v2/weather/historical/${id}`, {
      method: 'DELETE'
    });
  }

  // ============ Climate Zone (CRUD) ============

  async listClimateZones(skip: number = 0, limit: number = 100) {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    return this.client.request<ClimateZone[]>(`/api/v2/weather/climate-zones?${params}`);
  }

  async createClimateZone(zone: ClimateZoneCreate) {
    return this.client.request<ClimateZone>('/api/v2/weather/climate-zones', {
      method: 'POST',
      body: JSON.stringify(zone)
    });
  }

  async deleteClimateZone(id: number) {
    return this.client.request<ClimateZone>(`/api/v2/weather/climate-zones/${id}`, {
      method: 'DELETE'
    });
  }

  // ============ Alert Subscription (CRUD) ============

  async listAlertSubscriptions(userId?: number, skip: number = 0, limit: number = 100) {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (userId) params.append('user_id', String(userId));
    return this.client.request<AlertSubscription[]>(`/api/v2/weather/alerts/subscriptions?${params}`);
  }

  async createAlertSubscription(subscription: AlertSubscriptionCreate) {
    return this.client.request<AlertSubscription>('/api/v2/weather/alerts/subscriptions', {
      method: 'POST',
      body: JSON.stringify(subscription)
    });
  }

  async updateAlertSubscription(id: number, subscription: AlertSubscriptionUpdate) {
    return this.client.request<AlertSubscription>(`/api/v2/weather/alerts/subscriptions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(subscription)
    });
  }

  async deleteAlertSubscription(id: number) {
    return this.client.request<AlertSubscription>(`/api/v2/weather/alerts/subscriptions/${id}`, {
      method: 'DELETE'
    });
  }
}

export interface WeatherStation {
  id: number;
  name: string;
  location_id?: number;
  latitude: number;
  longitude: number;
  elevation?: number;
  provider?: string;
  status?: string;
  additional_info?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface WeatherStationCreate {
  name: string;
  location_id?: number;
  latitude: number;
  longitude: number;
  elevation?: number;
  provider?: string;
  status?: string;
  additional_info?: Record<string, any>;
}

export interface WeatherStationUpdate {
  name?: string;
  location_id?: number;
  latitude?: number;
  longitude?: number;
  elevation?: number;
  provider?: string;
  status?: string;
  additional_info?: Record<string, any>;
}

export interface ForecastData {
  id: number;
  station_id: number;
  forecast_date: string;
  generated_at: string;
  data: Record<string, any>;
  source?: string;
  created_at: string;
  updated_at: string;
}

export interface ForecastDataCreate {
  station_id: number;
  forecast_date: string;
  data: Record<string, any>;
  source?: string;
}

export interface HistoricalRecord {
  id: number;
  station_id: number;
  date: string;
  temperature_max?: number;
  temperature_min?: number;
  precipitation?: number;
  humidity?: number;
  wind_speed?: number;
  data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface HistoricalRecordCreate {
  station_id: number;
  date: string;
  temperature_max?: number;
  temperature_min?: number;
  precipitation?: number;
  humidity?: number;
  wind_speed?: number;
  data?: Record<string, any>;
}

export interface ClimateZone {
  id: number;
  name: string;
  code: string;
  description?: string;
  additional_info?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ClimateZoneCreate {
  name: string;
  code: string;
  description?: string;
  additional_info?: Record<string, any>;
}

export interface AlertSubscription {
  id: number;
  user_id: number;
  location_id?: number;
  station_id?: number;
  alert_type: string;
  threshold: Record<string, any>;
  is_active?: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertSubscriptionCreate {
  user_id: number;
  location_id?: number;
  station_id?: number;
  alert_type: string;
  threshold: Record<string, any>;
  is_active?: boolean;
}

export interface AlertSubscriptionUpdate {
  location_id?: number;
  station_id?: number;
  alert_type?: string;
  threshold?: Record<string, any>;
  is_active?: boolean;
}

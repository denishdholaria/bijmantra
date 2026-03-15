export interface IoTDevice {
  id: number;
  device_db_id: string;
  name: string;
  description?: string;
  device_type: string;
  connectivity?: string;
  protocol?: string;
  status: string;
  battery_level?: number;
  signal_strength?: number;
  firmware_version?: string;
  location_description?: string;
  elevation?: number;
  field_id?: number;
  environment_id?: string;
  study_id?: number;
  organization_id: number;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  installation_date?: string;
  calibration_date?: string;
  last_seen?: string;
  additional_info?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface IoTDeviceCreate {
  device_db_id: string;
  name: string;
  description?: string;
  device_type: string;
  connectivity?: string;
  protocol?: string;
  location_description?: string;
  elevation?: number;
  field_id?: number;
  environment_id?: string;
  study_id?: number;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  additional_info?: Record<string, any>;
  sensors?: string[];
}

export interface IoTDeviceUpdate {
  name?: string;
  description?: string;
  device_type?: string;
  connectivity?: string;
  protocol?: string;
  status?: string;
  location_description?: string;
  elevation?: number;
  field_id?: number;
  environment_id?: string;
  study_id?: number;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  calibration_date?: string;
  additional_info?: Record<string, any>;
}

export interface IoTTelemetry {
  timestamp: string;
  device_id: number;
  sensor_id: number;
  value: number;
  raw_value?: number;
  quality?: string;
  quality_code?: number;
  additional_info?: Record<string, any>;
}

export interface IoTTelemetryCreate {
  device_db_id: string;
  sensor_code: string;
  value: number;
  timestamp?: string;
  raw_value?: number;
  quality?: string;
  quality_code?: number;
  additional_info?: Record<string, any>;
}

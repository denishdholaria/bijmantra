export type SensorTimeRange = '7d' | '30d' | '90d' | '1y';

export interface SensorLocation {
  id: string;
  name: string;
  type: string;
  locationLabel: string;
  sensorCount: number;
  sensors: string[];
  status: string;
  battery?: number;
  signal?: number;
  lastSeen?: string | null;
  coordinates?: {
    latitude: number;
    longitude: number;
  } | null;
}

export interface SensorReading {
  id: string;
  sensor: string;
  value: number;
  unit: string;
  timestamp: string;
}

export interface SensorChartPoint {
  timestamp: string;
  temperature: number | null;
  humidity: number | null;
  rainfall: number | null;
}

export interface SensorSeriesResult {
  locationId: string;
  range: SensorTimeRange;
  points: SensorChartPoint[];
  latestReadings: SensorReading[];
}

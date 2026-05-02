import { apiClient } from '@/lib/api-client';
import type {
  SensorChartPoint,
  SensorLocation,
  SensorReading,
  SensorSeriesResult,
  SensorTimeRange,
} from '../types';

interface DevicePayload {
  devices: Array<{
    device_id?: string;
    id?: string;
    name: string;
    device_type?: string;
    type?: string;
    location: string;
    sensors: string[];
    status: string;
    battery?: number;
    signal?: number;
    last_seen?: string | null;
    coordinates?: { latitude: number; longitude: number } | null;
  }>;
}

interface ReadingPayload {
  readings: Array<{
    id: string;
    device_id: string;
    sensor: string;
    value: number;
    unit: string;
    timestamp: string;
  }>;
}

const RANGE_TO_DAYS: Record<SensorTimeRange, number> = {
  '7d': 7,
  '30d': 30,
  '90d': 90,
  '1y': 365,
};

function toIsoSince(range: SensorTimeRange): string {
  const since = new Date();
  since.setDate(since.getDate() - RANGE_TO_DAYS[range]);
  return since.toISOString();
}

function toChartPoints(readings: SensorReading[]): SensorChartPoint[] {
  const pointsByTimestamp = new Map<string, SensorChartPoint>();

  for (const reading of readings) {
    const timestampKey = reading.timestamp.slice(0, 10);
    const existing = pointsByTimestamp.get(timestampKey) ?? {
      timestamp: timestampKey,
      temperature: null,
      humidity: null,
      rainfall: null,
    };

    if (reading.sensor === 'temperature') {
      existing.temperature = reading.value;
    }
    if (reading.sensor === 'humidity') {
      existing.humidity = reading.value;
    }
    if (reading.sensor === 'rainfall') {
      existing.rainfall = reading.value;
    }

    pointsByTimestamp.set(timestampKey, existing);
  }

  return Array.from(pointsByTimestamp.values()).sort((left, right) =>
    left.timestamp.localeCompare(right.timestamp)
  );
}

class SensorDashboardService {
  async getLocations(): Promise<SensorLocation[]> {
    const payload = await apiClient.get<DevicePayload>('/api/v2/sensors/devices');

    return (payload.devices ?? []).map((device) => ({
      id: device.device_id ?? device.id ?? device.name,
      name: device.name,
      type: device.device_type ?? device.type ?? 'sensor-device',
      locationLabel: device.location,
      sensorCount: device.sensors.length,
      sensors: device.sensors,
      status: device.status,
      battery: device.battery,
      signal: device.signal,
      lastSeen: device.last_seen ?? null,
      coordinates: device.coordinates ?? null,
    }));
  }

  async getSensorSeries(locationId: string, range: SensorTimeRange): Promise<SensorSeriesResult> {
    const searchParams = new URLSearchParams({
      device_id: locationId,
      since: toIsoSince(range),
      limit: '1000',
    });

    const payload = await apiClient.get<ReadingPayload>(
      `/api/v2/sensors/readings?${searchParams.toString()}`
    );

    const readings: SensorReading[] = (payload.readings ?? [])
      .filter((reading) =>
        reading.sensor === 'temperature' ||
        reading.sensor === 'humidity' ||
        reading.sensor === 'rainfall'
      )
      .map((reading) => ({
        id: reading.id,
        sensor: reading.sensor,
        value: reading.value,
        unit: reading.unit,
        timestamp: reading.timestamp,
      }));

    return {
      locationId,
      range,
      points: toChartPoints(readings),
      latestReadings: readings.slice(0, 12),
    };
  }
}

export const sensorDashboardService = new SensorDashboardService();

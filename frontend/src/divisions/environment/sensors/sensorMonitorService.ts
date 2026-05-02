/**
 * Service layer for environmental sensor monitoring operations
 */

import type { SensorReading, SensorFilter } from './types';

class SensorMonitorService {
  async fetchReadings(filter: SensorFilter): Promise<SensorReading[]> {
    // TODO: Replace with actual API call
    const params = new URLSearchParams();
    if (filter.sensorId) params.append('sensor_id', filter.sensorId);
    if (filter.sensorType) params.append('sensor_type', filter.sensorType);
    if (filter.location) params.append('location', filter.location);
    if (filter.startDate) params.append('start_date', filter.startDate.toISOString());
    if (filter.endDate) params.append('end_date', filter.endDate.toISOString());

    const response = await fetch(`/api/v2/environment/sensors/readings?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch sensor readings');
    }
    return response.json();
  }

  async getLatestReading(sensorId: string): Promise<SensorReading> {
    const response = await fetch(`/api/v2/environment/sensors/${sensorId}/latest`);
    if (!response.ok) {
      throw new Error('Failed to fetch latest reading');
    }
    return response.json();
  }
}

export const sensorMonitorService = new SensorMonitorService();

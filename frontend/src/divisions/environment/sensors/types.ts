/**
 * Type definitions for Environment Sensors module
 */

export interface SensorReading {
  id: string;
  sensorId: string;
  sensorType: 'temperature' | 'humidity' | 'light' | 'co2' | 'soil_moisture' | 'ph';
  value: number;
  unit: string;
  timestamp: Date;
  location: string;
  quality: 'good' | 'fair' | 'poor';
}

export interface SensorFilter {
  sensorId?: string;
  sensorType?: SensorReading['sensorType'];
  location?: string;
  startDate?: Date;
  endDate?: Date;
}

export interface SensorMonitorState {
  readings: SensorReading[];
  loading: boolean;
  error: string | null;
  filter: SensorFilter;
}

/**
 * Environment Sensor Monitor Panel Component
 * Main UI component for environmental sensor monitoring
 */

import React from 'react';
import { useSensorMonitor } from './useSensorMonitor';
import type { SensorFilter } from './types';

interface SensorMonitorPanelProps {
  initialFilter?: SensorFilter;
}

export function SensorMonitorPanel({ initialFilter }: SensorMonitorPanelProps) {
  const { readings, loading, error, updateFilter, reload } = useSensorMonitor(initialFilter);

  if (loading) {
    return <div>Loading sensor data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="sensor-monitor-panel">
      <h2>Environment Sensors</h2>
      <div className="sensor-readings">
        {readings.length === 0 ? (
          <p>No sensor readings found</p>
        ) : (
          <ul>
            {readings.map(reading => (
              <li key={reading.id}>
                {reading.sensorId} - {reading.value} {reading.unit} at {new Date(reading.timestamp).toLocaleString()}
              </li>
            ))}
          </ul>
        )}
      </div>
      <button onClick={reload}>Reload</button>
    </div>
  );
}

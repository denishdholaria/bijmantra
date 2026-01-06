/**
 * Live Sensor Chart Component
 * Real-time streaming chart for IoT sensor data
 * Uses ECharts with WebSocket/polling support
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { EChartsWrapper } from './EChartsWrapper';
import type ReactEChartsCore from 'echarts-for-react/lib/core';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Play, Pause, RefreshCw, Download, Settings } from 'lucide-react';

interface SensorReading {
  timestamp: number;
  value: number;
  unit: string;
}

interface SensorConfig {
  id: string;
  name: string;
  type: string;
  unit: string;
  min?: number;
  max?: number;
  warningThreshold?: number;
  criticalThreshold?: number;
  color?: string;
}

interface LiveSensorChartProps {
  sensors: SensorConfig[];
  fetchData?: (sensorId: string) => Promise<SensorReading>;
  pollingInterval?: number;
  maxDataPoints?: number;
  height?: number;
  showControls?: boolean;
  title?: string;
  description?: string;
}

export function LiveSensorChart({
  sensors,
  fetchData,
  pollingInterval = 3000,
  maxDataPoints = 60,
  height = 300,
  showControls = true,
  title = 'Live Sensor Data',
  description = 'Real-time environmental monitoring',
}: LiveSensorChartProps) {
  const [isLive, setIsLive] = useState(true);
  const [selectedSensors, setSelectedSensors] = useState<string[]>(sensors.slice(0, 3).map(s => s.id));
  const [data, setData] = useState<Record<string, SensorReading[]>>({});
  const [latestValues, setLatestValues] = useState<Record<string, SensorReading>>({});
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chartRef = useRef<ReactEChartsCore>(null);

  // Generate placeholder reading when no data available (shows as dash)
  const generatePlaceholderReading = useCallback((sensor: SensorConfig): SensorReading => {
    return {
      timestamp: Date.now(),
      value: NaN, // Will display as '-' in UI
      unit: sensor.unit,
    };
  }, []);

  // Fetch data for all selected sensors
  const updateData = useCallback(async () => {
    if (!fetchData) {
      // No data source provided - show empty state
      return;
    }
    
    const newData = { ...data };
    const newLatest: Record<string, SensorReading> = {};

    for (const sensorId of selectedSensors) {
      const sensor = sensors.find(s => s.id === sensorId);
      if (!sensor) continue;

      let reading: SensorReading;
      try {
        reading = await fetchData(sensorId);
      } catch {
        // On error, use placeholder (will show as '-')
        reading = generatePlaceholderReading(sensor);
      }

      // Initialize array if needed
      if (!newData[sensorId]) {
        newData[sensorId] = [];
      }

      // Only add valid readings to chart
      if (!isNaN(reading.value)) {
        newData[sensorId] = [...newData[sensorId], reading];

        // Trim to max data points
        if (newData[sensorId].length > maxDataPoints) {
          newData[sensorId] = newData[sensorId].slice(-maxDataPoints);
        }
      }

      newLatest[sensorId] = reading;
    }

    setData(newData);
    setLatestValues(newLatest);
  }, [data, selectedSensors, sensors, fetchData, generatePlaceholderReading, maxDataPoints]);

  // Start/stop polling
  useEffect(() => {
    if (isLive) {
      updateData();
      intervalRef.current = setInterval(updateData, pollingInterval);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isLive, pollingInterval, updateData]);

  // Build chart options
  const getChartOptions = () => {
    const series = selectedSensors.map(sensorId => {
      const sensor = sensors.find(s => s.id === sensorId);
      const sensorData = data[sensorId] || [];
      
      return {
        name: sensor?.name || sensorId,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 2,
          color: sensor?.color,
        },
        areaStyle: {
          opacity: 0.1,
          color: sensor?.color,
        },
        data: sensorData.map(d => [d.timestamp, d.value]),
        markLine: sensor?.warningThreshold ? {
          silent: true,
          data: [
            {
              yAxis: sensor.warningThreshold,
              lineStyle: { color: '#f59e0b', type: 'dashed' },
              label: { show: false },
            },
            ...(sensor.criticalThreshold ? [{
              yAxis: sensor.criticalThreshold,
              lineStyle: { color: '#ef4444', type: 'dashed' },
              label: { show: false },
            }] : []),
          ],
        } : undefined,
      };
    });

    return {
      animation: false,
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          if (!params.length) return '';
          const time = new Date(params[0].value[0]).toLocaleTimeString();
          let html = `<div class="font-medium">${time}</div>`;
          params.forEach((p: any) => {
            const sensor = sensors.find(s => s.name === p.seriesName);
            html += `<div class="flex items-center gap-2">
              <span style="background:${p.color}" class="w-2 h-2 rounded-full"></span>
              <span>${p.seriesName}: ${p.value[1]} ${sensor?.unit || ''}</span>
            </div>`;
          });
          return html;
        },
      },
      legend: {
        data: selectedSensors.map(id => sensors.find(s => s.id === id)?.name || id),
        bottom: 0,
      },
      grid: {
        left: 50,
        right: 20,
        top: 20,
        bottom: 40,
      },
      xAxis: {
        type: 'time',
        splitLine: { show: false },
        axisLabel: {
          formatter: (value: number) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { type: 'dashed', opacity: 0.3 } },
      },
      series,
    };
  };

  // Export data as CSV
  const exportData = () => {
    let csv = 'Timestamp,Sensor,Value,Unit\n';
    Object.entries(data).forEach(([sensorId, readings]) => {
      const sensor = sensors.find(s => s.id === sensorId);
      readings.forEach(r => {
        csv += `${new Date(r.timestamp).toISOString()},${sensor?.name || sensorId},${r.value},${r.unit}\n`;
      });
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sensor-data-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Get status badge for a sensor value
  const getStatusBadge = (sensorId: string) => {
    const sensor = sensors.find(s => s.id === sensorId);
    const latest = latestValues[sensorId];
    if (!sensor || !latest) return null;

    if (sensor.criticalThreshold && latest.value >= sensor.criticalThreshold) {
      return <Badge className="bg-red-100 text-red-800">Critical</Badge>;
    }
    if (sensor.warningThreshold && latest.value >= sensor.warningThreshold) {
      return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>;
    }
    return <Badge className="bg-green-100 text-green-800">Normal</Badge>;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {title}
              {isLive && (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-xs text-green-600 font-normal">LIVE</span>
                </span>
              )}
            </CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          {showControls && (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={isLive ? 'default' : 'outline'}
                onClick={() => setIsLive(!isLive)}
              >
                {isLive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button size="sm" variant="outline" onClick={updateData}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={exportData}>
                <Download className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Sensor selector */}
        {showControls && (
          <div className="flex flex-wrap gap-2 mb-4">
            {sensors.map(sensor => (
              <Button
                key={sensor.id}
                size="sm"
                variant={selectedSensors.includes(sensor.id) ? 'default' : 'outline'}
                onClick={() => {
                  if (selectedSensors.includes(sensor.id)) {
                    setSelectedSensors(selectedSensors.filter(id => id !== sensor.id));
                  } else {
                    setSelectedSensors([...selectedSensors, sensor.id]);
                  }
                }}
                style={{ borderColor: sensor.color, color: selectedSensors.includes(sensor.id) ? 'white' : sensor.color }}
              >
                {sensor.name}
              </Button>
            ))}
          </div>
        )}

        {/* Current values */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          {selectedSensors.map(sensorId => {
            const sensor = sensors.find(s => s.id === sensorId);
            const latest = latestValues[sensorId];
            return (
              <div key={sensorId} className="p-3 bg-muted rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-muted-foreground">{sensor?.name}</span>
                  {getStatusBadge(sensorId)}
                </div>
                <p className="text-xl font-bold" style={{ color: sensor?.color }}>
                  {latest?.value ?? '-'} <span className="text-sm font-normal">{sensor?.unit}</span>
                </p>
              </div>
            );
          })}
        </div>

        {/* Chart */}
        <EChartsWrapper
          ref={chartRef}
          option={getChartOptions()}
          style={{ height }}
          notMerge={true}
        />
      </CardContent>
    </Card>
  );
}

export default LiveSensorChart;

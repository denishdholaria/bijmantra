/**
 * LiveSensorTelemetryChart.tsx
 *
 * A high-frequency streaming telemetry chart component using ECharts.
 * Designed for isolated usage in monitoring sensor data streams.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { EChartsOption } from 'echarts';
import { EChartsWrapper } from '@/components/charts/EChartsWrapper';
import type ReactEChartsCore from 'echarts-for-react/lib/core';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Pause, Activity, RefreshCw } from 'lucide-react';

export interface TelemetryPoint {
  timestamp: number;
  value: number;
}

export interface LiveSensorTelemetryChartProps {
  /** Unique identifier for the sensor */
  sensorId: string;
  /** Title for the chart */
  title?: string;
  /** Description for the chart */
  description?: string;
  /** Unit of measurement */
  unit?: string;
  /** Primary color for the series */
  color?: string;
  /** Maximum number of data points to display */
  maxPoints?: number;
  /** Interval in ms for data updates */
  updateInterval?: number;
  /** Initial height of the chart */
  height?: number;
  /** If true, simulates incoming data */
  simulate?: boolean;
}

/**
 * LiveSensorTelemetryChart Component
 *
 * Renders a real-time streaming line chart for sensor telemetry.
 * Isolated component following TailwindCSS v4 and Shadcn patterns.
 */
export function LiveSensorTelemetryChart({
  sensorId,
  title = 'Sensor Telemetry',
  description = 'Real-time telemetry stream',
  unit = '',
  color = '#3b82f6',
  maxPoints = 100,
  updateInterval = 500,
  height = 300,
  simulate = false,
}: LiveSensorTelemetryChartProps) {
  const [data, setData] = useState<TelemetryPoint[]>([]);
  const [isLive, setIsLive] = useState(true);
  const chartRef = useRef<ReactEChartsCore>(null);
  const dataRef = useRef<TelemetryPoint[]>([]);

  // Update logic
  const addDataPoint = useCallback((point: TelemetryPoint) => {
    const newData = [...dataRef.current, point].slice(-maxPoints);
    dataRef.current = newData;
    setData(newData);
  }, [maxPoints]);

  // Simulation effect
  useEffect(() => {
    if (!simulate || !isLive) return;

    const interval = setInterval(() => {
      const newPoint: TelemetryPoint = {
        timestamp: Date.now(),
        value: Math.random() * 100, // Simulated value
      };
      addDataPoint(newPoint);
    }, updateInterval);

    return () => clearInterval(interval);
  }, [simulate, isLive, updateInterval, addDataPoint]);

  // ECharts options
  const getOption = (): EChartsOption => {
    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const p = (Array.isArray(params) ? params[0] : params) as {
            value: [number, number];
            marker: string;
            seriesName: string;
          };
          return `${new Date(p.value[0]).toLocaleTimeString()}<br/>${p.marker} ${p.seriesName}: <b>${p.value[1].toFixed(2)} ${unit}</b>`;
        },
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: '#eee',
        borderWidth: 1,
        textStyle: {
          color: '#333',
        },
      },
      grid: {
        top: 40,
        left: 50,
        right: 20,
        bottom: 40,
      },
      xAxis: {
        type: 'time',
        splitLine: {
          show: false,
        },
        axisLabel: {
          formatter: (value: number) => {
            const date = new Date(value);
            return date.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false
            });
          },
          fontSize: 10,
        },
      },
      yAxis: {
        type: 'value',
        boundaryGap: [0, '100%'],
        splitLine: {
          lineStyle: {
            type: 'dashed',
            opacity: 0.2,
          },
        },
        axisLabel: {
          fontSize: 10,
        },
      },
      series: [
        {
          name: title,
          type: 'line',
          showSymbol: false,
          data: data.map(p => [p.timestamp, p.value]),
          itemStyle: {
            color: color,
          },
          lineStyle: {
            width: 2,
            join: 'round',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: color },
                { offset: 1, color: 'transparent' },
              ],
            },
            opacity: 0.1,
          },
          animation: false,
        },
      ],
    };
  };

  const latestValue = data.length > 0 ? data[data.length - 1].value : null;

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
        <div>
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-500" />
            {title}
            {isLive && (
              <Badge variant="outline" className="ml-2 bg-green-50 text-green-700 border-green-200 flex items-center gap-1 px-1.5 py-0.5">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                LIVE
              </Badge>
            )}
          </CardTitle>
          <CardDescription className="text-sm">{description}</CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsLive(!isLive)}
            className="h-8 w-8 p-0"
          >
            {isLive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            <span className="sr-only">{isLive ? 'Pause' : 'Resume'}</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setData([]);
              dataRef.current = [];
            }}
            className="h-8 w-8 p-0"
          >
            <RefreshCw className="h-4 w-4" />
            <span className="sr-only">Reset</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight">
            {latestValue !== null ? latestValue.toFixed(2) : '--'}
          </span>
          <span className="text-muted-foreground font-medium">{unit}</span>
        </div>

        <div className="rounded-md border bg-card p-2">
          <EChartsWrapper
            ref={chartRef}
            option={getOption()}
            style={{ height }}
            notMerge={true}
          />
        </div>

        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
          <span>Sensor ID: {sensorId}</span>
          <span>Buffer: {data.length} / {maxPoints} points</span>
        </div>
      </CardContent>
    </Card>
  );
}

export default LiveSensorTelemetryChart;

import { useDeferredValue, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useSensorData } from './hooks/useSensorData';
import type { SensorTimeRange } from './types';

interface SensorDataChartProps {
  locationId: string | null;
  locationName?: string;
}

const RANGE_OPTIONS: Array<{ value: SensorTimeRange; label: string }> = [
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
  { value: '90d', label: '90 days' },
  { value: '1y', label: '1 year' },
];

function formatTick(value: string) {
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
}

export function SensorDataChart({ locationId, locationName }: SensorDataChartProps) {
  const [range, setRange] = useState<SensorTimeRange>('30d');
  const chartQuery = useSensorData(locationId, range);
  const chartPoints = useDeferredValue(chartQuery.data?.points ?? []);

  if (!locationId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sensor Data</CardTitle>
          <CardDescription>
            Select a sensor location to render temperature, humidity, and rainfall trends.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle>Sensor Data</CardTitle>
            <CardDescription>
              {locationName ?? 'Selected location'} · Environmental series for the active time range.
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            {RANGE_OPTIONS.map((option) => (
              <Button
                key={option.value}
                variant={range === option.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRange(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {chartQuery.isLoading ? (
          <Skeleton className="h-[320px] w-full" />
        ) : chartQuery.isError ? (
          <Card className="border-destructive/40">
            <CardHeader>
              <CardTitle className="text-lg">Unable to load sensor series</CardTitle>
              <CardDescription>
                {chartQuery.error instanceof Error
                  ? chartQuery.error.message
                  : 'The chart request failed.'}
              </CardDescription>
            </CardHeader>
          </Card>
        ) : chartPoints.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">No chart data available</CardTitle>
              <CardDescription>
                No temperature, humidity, or rainfall readings were returned for this location and time range.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-4">
            <div className="h-[320px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartPoints} margin={{ top: 16, right: 16, left: 8, bottom: 12 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={formatTick}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    label={{ value: 'Date', position: 'insideBottom', offset: -6 }}
                  />
                  <YAxis
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    label={{ value: 'Value', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip labelFormatter={(value) => formatTick(String(value))} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="temperature"
                    name="Temperature"
                    stroke="hsl(var(--chart-1))"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="humidity"
                    name="Humidity"
                    stroke="hsl(var(--chart-2))"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="rainfall"
                    name="Rainfall"
                    stroke="hsl(var(--chart-4))"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <p className="text-sm text-muted-foreground">
              Rendering {chartPoints.length} chart point{chartPoints.length === 1 ? '' : 's'} for the selected range.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

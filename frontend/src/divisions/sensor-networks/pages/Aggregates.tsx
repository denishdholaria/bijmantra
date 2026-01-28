/**
 * Environmental Aggregates Page
 *
 * BrAPI-aligned environmental summaries for G×E analysis.
 * Endpoint: /brapi/v2/extensions/iot/aggregates
 * 
 * This is the PRIMARY BRIDGE between IoT telemetry and BrAPI environments.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { BarChart3, Calendar, Download, Leaf, RefreshCw, Thermometer, Droplets, Sun, Wind, AlertCircle } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface Aggregate {
  environmentDbId: string;
  environmentalParameter: string;
  value: number;
  unit: string;
  period: string;
  startDate: string;
  endDate: string;
  minValue?: number;
  maxValue?: number;
  sampleCount?: number;
}

export function Aggregates() {
  const [environmentId, setEnvironmentId] = useState('env-kharif-2025-field-a');
  const [aggregates, setAggregates] = useState<Aggregate[]>([]);
  const [period, setPeriod] = useState<string>('daily');
  const [parameter, setParameter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAggregates = async () => {
    setError(null);
    setRefreshing(true);
    try {
      const params = new URLSearchParams({
        environmentDbId: environmentId,
        period: period,
      });
      if (parameter) params.append('parameter', parameter);
      
      const res = await fetch(`/brapi/v2/extensions/iot/aggregates?${params}`);
      if (res.ok) {
        const data = await res.json();
        setAggregates(data.result?.data || []);
      } else {
        setError('Failed to load aggregates. Server returned an error.');
      }
    } catch (err) {
      console.error('Failed to fetch aggregates:', err);
      setError('Failed to load aggregates. Please check your connection.');
      setAggregates([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAggregates();
  }, [environmentId, period, parameter]);

  const getParameterIcon = (param: string) => {
    if (param.includes('temperature')) return <Thermometer className="h-4 w-4 text-red-500" />;
    if (param.includes('precipitation') || param.includes('moisture') || param.includes('humidity')) return <Droplets className="h-4 w-4 text-blue-500" />;
    if (param.includes('solar') || param.includes('radiation')) return <Sun className="h-4 w-4 text-yellow-500" />;
    if (param.includes('wind')) return <Wind className="h-4 w-4 text-cyan-500" />;
    if (param.includes('gdd') || param.includes('degree')) return <Leaf className="h-4 w-4 text-green-500" />;
    return <BarChart3 className="h-4 w-4 text-gray-500" />;
  };

  // Group aggregates by parameter for summary cards
  const parameterSummary = aggregates.reduce((acc, agg) => {
    if (!acc[agg.environmentalParameter]) {
      acc[agg.environmentalParameter] = { values: [], unit: agg.unit };
    }
    acc[agg.environmentalParameter].values.push(agg.value);
    return acc;
  }, {} as Record<string, { values: number[]; unit: string }>);

  // Prepare chart data
  const chartData = aggregates
    .filter(a => a.environmentalParameter === 'air_temperature_mean')
    .map(a => ({
      date: a.startDate,
      temperature: Math.round(a.value * 10) / 10,
      gdd: aggregates.find(g => g.startDate === a.startDate && g.environmentalParameter === 'growing_degree_days')?.value || 0,
    }));

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <div className="grid md:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="h-8 w-8" />
            Environmental Aggregates
          </h1>
          <p className="text-muted-foreground mt-1">
            BrAPI-aligned environmental summaries for G×E analysis
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchAggregates} disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={fetchAggregates} disabled={refreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[250px]">
              <label className="text-sm font-medium mb-2 block">Environment ID</label>
              <Input
                value={environmentId}
                onChange={(e) => setEnvironmentId(e.target.value)}
                placeholder="Enter environment ID"
              />
            </div>
            
            <div className="w-[150px]">
              <label className="text-sm font-medium mb-2 block">Period</label>
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hourly">Hourly</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="seasonal">Seasonal</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-[200px]">
              <label className="text-sm font-medium mb-2 block">Parameter</label>
              <Select value={parameter || '__all__'} onValueChange={(v) => setParameter(v === '__all__' ? '' : v)}>
                <SelectTrigger>
                  <SelectValue placeholder="All parameters" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All parameters</SelectItem>
                  <SelectItem value="air_temperature_mean">Temperature Mean</SelectItem>
                  <SelectItem value="growing_degree_days">GDD</SelectItem>
                  <SelectItem value="precipitation_total">Precipitation</SelectItem>
                  <SelectItem value="soil_moisture_mean">Soil Moisture</SelectItem>
                  <SelectItem value="relative_humidity_mean">Humidity</SelectItem>
                  <SelectItem value="solar_radiation_total">Solar Radiation</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-end">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export for G×E
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Object.entries(parameterSummary).slice(0, 6).map(([param, data]) => {
          const avg = data.values.reduce((a, b) => a + b, 0) / data.values.length;
          return (
            <Card key={param}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-2">
                  {getParameterIcon(param)}
                  <span className="text-xs text-muted-foreground capitalize">
                    {param.replace(/_/g, ' ').replace('mean', '').replace('total', '')}
                  </span>
                </div>
                <div className="text-2xl font-bold">
                  {avg.toFixed(1)} <span className="text-sm font-normal text-muted-foreground">{data.unit}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Temperature & GDD Trend</CardTitle>
          <CardDescription>Daily temperature and growing degree days accumulation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="temperature" name="Temperature (°C)" fill="#ef4444" />
                <Bar yAxisId="right" dataKey="gdd" name="GDD (°C·day)" fill="#22c55e" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardHeader>
          <CardTitle>Aggregate Data</CardTitle>
          <CardDescription>
            {aggregates.length} records • Environment: {environmentId}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Parameter</TableHead>
                <TableHead>Value</TableHead>
                <TableHead>Unit</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Range</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {aggregates.slice(0, 20).map((agg, i) => (
                <TableRow key={i}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {getParameterIcon(agg.environmentalParameter)}
                      <span className="capitalize">{agg.environmentalParameter.replace(/_/g, ' ')}</span>
                    </div>
                  </TableCell>
                  <TableCell className="font-bold">{agg.value.toFixed(1)}</TableCell>
                  <TableCell>{agg.unit}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{agg.period}</Badge>
                  </TableCell>
                  <TableCell>{agg.startDate}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {agg.minValue !== undefined && agg.maxValue !== undefined
                      ? `${agg.minValue.toFixed(1)} - ${agg.maxValue.toFixed(1)}`
                      : '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* G×E Integration Info */}
      <Card className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-300">
            <Leaf className="h-5 w-5" />
            G×E Analysis Integration
          </CardTitle>
        </CardHeader>
        <CardContent className="text-green-700 dark:text-green-300">
          <p className="mb-2">
            These environmental aggregates can be used as covariates in Genotype × Environment (G×E) analysis:
          </p>
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li><strong>AMMI Analysis</strong>: Use temperature and rainfall as environmental indices</li>
            <li><strong>GGE Biplot</strong>: Correlate GDD with yield performance</li>
            <li><strong>Finlay-Wilkinson</strong>: Regress genotype performance on environmental mean</li>
            <li><strong>Mega-Environment</strong>: Cluster environments by similar conditions</li>
          </ul>
          <div className="mt-4">
            <Button variant="outline" className="border-green-300 text-green-700 hover:bg-green-100">
              Open G×E Analysis Tool
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Aggregates;

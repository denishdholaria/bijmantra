/**
 * Carbon Monitoring Dashboard
 *
 * Tracks soil and vegetation carbon stocks across locations.
 * Connected to /api/v2/carbon endpoints.
 *
 * Features:
 * - Carbon stock overview metrics
 * - Time series visualization
 * - Location-based carbon tracking
 * - Recent measurements table
 */

import { useState, useEffect } from 'react';
import { lazy } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Leaf, TrendingUp, MapPin, Calendar, RefreshCw,
  AlertCircle, Info, BarChart3, LineChart
} from 'lucide-react';

interface CarbonDashboard {
  total_locations: number;
  total_carbon_stock: number;
  average_carbon_per_location: number;
  soil_carbon_total: number;
  vegetation_carbon_total: number;
  recent_measurements: number;
  sequestration_rate: number | null;
}

interface CarbonStock {
  id: number;
  location_id: number;
  measurement_date: string;
  soil_carbon_stock: number | null;
  vegetation_carbon_stock: number | null;
  total_carbon_stock: number;
  measurement_type: string;
  confidence_level: number;
}

export function CarbonDashboard() {
  const [dashboard, setDashboard] = useState<CarbonDashboard | null>(null);
  const [stocks, setStocks] = useState<CarbonStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch('/api/v2/carbon/dashboard', { headers });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      } else if (res.status === 401) {
        setError('Authentication required');
      } else {
        throw new Error('Failed to fetch dashboard');
      }
    } catch (err) {
      setError('Carbon monitoring service unavailable');
      setDashboard(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchStocks = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch('/api/v2/carbon/stocks?limit=10', { headers });
      if (res.ok) {
        const data = await res.json();
        setStocks(data);
      }
    } catch (err) {
      console.error('Failed to fetch stocks:', err);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchStocks();
  }, []);

  const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('en-US', { maximumFractionDigits: 2 });
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return <Badge className="bg-green-100 text-green-800">High</Badge>;
    if (confidence >= 0.6) return <Badge className="bg-yellow-100 text-yellow-800">Medium</Badge>;
    return <Badge className="bg-red-100 text-red-800">Low</Badge>;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Carbon Monitoring</h1>
          <Button onClick={fetchDashboard} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <div>
                <p className="font-medium text-red-900">{error}</p>
                <p className="text-sm text-red-700 mt-1">
                  Please check your connection and try again.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Carbon Monitoring</h1>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Leaf className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Carbon Data Available
              </h3>
              <p className="text-gray-600 mb-4">
                Start tracking carbon stocks by adding measurements for your locations.
              </p>
              <Button>
                <MapPin className="h-4 w-4 mr-2" />
                Add Carbon Stock
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Carbon Monitoring</h1>
          <p className="text-gray-600 mt-1">
            Track soil and vegetation carbon stocks across your locations
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchDashboard} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <MapPin className="h-4 w-4 mr-2" />
            Add Stock
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Locations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">
                  {dashboard.total_locations}
                </div>
                <p className="text-xs text-gray-500 mt-1">Monitored sites</p>
              </div>
              <MapPin className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Carbon Stock
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">
                  {formatNumber(dashboard.total_carbon_stock)}
                </div>
                <p className="text-xs text-gray-500 mt-1">tonnes C</p>
              </div>
              <Leaf className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Average per Location
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">
                  {formatNumber(dashboard.average_carbon_per_location)}
                </div>
                <p className="text-xs text-gray-500 mt-1">tonnes C/location</p>
              </div>
              <BarChart3 className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Sequestration Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">
                  {dashboard.sequestration_rate 
                    ? formatNumber(dashboard.sequestration_rate)
                    : 'N/A'}
                </div>
                <p className="text-xs text-gray-500 mt-1">t C/ha/year</p>
              </div>
              <TrendingUp className="h-8 w-8 text-emerald-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Carbon Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Carbon Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Soil Carbon</span>
                  <span className="text-sm font-bold">
                    {formatNumber(dashboard.soil_carbon_total)} t C
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-amber-600 h-3 rounded-full transition-all"
                    style={{
                      width: `${(dashboard.soil_carbon_total / dashboard.total_carbon_stock) * 100}%`
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {((dashboard.soil_carbon_total / dashboard.total_carbon_stock) * 100).toFixed(1)}% of total
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Vegetation Carbon</span>
                  <span className="text-sm font-bold">
                    {formatNumber(dashboard.vegetation_carbon_total)} t C
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-green-600 h-3 rounded-full transition-all"
                    style={{
                      width: `${(dashboard.vegetation_carbon_total / dashboard.total_carbon_stock) * 100}%`
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {((dashboard.vegetation_carbon_total / dashboard.total_carbon_stock) * 100).toFixed(1)}% of total
                </p>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium mb-1">Carbon Stock Formula</p>
                  <p className="text-blue-800">
                    Stock (t/ha) = SOC (%) × BD (g/cm³) × Depth (cm) × 100
                  </p>
                  <p className="text-xs text-blue-700 mt-2">
                    Typical sequestration rates: 0.2-1.0 t C/ha/year
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-gray-600" />
                  <div>
                    <p className="text-sm font-medium">Recent Measurements</p>
                    <p className="text-xs text-gray-500">Last 30 days</p>
                  </div>
                </div>
                <span className="text-lg font-bold">{dashboard.recent_measurements}</span>
              </div>

              {dashboard.sequestration_rate && dashboard.sequestration_rate > 0 && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <div className="flex items-start gap-2">
                    <TrendingUp className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-green-900">
                        Positive Sequestration
                      </p>
                      <p className="text-xs text-green-700 mt-1">
                        Carbon stocks are increasing at {formatNumber(dashboard.sequestration_rate)} t C/ha/year
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="pt-3 border-t">
                <h4 className="text-sm font-medium mb-3">Quick Actions</h4>
                <div className="space-y-2">
                  <Link to="/earth-systems/carbon/time-series">
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <LineChart className="h-4 w-4 mr-2" />
                      View Time Series
                    </Button>
                  </Link>
                  <Link to="/earth-systems/carbon/measurements">
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Calendar className="h-4 w-4 mr-2" />
                      Add Measurement
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Carbon Stocks Table */}
      {stocks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Carbon Stocks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                      Date
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                      Location
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                      Soil Carbon
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                      Vegetation
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                      Total
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                      Type
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                      Confidence
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {stocks.map((stock) => (
                    <tr key={stock.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm">
                        {new Date(stock.measurement_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-sm">
                        Location {stock.location_id}
                      </td>
                      <td className="py-3 px-4 text-sm text-right">
                        {formatNumber(stock.soil_carbon_stock)} t/ha
                      </td>
                      <td className="py-3 px-4 text-sm text-right">
                        {formatNumber(stock.vegetation_carbon_stock)} t/ha
                      </td>
                      <td className="py-3 px-4 text-sm text-right font-medium">
                        {formatNumber(stock.total_carbon_stock)} t/ha
                      </td>
                      <td className="py-3 px-4 text-sm">
                        <Badge variant="outline">{stock.measurement_type}</Badge>
                      </td>
                      <td className="py-3 px-4 text-sm">
                        {getConfidenceBadge(stock.confidence_level)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

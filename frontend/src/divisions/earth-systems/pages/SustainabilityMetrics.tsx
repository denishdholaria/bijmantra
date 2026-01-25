/**
 * Sustainability Metrics Dashboard
 *
 * Tracks impact metrics, SDG alignment, and variety releases.
 * Connected to /api/v2/impact and /api/v2/emissions endpoints.
 *
 * Features:
 * - Impact metrics overview (hectares, farmers, yield)
 * - SDG indicators alignment
 * - Variety releases timeline
 * - Emissions reduction tracking
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp, Users, Sprout, Leaf, Target, Award,
  RefreshCw, AlertCircle, Info, BarChart3, Globe
} from 'lucide-react';

interface ImpactDashboard {
  total_hectares: number;
  total_farmers: number;
  average_yield_improvement: number;
  total_carbon_sequestered: number;
  total_emissions_reduced: number;
  variety_releases_count: number;
  policy_adoptions_count: number;
}

interface SDGIndicator {
  id: number;
  sdg_goal: number;
  indicator_code: string;
  indicator_name: string;
  target_value: number | null;
  current_value: number;
  unit: string;
  progress_percentage: number;
}

interface VarietyRelease {
  id: number;
  variety_name: string;
  release_date: string;
  hectares_adopted: number | null;
  farmers_reached: number | null;
  yield_improvement_percent: number | null;
}

interface EmissionsDashboard {
  total_sources: number;
  total_emissions: number;
  fertilizer_emissions: number;
  fuel_emissions: number;
  irrigation_emissions: number;
}

export function SustainabilityMetrics() {
  const [impact, setImpact] = useState<ImpactDashboard | null>(null);
  const [sdg, setSdg] = useState<SDGIndicator[]>([]);
  const [releases, setReleases] = useState<VarietyRelease[]>([]);
  const [emissions, setEmissions] = useState<EmissionsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
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

      // Fetch impact dashboard
      const impactRes = await fetch('/api/v2/impact/dashboard', { headers });
      if (impactRes.ok) {
        const impactData = await impactRes.json();
        setImpact(impactData);
      } else if (impactRes.status === 401) {
        setError('Authentication required');
        return;
      }

      // Fetch SDG indicators
      const sdgRes = await fetch('/api/v2/impact/sdg', { headers });
      if (sdgRes.ok) {
        const sdgData = await sdgRes.json();
        setSdg(sdgData);
      }

      // Fetch variety releases
      const releasesRes = await fetch('/api/v2/impact/releases?limit=5', { headers });
      if (releasesRes.ok) {
        const releasesData = await releasesRes.json();
        setReleases(releasesData);
      }

      // Fetch emissions dashboard
      const emissionsRes = await fetch('/api/v2/emissions/dashboard', { headers });
      if (emissionsRes.ok) {
        const emissionsData = await emissionsRes.json();
        setEmissions(emissionsData);
      }
    } catch (err) {
      setError('Sustainability metrics service unavailable');
      setImpact(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('en-US', { maximumFractionDigits: 2 });
  };

  const getSDGColor = (goal: number) => {
    const colors: Record<number, string> = {
      2: 'bg-yellow-500',
      13: 'bg-green-600',
      15: 'bg-emerald-500',
      17: 'bg-blue-600',
    };
    return colors[goal] || 'bg-gray-500';
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'bg-green-600';
    if (progress >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
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
          <h1 className="text-3xl font-bold">Sustainability Metrics</h1>
          <Button onClick={fetchData} variant="outline" size="sm">
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

  if (!impact) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Sustainability Metrics</h1>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Target className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Impact Data Available
              </h3>
              <p className="text-gray-600 mb-4">
                Start tracking sustainability metrics by recording variety releases and impact data.
              </p>
              <Button>
                <Award className="h-4 w-4 mr-2" />
                Add Variety Release
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
          <h1 className="text-3xl font-bold">Sustainability Metrics</h1>
          <p className="text-gray-600 mt-1">
            Track impact, SDG alignment, and emissions reduction
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <Award className="h-4 w-4 mr-2" />
            Add Release
          </Button>
        </div>
      </div>

      {/* Impact Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Hectares Impacted
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">
                  {formatNumber(impact.total_hectares)}
                </div>
                <p className="text-xs text-gray-500 mt-1">Total area</p>
              </div>
              <Sprout className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Farmers Reached
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">
                  {formatNumber(impact.total_farmers)}
                </div>
                <p className="text-xs text-gray-500 mt-1">Beneficiaries</p>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Yield Improvement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">
                  {formatNumber(impact.average_yield_improvement)}%
                </div>
                <p className="text-xs text-gray-500 mt-1">Average gain</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Carbon Sequestered
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold">
                  {formatNumber(impact.total_carbon_sequestered)}
                </div>
                <p className="text-xs text-gray-500 mt-1">tonnes C</p>
              </div>
              <Leaf className="h-8 w-8 text-emerald-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SDG Indicators and Emissions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SDG Indicators */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              UN SDG Alignment
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sdg.length > 0 ? (
              <div className="space-y-4">
                {sdg.map((indicator) => (
                  <div key={indicator.id}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded ${getSDGColor(indicator.sdg_goal)} flex items-center justify-center text-white text-xs font-bold`}>
                          {indicator.sdg_goal}
                        </div>
                        <div>
                          <p className="text-sm font-medium">{indicator.indicator_name}</p>
                          <p className="text-xs text-gray-500">{indicator.indicator_code}</p>
                        </div>
                      </div>
                      <span className="text-sm font-bold">
                        {formatNumber(indicator.current_value)} {indicator.unit}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${getProgressColor(indicator.progress_percentage)}`}
                        style={{ width: `${Math.min(indicator.progress_percentage, 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {indicator.progress_percentage.toFixed(1)}% of target
                      {indicator.target_value && ` (${formatNumber(indicator.target_value)} ${indicator.unit})`}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Globe className="h-8 w-8 mx-auto text-gray-400 mb-2" />
                <p className="text-sm text-gray-600">No SDG indicators tracked yet</p>
              </div>
            )}

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium mb-1">UN SDG Framework</p>
                  <p className="text-blue-800 text-xs">
                    SDG 2: Zero Hunger | SDG 13: Climate Action | SDG 15: Life on Land | SDG 17: Partnerships
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Emissions Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Emissions Tracking</CardTitle>
          </CardHeader>
          <CardContent>
            {emissions ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">Total Emissions Reduced</p>
                    <p className="text-xs text-gray-500">All sources</p>
                  </div>
                  <span className="text-lg font-bold text-green-600">
                    {formatNumber(impact.total_emissions_reduced)} kg CO₂e
                  </span>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Fertilizer Emissions</span>
                    <span className="text-sm font-bold">
                      {formatNumber(emissions.fertilizer_emissions)} kg CO₂e
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-orange-500 h-3 rounded-full transition-all"
                      style={{
                        width: `${(emissions.fertilizer_emissions / emissions.total_emissions) * 100}%`
                      }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {((emissions.fertilizer_emissions / emissions.total_emissions) * 100).toFixed(1)}% of total
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Fuel Emissions</span>
                    <span className="text-sm font-bold">
                      {formatNumber(emissions.fuel_emissions)} kg CO₂e
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-red-500 h-3 rounded-full transition-all"
                      style={{
                        width: `${(emissions.fuel_emissions / emissions.total_emissions) * 100}%`
                      }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {((emissions.fuel_emissions / emissions.total_emissions) * 100).toFixed(1)}% of total
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Irrigation Emissions</span>
                    <span className="text-sm font-bold">
                      {formatNumber(emissions.irrigation_emissions)} kg CO₂e
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-blue-500 h-3 rounded-full transition-all"
                      style={{
                        width: `${(emissions.irrigation_emissions / emissions.total_emissions) * 100}%`
                      }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {((emissions.irrigation_emissions / emissions.total_emissions) * 100).toFixed(1)}% of total
                  </p>
                </div>

                <div className="pt-3 border-t">
                  <p className="text-xs text-gray-600">
                    Total emission sources tracked: <span className="font-medium">{emissions.total_sources}</span>
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <BarChart3 className="h-8 w-8 mx-auto text-gray-400 mb-2" />
                <p className="text-sm text-gray-600">No emissions data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Variety Releases */}
      {releases.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Variety Releases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                      Variety
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                      Release Date
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                      Hectares Adopted
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                      Farmers Reached
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                      Yield Improvement
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {releases.map((release) => (
                    <tr key={release.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-medium">
                        {release.variety_name}
                      </td>
                      <td className="py-3 px-4 text-sm">
                        {new Date(release.release_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-sm text-right">
                        {formatNumber(release.hectares_adopted)} ha
                      </td>
                      <td className="py-3 px-4 text-sm text-right">
                        {formatNumber(release.farmers_reached)}
                      </td>
                      <td className="py-3 px-4 text-sm text-right">
                        {release.yield_improvement_percent ? (
                          <Badge className="bg-green-100 text-green-800">
                            +{formatNumber(release.yield_improvement_percent)}%
                          </Badge>
                        ) : (
                          <span className="text-gray-400">N/A</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-green-600 rounded-lg">
                <Award className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Variety Releases</p>
                <p className="text-2xl font-bold text-gray-900">
                  {impact.variety_releases_count}
                </p>
                <p className="text-xs text-gray-600 mt-2">
                  New varieties released to farmers
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-600 rounded-lg">
                <Target className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Policy Adoptions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {impact.policy_adoptions_count}
                </p>
                <p className="text-xs text-gray-600 mt-2">
                  Policies influenced by research
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

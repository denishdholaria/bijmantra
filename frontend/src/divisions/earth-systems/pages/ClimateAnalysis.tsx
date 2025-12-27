/**
 * Climate Analysis Page
 *
 * Long-term climate trends and historical data analysis.
 * Connected to /api/v2/climate/analysis API.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, TrendingUp, TrendingDown, Minus, Thermometer, CloudRain, Calendar } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

export function ClimateAnalysis() {
  const [locationId] = useState('LOC-001');
  const [years, setYears] = useState('30');

  const { data: climateData, isLoading, error, refetch } = useQuery({
    queryKey: ['climate-analysis', locationId, years],
    queryFn: () => apiClient.getClimateAnalysis(locationId, 'Research Station', parseInt(years)),
  });

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'decreasing': return <TrendingDown className="h-4 w-4 text-blue-500" />;
      default: return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getChangeColor = (change: number, name: string) => {
    // For some metrics, increase is bad (temperature, heat stress)
    // For others, decrease is bad (rainfall)
    const badIfIncreasing = ['Average Temperature', 'Heat Stress Days', 'Heavy Rain Events'];
    const badIfDecreasing = ['Annual Rainfall', 'Frost-Free Days'];
    
    if (badIfIncreasing.includes(name)) {
      return change > 0 ? 'text-red-500' : change < 0 ? 'text-green-500' : 'text-gray-500';
    }
    if (badIfDecreasing.includes(name)) {
      return change < 0 ? 'text-orange-500' : change > 0 ? 'text-green-500' : 'text-gray-500';
    }
    return change > 0 ? 'text-green-500' : change < 0 ? 'text-orange-500' : 'text-gray-500';
  };

  const getIndicatorIcon = (name: string) => {
    if (name.includes('Temperature') || name.includes('Heat')) return '🌡️';
    if (name.includes('Rainfall') || name.includes('Rain')) return '🌧️';
    if (name.includes('Growing') || name.includes('Frost')) return '🌱';
    return '📊';
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Climate Analysis</h1>
          <p className="text-gray-600 mt-1">Long-term climate trends and historical patterns</p>
        </div>
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load climate data. Please try again.
            <Button variant="outline" size="sm" className="ml-4" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" /> Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Climate Analysis</h1>
          <p className="text-gray-600 mt-1">Long-term climate trends and historical patterns</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={years} onValueChange={setYears}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10 Years</SelectItem>
              <SelectItem value="20">20 Years</SelectItem>
              <SelectItem value="30">30 Years</SelectItem>
              <SelectItem value="50">50 Years</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Key Climate Indicators */}
      {isLoading ? (
        <div className="grid md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : climateData?.indicators && (
        <>
          {/* Primary Indicators */}
          <div className="grid md:grid-cols-3 gap-4">
            {climateData.indicators.slice(0, 3).map((indicator) => (
              <Card key={indicator.name}>
                <CardContent className="p-6 text-center">
                  <div className="text-4xl mb-2">{getIndicatorIcon(indicator.name)}</div>
                  <div className="text-2xl font-bold">
                    {indicator.current_value}{indicator.unit}
                  </div>
                  <div className="text-sm text-gray-500">{indicator.name}</div>
                  <div className={`text-sm mt-2 flex items-center justify-center gap-1 ${getChangeColor(indicator.change, indicator.name)}`}>
                    {getTrendIcon(indicator.trend)}
                    {indicator.change > 0 ? '+' : ''}{indicator.change}{indicator.unit} vs {years}-yr avg
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Secondary Indicators */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>📈</span> Climate Indicators ({years}-Year Comparison)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {climateData.indicators.slice(3).map((indicator) => (
                  <div key={indicator.name} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{indicator.name}</span>
                      {getTrendIcon(indicator.trend)}
                    </div>
                    <div className="mt-2">
                      <span className="text-xl font-bold">{indicator.current_value}</span>
                      <span className="text-sm text-gray-500 ml-1">{indicator.unit}</span>
                    </div>
                    <div className="flex items-center justify-between mt-2 text-sm">
                      <span className="text-gray-500">Historical: {indicator.historical_avg}{indicator.unit}</span>
                      <Badge variant={indicator.change > 0 ? 'destructive' : 'secondary'} className="text-xs">
                        {indicator.change > 0 ? '+' : ''}{indicator.change_percent.toFixed(1)}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Climate Trends Visualization Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" /> Climate Trends ({years} Years)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gradient-to-br from-blue-50 to-green-50 rounded-lg border-2 border-dashed border-gray-200">
            <div className="text-center">
              <div className="text-4xl mb-2">📊</div>
              <p className="text-gray-500">Climate trend visualization</p>
              <p className="text-sm text-gray-400 mt-1">Temperature, rainfall, and growing season trends</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Adaptation Recommendations */}
      {climateData?.recommendations && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>🎯</span> Adaptation Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {climateData.recommendations.map((rec, index) => (
                <div key={index} className={`flex items-start gap-3 p-4 rounded-lg ${
                  rec.priority === 'high' ? 'bg-red-50 border border-red-200' :
                  rec.priority === 'medium' ? 'bg-yellow-50 border border-yellow-200' :
                  'bg-blue-50 border border-blue-200'
                }`}>
                  <span className="text-2xl">{rec.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{rec.title}</span>
                      <Badge variant={rec.priority === 'high' ? 'destructive' : 'secondary'} className="text-xs">
                        {rec.priority}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Source Info */}
      {climateData && (
        <div className="text-xs text-gray-400 text-center">
          Analysis generated: {new Date(climateData.generated_at).toLocaleString()} · 
          Location: {climateData.location_name} · 
          Period: {climateData.analysis_period}
        </div>
      )}
    </div>
  );
}

export default ClimateAnalysis;

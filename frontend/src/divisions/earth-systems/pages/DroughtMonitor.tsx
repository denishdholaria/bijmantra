/**
 * Drought Monitor Page
 *
 * Monitor drought conditions and water stress indicators.
 * Connected to /api/v2/climate/drought API.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, AlertTriangle, Droplets, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

const DROUGHT_SCALE = [
  { status: 'None', description: 'No Drought', color: 'bg-green-200', textColor: 'text-green-800' },
  { status: 'D0', description: 'Abnormally Dry', color: 'bg-yellow-200', textColor: 'text-yellow-800' },
  { status: 'D1', description: 'Moderate Drought', color: 'bg-orange-300', textColor: 'text-orange-800' },
  { status: 'D2', description: 'Severe Drought', color: 'bg-orange-500', textColor: 'text-white' },
  { status: 'D3', description: 'Extreme Drought', color: 'bg-red-500', textColor: 'text-white' },
  { status: 'D4', description: 'Exceptional Drought', color: 'bg-red-800', textColor: 'text-white' },
];

export function DroughtMonitor() {
  const [locationId] = useState('LOC-001');

  const { data: droughtData, isLoading, error, refetch } = useQuery({
    queryKey: ['drought-monitor', locationId],
    queryFn: () => apiClient.getDroughtMonitor(locationId, 'Research Station'),
    refetchInterval: 60000, // Refresh every minute
  });

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return <TrendingUp className="h-3 w-3" />;
      case 'declining': return <TrendingDown className="h-3 w-3" />;
      default: return <Minus className="h-3 w-3" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Good': return 'bg-green-100 text-green-700';
      case 'Moderate': return 'bg-yellow-100 text-yellow-700';
      case 'High':
      case 'Watch': return 'bg-orange-100 text-orange-700';
      case 'Warning': return 'bg-red-100 text-red-700';
      case 'Critical': return 'bg-red-200 text-red-800';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getRegionStyle = (status: string) => {
    const scale = DROUGHT_SCALE.find(s => s.status === status) || DROUGHT_SCALE[0];
    return `${scale.color} ${scale.textColor}`;
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Drought Monitor</h1>
          <p className="text-gray-600 mt-1">Monitor drought conditions and water stress</p>
        </div>
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load drought data. Please try again.
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
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Drought Monitor</h1>
          <p className="text-gray-600 mt-1">Monitor drought conditions and water stress</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Alert Banner */}
      {isLoading ? (
        <Skeleton className="h-24 w-full" />
      ) : droughtData?.alert_active && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <AlertTriangle className="h-12 w-12 text-orange-500" />
              <div>
                <div className="text-xl font-bold text-orange-800">Drought Watch Active</div>
                <p className="text-orange-700">{droughtData.alert_message}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Indicators Grid */}
      {isLoading ? (
        <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <Skeleton className="h-16 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : droughtData?.indicators && (
        <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-4">
          {droughtData.indicators.map((ind) => (
            <Card key={ind.name}>
              <CardContent className="p-4">
                <div className="text-sm text-gray-500 truncate" title={ind.name}>{ind.name}</div>
                <div className="text-2xl font-bold mt-1">
                  {ind.value}
                  {ind.unit && <span className="text-sm font-normal text-gray-500 ml-1">{ind.unit}</span>}
                </div>
                <div className="flex items-center justify-between mt-2">
                  <Badge className={`text-xs ${getStatusColor(ind.status)}`}>
                    {ind.status}
                  </Badge>
                  <span className="text-xs text-gray-500 flex items-center gap-1">
                    {getTrendIcon(ind.trend)} {ind.trend}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Regional Status */}
      {isLoading ? (
        <Card>
          <CardHeader><CardTitle>🗺️ Regional Drought Status</CardTitle></CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      ) : droughtData?.regions && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>🗺️</span> Regional Drought Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {droughtData.regions.map((region) => (
                <div key={region.name} className={`p-4 rounded-lg ${getRegionStyle(region.status)}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{region.name}</span>
                    <span className="font-bold">{region.status}</span>
                  </div>
                  <p className="text-sm mt-1 opacity-80">{region.description}</p>
                  <div className="flex justify-between mt-2 text-xs opacity-70">
                    <span>Soil Moisture: {(region.soil_moisture * 100).toFixed(0)}%</span>
                    <span>{region.days_since_rain} days since rain</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Drought Scale Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Droplets className="h-5 w-5" /> Drought Intensity Scale
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {DROUGHT_SCALE.map((level) => (
              <div key={level.status} className={`flex-1 min-w-[100px] p-2 ${level.color} ${level.textColor} rounded text-center text-sm`}>
                <div className="font-bold">{level.status}</div>
                <div className="text-xs opacity-80">{level.description}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      {droughtData?.recommendations && droughtData.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>💧</span> Water Management Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {droughtData.recommendations.map((rec, index) => {
                const priorityColors = {
                  high: 'border-red-300 bg-red-50',
                  medium: 'border-yellow-300 bg-yellow-50',
                  low: 'border-blue-300 bg-blue-50'
                };
                const priorityIcons = { high: '🔴', medium: '🟡', low: '🔵' };
                const priority = rec.priority as keyof typeof priorityColors;
                
                return (
                  <div key={index} className={`p-4 border rounded-lg ${priorityColors[priority] || priorityColors.low}`}>
                    <div className="flex items-start gap-3">
                      <span className="text-lg">{priorityIcons[priority] || '🔵'}</span>
                      <div className="flex-1">
                        <div className="font-medium">{rec.action}</div>
                        <p className="text-sm text-gray-600 mt-1">{rec.impact}</p>
                      </div>
                      <Badge variant="outline" className="text-xs capitalize">{rec.priority}</Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Source Info */}
      {droughtData && (
        <div className="text-xs text-gray-400 text-center">
          Last updated: {new Date(droughtData.generated_at).toLocaleString()} · 
          Auto-refresh: 1 minute
        </div>
      )}
    </div>
  );
}

export default DroughtMonitor;

/**
 * Growing Degree Days Page
 *
 * Track accumulated heat units for crop development.
 * Connected to /api/v2/weather/gdd and /api/v2/crop-calendar APIs.
 */

import { useState, useTransition } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RefreshCw, Thermometer, Calendar, TrendingUp, Leaf } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { ApiKeyNotice } from '@/components/ApiKeyNotice';

interface CropConfig {
  name: string;
  baseTemp: number;
  targetGDD: number;
  stages: { name: string; gdd: number }[];
}

const CROP_CONFIGS: Record<string, CropConfig> = {
  wheat: {
    name: 'Wheat',
    baseTemp: 0,
    targetGDD: 1500,
    stages: [
      { name: 'Emergence', gdd: 100 },
      { name: 'Tillering', gdd: 400 },
      { name: 'Stem Extension', gdd: 700 },
      { name: 'Heading', gdd: 1000 },
      { name: 'Grain Fill', gdd: 1250 },
      { name: 'Maturity', gdd: 1500 },
    ],
  },
  maize: {
    name: 'Maize',
    baseTemp: 10,
    targetGDD: 1400,
    stages: [
      { name: 'Emergence', gdd: 100 },
      { name: 'V6', gdd: 350 },
      { name: 'V12', gdd: 600 },
      { name: 'Tasseling', gdd: 800 },
      { name: 'Silking', gdd: 900 },
      { name: 'Maturity', gdd: 1400 },
    ],
  },
  rice: {
    name: 'Rice',
    baseTemp: 10,
    targetGDD: 1200,
    stages: [
      { name: 'Emergence', gdd: 80 },
      { name: 'Tillering', gdd: 300 },
      { name: 'Panicle Init', gdd: 600 },
      { name: 'Heading', gdd: 900 },
      { name: 'Grain Fill', gdd: 1050 },
      { name: 'Maturity', gdd: 1200 },
    ],
  },
  soybean: {
    name: 'Soybean',
    baseTemp: 10,
    targetGDD: 1300,
    stages: [
      { name: 'Emergence', gdd: 90 },
      { name: 'V3', gdd: 250 },
      { name: 'Flowering', gdd: 500 },
      { name: 'Pod Set', gdd: 750 },
      { name: 'Pod Fill', gdd: 1000 },
      { name: 'Maturity', gdd: 1300 },
    ],
  },
};

export function GrowingDegrees() {
  const [selectedCrop, setSelectedCrop] = useState('wheat');
  const [locationId] = useState('LOC-001'); // Default location
  const [isPending, startTransition] = useTransition();

  const cropConfig = CROP_CONFIGS[selectedCrop];

  // Handle crop change with transition to prevent React DOM errors
  const handleCropChange = (value: string) => {
    startTransition(() => {
      setSelectedCrop(value);
    });
  };

  // Fetch GDD data from weather API
  const { data: gddData, isLoading, error, refetch } = useQuery({
    queryKey: ['gdd', locationId, selectedCrop],
    queryFn: () => apiClient.getWeatherGDD(locationId, 'Research Station', selectedCrop, 30),
  });

  // Calculate current stage based on cumulative GDD
  const getCurrentStage = (cumulativeGDD: number) => {
    const stages = cropConfig.stages;
    for (let i = stages.length - 1; i >= 0; i--) {
      if (cumulativeGDD >= stages[i].gdd) {
        return stages[i].name;
      }
    }
    return 'Pre-emergence';
  };

  // Calculate progress percentage
  const getProgress = (cumulativeGDD: number) => {
    return Math.min(100, Math.round((cumulativeGDD / cropConfig.targetGDD) * 100));
  };

  // Get the latest cumulative GDD
  const latestGDD = gddData?.gdd_data?.[gddData.gdd_data.length - 1]?.gdd_cumulative ?? 0;
  const weeklyGDD = gddData?.gdd_data?.slice(-7).reduce((sum, d) => sum + d.gdd_daily, 0) ?? 0;
  const currentStage = getCurrentStage(latestGDD);
  const progress = getProgress(latestGDD);

  // Calculate days to next stage
  const getNextStage = () => {
    const stages = cropConfig.stages;
    for (const stage of stages) {
      if (latestGDD < stage.gdd) {
        const gddRemaining = stage.gdd - latestGDD;
        const avgDailyGDD = weeklyGDD / 7 || 5; // Fallback to 5 GDD/day
        const daysRemaining = Math.ceil(gddRemaining / avgDailyGDD);
        return { name: stage.name, gddRemaining, daysRemaining };
      }
    }
    return null;
  };

  const nextStage = getNextStage();

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Growing Degree Days</h1>
          <p className="text-gray-600 mt-1">Track accumulated heat units for crop development</p>
        </div>
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load GDD data. Please try again.
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
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Growing Degree Days</h1>
          <p className="text-gray-600 mt-1">Track accumulated heat units for crop development</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedCrop} onValueChange={handleCropChange}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Select crop" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(CROP_CONFIGS).map(([key, config]) => (
                <SelectItem key={key} value={key}>{config.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={() => refetch()} disabled={isLoading || isPending}>
            <RefreshCw className={`h-4 w-4 ${isLoading || isPending ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* API Key Notice */}
      <ApiKeyNotice serviceId="openweathermap" variant="inline" />

      {/* Current Season Summary */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-orange-50 to-yellow-50">
          <CardContent className="p-6 text-center">
            {isLoading ? (
              <Skeleton className="h-12 w-24 mx-auto" />
            ) : (
              <>
                <Thermometer className="h-8 w-8 mx-auto text-orange-500 mb-2" />
                <div className="text-4xl font-bold text-orange-600">{Math.round(latestGDD)}</div>
                <div className="text-sm text-gray-600 mt-1">Season GDD (Base {cropConfig.baseTemp}°C)</div>
              </>
            )}
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50">
          <CardContent className="p-6 text-center">
            {isLoading ? (
              <Skeleton className="h-12 w-24 mx-auto" />
            ) : (
              <>
                <TrendingUp className="h-8 w-8 mx-auto text-green-500 mb-2" />
                <div className="text-4xl font-bold text-green-600">+{Math.round(weeklyGDD)}</div>
                <div className="text-sm text-gray-600 mt-1">GDD This Week</div>
              </>
            )}
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-50 to-cyan-50">
          <CardContent className="p-6 text-center">
            {isLoading ? (
              <Skeleton className="h-12 w-24 mx-auto" />
            ) : (
              <>
                <Leaf className="h-8 w-8 mx-auto text-blue-500 mb-2" />
                <div className="text-4xl font-bold text-blue-600">{progress}%</div>
                <div className="text-sm text-gray-600 mt-1">Progress to Maturity</div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Crop Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🌾</span> {cropConfig.name} Development Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Progress bar with stages */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Current Stage: <Badge variant="secondary">{currentStage}</Badge></span>
                  <span className="text-sm text-gray-500">
                    {Math.round(latestGDD)} / {cropConfig.targetGDD} GDD
                  </span>
                </div>
                <div className="relative h-6 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                  {/* Stage markers */}
                  {cropConfig.stages.map((stage) => (
                    <div
                      key={stage.name}
                      className="absolute top-0 h-full w-0.5 bg-gray-400"
                      style={{ left: `${(stage.gdd / cropConfig.targetGDD) * 100}%` }}
                      title={`${stage.name}: ${stage.gdd} GDD`}
                    />
                  ))}
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Planting</span>
                  <span>Maturity</span>
                </div>
              </div>

              {/* Stage timeline */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                {cropConfig.stages.map((stage) => {
                  const isComplete = latestGDD >= stage.gdd;
                  const isCurrent = currentStage === stage.name;
                  return (
                    <div
                      key={stage.name}
                      className={`p-3 rounded-lg text-center ${
                        isComplete ? 'bg-green-100 border-green-300' :
                        isCurrent ? 'bg-yellow-100 border-yellow-300' :
                        'bg-gray-50 border-gray-200'
                      } border`}
                    >
                      <div className={`text-sm font-medium ${isComplete ? 'text-green-700' : isCurrent ? 'text-yellow-700' : 'text-gray-500'}`}>
                        {stage.name}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{stage.gdd} GDD</div>
                      {isComplete && <span className="text-green-500">✓</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Phenology Predictions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" /> Phenology Predictions
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid md:grid-cols-2 gap-4">
              {[1, 2].map((i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : nextStage ? (
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50">
                <div className="font-medium text-gray-700">Next Stage</div>
                <div className="text-xl font-bold text-blue-600 mt-1">{nextStage.name}</div>
                <div className="flex justify-between mt-3 text-sm text-gray-600">
                  <span>📅 ~{nextStage.daysRemaining} days</span>
                  <span>{nextStage.gddRemaining} GDD remaining</span>
                </div>
              </div>
              <div className="p-4 border rounded-lg bg-gradient-to-br from-green-50 to-emerald-50">
                <div className="font-medium text-gray-700">Estimated Maturity</div>
                <div className="text-xl font-bold text-green-600 mt-1">
                  {Math.ceil((cropConfig.targetGDD - latestGDD) / (weeklyGDD / 7 || 5))} days
                </div>
                <div className="flex justify-between mt-3 text-sm text-gray-600">
                  <span>Target: {cropConfig.targetGDD} GDD</span>
                  <span>{cropConfig.targetGDD - Math.round(latestGDD)} GDD remaining</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 border rounded-lg bg-green-50 text-center">
              <span className="text-2xl">🎉</span>
              <div className="text-lg font-bold text-green-700 mt-2">Crop has reached maturity!</div>
              <p className="text-sm text-gray-600 mt-1">All growth stages complete</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Daily GDD Data */}
      {gddData?.gdd_data && gddData.gdd_data.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>📊 Recent GDD Accumulation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-3">Date</th>
                    <th className="text-right py-2 px-3">Daily GDD</th>
                    <th className="text-right py-2 px-3">Cumulative</th>
                  </tr>
                </thead>
                <tbody>
                  {gddData.gdd_data.slice(-10).map((day) => (
                    <tr key={day.date} className="border-b hover:bg-gray-50">
                      <td className="py-2 px-3">{new Date(day.date).toLocaleDateString()}</td>
                      <td className="text-right py-2 px-3 font-medium text-green-600">+{day.gdd_daily.toFixed(1)}</td>
                      <td className="text-right py-2 px-3">{day.gdd_cumulative.toFixed(0)}</td>
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

export default GrowingDegrees;

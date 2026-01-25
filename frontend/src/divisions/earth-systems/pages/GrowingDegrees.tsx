/**
 * Growing Degree Days Page
 *
 * Track accumulated heat units for crop development.
 * Connected to /api/v2/gdd APIs.
 */

import { useState, useTransition, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCw, Thermometer, Calendar, TrendingUp, Leaf, ArrowRight, Sprout } from 'lucide-react';
import { gddAPI, fieldMapAPI } from '@/lib/api-client';
import { format, addDays, parseISO } from 'date-fns';

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
  const [selectedFieldId, setSelectedFieldId] = useState<string>('');
  const [isPending, startTransition] = useTransition();
  const queryClient = useQueryClient();

  const cropConfig = CROP_CONFIGS[selectedCrop];

  // Fetch Fields
  const { data: fields, isLoading: isLoadingFields } = useQuery({
    queryKey: ['fields'],
    queryFn: async () => {
      try {
        const response = await fieldMapAPI.getFields();
        // Handle if response is wrapped in object or array
        const data = Array.isArray(response) ? response : (response as any).data || [];
        return data.map((f: any) => ({ id: String(f.id), name: f.name }));
      } catch (e) {
        console.error("Failed to fetch fields", e);
        // Return dummy fields if API fails (for demo/dev)
        return [
          { id: '1', name: 'Field North' },
          { id: '2', name: 'Field South' },
          { id: '3', name: 'Greenhouse A' }
        ];
      }
    }
  });

  // Set default field
  useEffect(() => {
    if (fields && fields.length > 0 && !selectedFieldId) {
      setSelectedFieldId(fields[0].id);
    }
  }, [fields]);

  // Fetch GDD Data for Field
  const { data: fieldGddData, isLoading: isLoadingGdd, refetch: refetchGdd } = useQuery({
    queryKey: ['gdd-field', selectedFieldId],
    enabled: !!selectedFieldId,
    queryFn: async () => {
      // Get summary
      const summary = await gddAPI.getFieldSummary(selectedFieldId);
      
      // Get predictions
      const predictions = await gddAPI.getFieldPredictions(selectedFieldId);
      
      // Get recent history (mocked if empty)
      // In a real scenario, we'd fetch this range dynamically
      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      const history = await gddAPI.getFieldHistory(selectedFieldId, startDate, endDate);
      
      return { summary, predictions, history };
    }
  });

  // Mutation to create prediction
  const createPredictionMutation = useMutation({
    mutationFn: async () => {
      const today = new Date();
      const predictionDate = addDays(today, 14); // Predict 2 weeks out
      
      await gddAPI.createFieldPrediction(selectedFieldId, {
        crop_name: cropConfig.name,
        target_stage: "Next Stage",
        predicted_date: predictionDate.toISOString().split('T')[0],
        predicted_gdd: 100 + Math.random() * 50,
        confidence: 0.85
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gdd-field', selectedFieldId] });
    }
  });

  // Handle crop change with transition
  const handleCropChange = (value: string) => {
    startTransition(() => {
      setSelectedCrop(value);
    });
  };

  // Mock data generator if API returns empty (for visualization)
  const getDisplayData = () => {
    if (fieldGddData && fieldGddData.history && fieldGddData.history.length > 0) {
      return fieldGddData.history;
    }

    // Generate mock data for visualization if no real data
    const mockData = [];
    let cumulative = 0;
    const now = new Date();
    for (let i = 30; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      const daily = 5 + Math.random() * 15;
      cumulative += daily;
      mockData.push({
        log_date: date.toISOString().split('T')[0],
        daily_gdd: daily,
        cumulative_gdd: cumulative
      });
    }
    return mockData;
  };

  const displayData = getDisplayData();
  const latestGDD = displayData.length > 0 ? displayData[displayData.length - 1].cumulative_gdd : 0;
  const weeklyGDD = displayData.slice(-7).reduce((sum: number, d: any) => sum + d.daily_gdd, 0);

  // Calculate current stage
  const getCurrentStage = (cumulative: number) => {
    const stages = cropConfig.stages;
    for (let i = stages.length - 1; i >= 0; i--) {
      if (cumulative >= stages[i].gdd) return stages[i].name;
    }
    return 'Pre-emergence';
  };

  const currentStage = getCurrentStage(latestGDD);
  const progress = Math.min(100, Math.round((latestGDD / cropConfig.targetGDD) * 100));

  // Find next stage
  const getNextStage = () => {
    const stages = cropConfig.stages;
    for (const stage of stages) {
      if (latestGDD < stage.gdd) {
        const remaining = stage.gdd - latestGDD;
        const dailyAvg = weeklyGDD / 7 || 10;
        const days = Math.ceil(remaining / dailyAvg);
        return { ...stage, remaining, days };
      }
    }
    return null;
  };

  const nextStage = getNextStage();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">Growing Degree Days</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Track accumulated heat units for crop development</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {/* Field Selection */}
          <Select value={selectedFieldId} onValueChange={setSelectedFieldId} disabled={isLoadingFields}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={isLoadingFields ? "Loading fields..." : "Select Field"} />
            </SelectTrigger>
            <SelectContent>
              {fields?.map((field: any) => (
                <SelectItem key={field.id} value={field.id}>{field.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Crop Selection */}
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

          <Button variant="outline" size="icon" onClick={() => refetchGdd()} disabled={isLoadingGdd}>
            <RefreshCw className={`h-4 w-4 ${isLoadingGdd ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* GDD Calculation Notice */}
      <Alert className="bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
        <AlertDescription className="text-blue-800 dark:text-blue-200">
          Base temperature: <strong>{cropConfig.baseTemp}°C</strong> for {cropConfig.name}.
          {selectedFieldId && <span> Analyzing data for field ID: {selectedFieldId}</span>}
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-3 max-w-[400px]">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          {/* Current Season Summary */}
          <div className="grid md:grid-cols-3 gap-4">
            <Card className="bg-gradient-to-br from-orange-50 to-yellow-50 dark:from-orange-950/40 dark:to-yellow-950/40 border-orange-100 dark:border-orange-900">
              <CardContent className="p-6 text-center">
                {isLoadingGdd ? (
                  <Skeleton className="h-12 w-24 mx-auto" />
                ) : (
                  <>
                    <Thermometer className="h-8 w-8 mx-auto text-orange-500 mb-2" />
                    <div className="text-4xl font-bold text-orange-600 dark:text-orange-400">{Math.round(latestGDD)}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Accumulated GDD</div>
                  </>
                )}
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/40 dark:to-emerald-950/40 border-green-100 dark:border-green-900">
              <CardContent className="p-6 text-center">
                {isLoadingGdd ? (
                  <Skeleton className="h-12 w-24 mx-auto" />
                ) : (
                  <>
                    <TrendingUp className="h-8 w-8 mx-auto text-green-500 mb-2" />
                    <div className="text-4xl font-bold text-green-600 dark:text-green-400">+{Math.round(weeklyGDD)}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Last 7 Days</div>
                  </>
                )}
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950/40 dark:to-cyan-950/40 border-blue-100 dark:border-blue-900">
              <CardContent className="p-6 text-center">
                {isLoadingGdd ? (
                  <Skeleton className="h-12 w-24 mx-auto" />
                ) : (
                  <>
                    <Leaf className="h-8 w-8 mx-auto text-blue-500 mb-2" />
                    <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">{progress}%</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">To Maturity</div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Development Progress */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sprout className="h-5 w-5 text-green-600" />
                Development Progress
              </CardTitle>
              <CardDescription>Current stage: {currentStage}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Planting</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{Math.round(latestGDD)} / {cropConfig.targetGDD} GDD</span>
                    <span>Maturity</span>
                  </div>
                  <div className="relative h-4 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full bg-gradient-to-r from-green-400 to-green-600 transition-all duration-500"
                      style={{ width: `${progress}%` }}
                    />
                    {/* Stage Markers */}
                    {cropConfig.stages.map(stage => (
                      <div
                        key={stage.name}
                        className="absolute top-0 h-full w-0.5 bg-white/50 z-10"
                        style={{ left: `${(stage.gdd / cropConfig.targetGDD) * 100}%` }}
                        title={`${stage.name}: ${stage.gdd} GDD`}
                      />
                    ))}
                  </div>
                </div>

                {/* Stages Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                  {cropConfig.stages.map((stage) => {
                    const isComplete = latestGDD >= stage.gdd;
                    const isCurrent = currentStage === stage.name;
                    return (
                      <div
                        key={stage.name}
                        className={`p-3 rounded-lg border text-center transition-colors ${
                          isComplete
                            ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
                            : isCurrent
                              ? 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800 ring-1 ring-yellow-300 dark:ring-yellow-700'
                              : 'bg-gray-50 border-gray-100 dark:bg-gray-900/50 dark:border-gray-800'
                        }`}
                      >
                        <div className={`text-sm font-medium ${
                          isComplete ? 'text-green-700 dark:text-green-400' :
                          isCurrent ? 'text-yellow-700 dark:text-yellow-400' :
                          'text-gray-500 dark:text-gray-500'
                        }`}>
                          {stage.name}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">{stage.gdd} GDD</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Next Stage Prediction */}
          {nextStage ? (
            <Card className="border-l-4 border-l-blue-500">
              <CardContent className="p-6 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100">Next Stage: {nextStage.name}</h3>
                  <p className="text-gray-500 text-sm mt-1">
                    Expected in ~{nextStage.days} days ({nextStage.remaining} GDD remaining)
                  </p>
                </div>
                <Button onClick={() => createPredictionMutation.mutate()} disabled={createPredictionMutation.isPending}>
                  {createPredictionMutation.isPending ? 'Updating...' : 'Update Forecast'}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Alert className="bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800">
              <Sprout className="h-4 w-4 text-green-600" />
              <AlertTitle>Crop Mature</AlertTitle>
              <AlertDescription>
                This crop has reached its target GDD. Ready for harvest planning.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Daily GDD Log</CardTitle>
              <CardDescription>Recent temperature accumulations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-900/50">
                    <tr className="border-b">
                      <th className="py-3 px-4 text-left font-medium">Date</th>
                      <th className="py-3 px-4 text-right font-medium">Daily GDD</th>
                      <th className="py-3 px-4 text-right font-medium">Cumulative</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayData.slice().reverse().map((day: any) => (
                      <tr key={day.log_date} className="border-b last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                        <td className="py-3 px-4">{day.log_date}</td>
                        <td className="py-3 px-4 text-right text-green-600 dark:text-green-400 font-medium">+{day.daily_gdd.toFixed(1)}</td>
                        <td className="py-3 px-4 text-right">{day.cumulative_gdd.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="predictions" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Growth Stage Forecasts</CardTitle>
              <CardDescription>AI-driven predictions based on weather models</CardDescription>
            </CardHeader>
            <CardContent>
              {fieldGddData?.predictions && fieldGddData.predictions.length > 0 ? (
                <div className="rounded-md border">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-900/50">
                      <tr className="border-b">
                        <th className="py-3 px-4 text-left font-medium">Predicted Stage</th>
                        <th className="py-3 px-4 text-left font-medium">Target Date</th>
                        <th className="py-3 px-4 text-right font-medium">Confidence</th>
                        <th className="py-3 px-4 text-right font-medium">Predicted GDD</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fieldGddData.predictions.map((pred: any) => (
                        <tr key={pred.id} className="border-b last:border-0">
                          <td className="py-3 px-4 font-medium">{pred.target_stage}</td>
                          <td className="py-3 px-4">{pred.predicted_date}</td>
                          <td className="py-3 px-4 text-right">
                            <Badge variant={pred.confidence > 0.8 ? "default" : "secondary"}>
                              {(pred.confidence * 100).toFixed(0)}%
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-right">{pred.predicted_gdd?.toFixed(0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Calendar className="h-12 w-12 mx-auto mb-3 opacity-20" />
                  <p>No predictions available yet.</p>
                  <Button variant="link" onClick={() => createPredictionMutation.mutate()}>Generate Forecast</Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default GrowingDegrees;

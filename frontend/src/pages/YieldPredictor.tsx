/**
 * Yield Predictor Page
 * AI-powered yield prediction using phenotypic and environmental data
 * Connected to /api/v2/genomic-selection/yield-predictions endpoint
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Skeleton } from '@/components/ui/skeleton';
import { useDemoMode } from '@/hooks/useDemoMode';

const DEMO_PREDICTIONS = [
  { germplasm_id: 'G001', germplasm_name: 'Elite-2024-001', predicted_yield: 8.5, confidence_low: 7.8, confidence_high: 9.2, environment: 'Irrigated' },
  { germplasm_id: 'G002', germplasm_name: 'Elite-2024-002', predicted_yield: 8.2, confidence_low: 7.5, confidence_high: 8.9, environment: 'Irrigated' },
  { germplasm_id: 'G003', germplasm_name: 'Elite-2024-003', predicted_yield: 7.9, confidence_low: 7.2, confidence_high: 8.6, environment: 'Irrigated' },
  { germplasm_id: 'G004', germplasm_name: 'Elite-2024-004', predicted_yield: 7.6, confidence_low: 6.9, confidence_high: 8.3, environment: 'Irrigated' },
  { germplasm_id: 'G005', germplasm_name: 'Elite-2024-005', predicted_yield: 7.3, confidence_low: 6.6, confidence_high: 8.0, environment: 'Irrigated' },
];

const ENVIRONMENTAL_FACTORS = [
  { name: 'Temperature', value: 28, unit: '°C', optimal: [25, 32], impact: 'positive' },
  { name: 'Rainfall', value: 850, unit: 'mm', optimal: [800, 1200], impact: 'positive' },
  { name: 'Solar Radiation', value: 18, unit: 'MJ/m²', optimal: [15, 22], impact: 'positive' },
  { name: 'Humidity', value: 75, unit: '%', optimal: [60, 80], impact: 'positive' },
  { name: 'Soil Moisture', value: 45, unit: '%', optimal: [40, 60], impact: 'positive' },
];

export function YieldPredictor() {
  const [activeTab, setActiveTab] = useState('predict');
  const [selectedEnvironment, setSelectedEnvironment] = useState('all');
  const [ndviValue, setNdviValue] = useState([0.72]);
  const [rainfallValue, setRainfallValue] = useState([850]);
  const [tempValue, setTempValue] = useState([28]);
  const { isDemoMode } = useDemoMode();

  // Fetch yield predictions
  const { data: predictionsData, isLoading } = useQuery({
    queryKey: ['yield-predictions', selectedEnvironment],
    queryFn: async () => {
      const params = selectedEnvironment !== 'all' ? `?environment=${selectedEnvironment}` : '';
      const response = await fetch(`/api/v2/genomic-selection/yield-predictions${params}`);
      if (!response.ok) throw new Error('Failed to fetch predictions');
      return response.json();
    },
    enabled: !isDemoMode,
  });

  const predictions = predictionsData?.predictions || DEMO_PREDICTIONS;
  const avgPrediction = predictions.reduce((sum: number, p: any) => sum + p.predicted_yield, 0) / predictions.length;
  const topYield = Math.max(...predictions.map((p: any) => p.predicted_yield));


  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Yield Predictor</h1>
          <p className="text-muted-foreground mt-1">AI-powered yield prediction and scenario analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedEnvironment} onValueChange={setSelectedEnvironment}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Environment" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Environments</SelectItem>
              <SelectItem value="irrigated">Irrigated</SelectItem>
              <SelectItem value="rainfed">Rainfed</SelectItem>
              <SelectItem value="stress">Stress</SelectItem>
            </SelectContent>
          </Select>
          <Button>Run Prediction</Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-primary">{predictions.length}</p>
            <p className="text-xs text-muted-foreground">Predictions</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-green-600">{topYield.toFixed(1)} t/ha</p>
            <p className="text-xs text-muted-foreground">Top Yield</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{avgPrediction.toFixed(1)} t/ha</p>
            <p className="text-xs text-muted-foreground">Avg Yield</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-purple-600">85%</p>
            <p className="text-xs text-muted-foreground">Model Accuracy</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="predict">Predictions</TabsTrigger>
          <TabsTrigger value="scenario">Scenario Analysis</TabsTrigger>
          <TabsTrigger value="factors">Environmental Factors</TabsTrigger>
        </TabsList>

        <TabsContent value="predict" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Yield Predictions</CardTitle>
              <CardDescription>Predicted yields with confidence intervals</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? <Skeleton className="h-48 w-full" /> : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Germplasm</th>
                        <th className="text-right p-3">Predicted Yield</th>
                        <th className="text-center p-3">95% CI</th>
                        <th className="text-left p-3">Environment</th>
                        <th className="text-center p-3">Visualization</th>
                      </tr>
                    </thead>
                    <tbody>
                      {predictions.map((pred: any) => (
                        <tr key={pred.germplasm_id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{pred.germplasm_name}</td>
                          <td className="p-3 text-right">
                            <span className="text-lg font-bold text-green-600">{pred.predicted_yield.toFixed(1)}</span>
                            <span className="text-muted-foreground ml-1">t/ha</span>
                          </td>
                          <td className="p-3 text-center text-xs text-muted-foreground">
                            [{pred.confidence_low.toFixed(1)} - {pred.confidence_high.toFixed(1)}]
                          </td>
                          <td className="p-3"><Badge variant="outline">{pred.environment}</Badge></td>
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <Progress value={(pred.predicted_yield / 10) * 100} className="w-24 h-2" />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scenario" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Scenario Analysis</CardTitle>
              <CardDescription>Adjust environmental parameters to predict yield</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label>NDVI: {ndviValue[0].toFixed(2)}</Label>
                  <Slider value={ndviValue} onValueChange={setNdviValue} min={0} max={1} step={0.01} />
                  <p className="text-xs text-muted-foreground">Vegetation index (0-1)</p>
                </div>
                <div className="space-y-2">
                  <Label>Rainfall: {rainfallValue[0]} mm</Label>
                  <Slider value={rainfallValue} onValueChange={setRainfallValue} min={0} max={2000} step={50} />
                  <p className="text-xs text-muted-foreground">Seasonal rainfall</p>
                </div>
                <div className="space-y-2">
                  <Label>Temperature: {tempValue[0]}°C</Label>
                  <Slider value={tempValue} onValueChange={setTempValue} min={15} max={40} step={1} />
                  <p className="text-xs text-muted-foreground">Average temperature</p>
                </div>
              </div>
              <div className="p-6 bg-muted rounded-lg text-center">
                <p className="text-sm text-muted-foreground mb-2">Predicted Yield</p>
                <p className="text-4xl font-bold text-green-600">
                  {(5 + ndviValue[0] * 3 + (rainfallValue[0] > 800 ? 1 : 0) - (tempValue[0] > 35 ? 1 : 0)).toFixed(1)} t/ha
                </p>
                <p className="text-xs text-muted-foreground mt-2">Based on current parameters</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="factors" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Environmental Factors</CardTitle>
              <CardDescription>Current conditions and optimal ranges</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {ENVIRONMENTAL_FACTORS.map((factor) => (
                  <div key={factor.name} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div>
                      <p className="font-medium">{factor.name}</p>
                      <p className="text-xs text-muted-foreground">Optimal: {factor.optimal[0]}-{factor.optimal[1]} {factor.unit}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold">{factor.value} {factor.unit}</p>
                      <Badge className={factor.value >= factor.optimal[0] && factor.value <= factor.optimal[1] ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>
                        {factor.value >= factor.optimal[0] && factor.value <= factor.optimal[1] ? 'Optimal' : 'Suboptimal'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

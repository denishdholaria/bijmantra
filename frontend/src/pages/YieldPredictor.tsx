/**
 * Yield Predictor Page
 * AI-powered yield prediction using phenotypic and environmental data
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'

interface YieldPrediction {
  id: string
  trialName: string
  germplasm: string
  predictedYield: number
  confidenceInterval: [number, number]
  confidence: number
  factors: { name: string; impact: number; direction: 'positive' | 'negative' }[]
}

interface EnvironmentalFactor {
  name: string
  value: number
  unit: string
  optimal: [number, number]
  impact: 'positive' | 'negative' | 'neutral'
}

const predictions: YieldPrediction[] = [
  { id: 'p1', trialName: 'Yield Trial 2024', germplasm: 'Elite-001', predictedYield: 6.2, confidenceInterval: [5.8, 6.6], confidence: 0.85, factors: [{ name: 'NDVI', impact: 15, direction: 'positive' }, { name: 'Rainfall', impact: 8, direction: 'positive' }, { name: 'Disease', impact: -5, direction: 'negative' }] },
  { id: 'p2', trialName: 'Yield Trial 2024', germplasm: 'Elite-002', predictedYield: 5.8, confidenceInterval: [5.4, 6.2], confidence: 0.82, factors: [{ name: 'NDVI', impact: 12, direction: 'positive' }, { name: 'Stress', impact: -8, direction: 'negative' }] },
  { id: 'p3', trialName: 'Yield Trial 2024', germplasm: 'Elite-003', predictedYield: 6.5, confidenceInterval: [6.0, 7.0], confidence: 0.78, factors: [{ name: 'NDVI', impact: 18, direction: 'positive' }, { name: 'Rainfall', impact: 10, direction: 'positive' }] },
  { id: 'p4', trialName: 'Yield Trial 2024', germplasm: 'Elite-004', predictedYield: 5.5, confidenceInterval: [5.1, 5.9], confidence: 0.88, factors: [{ name: 'NDVI', impact: 10, direction: 'positive' }, { name: 'Disease', impact: -12, direction: 'negative' }] },
  { id: 'p5', trialName: 'Yield Trial 2024', germplasm: 'Check-001', predictedYield: 5.0, confidenceInterval: [4.6, 5.4], confidence: 0.90, factors: [{ name: 'NDVI', impact: 8, direction: 'positive' }] },
]

const environmentalFactors: EnvironmentalFactor[] = [
  { name: 'Temperature', value: 28, unit: '°C', optimal: [25, 32], impact: 'positive' },
  { name: 'Rainfall', value: 850, unit: 'mm', optimal: [800, 1200], impact: 'positive' },
  { name: 'Solar Radiation', value: 18, unit: 'MJ/m²', optimal: [15, 22], impact: 'positive' },
  { name: 'Humidity', value: 75, unit: '%', optimal: [60, 80], impact: 'positive' },
  { name: 'Soil Moisture', value: 45, unit: '%', optimal: [40, 60], impact: 'positive' },
  { name: 'N Fertilizer', value: 120, unit: 'kg/ha', optimal: [100, 150], impact: 'positive' },
]

export function YieldPredictor() {
  const [activeTab, setActiveTab] = useState('predict')
  const [selectedTrial, setSelectedTrial] = useState('all')
  const [ndviValue, setNdviValue] = useState([0.72])
  const [rainfallValue, setRainfallValue] = useState([850])
  const [tempValue, setTempValue] = useState([28])

  const avgPrediction = predictions.reduce((sum, p) => sum + p.predictedYield, 0) / predictions.length
  const topYield = Math.max(...predictions.map(p => p.predictedYield))

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.85) return 'text-green-600'
    if (conf >= 0.75) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getImpactColor = (direction: string) => {
    return direction === 'positive' ? 'text-green-600' : 'text-red-600'
  }

  const isInOptimalRange = (value: number, optimal: [number, number]) => {
    return value >= optimal[0] && value <= optimal[1]
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">🎯 Yield Predictor</h1>
          <p className="text-muted-foreground mt-1">AI-powered yield prediction and scenario analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedTrial} onValueChange={setSelectedTrial}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select trial" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Trials</SelectItem>
              <SelectItem value="yield2024">Yield Trial 2024</SelectItem>
              <SelectItem value="drought">Drought Trial</SelectItem>
            </SelectContent>
          </Select>
          <Button>🔄 Refresh Predictions</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-700">{avgPrediction.toFixed(1)}</p>
            <p className="text-sm text-green-600">Avg Predicted (t/ha)</p>
          </CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-700">{topYield.toFixed(1)}</p>
            <p className="text-sm text-blue-600">Top Predicted (t/ha)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{predictions.length}</p>
            <p className="text-sm text-muted-foreground">Predictions</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">84%</p>
            <p className="text-sm text-muted-foreground">Model Accuracy</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="predict">🎯 Predictions</TabsTrigger>
          <TabsTrigger value="scenario">🔮 Scenario Analysis</TabsTrigger>
          <TabsTrigger value="factors">📊 Contributing Factors</TabsTrigger>
          <TabsTrigger value="model">🧠 Model Info</TabsTrigger>
        </TabsList>

        <TabsContent value="predict" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Yield Predictions</CardTitle>
              <CardDescription>AI-predicted yields with confidence intervals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {predictions.map((pred) => (
                  <div key={pred.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-bold">{pred.germplasm}</h4>
                        <p className="text-sm text-muted-foreground">{pred.trialName}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-green-600">{pred.predictedYield.toFixed(1)} t/ha</p>
                        <p className="text-xs text-muted-foreground">
                          CI: {pred.confidenceInterval[0].toFixed(1)} - {pred.confidenceInterval[1].toFixed(1)}
                        </p>
                      </div>
                    </div>
                    
                    {/* Yield bar visualization */}
                    <div className="relative h-8 bg-muted rounded-full overflow-hidden mb-3">
                      <div 
                        className="absolute h-full bg-green-200 rounded-full"
                        style={{ 
                          left: `${(pred.confidenceInterval[0] / 8) * 100}%`,
                          width: `${((pred.confidenceInterval[1] - pred.confidenceInterval[0]) / 8) * 100}%`
                        }}
                      />
                      <div 
                        className="absolute h-full w-1 bg-green-600"
                        style={{ left: `${(pred.predictedYield / 8) * 100}%` }}
                      />
                      <div className="absolute inset-0 flex items-center justify-between px-2 text-xs">
                        <span>0</span>
                        <span>8 t/ha</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex gap-2">
                        {pred.factors.map((f, i) => (
                          <Badge key={i} variant="outline" className={`text-xs ${getImpactColor(f.direction)}`}>
                            {f.direction === 'positive' ? '↑' : '↓'} {f.name} ({f.impact > 0 ? '+' : ''}{f.impact}%)
                          </Badge>
                        ))}
                      </div>
                      <span className={`text-sm font-medium ${getConfidenceColor(pred.confidence)}`}>
                        {(pred.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scenario" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Scenario Parameters</CardTitle>
                <CardDescription>Adjust parameters to see yield impact</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>NDVI (Vegetation Index): {ndviValue[0].toFixed(2)}</Label>
                  <Slider
                    value={ndviValue}
                    onValueChange={setNdviValue}
                    min={0.3}
                    max={0.9}
                    step={0.01}
                  />
                  <p className="text-xs text-muted-foreground">Higher NDVI indicates healthier vegetation</p>
                </div>

                <div className="space-y-2">
                  <Label>Seasonal Rainfall: {rainfallValue[0]} mm</Label>
                  <Slider
                    value={rainfallValue}
                    onValueChange={setRainfallValue}
                    min={400}
                    max={1500}
                    step={50}
                  />
                  <p className="text-xs text-muted-foreground">Total rainfall during growing season</p>
                </div>

                <div className="space-y-2">
                  <Label>Avg Temperature: {tempValue[0]}°C</Label>
                  <Slider
                    value={tempValue}
                    onValueChange={setTempValue}
                    min={15}
                    max={40}
                    step={1}
                  />
                  <p className="text-xs text-muted-foreground">Average temperature during grain filling</p>
                </div>

                <Button className="w-full">🔮 Run Scenario</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Scenario Result</CardTitle>
                <CardDescription>Predicted yield under current scenario</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-5xl font-bold text-green-600">
                    {(4.5 + ndviValue[0] * 3 + (rainfallValue[0] - 600) / 500 - Math.abs(tempValue[0] - 28) * 0.1).toFixed(1)}
                  </p>
                  <p className="text-lg text-muted-foreground">t/ha predicted</p>
                  
                  <div className="mt-6 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>NDVI Impact</span>
                      <span className="text-green-600">+{(ndviValue[0] * 3).toFixed(1)} t/ha</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Rainfall Impact</span>
                      <span className={rainfallValue[0] >= 800 ? 'text-green-600' : 'text-red-600'}>
                        {rainfallValue[0] >= 800 ? '+' : ''}{((rainfallValue[0] - 600) / 500).toFixed(1)} t/ha
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Temperature Impact</span>
                      <span className={Math.abs(tempValue[0] - 28) < 5 ? 'text-green-600' : 'text-red-600'}>
                        {Math.abs(tempValue[0] - 28) < 5 ? '+' : '-'}{(Math.abs(tempValue[0] - 28) * 0.1).toFixed(1)} t/ha
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Scenario Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Scenario Comparison</CardTitle>
              <CardDescription>Compare different scenarios</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { name: 'Optimistic', yield: 6.8, conditions: 'Good rainfall, no stress' },
                  { name: 'Baseline', yield: 5.5, conditions: 'Normal conditions' },
                  { name: 'Pessimistic', yield: 4.2, conditions: 'Drought, disease pressure' },
                ].map((scenario) => (
                  <div key={scenario.name} className="p-4 border rounded-lg text-center">
                    <h4 className="font-bold">{scenario.name}</h4>
                    <p className="text-3xl font-bold text-primary my-2">{scenario.yield} t/ha</p>
                    <p className="text-xs text-muted-foreground">{scenario.conditions}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="factors" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Environmental Factors</CardTitle>
              <CardDescription>Current conditions affecting yield</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {environmentalFactors.map((factor) => {
                  const inRange = isInOptimalRange(factor.value, factor.optimal)
                  return (
                    <div key={factor.name} className="flex items-center gap-4">
                      <div className="w-32">
                        <p className="font-medium">{factor.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Optimal: {factor.optimal[0]}-{factor.optimal[1]} {factor.unit}
                        </p>
                      </div>
                      <div className="flex-1">
                        <div className="relative h-4 bg-muted rounded-full">
                          <div 
                            className="absolute h-full bg-green-200 rounded-full"
                            style={{
                              left: `${(factor.optimal[0] / (factor.optimal[1] * 1.5)) * 100}%`,
                              width: `${((factor.optimal[1] - factor.optimal[0]) / (factor.optimal[1] * 1.5)) * 100}%`
                            }}
                          />
                          <div 
                            className={`absolute h-full w-2 rounded-full ${inRange ? 'bg-green-600' : 'bg-red-500'}`}
                            style={{ left: `${(factor.value / (factor.optimal[1] * 1.5)) * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="w-24 text-right">
                        <span className={`font-bold ${inRange ? 'text-green-600' : 'text-red-600'}`}>
                          {factor.value} {factor.unit}
                        </span>
                      </div>
                      <Badge className={inRange ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}>
                        {inRange ? '✓ Optimal' : '⚠ Suboptimal'}
                      </Badge>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* Feature Importance */}
          <Card>
            <CardHeader>
              <CardTitle>Feature Importance</CardTitle>
              <CardDescription>Most important factors for yield prediction</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { feature: 'NDVI at flowering', importance: 0.28 },
                  { feature: 'Rainfall (grain filling)', importance: 0.22 },
                  { feature: 'Temperature (flowering)', importance: 0.18 },
                  { feature: 'Disease severity', importance: 0.15 },
                  { feature: 'N fertilizer', importance: 0.10 },
                  { feature: 'Plant density', importance: 0.07 },
                ].map((item) => (
                  <div key={item.feature} className="flex items-center gap-4">
                    <span className="w-48 text-sm">{item.feature}</span>
                    <Progress value={item.importance * 100} className="flex-1 h-3" />
                    <span className="w-12 text-right font-bold">{(item.importance * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="model" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Information</CardTitle>
              <CardDescription>Details about the yield prediction model</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-2xl font-bold">Random Forest</p>
                  <p className="text-xs text-muted-foreground">Algorithm</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-2xl font-bold">84%</p>
                  <p className="text-xs text-muted-foreground">R² Score</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-2xl font-bold">0.42 t/ha</p>
                  <p className="text-xs text-muted-foreground">RMSE</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-2xl font-bold">5,000+</p>
                  <p className="text-xs text-muted-foreground">Training Samples</p>
                </div>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-bold text-blue-800 mb-2">📊 Model Features</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Remote sensing indices (NDVI, GNDVI, NDRE)</li>
                  <li>• Weather data (temperature, rainfall, radiation)</li>
                  <li>• Soil properties (texture, organic matter, pH)</li>
                  <li>• Management practices (fertilizer, irrigation)</li>
                  <li>• Disease and stress observations</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

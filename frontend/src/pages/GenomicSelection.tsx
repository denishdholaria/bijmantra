/**
 * Genomic Selection Page
 * GS model training, prediction, and selection tools
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
import { Switch } from '@/components/ui/switch'

interface GSModel {
  id: string
  name: string
  method: string
  trait: string
  accuracy: number
  heritability: number
  markers: number
  trainSize: number
  validSize: number
  status: 'trained' | 'training' | 'pending'
  createdAt: string
}

interface Prediction {
  germplasmId: string
  germplasmName: string
  gebv: number
  reliability: number
  rank: number
  selected: boolean
}

const sampleModels: GSModel[] = [
  {
    id: 'gs1',
    name: 'Yield_GBLUP_2024',
    method: 'GBLUP',
    trait: 'Grain Yield',
    accuracy: 0.72,
    heritability: 0.45,
    markers: 12500,
    trainSize: 500,
    validSize: 100,
    status: 'trained',
    createdAt: '2024-11-15',
  },
  {
    id: 'gs2',
    name: 'Height_BayesB_2024',
    method: 'BayesB',
    trait: 'Plant Height',
    accuracy: 0.81,
    heritability: 0.68,
    markers: 12500,
    trainSize: 500,
    validSize: 100,
    status: 'trained',
    createdAt: '2024-11-18',
  },
  {
    id: 'gs3',
    name: 'DTF_RKHS_2024',
    method: 'RKHS',
    trait: 'Days to Flowering',
    accuracy: 0.65,
    heritability: 0.52,
    markers: 12500,
    trainSize: 500,
    validSize: 100,
    status: 'trained',
    createdAt: '2024-11-20',
  },
  {
    id: 'gs4',
    name: 'MultiTrait_MT_2024',
    method: 'Multi-trait',
    trait: 'Multiple',
    accuracy: 0.68,
    heritability: 0.55,
    markers: 12500,
    trainSize: 500,
    validSize: 100,
    status: 'training',
    createdAt: '2024-11-25',
  },
]

const predictions: Prediction[] = [
  { germplasmId: 'G001', germplasmName: 'Elite-2024-001', gebv: 2.45, reliability: 0.85, rank: 1, selected: true },
  { germplasmId: 'G002', germplasmName: 'Elite-2024-002', gebv: 2.32, reliability: 0.82, rank: 2, selected: true },
  { germplasmId: 'G003', germplasmName: 'Elite-2024-003', gebv: 2.18, reliability: 0.79, rank: 3, selected: true },
  { germplasmId: 'G004', germplasmName: 'Elite-2024-004', gebv: 1.95, reliability: 0.81, rank: 4, selected: true },
  { germplasmId: 'G005', germplasmName: 'Elite-2024-005', gebv: 1.82, reliability: 0.77, rank: 5, selected: true },
  { germplasmId: 'G006', germplasmName: 'Elite-2024-006', gebv: 1.68, reliability: 0.75, rank: 6, selected: false },
  { germplasmId: 'G007', germplasmName: 'Elite-2024-007', gebv: 1.55, reliability: 0.73, rank: 7, selected: false },
  { germplasmId: 'G008', germplasmName: 'Elite-2024-008', gebv: 1.42, reliability: 0.71, rank: 8, selected: false },
  { germplasmId: 'G009', germplasmName: 'Elite-2024-009', gebv: 1.28, reliability: 0.69, rank: 9, selected: false },
  { germplasmId: 'G010', germplasmName: 'Elite-2024-010', gebv: 1.15, reliability: 0.68, rank: 10, selected: false },
]

export function GenomicSelection() {
  const [activeTab, setActiveTab] = useState('models')
  const [selectedModel, setSelectedModel] = useState('gs1')
  const [selectionIntensity, setSelectionIntensity] = useState([20])
  const [useRelationship, setUseRelationship] = useState(true)

  const currentModel = sampleModels.find(m => m.id === selectedModel)
  const selectedCount = Math.ceil(predictions.length * (selectionIntensity[0] / 100))

  const getAccuracyColor = (acc: number) => {
    if (acc >= 0.7) return 'text-green-600'
    if (acc >= 0.5) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'trained':
        return <Badge className="bg-green-100 text-green-700">✓ Trained</Badge>
      case 'training':
        return <Badge className="bg-yellow-100 text-yellow-700">⏳ Training</Badge>
      default:
        return <Badge variant="secondary">Pending</Badge>
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genomic Selection</h1>
          <p className="text-muted-foreground mt-1">GS model training and GEBV prediction</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">📥 Import Genotypes</Button>
          <Button>🧬 New Model</Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="predict">Predict</TabsTrigger>
          <TabsTrigger value="select">Selection</TabsTrigger>
          <TabsTrigger value="accuracy">Accuracy</TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="space-y-6 mt-4">
          {/* Model Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {sampleModels.map((model) => (
              <Card 
                key={model.id}
                className={`cursor-pointer transition-all ${
                  selectedModel === model.id ? 'ring-2 ring-primary' : 'hover:shadow-md'
                }`}
                onClick={() => setSelectedModel(model.id)}
              >
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between mb-2">
                    <Badge variant="outline">{model.method}</Badge>
                    {getStatusBadge(model.status)}
                  </div>
                  <h3 className="font-bold mt-2">{model.name}</h3>
                  <p className="text-sm text-muted-foreground">{model.trait}</p>
                  <div className="mt-3 space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>Accuracy</span>
                      <span className={`font-bold ${getAccuracyColor(model.accuracy)}`}>
                        {(model.accuracy * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Progress value={model.accuracy * 100} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Model Details */}
          {currentModel && (
            <Card>
              <CardHeader>
                <CardTitle>{currentModel.name}</CardTitle>
                <CardDescription>Model details and parameters</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-muted rounded-lg text-center">
                    <p className="text-2xl font-bold text-primary">{currentModel.method}</p>
                    <p className="text-xs text-muted-foreground">Method</p>
                  </div>
                  <div className="p-4 bg-muted rounded-lg text-center">
                    <p className="text-2xl font-bold">{currentModel.markers.toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">Markers</p>
                  </div>
                  <div className="p-4 bg-muted rounded-lg text-center">
                    <p className="text-2xl font-bold">{currentModel.trainSize}</p>
                    <p className="text-xs text-muted-foreground">Training Size</p>
                  </div>
                  <div className="p-4 bg-muted rounded-lg text-center">
                    <p className="text-2xl font-bold">{(currentModel.heritability * 100).toFixed(0)}%</p>
                    <p className="text-xs text-muted-foreground">Heritability</p>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-3">Model Performance</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span>Prediction Accuracy (r)</span>
                        <span className="font-bold">{currentModel.accuracy.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Heritability (h²)</span>
                        <span className="font-bold">{currentModel.heritability.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Accuracy/√h²</span>
                        <span className="font-bold">
                          {(currentModel.accuracy / Math.sqrt(currentModel.heritability)).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-3">Cross-Validation</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span>CV Folds</span>
                        <span className="font-bold">5</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Mean Accuracy</span>
                        <span className="font-bold">{(currentModel.accuracy - 0.02).toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Std. Dev</span>
                        <span className="font-bold">0.04</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* New Model Form */}
          <Card>
            <CardHeader>
              <CardTitle>Train New Model</CardTitle>
              <CardDescription>Configure and train a new GS model</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Model Name</Label>
                  <Input placeholder="e.g., Yield_GBLUP_2024" />
                </div>
                <div className="space-y-2">
                  <Label>Target Trait</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select trait" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="yield">Grain Yield</SelectItem>
                      <SelectItem value="height">Plant Height</SelectItem>
                      <SelectItem value="dtf">Days to Flowering</SelectItem>
                      <SelectItem value="protein">Protein Content</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Method</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select method" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gblup">GBLUP</SelectItem>
                      <SelectItem value="bayesa">BayesA</SelectItem>
                      <SelectItem value="bayesb">BayesB</SelectItem>
                      <SelectItem value="bayesc">BayesCπ</SelectItem>
                      <SelectItem value="rkhs">RKHS</SelectItem>
                      <SelectItem value="rf">Random Forest</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="mt-4 flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Switch checked={useRelationship} onCheckedChange={setUseRelationship} />
                  <Label>Use genomic relationship matrix (G)</Label>
                </div>
              </div>
              <Button className="mt-4">🚀 Start Training</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="predict" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>GEBV Predictions</CardTitle>
              <CardDescription>Genomic estimated breeding values for selection candidates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex gap-4">
                <Select value={selectedModel} onValueChange={setSelectedModel}>
                  <SelectTrigger className="w-64">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {sampleModels.filter(m => m.status === 'trained').map(m => (
                      <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button>🔄 Run Prediction</Button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-center p-3">Rank</th>
                      <th className="text-left p-3">Germplasm</th>
                      <th className="text-right p-3">GEBV</th>
                      <th className="text-right p-3">Reliability</th>
                      <th className="text-center p-3">Status</th>
                      <th className="text-center p-3">Select</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((pred) => (
                      <tr key={pred.germplasmId} className={`border-b hover:bg-muted/50 ${pred.selected ? 'bg-green-50' : ''}`}>
                        <td className="p-3 text-center font-bold">{pred.rank}</td>
                        <td className="p-3">
                          <p className="font-medium">{pred.germplasmName}</p>
                          <p className="text-xs text-muted-foreground">{pred.germplasmId}</p>
                        </td>
                        <td className="p-3 text-right">
                          <span className={`font-bold ${pred.gebv > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {pred.gebv > 0 ? '+' : ''}{pred.gebv.toFixed(2)}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Progress value={pred.reliability * 100} className="w-16 h-2" />
                            <span className="text-xs">{(pred.reliability * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="p-3 text-center">
                          {pred.rank <= 3 ? (
                            <Badge className="bg-yellow-100 text-yellow-700">⭐ Top</Badge>
                          ) : pred.rank <= 5 ? (
                            <Badge className="bg-blue-100 text-blue-700">Elite</Badge>
                          ) : (
                            <Badge variant="secondary">Candidate</Badge>
                          )}
                        </td>
                        <td className="p-3 text-center">
                          <input type="checkbox" defaultChecked={pred.selected} className="w-4 h-4" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* GEBV Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>GEBV Distribution</CardTitle>
              <CardDescription>Distribution of genomic breeding values</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-48 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">📊</span>
                  <p className="mt-2 text-muted-foreground">GEBV Histogram</p>
                  <p className="text-xs text-muted-foreground">Mean: 1.58 | SD: 0.45</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="select" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Selection Strategy</CardTitle>
              <CardDescription>Configure selection parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Selection Intensity: {selectionIntensity[0]}% ({selectedCount} individuals)</Label>
                    <Slider
                      value={selectionIntensity}
                      onValueChange={setSelectionIntensity}
                      min={5}
                      max={50}
                      step={5}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Selection Method</Label>
                    <Select defaultValue="truncation">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="truncation">Truncation Selection</SelectItem>
                        <SelectItem value="ocs">Optimal Contribution Selection</SelectItem>
                        <SelectItem value="index">Selection Index</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-3">Expected Genetic Gain</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Selection Differential (S)</span>
                      <span className="font-bold">1.85 σ</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Accuracy (r)</span>
                      <span className="font-bold">{currentModel?.accuracy.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Heritability (h²)</span>
                      <span className="font-bold">{currentModel?.heritability.toFixed(2)}</span>
                    </div>
                    <hr className="my-2" />
                    <div className="flex justify-between text-lg">
                      <span>ΔG per cycle</span>
                      <span className="font-bold text-green-600">
                        +{((1.85 * (currentModel?.accuracy || 0.7) * Math.sqrt(currentModel?.heritability || 0.5)) * 0.8).toFixed(2)} units
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Selection Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-green-700">{selectedCount}</p>
                <p className="text-sm text-green-600">Selected Individuals</p>
              </CardContent>
            </Card>
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-blue-700">
                  {predictions.slice(0, selectedCount).reduce((sum, p) => sum + p.gebv, 0) / selectedCount || 0}
                </p>
                <p className="text-sm text-blue-600">Mean GEBV (Selected)</p>
              </CardContent>
            </Card>
            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-purple-700">
                  {((predictions.slice(0, selectedCount).reduce((sum, p) => sum + p.gebv, 0) / selectedCount) - 
                    (predictions.reduce((sum, p) => sum + p.gebv, 0) / predictions.length)).toFixed(2)}
                </p>
                <p className="text-sm text-purple-600">Selection Differential</p>
              </CardContent>
            </Card>
          </div>

          <Button className="w-full">✅ Confirm Selection & Export</Button>
        </TabsContent>

        <TabsContent value="accuracy" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Accuracy Comparison</CardTitle>
              <CardDescription>Compare prediction accuracy across models</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sampleModels.filter(m => m.status === 'trained').map((model) => (
                  <div key={model.id} className="flex items-center gap-4">
                    <div className="w-48">
                      <p className="font-medium">{model.name}</p>
                      <p className="text-xs text-muted-foreground">{model.method}</p>
                    </div>
                    <div className="flex-1">
                      <Progress value={model.accuracy * 100} className="h-4" />
                    </div>
                    <span className={`w-16 text-right font-bold ${getAccuracyColor(model.accuracy)}`}>
                      {(model.accuracy * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Accuracy by Trait */}
          <Card>
            <CardHeader>
              <CardTitle>Factors Affecting Accuracy</CardTitle>
              <CardDescription>Key factors influencing GS prediction accuracy</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <h4 className="font-medium">Positive Factors</h4>
                  {[
                    { factor: 'High heritability', impact: 85 },
                    { factor: 'Large training population', impact: 78 },
                    { factor: 'High marker density', impact: 72 },
                    { factor: 'Close relatedness', impact: 68 },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      <span className="flex-1 text-sm">{item.factor}</span>
                      <Progress value={item.impact} className="w-24 h-2" />
                    </div>
                  ))}
                </div>
                <div className="space-y-3">
                  <h4 className="font-medium">Challenges</h4>
                  {[
                    { factor: 'Small training size', impact: 65 },
                    { factor: 'Low heritability traits', impact: 55 },
                    { factor: 'Population structure', impact: 45 },
                    { factor: 'G×E interaction', impact: 40 },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-red-500">⚠</span>
                      <span className="flex-1 text-sm">{item.factor}</span>
                      <Progress value={item.impact} className="w-24 h-2" />
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800">💡 Recommendations</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 space-y-2">
              <p>• Increase training population size to improve accuracy for low-heritability traits</p>
              <p>• Consider multi-trait models to leverage genetic correlations</p>
              <p>• Update models annually with new phenotypic data</p>
              <p>• Use optimal contribution selection to balance genetic gain and diversity</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

/**
 * Phenomic Selection Page
 * High-throughput phenotyping and phenomic prediction
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'

interface SpectralIndex {
  name: string
  abbreviation: string
  formula: string
  value: number
  correlation: number
  trait: string
}

interface PhenomicModel {
  id: string
  name: string
  trait: string
  platform: string
  accuracy: number
  features: number
  samples: number
  status: 'trained' | 'training' | 'pending'
}

const spectralIndices: SpectralIndex[] = [
  { name: 'Normalized Difference Vegetation Index', abbreviation: 'NDVI', formula: '(NIR-Red)/(NIR+Red)', value: 0.72, correlation: 0.85, trait: 'Biomass' },
  { name: 'Green Normalized Difference VI', abbreviation: 'GNDVI', formula: '(NIR-Green)/(NIR+Green)', value: 0.68, correlation: 0.78, trait: 'Chlorophyll' },
  { name: 'Normalized Difference Red Edge', abbreviation: 'NDRE', formula: '(NIR-RedEdge)/(NIR+RedEdge)', value: 0.45, correlation: 0.82, trait: 'N Status' },
  { name: 'Chlorophyll Index', abbreviation: 'CI', formula: '(NIR/RedEdge)-1', value: 2.35, correlation: 0.75, trait: 'Chlorophyll' },
  { name: 'Canopy Chlorophyll Content Index', abbreviation: 'CCCI', formula: 'NDRE/NDVI', value: 0.62, correlation: 0.72, trait: 'N Uptake' },
  { name: 'Plant Senescence Reflectance Index', abbreviation: 'PSRI', formula: '(Red-Green)/NIR', value: 0.15, correlation: 0.68, trait: 'Senescence' },
]

const phenomicModels: PhenomicModel[] = [
  { id: 'pm1', name: 'Yield_HTP_2024', trait: 'Grain Yield', platform: 'UAV Multispectral', accuracy: 0.78, features: 45, samples: 500, status: 'trained' },
  { id: 'pm2', name: 'Biomass_RGB_2024', trait: 'Biomass', platform: 'RGB Imaging', accuracy: 0.82, features: 28, samples: 500, status: 'trained' },
  { id: 'pm3', name: 'NStatus_Hyper_2024', trait: 'N Status', platform: 'Hyperspectral', accuracy: 0.85, features: 120, samples: 300, status: 'trained' },
  { id: 'pm4', name: 'Stress_Thermal_2024', trait: 'Drought Stress', platform: 'Thermal Imaging', accuracy: 0.72, features: 15, samples: 400, status: 'trained' },
  { id: 'pm5', name: 'Height_LiDAR_2024', trait: 'Plant Height', platform: 'LiDAR', accuracy: 0.92, features: 8, samples: 500, status: 'trained' },
]

export function PhenomicSelection() {
  const [activeTab, setActiveTab] = useState('indices')
  const [selectedPlatform, setSelectedPlatform] = useState('all')

  const getAccuracyColor = (acc: number) => {
    if (acc >= 0.8) return 'text-green-600'
    if (acc >= 0.7) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Phenomic Selection</h1>
          <p className="text-muted-foreground mt-1">High-throughput phenotyping and prediction</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Platform" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Platforms</SelectItem>
              <SelectItem value="uav">UAV</SelectItem>
              <SelectItem value="ground">Ground-based</SelectItem>
              <SelectItem value="satellite">Satellite</SelectItem>
            </SelectContent>
          </Select>
          <Button>📷 Import Data</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{phenomicModels.length}</p>
            <p className="text-sm text-muted-foreground">Prediction Models</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{spectralIndices.length}</p>
            <p className="text-sm text-muted-foreground">Spectral Indices</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">82%</p>
            <p className="text-sm text-muted-foreground">Avg Accuracy</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">2,200</p>
            <p className="text-sm text-muted-foreground">Plots Phenotyped</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="indices">Spectral Indices</TabsTrigger>
          <TabsTrigger value="models">Prediction Models</TabsTrigger>
          <TabsTrigger value="platforms">Platforms</TabsTrigger>
          <TabsTrigger value="integration">GS Integration</TabsTrigger>
        </TabsList>

        <TabsContent value="indices" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Vegetation Indices</CardTitle>
              <CardDescription>Spectral indices for trait prediction</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Index</th>
                      <th className="text-left p-3">Full Name</th>
                      <th className="text-left p-3">Formula</th>
                      <th className="text-right p-3">Value</th>
                      <th className="text-right p-3">Correlation</th>
                      <th className="text-left p-3">Target Trait</th>
                    </tr>
                  </thead>
                  <tbody>
                    {spectralIndices.map((index) => (
                      <tr key={index.abbreviation} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-bold">{index.abbreviation}</td>
                        <td className="p-3">{index.name}</td>
                        <td className="p-3 font-mono text-xs">{index.formula}</td>
                        <td className="p-3 text-right font-mono">{index.value.toFixed(2)}</td>
                        <td className="p-3 text-right">
                          <span className={index.correlation >= 0.8 ? 'text-green-600 font-bold' : index.correlation >= 0.7 ? 'text-yellow-600' : ''}>
                            {index.correlation.toFixed(2)}
                          </span>
                        </td>
                        <td className="p-3">
                          <Badge variant="outline">{index.trait}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Index Visualization */}
          <Card>
            <CardHeader>
              <CardTitle>Index Distribution</CardTitle>
              <CardDescription>NDVI values across field</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-48 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">🗺️</span>
                  <p className="mt-2 text-muted-foreground">NDVI Heatmap</p>
                  <p className="text-xs text-muted-foreground">Range: 0.45 - 0.85</p>
                </div>
              </div>
              <div className="flex items-center justify-center gap-2 mt-4">
                <div className="w-4 h-4 bg-red-500 rounded" />
                <span className="text-xs">Low</span>
                <div className="w-4 h-4 bg-yellow-500 rounded ml-2" />
                <span className="text-xs">Medium</span>
                <div className="w-4 h-4 bg-green-500 rounded ml-2" />
                <span className="text-xs">High</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Phenomic Prediction Models</CardTitle>
              <CardDescription>Machine learning models for trait prediction</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {phenomicModels.map((model) => (
                  <div key={model.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h4 className="font-bold">{model.name}</h4>
                        <p className="text-sm text-muted-foreground">{model.trait} | {model.platform}</p>
                      </div>
                      <Badge className={model.status === 'trained' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>
                        {model.status === 'trained' ? '✓ Trained' : '⏳ Training'}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm mb-2">
                      <div>
                        <p className="text-muted-foreground">Features</p>
                        <p className="font-bold">{model.features}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Samples</p>
                        <p className="font-bold">{model.samples}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Accuracy</p>
                        <p className={`font-bold ${getAccuracyColor(model.accuracy)}`}>{(model.accuracy * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                    <Progress value={model.accuracy * 100} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Train New Model */}
          <Card>
            <CardHeader>
              <CardTitle>Train New Model</CardTitle>
              <CardDescription>Create phenomic prediction model</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Target Trait</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select trait" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="yield">Grain Yield</SelectItem>
                      <SelectItem value="biomass">Biomass</SelectItem>
                      <SelectItem value="height">Plant Height</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Algorithm</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select algorithm" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pls">PLSR</SelectItem>
                      <SelectItem value="rf">Random Forest</SelectItem>
                      <SelectItem value="svr">SVR</SelectItem>
                      <SelectItem value="nn">Neural Network</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Feature Set</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select features" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="vi">Vegetation Indices</SelectItem>
                      <SelectItem value="bands">Raw Bands</SelectItem>
                      <SelectItem value="all">All Features</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button className="mt-4">🚀 Train Model</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="platforms" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { name: 'UAV Multispectral', icon: '🚁', sensors: ['RGB', 'NIR', 'RedEdge'], resolution: '5 cm', coverage: '50 ha/day', traits: ['Biomass', 'NDVI', 'Canopy Cover'] },
              { name: 'Hyperspectral', icon: '🌈', sensors: ['400-2500 nm'], resolution: '1 nm', coverage: '10 ha/day', traits: ['N Status', 'Chlorophyll', 'Water Content'] },
              { name: 'Thermal Imaging', icon: '🌡️', sensors: ['LWIR'], resolution: '10 cm', coverage: '30 ha/day', traits: ['Canopy Temp', 'Stress Index', 'Stomatal Conductance'] },
              { name: 'LiDAR', icon: '📡', sensors: ['3D Point Cloud'], resolution: '2 cm', coverage: '20 ha/day', traits: ['Plant Height', 'Canopy Volume', 'LAI'] },
            ].map((platform) => (
              <Card key={platform.name}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="text-2xl">{platform.icon}</span>
                    {platform.name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Sensors</span>
                      <span>{platform.sensors.join(', ')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Resolution</span>
                      <span>{platform.resolution}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Coverage</span>
                      <span>{platform.coverage}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Target Traits:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {platform.traits.map((t) => (
                          <Badge key={t} variant="outline" className="text-xs">{t}</Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="integration" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Phenomic-Genomic Integration</CardTitle>
              <CardDescription>Combine HTP data with genomic selection</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-muted rounded-lg">
                <h4 className="font-bold mb-2">Integration Approaches</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-3 bg-background rounded border">
                    <h5 className="font-medium">Phenomic BLUP</h5>
                    <p className="text-xs text-muted-foreground mt-1">Use HTP data as secondary traits in multi-trait GBLUP</p>
                    <Badge className="mt-2 bg-green-100 text-green-700">+12% accuracy</Badge>
                  </div>
                  <div className="p-3 bg-background rounded border">
                    <h5 className="font-medium">Feature Stacking</h5>
                    <p className="text-xs text-muted-foreground mt-1">Combine genomic and phenomic features</p>
                    <Badge className="mt-2 bg-green-100 text-green-700">+8% accuracy</Badge>
                  </div>
                  <div className="p-3 bg-background rounded border">
                    <h5 className="font-medium">Indirect Selection</h5>
                    <p className="text-xs text-muted-foreground mt-1">Use HTP traits as proxies for target traits</p>
                    <Badge className="mt-2 bg-green-100 text-green-700">+15% efficiency</Badge>
                  </div>
                </div>
              </div>

              {/* Accuracy Comparison */}
              <div>
                <h4 className="font-medium mb-3">Prediction Accuracy Comparison</h4>
                <div className="space-y-3">
                  {[
                    { method: 'Genomic Only (GBLUP)', accuracy: 0.72 },
                    { method: 'Phenomic Only (PLSR)', accuracy: 0.78 },
                    { method: 'Combined (GP + HTP)', accuracy: 0.85 },
                  ].map((item) => (
                    <div key={item.method} className="flex items-center gap-4">
                      <span className="w-48 text-sm">{item.method}</span>
                      <Progress value={item.accuracy * 100} className="flex-1 h-3" />
                      <span className={`w-16 text-right font-bold ${getAccuracyColor(item.accuracy)}`}>
                        {(item.accuracy * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800">💡 Best Practices</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 space-y-2">
              <p>• Collect HTP data at multiple growth stages for better prediction</p>
              <p>• Use vegetation indices highly correlated with target traits</p>
              <p>• Combine genomic and phenomic data for maximum accuracy</p>
              <p>• Validate models across environments before deployment</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

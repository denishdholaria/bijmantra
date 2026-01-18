/**
 * Phenomic Selection Page
 * High-throughput phenotyping and phenomic prediction
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Scan, Database, Cpu, Activity, Waves, Target, Zap, FlaskConical } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

export function PhenomicSelection() {
  const [activeTab, setActiveTab] = useState('datasets')
  const [selectedCrop, setSelectedCrop] = useState('all')
  const [selectedPlatform, setSelectedPlatform] = useState('all')

  // Fetch datasets
  const { data: datasets = [], isLoading: loadingDatasets } = useQuery({
    queryKey: ['phenomic-datasets', selectedCrop, selectedPlatform],
    queryFn: () => apiClient.getPhenomicDatasets({
      crop: selectedCrop !== 'all' ? selectedCrop : undefined,
      platform: selectedPlatform !== 'all' ? selectedPlatform : undefined
    })
  })

  // Fetch models
  const { data: models = [], isLoading: loadingModels } = useQuery({
    queryKey: ['phenomic-models'],
    queryFn: () => apiClient.getPhenomicModels()
  })

  // Fetch statistics
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['phenomic-statistics'],
    queryFn: () => apiClient.getPhenomicStatistics()
  })

  const getAccuracyColor = (acc: number) => {
    if (acc >= 0.85) return 'text-green-600'
    if (acc >= 0.75) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getPlatformIcon = (platform: string) => {
    switch (platform?.toLowerCase()) {
      case 'nirs': return <Waves className="h-5 w-5" />
      case 'hyperspectral': return <Activity className="h-5 w-5" />
      case 'thermal': return <Target className="h-5 w-5" />
      default: return <Scan className="h-5 w-5" />
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Scan className="h-7 w-7 text-primary" />
            Phenomic Selection
          </h1>
          <p className="text-muted-foreground mt-1">High-throughput phenotyping and prediction</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedCrop} onValueChange={setSelectedCrop}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Crop" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Crops</SelectItem>
              <SelectItem value="rice">Rice</SelectItem>
              <SelectItem value="wheat">Wheat</SelectItem>
              <SelectItem value="maize">Maize</SelectItem>
            </SelectContent>
          </Select>
          <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Platform" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Platforms</SelectItem>
              <SelectItem value="nirs">NIRS</SelectItem>
              <SelectItem value="hyperspectral">Hyperspectral</SelectItem>
              <SelectItem value="thermal">Thermal</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Database className="h-5 w-5 text-primary" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.total_datasets || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Datasets</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Cpu className="h-5 w-5 text-green-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.deployed_models || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Deployed Models</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <FlaskConical className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.total_samples?.toLocaleString() || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Total Samples</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Zap className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{((stats?.avg_accuracy || 0) * 100).toFixed(0)}%</p>
                )}
                <p className="text-xs text-muted-foreground">Avg Accuracy</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="datasets">Datasets</TabsTrigger>
          <TabsTrigger value="models">Prediction Models</TabsTrigger>
          <TabsTrigger value="platforms">Platforms</TabsTrigger>
        </TabsList>

        <TabsContent value="datasets" className="space-y-6 mt-4">
          {loadingDatasets ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full" />)}
            </div>
          ) : datasets.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No datasets found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {datasets.map((dataset: any) => (
                <Card key={dataset.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          {getPlatformIcon(dataset.platform)}
                        </div>
                        <div>
                          <h3 className="font-bold">{dataset.name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {dataset.crop} • {dataset.platform}
                          </p>
                        </div>
                      </div>
                      <Badge variant={dataset.status === 'active' ? 'default' : 'secondary'}>
                        {dataset.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Samples</p>
                        <p className="font-bold">{dataset.samples?.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Wavelengths</p>
                        <p className="font-bold">{dataset.wavelengths?.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Accuracy</p>
                        <p className={`font-bold ${getAccuracyColor(dataset.accuracy)}`}>
                          {(dataset.accuracy * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Created</p>
                        <p className="font-bold">{dataset.created_at}</p>
                      </div>
                    </div>
                    {dataset.traits_predicted && (
                      <div className="mt-3">
                        <p className="text-xs text-muted-foreground mb-1">Predicted Traits:</p>
                        <div className="flex flex-wrap gap-1">
                          {dataset.traits_predicted.map((trait: string) => (
                            <Badge key={trait} variant="outline" className="text-xs">{trait}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="models" className="space-y-6 mt-4">
          {loadingModels ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full" />)}
            </div>
          ) : models.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Cpu className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No models found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {models.map((model: any) => (
                <Card key={model.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-bold">{model.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {model.target_trait} • {model.type}
                        </p>
                      </div>
                      <Badge className={
                        model.status === 'deployed' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-yellow-100 text-yellow-700'
                      }>
                        {model.status === 'deployed' ? '✓ Deployed' : '⏳ Training'}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm mb-3">
                      <div>
                        <p className="text-muted-foreground">R²</p>
                        <p className={`font-bold ${getAccuracyColor(model.r_squared || 0)}`}>
                          {(model.r_squared || 0).toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">RMSE</p>
                        <p className="font-bold">{(model.rmse || 0).toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Components</p>
                        <p className="font-bold">{model.components || model.n_estimators || '-'}</p>
                      </div>
                    </div>
                    <Progress value={(model.r_squared || 0) * 100} className="h-2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="platforms" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { 
                name: 'NIRS (Near-Infrared)', 
                icon: <Waves className="h-6 w-6" />,
                description: 'Non-destructive analysis of grain quality',
                wavelengths: '780-2500 nm',
                traits: ['Protein', 'Amylose', 'Moisture', 'Oil'],
                throughput: '100 samples/hour'
              },
              { 
                name: 'Hyperspectral Imaging', 
                icon: <Activity className="h-6 w-6" />,
                description: 'Detailed spectral analysis across visible-NIR',
                wavelengths: '400-2500 nm',
                traits: ['Yield', 'Biomass', 'Chlorophyll', 'Water Content'],
                throughput: '50 ha/day'
              },
              { 
                name: 'Thermal Imaging', 
                icon: <Target className="h-6 w-6" />,
                description: 'Canopy temperature for stress detection',
                wavelengths: 'LWIR (8-14 μm)',
                traits: ['Drought Tolerance', 'Heat Stress', 'Stomatal Conductance'],
                throughput: '30 ha/day'
              },
              { 
                name: 'RGB Imaging', 
                icon: <Scan className="h-6 w-6" />,
                description: 'High-resolution visible light imaging',
                wavelengths: '400-700 nm',
                traits: ['Canopy Cover', 'Plant Count', 'Senescence'],
                throughput: '100 ha/day'
              },
            ].map((platform) => (
              <Card key={platform.name}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      {platform.icon}
                    </div>
                    {platform.name}
                  </CardTitle>
                  <CardDescription>{platform.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Wavelengths</span>
                      <span className="font-medium">{platform.wavelengths}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Throughput</span>
                      <span className="font-medium">{platform.throughput}</span>
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
      </Tabs>
    </div>
  )
}

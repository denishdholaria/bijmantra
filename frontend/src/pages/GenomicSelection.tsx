/**
 * Genomic Selection Page
 * GS model training, prediction, and selection tools
 * Connected to /api/v2/genomic-selection endpoints
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient, GSModel, GEBVPrediction, GSMethod, GSSummary } from '@/lib/api-client';

export function GenomicSelection() {
  const [activeTab, setActiveTab] = useState('models');
  const [selectedModel, setSelectedModel] = useState('gs1');

  // Fetch models
  const { data: modelsData, isLoading: loadingModels } = useQuery({
    queryKey: ['genomic-selection', 'models'],
    queryFn: () => apiClient.genomicSelectionService.getModels(),
  });

  // Fetch predictions for selected model
  const { data: predictionsData, isLoading: loadingPredictions } = useQuery({
    queryKey: ['genomic-selection', 'predictions', selectedModel],
    queryFn: () => apiClient.genomicSelectionService.getPredictions(selectedModel),
    enabled: !!selectedModel,
  });

  // Fetch summary
  const { data: summaryData } = useQuery({
    queryKey: ['genomic-selection', 'summary'],
    queryFn: () => apiClient.genomicSelectionService.getSummary(),
  });

  // Fetch methods
  const { data: methodsData } = useQuery({
    queryKey: ['genomic-selection', 'methods'],
    queryFn: () => apiClient.genomicSelectionService.getMethods(),
  });

  const models: GSModel[] = modelsData?.models || [];
  const predictions: GEBVPrediction[] = predictionsData?.predictions || [];
  const methods: GSMethod[] = methodsData?.methods || [];
  const summary: GSSummary | undefined = summaryData;


  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genomic Selection</h1>
          <p className="text-muted-foreground mt-1">GS model training and GEBV prediction</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              {models.map((m: any) => (
                <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button>Train New Model</Button>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-primary">{summary.trained_models}</p>
              <p className="text-xs text-muted-foreground">Trained Models</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-blue-600">{summary.average_accuracy}</p>
              <p className="text-xs text-muted-foreground">Avg Accuracy</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-green-600">{summary.total_predictions}</p>
              <p className="text-xs text-muted-foreground">Predictions</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-purple-600">{summary.selected_candidates}</p>
              <p className="text-xs text-muted-foreground">Selected</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-orange-600">{summary.traits_covered?.length || 0}</p>
              <p className="text-xs text-muted-foreground">Traits</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          <TabsTrigger value="selection">Selection</TabsTrigger>
          <TabsTrigger value="methods">Methods</TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>GS Models</CardTitle>
              <CardDescription>Trained genomic selection models</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingModels ? <Skeleton className="h-48 w-full" /> : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Model Name</th>
                        <th className="text-left p-3">Method</th>
                        <th className="text-left p-3">Trait</th>
                        <th className="text-right p-3">Accuracy</th>
                        <th className="text-right p-3">h²</th>
                        <th className="text-right p-3">Markers</th>
                        <th className="text-center p-3">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {models.map((model: any) => (
                        <tr key={model.id} className="border-b hover:bg-muted/50 cursor-pointer" onClick={() => setSelectedModel(model.id)}>
                          <td className="p-3 font-medium">{model.name}</td>
                          <td className="p-3"><Badge variant="outline">{model.method}</Badge></td>
                          <td className="p-3">{model.trait}</td>
                          <td className="p-3 text-right">
                            <span className={`font-bold ${model.accuracy >= 0.7 ? 'text-green-600' : model.accuracy >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                              {model.accuracy.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-3 text-right font-mono">{model.heritability.toFixed(2)}</td>
                          <td className="p-3 text-right">{model.markers.toLocaleString()}</td>
                          <td className="p-3 text-center">
                            <Badge className={model.status === 'trained' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>
                              {model.status}
                            </Badge>
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

        <TabsContent value="predictions" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>GEBV Predictions</CardTitle>
              <CardDescription>Genomic estimated breeding values for candidates</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingPredictions ? <Skeleton className="h-48 w-full" /> : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-center p-3">Rank</th>
                        <th className="text-left p-3">Germplasm</th>
                        <th className="text-right p-3">GEBV</th>
                        <th className="text-right p-3">Reliability</th>
                        <th className="text-center p-3">Selected</th>
                      </tr>
                    </thead>
                    <tbody>
                      {predictions.map((pred: any) => (
                        <tr key={pred.germplasm_id} className={`border-b hover:bg-muted/50 ${pred.selected ? 'bg-green-50' : ''}`}>
                          <td className="p-3 text-center font-bold">{pred.rank}</td>
                          <td className="p-3 font-medium">{pred.germplasm_name}</td>
                          <td className="p-3 text-right">
                            <span className={`font-bold ${pred.gebv >= 2 ? 'text-green-600' : pred.gebv >= 1 ? 'text-yellow-600' : 'text-muted-foreground'}`}>
                              {pred.gebv.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Progress value={pred.reliability * 100} className="w-16 h-2" />
                              <span className="text-xs">{(pred.reliability * 100).toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className="p-3 text-center">
                            {pred.selected ? <Badge className="bg-green-100 text-green-700">Yes</Badge> : <Badge variant="outline">No</Badge>}
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

        <TabsContent value="selection" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Selection Response</CardTitle>
              <CardDescription>Expected genetic gain from selection</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-3xl font-bold text-primary">1.89</p>
                  <p className="text-sm text-muted-foreground">Expected Response</p>
                  <p className="text-xs text-muted-foreground mt-1">R = i × r × σg</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-3xl font-bold text-green-600">37.8%</p>
                  <p className="text-sm text-muted-foreground">Response %</p>
                  <p className="text-xs text-muted-foreground mt-1">Relative to mean</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-3xl font-bold text-blue-600">1.755</p>
                  <p className="text-sm text-muted-foreground">Selection Differential</p>
                  <p className="text-xs text-muted-foreground mt-1">Top 10% selected</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="methods" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>GS Methods</CardTitle>
              <CardDescription>Available genomic selection methods</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(methods.length > 0 ? methods : [
                  { id: 'gblup', name: 'GBLUP', description: 'Genomic Best Linear Unbiased Prediction' },
                  { id: 'bayesb', name: 'BayesB', description: 'Bayesian regression with mixture prior' },
                  { id: 'rkhs', name: 'RKHS', description: 'Reproducing Kernel Hilbert Space' },
                  { id: 'rf', name: 'Random Forest', description: 'Machine learning ensemble method' },
                ]).map((method: any) => (
                  <div key={method.id} className="p-4 border rounded-lg">
                    <h4 className="font-bold">{method.name}</h4>
                    <p className="text-sm text-muted-foreground">{method.description}</p>
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

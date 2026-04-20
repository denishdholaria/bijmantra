/**
 * Plant Vision Page
 * AI-powered disease detection and growth stage analysis
 * Connected to /api/v2/vision/* API
 */
import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Camera, Leaf, Bug, History, Settings, Microscope, Sprout, AlertTriangle, TrendingUp, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PlantVisionAnalyzer } from '@/components/camera/PlantVisionAnalyzer';
import { apiClient } from '@/lib/api-client';
import type { DiseaseRecord } from '@/lib/api/ai/disease';
import type { VisionCrop, VisionDatasetSummary, VisionModelSummary } from '@/lib/api/ai/vision';

interface AnalysisHistory {
  id: string;
  timestamp: string;
  cropType: string;
  imageUrl: string;
  results: Array<{
    type: string;
    label: string;
    confidence: number;
    severity?: string;
  }>;
}

interface CropInfo {
  code: string;
  name: string;
  icon: string;
  diseases: number;
  stages: number;
}

interface VisionStats {
  supportedCrops: number;
  publishedDatasets: number;
  readyModels: number;
  totalImages: number;
}

// Fetch supported crops from API
async function fetchCrops(): Promise<CropInfo[]> {
  const response = await apiClient.visionService.getCrops();
  return response.crops || [];
}

async function fetchVisionOperationalData(): Promise<{
  crops: VisionCrop[];
  models: VisionModelSummary[];
  datasets: VisionDatasetSummary[];
}> {
  const [cropsRes, modelsRes, datasetsRes] = await Promise.all([
    apiClient.visionService.getCrops(),
    apiClient.visionService.getModels(),
    apiClient.visionService.getDatasets(),
  ]);

  return {
    crops: cropsRes.crops || [],
    models: modelsRes.models || [],
    datasets: datasetsRes.datasets || [],
  };
}

// Fetch diseases from disease API
async function fetchDiseases(crop: string): Promise<DiseaseRecord[]> {
  const response = await apiClient.diseaseService.getDiseases({ crop });
  return response.diseases || [];
}

export function PlantVision() {
  const [selectedCrop, setSelectedCrop] = useState('');
  const [history, setHistory] = useState<AnalysisHistory[]>([]);

  const {
    data: operationalData,
    isLoading: operationalDataLoading,
    isError: operationalDataError,
  } = useQuery({
    queryKey: ['vision-operational-data'],
    queryFn: fetchVisionOperationalData,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const crops = operationalData?.crops || [];

  useEffect(() => {
    if (crops.length === 0) {
      return;
    }

    const cropStillExists = crops.some((crop) => crop.code === selectedCrop);
    if (!selectedCrop || !cropStillExists) {
      setSelectedCrop(crops[0].code);
    }
  }, [crops, selectedCrop]);

  const stats: VisionStats = useMemo(() => {
    const models = operationalData?.models || [];
    const datasets = operationalData?.datasets || [];
    return {
      supportedCrops: crops.length,
      publishedDatasets: datasets.length,
      readyModels: models.filter((model) => model.status === 'ready' || model.status === 'deployed').length,
      totalImages: datasets.reduce((sum, dataset) => sum + (dataset.total_images || 0), 0),
    };
  }, [crops, operationalData]);

  const selectedCropInfo = useMemo(
    () => crops.find((crop) => crop.code === selectedCrop) ?? null,
    [crops, selectedCrop],
  );

  // Fetch diseases for selected crop
  const { data: diseases = [], isLoading: diseasesLoading, isError: diseasesError } = useQuery({
    queryKey: ['crop-diseases', selectedCrop],
    queryFn: () => fetchDiseases(selectedCrop),
    enabled: Boolean(selectedCrop),
    staleTime: 1000 * 60 * 30, // 30 minutes
  });

  const handleAnalysisComplete = (results: Array<{ type: string; label: string; confidence: number; severity?: string }>, imageData: string) => {
    const newEntry: AnalysisHistory = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      cropType: selectedCrop,
      imageUrl: imageData,
      results,
    };
    setHistory([newEntry, ...history]);
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Microscope className="h-6 w-6" />
            Plant Vision
          </h1>
          <p className="text-muted-foreground">
            AI-powered disease detection and growth stage analysis
          </p>
        </div>
        <Select value={selectedCrop} onValueChange={setSelectedCrop} disabled={operationalDataLoading || crops.length === 0}>
          <SelectTrigger className="w-40" aria-label="Select crop">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {crops.map((crop) => (
              <SelectItem key={crop.code} value={crop.code}>
                <span className="flex items-center gap-2">
                  <span>{crop.icon}</span>
                  <span>{crop.name}</span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {operationalDataError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Plant Vision registry unavailable</AlertTitle>
          <AlertDescription>
            Crop, dataset, and model metadata could not be loaded from the backend. This page no longer injects fallback catalog data when the live service is unavailable.
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <Camera className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                {operationalDataLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <p className="text-2xl font-bold">{stats.supportedCrops}</p>
                )}
                <p className="text-xs text-muted-foreground">Supported Crops</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
                <Bug className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                {operationalDataLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <p className="text-2xl font-bold">{stats.publishedDatasets}</p>
                )}
                <p className="text-xs text-muted-foreground">Vision Datasets</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <Leaf className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                {operationalDataLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <p className="text-2xl font-bold">{stats.readyModels}</p>
                )}
                <p className="text-xs text-muted-foreground">Ready Models</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <TrendingUp className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                {operationalDataLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <p className="text-2xl font-bold">{stats.totalImages}</p>
                )}
                <p className="text-xs text-muted-foreground">Catalogued Images</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Analyzer */}
        {selectedCrop ? (
          <PlantVisionAnalyzer
            cropType={selectedCrop}
            onAnalysisComplete={handleAnalysisComplete}
          />
        ) : (
          <Card>
            <CardContent className="p-6 text-center text-muted-foreground">
              <Microscope className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No crop is available for inference yet</p>
              <p className="text-sm">Publish crop metadata through the vision service to enable live analysis.</p>
            </CardContent>
          </Card>
        )}

        {/* History & Info */}
        <div className="space-y-6">
          <Tabs defaultValue="history">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="history">
                <History className="h-4 w-4 mr-2" />
                History
              </TabsTrigger>
              <TabsTrigger value="diseases">
                <Bug className="h-4 w-4 mr-2" />
                Diseases
              </TabsTrigger>
              <TabsTrigger value="stages">
                <Sprout className="h-4 w-4 mr-2" />
                Stages
              </TabsTrigger>
            </TabsList>

            <TabsContent value="history" className="space-y-4">
              {history.length === 0 ? (
                <Card>
                  <CardContent className="p-6 text-center text-muted-foreground">
                    <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No analysis history yet</p>
                    <p className="text-sm">Capture or upload an image to get started</p>
                  </CardContent>
                </Card>
              ) : (
                history.slice(0, 5).map((entry) => (
                  <Card key={entry.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="font-medium capitalize">{entry.cropType}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(entry.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <Badge variant="outline">{entry.results.length} findings</Badge>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {entry.results.map((result, i) => (
                          <Badge key={i} variant={getSeverityColor(result.severity)}>
                            {result.label}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </TabsContent>

            <TabsContent value="diseases" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Common Diseases</CardTitle>
                  <CardDescription>Diseases detectable for {selectedCrop}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {diseasesLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                  ) : diseases.length > 0 ? (
                    diseases.map((disease) => (
                      <DiseaseItem 
                        key={disease.id || disease.name} 
                        name={disease.name} 
                        pathogen={disease.pathogen} 
                        severity={disease.severity || 'medium'} 
                      />
                    ))
                  ) : (
                    <EmptyTabState
                      title={diseasesError ? 'Disease catalog unavailable' : 'No disease catalog entries published'}
                      description={diseasesError
                        ? 'The disease catalog could not be loaded for this crop.'
                        : `No disease records are currently published for ${selectedCropInfo?.name || selectedCrop}.`
                      }
                    />
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="stages" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Growth Stages (BBCH Scale)</CardTitle>
                  <CardDescription>Identifiable stages for {selectedCrop}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {selectedCropInfo ? (
                    <div className="rounded-lg bg-muted/50 p-4 space-y-2">
                      <p className="font-medium">{selectedCropInfo.stages} stage groups registered</p>
                      <p className="text-sm text-muted-foreground">
                        The crop registry currently exposes stage counts only. Detailed BBCH descriptors are not yet published through the live API for {selectedCropInfo.name}.
                      </p>
                    </div>
                  ) : (
                    <EmptyTabState
                      title="No stage metadata available"
                      description="Select a published crop to inspect the registered growth-stage coverage."
                    />
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Tips for Best Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-start gap-2">
              <div className="p-1.5 bg-blue-100 dark:bg-blue-900 rounded">
                <Camera className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="font-medium">Good Lighting</p>
                <p className="text-muted-foreground">Natural daylight works best</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="p-1.5 bg-green-100 dark:bg-green-900 rounded">
                <Leaf className="h-4 w-4 text-green-600" />
              </div>
              <div>
                <p className="font-medium">Focus on Symptoms</p>
                <p className="text-muted-foreground">Center affected areas in frame</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="p-1.5 bg-yellow-100 dark:bg-yellow-900 rounded">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
              </div>
              <div>
                <p className="font-medium">Multiple Angles</p>
                <p className="text-muted-foreground">Take several photos if unsure</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="p-1.5 bg-purple-100 dark:bg-purple-900 rounded">
                <Microscope className="h-4 w-4 text-purple-600" />
              </div>
              <div>
                <p className="font-medium">Close-Up Details</p>
                <p className="text-muted-foreground">Capture lesions and spots clearly</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper components
function EmptyTabState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
      <p className="font-medium text-foreground">{title}</p>
      <p className="mt-1">{description}</p>
    </div>
  );
}

function DiseaseItem({ name, pathogen, severity }: { name: string; pathogen: string; severity: string }) {
  return (
    <div className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
      <div>
        <p className="font-medium">{name}</p>
        <p className="text-xs text-muted-foreground italic">{pathogen}</p>
      </div>
      <Badge variant={severity === 'high' ? 'destructive' : severity === 'medium' ? 'secondary' : 'outline'}>
        {severity}
      </Badge>
    </div>
  );
}

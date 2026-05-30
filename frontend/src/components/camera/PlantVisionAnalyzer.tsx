import { useState, useCallback } from 'react';
import { Camera, Leaf, Bug, Thermometer, AlertTriangle, CheckCircle, Loader2, Upload, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { CameraCapture } from './CameraCapture';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api-client';
import type { VisionAnalyzeResponse, VisionPrediction } from '@/lib/api/ai/vision';

interface AnalysisResult {
  type: 'disease' | 'growth_stage' | 'nutrient' | 'pest' | 'stress' | 'trait';
  confidence: number;
  label: string;
  description: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  recommendations?: string[];
}

interface PlantVisionAnalyzerProps {
  onAnalysisComplete?: (results: AnalysisResult[], imageData: string) => void;
  cropType?: string;
  className?: string;
}

const ACCEPTED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
const MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024;

function validateLocalFile(file: File): string | null {
  if (!ACCEPTED_IMAGE_TYPES.has(file.type)) {
    return 'Unsupported file type. Use JPEG, PNG, or WebP.';
  }
  if (file.size > MAX_IMAGE_SIZE_BYTES) {
    return 'Image is larger than the 10 MB upload limit.';
  }
  return null;
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => resolve(event.target?.result as string);
    reader.onerror = () => reject(new Error('Unable to read image file.'));
    reader.readAsDataURL(file);
  });
}

function dataUrlToFile(dataUrl: string, filename: string): File {
  const [header, payload] = dataUrl.split(',');
  const mime = header?.match(/data:(.*?);base64/)?.[1] || 'image/jpeg';
  const binary = window.atob(payload || '');
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new File([bytes], filename, { type: mime });
}

function normalizeSeverity(value?: string): AnalysisResult['severity'] | undefined {
  if (value === 'low' || value === 'medium' || value === 'high' || value === 'critical') {
    return value;
  }
  return undefined;
}

function normalizeType(value?: string): AnalysisResult['type'] {
  if (
    value === 'disease' ||
    value === 'growth_stage' ||
    value === 'nutrient' ||
    value === 'pest' ||
    value === 'stress' ||
    value === 'trait'
  ) {
    return value;
  }
  return 'disease';
}

function normalizePredictions(predictions: VisionPrediction[] | undefined): AnalysisResult[] {
  return (predictions || []).map((prediction, index) => ({
    type: normalizeType(prediction.type),
    confidence: Math.max(0, Math.min(1, prediction.confidence ?? 0)),
    label: prediction.label || `Finding ${index + 1}`,
    description: prediction.description || 'Backend model prediction',
    severity: normalizeSeverity(prediction.severity),
    recommendations: prediction.recommendations || [],
  }));
}

function getAnalysisMessage(response: VisionAnalyzeResponse): string | null {
  if (response.explainability?.message) {
    return response.explainability.message;
  }
  if (response.status === 'runtime_unavailable') {
    return 'Image validated, but no production Plant Vision runtime is deployed for this organization.';
  }
  return null;
}

export function PlantVisionAnalyzer({ onAnalysisComplete, cropType = 'rice', className }: PlantVisionAnalyzerProps) {
  const [showCamera, setShowCamera] = useState(false);
  const [imageData, setImageData] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisMessage, setAnalysisMessage] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [activeTab, setActiveTab] = useState('capture');

  const analyzeFile = useCallback(async (file: File, previewData: string) => {
    const validationError = validateLocalFile(file);
    if (validationError) {
      setLocalError(validationError);
      setIsAnalyzing(false);
      setAnalysisProgress(0);
      return;
    }

    setLocalError(null);
    setAnalysisMessage(null);
    setAnalysisStatus(null);
    setIsAnalyzing(true);
    setAnalysisProgress(15);
    setResults([]);

    try {
      setAnalysisProgress(65);
      const response = await apiClient.visionService.analyzeImage(file, cropType);
      const normalizedResults = normalizePredictions(response.predictions);

      setAnalysisProgress(100);
      setResults(normalizedResults);
      setAnalysisStatus(response.status);
      setAnalysisMessage(getAnalysisMessage(response));
      setActiveTab('results');

      if (normalizedResults.length > 0 && onAnalysisComplete) {
        onAnalysisComplete(normalizedResults, previewData);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Plant Vision analysis failed.';
      setLocalError(message);
      setActiveTab('capture');
    } finally {
      setIsAnalyzing(false);
    }
  }, [cropType, onAnalysisComplete]);

  const handleCapture = (image: string) => {
    try {
      const file = dataUrlToFile(image, `plant-${Date.now()}.jpg`);
      setImageData(image);
      setShowCamera(false);
      void analyzeFile(file, image);
    } catch {
      setLocalError('Captured image could not be prepared for analysis.');
      setShowCamera(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validationError = validateLocalFile(file);
    if (validationError) {
      setLocalError(validationError);
      setImageData(null);
      setResults([]);
      setAnalysisMessage(null);
      setAnalysisStatus(null);
      e.target.value = '';
      return;
    }

    try {
      const image = await readFileAsDataUrl(file);
      setImageData(image);
      void analyzeFile(file, image);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : 'Unable to load image preview.');
    } finally {
      e.target.value = '';
    }
  };

  const clearResults = () => {
    setImageData(null);
    setResults([]);
    setAnalysisMessage(null);
    setAnalysisStatus(null);
    setLocalError(null);
    setAnalysisProgress(0);
    setActiveTab('capture');
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical': return 'bg-destructive';
      case 'high': return 'bg-prakruti-narangi';
      case 'medium': return 'bg-prakruti-sona';
      case 'low': return 'bg-prakruti-patta';
      default: return 'bg-primary';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'disease': return <Bug className="h-4 w-4" />;
      case 'growth_stage': return <Leaf className="h-4 w-4" />;
      case 'nutrient': return <Thermometer className="h-4 w-4" />;
      case 'pest':
      case 'stress': return <AlertTriangle className="h-4 w-4" />;
      default: return <Leaf className="h-4 w-4" />;
    }
  };

  if (showCamera) {
    return (
      <CameraCapture
        onCapture={handleCapture}
        onClose={() => setShowCamera(false)}
        overlay="leaf"
        className={className}
      />
    );
  }

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="h-5 w-5" />
          Plant Vision Analyzer
        </CardTitle>
        <CardDescription>
          Capture or upload plant images for AI-powered disease detection and growth stage analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        {localError && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Analysis unavailable</AlertTitle>
            <AlertDescription>{localError}</AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="capture">Capture</TabsTrigger>
            <TabsTrigger value="results" disabled={!imageData && !analysisMessage && results.length === 0}>
              Results {results.length > 0 && `(${results.length})`}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="capture" className="space-y-4">
            {imageData && !isAnalyzing ? (
              <div className="relative">
                <img src={imageData} alt="Captured" className="w-full rounded-lg" />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={clearResults}
                  className="absolute top-2 right-2 bg-black/50 text-white hover:bg-black/70"
                  aria-label="Clear image"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : isAnalyzing ? (
              <div className="space-y-4 py-8">
                <div className="flex items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
                <Progress value={analysisProgress} className="w-full" />
                <p className="text-center text-sm text-muted-foreground">
                  Analyzing image... {analysisProgress}%
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <Button
                  variant="outline"
                  className="h-32 flex-col gap-2"
                  onClick={() => setShowCamera(true)}
                >
                  <Camera className="h-8 w-8" />
                  <span>Take Photo</span>
                </Button>
                <label className="cursor-pointer">
                  <Button
                    variant="outline"
                    className="h-32 w-full flex-col gap-2"
                    asChild
                  >
                    <div>
                      <Upload className="h-8 w-8" />
                      <span>Upload Image</span>
                    </div>
                  </Button>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
              </div>
            )}
          </TabsContent>

          <TabsContent value="results" className="space-y-4">
            {imageData && (
              <img src={imageData} alt="Analyzed" className="w-full h-48 object-cover rounded-lg" />
            )}

            {analysisMessage && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>{analysisStatus === 'runtime_unavailable' ? 'Runtime unavailable' : 'Analysis status'}</AlertTitle>
                <AlertDescription>{analysisMessage}</AlertDescription>
              </Alert>
            )}

            {results.length === 0 && analysisMessage && (
              <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                No predictions were returned. Plant Vision will only show findings produced by a configured backend model.
              </div>
            )}

            {results.map((result, index) => (
              <Card key={`${result.type}-${result.label}-${index}`} className="overflow-hidden">
                <div className={cn('h-1', getSeverityColor(result.severity))} />
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      {getTypeIcon(result.type)}
                      <span className="font-medium">{result.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {result.severity && (
                        <Badge variant={result.severity === 'high' || result.severity === 'critical' ? 'destructive' : 'secondary'}>
                          {result.severity}
                        </Badge>
                      )}
                      <Badge variant="outline">
                        {Math.round(result.confidence * 100)}% confidence
                      </Badge>
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground">{result.description}</p>

                  {result.recommendations && result.recommendations.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Recommendations:</p>
                      <ul className="text-sm space-y-1">
                        {result.recommendations.map((rec, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}

            {(results.length > 0 || imageData) && (
              <Button variant="outline" onClick={clearResults} className="w-full">
                Analyze Another Image
              </Button>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

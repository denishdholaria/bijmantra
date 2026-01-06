import { useState, useCallback } from 'react';
import { Camera, Leaf, Bug, Thermometer, AlertTriangle, CheckCircle, Loader2, Upload, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CameraCapture } from './CameraCapture';
import { cn } from '@/lib/utils';

interface AnalysisResult {
  type: 'disease' | 'growth_stage' | 'nutrient' | 'pest';
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

// Demo analysis results (simulated ML inference)
const DEMO_DISEASES: Record<string, AnalysisResult[]> = {
  rice: [
    { type: 'disease', confidence: 0.89, label: 'Bacterial Leaf Blight', description: 'Xanthomonas oryzae infection detected', severity: 'high', recommendations: ['Apply copper-based bactericide', 'Improve field drainage', 'Use resistant varieties like Xa21'] },
    { type: 'disease', confidence: 0.72, label: 'Rice Blast', description: 'Magnaporthe oryzae fungal infection', severity: 'medium', recommendations: ['Apply tricyclazole fungicide', 'Reduce nitrogen fertilization', 'Consider Pi-ta resistant varieties'] },
  ],
  wheat: [
    { type: 'disease', confidence: 0.85, label: 'Stem Rust', description: 'Puccinia graminis infection detected', severity: 'high', recommendations: ['Apply propiconazole fungicide', 'Plant Sr31 resistant varieties', 'Monitor neighboring fields'] },
    { type: 'disease', confidence: 0.68, label: 'Powdery Mildew', description: 'Blumeria graminis infection', severity: 'low', recommendations: ['Apply sulfur-based fungicide', 'Improve air circulation', 'Reduce plant density'] },
  ],
  maize: [
    { type: 'disease', confidence: 0.91, label: 'Northern Corn Leaf Blight', description: 'Exserohilum turcicum infection', severity: 'medium', recommendations: ['Apply strobilurin fungicide', 'Use Ht1 resistant hybrids', 'Rotate crops'] },
  ],
};

const GROWTH_STAGES: Record<string, AnalysisResult[]> = {
  rice: [
    { type: 'growth_stage', confidence: 0.94, label: 'Tillering (BBCH 21-29)', description: 'Active tiller formation stage', recommendations: ['Apply nitrogen top-dressing', 'Maintain 5cm water level', 'Scout for stem borers'] },
  ],
  wheat: [
    { type: 'growth_stage', confidence: 0.88, label: 'Heading (BBCH 51-59)', description: 'Ear emergence stage', recommendations: ['Apply fungicide if needed', 'Monitor for aphids', 'Avoid water stress'] },
  ],
  maize: [
    { type: 'growth_stage', confidence: 0.92, label: 'V6 - Six Leaf Stage', description: 'Vegetative growth phase', recommendations: ['Side-dress nitrogen', 'Scout for corn borers', 'Check for nutrient deficiencies'] },
  ],
};

const NUTRIENT_DEFICIENCIES: AnalysisResult[] = [
  { type: 'nutrient', confidence: 0.78, label: 'Nitrogen Deficiency', description: 'Yellowing of older leaves (chlorosis)', severity: 'medium', recommendations: ['Apply urea or ammonium sulfate', 'Split nitrogen applications', 'Check soil pH'] },
  { type: 'nutrient', confidence: 0.65, label: 'Potassium Deficiency', description: 'Leaf margin necrosis detected', severity: 'low', recommendations: ['Apply potassium chloride', 'Improve soil drainage', 'Test soil K levels'] },
];

export function PlantVisionAnalyzer({ onAnalysisComplete, cropType = 'rice', className }: PlantVisionAnalyzerProps) {
  const [showCamera, setShowCamera] = useState(false);
  const [imageData, setImageData] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [activeTab, setActiveTab] = useState('capture');


  // Simulate ML analysis (in production, this would call TensorFlow.js or backend API)
  const analyzeImage = useCallback(async (image: string) => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setResults([]);

    // Simulate progressive analysis
    const stages = [
      { progress: 20, delay: 300, message: 'Preprocessing image...' },
      { progress: 40, delay: 500, message: 'Detecting plant regions...' },
      { progress: 60, delay: 400, message: 'Analyzing disease symptoms...' },
      { progress: 80, delay: 300, message: 'Identifying growth stage...' },
      { progress: 100, delay: 200, message: 'Generating recommendations...' },
    ];

    for (const stage of stages) {
      await new Promise(resolve => setTimeout(resolve, stage.delay));
      setAnalysisProgress(stage.progress);
    }

    // Generate demo results based on crop type
    const diseases = DEMO_DISEASES[cropType] || DEMO_DISEASES.rice;
    const growthStage = GROWTH_STAGES[cropType] || GROWTH_STAGES.rice;
    
    // Randomly select results to simulate real detection
    const detectedResults: AnalysisResult[] = [];
    
    // Always include growth stage
    detectedResults.push(growthStage[0]);
    
    // Randomly include disease (70% chance)
    if (Math.random() > 0.3) {
      detectedResults.push(diseases[Math.floor(Math.random() * diseases.length)]);
    }
    
    // Randomly include nutrient deficiency (40% chance)
    if (Math.random() > 0.6) {
      detectedResults.push(NUTRIENT_DEFICIENCIES[Math.floor(Math.random() * NUTRIENT_DEFICIENCIES.length)]);
    }

    setResults(detectedResults);
    setIsAnalyzing(false);
    setActiveTab('results');

    if (onAnalysisComplete) {
      onAnalysisComplete(detectedResults, image);
    }
  }, [cropType, onAnalysisComplete]);

  // Handle image capture
  const handleCapture = (image: string) => {
    setImageData(image);
    setShowCamera(false);
    analyzeImage(image);
  };

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const image = event.target?.result as string;
      setImageData(image);
      analyzeImage(image);
    };
    reader.readAsDataURL(file);
  };

  // Clear results
  const clearResults = () => {
    setImageData(null);
    setResults([]);
    setActiveTab('capture');
  };

  // Get severity color
  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-blue-500';
    }
  };

  // Get type icon
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'disease': return <Bug className="h-4 w-4" />;
      case 'growth_stage': return <Leaf className="h-4 w-4" />;
      case 'nutrient': return <Thermometer className="h-4 w-4" />;
      case 'pest': return <AlertTriangle className="h-4 w-4" />;
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
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="capture">Capture</TabsTrigger>
            <TabsTrigger value="results" disabled={results.length === 0}>
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
                    accept="image/*"
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

            {results.map((result, index) => (
              <Card key={index} className="overflow-hidden">
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

            {results.length > 0 && (
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

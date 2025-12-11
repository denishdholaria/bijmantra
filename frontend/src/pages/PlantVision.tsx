import { useState } from 'react';
import { Camera, Leaf, Bug, History, Settings, Microscope, Sprout, AlertTriangle, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PlantVisionAnalyzer } from '@/components/camera/PlantVisionAnalyzer';

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

// Demo history data
const DEMO_HISTORY: AnalysisHistory[] = [
  {
    id: '1',
    timestamp: '2025-12-11T10:30:00Z',
    cropType: 'rice',
    imageUrl: '',
    results: [
      { type: 'disease', label: 'Bacterial Leaf Blight', confidence: 0.89, severity: 'high' },
      { type: 'growth_stage', label: 'Tillering (BBCH 21-29)', confidence: 0.94 },
    ],
  },
  {
    id: '2',
    timestamp: '2025-12-10T14:15:00Z',
    cropType: 'wheat',
    imageUrl: '',
    results: [
      { type: 'growth_stage', label: 'Heading (BBCH 51-59)', confidence: 0.88 },
      { type: 'nutrient', label: 'Nitrogen Deficiency', confidence: 0.72, severity: 'medium' },
    ],
  },
  {
    id: '3',
    timestamp: '2025-12-09T09:45:00Z',
    cropType: 'maize',
    imageUrl: '',
    results: [
      { type: 'disease', label: 'Northern Corn Leaf Blight', confidence: 0.91, severity: 'medium' },
    ],
  },
];

// Stats data
const STATS = {
  totalScans: 156,
  diseasesDetected: 42,
  healthyPlants: 98,
  accuracyRate: 94.2,
};

// Supported crops
const CROPS = [
  { value: 'rice', label: 'Rice', icon: '🌾' },
  { value: 'wheat', label: 'Wheat', icon: '🌾' },
  { value: 'maize', label: 'Maize', icon: '🌽' },
  { value: 'soybean', label: 'Soybean', icon: '🫘' },
  { value: 'cotton', label: 'Cotton', icon: '☁️' },
  { value: 'tomato', label: 'Tomato', icon: '🍅' },
  { value: 'potato', label: 'Potato', icon: '🥔' },
];

export function PlantVision() {
  const [selectedCrop, setSelectedCrop] = useState('rice');
  const [history, setHistory] = useState<AnalysisHistory[]>(DEMO_HISTORY);

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
        <Select value={selectedCrop} onValueChange={setSelectedCrop}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CROPS.map((crop) => (
              <SelectItem key={crop.value} value={crop.value}>
                <span className="flex items-center gap-2">
                  <span>{crop.icon}</span>
                  <span>{crop.label}</span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <Camera className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{STATS.totalScans}</p>
                <p className="text-xs text-muted-foreground">Total Scans</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                <Bug className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{STATS.diseasesDetected}</p>
                <p className="text-xs text-muted-foreground">Diseases Found</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <Leaf className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{STATS.healthyPlants}</p>
                <p className="text-xs text-muted-foreground">Healthy Plants</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <TrendingUp className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{STATS.accuracyRate}%</p>
                <p className="text-xs text-muted-foreground">Accuracy Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>


      {/* Main Content */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Analyzer */}
        <PlantVisionAnalyzer
          cropType={selectedCrop}
          onAnalysisComplete={handleAnalysisComplete}
        />

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
                  {selectedCrop === 'rice' && (
                    <>
                      <DiseaseItem name="Bacterial Leaf Blight" pathogen="Xanthomonas oryzae" severity="high" />
                      <DiseaseItem name="Rice Blast" pathogen="Magnaporthe oryzae" severity="high" />
                      <DiseaseItem name="Sheath Blight" pathogen="Rhizoctonia solani" severity="medium" />
                      <DiseaseItem name="Brown Spot" pathogen="Bipolaris oryzae" severity="low" />
                    </>
                  )}
                  {selectedCrop === 'wheat' && (
                    <>
                      <DiseaseItem name="Stem Rust" pathogen="Puccinia graminis" severity="high" />
                      <DiseaseItem name="Leaf Rust" pathogen="Puccinia triticina" severity="medium" />
                      <DiseaseItem name="Powdery Mildew" pathogen="Blumeria graminis" severity="low" />
                      <DiseaseItem name="Septoria" pathogen="Septoria tritici" severity="medium" />
                    </>
                  )}
                  {selectedCrop === 'maize' && (
                    <>
                      <DiseaseItem name="Northern Corn Leaf Blight" pathogen="Exserohilum turcicum" severity="high" />
                      <DiseaseItem name="Gray Leaf Spot" pathogen="Cercospora zeae-maydis" severity="medium" />
                      <DiseaseItem name="Common Rust" pathogen="Puccinia sorghi" severity="low" />
                    </>
                  )}
                  {!['rice', 'wheat', 'maize'].includes(selectedCrop) && (
                    <p className="text-muted-foreground text-sm">
                      Disease database for {selectedCrop} coming soon
                    </p>
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
                  {selectedCrop === 'rice' && (
                    <>
                      <StageItem code="00-09" name="Germination" description="Seed imbibition to coleoptile emergence" />
                      <StageItem code="10-19" name="Seedling" description="First leaf to 9 leaves unfolded" />
                      <StageItem code="21-29" name="Tillering" description="Beginning to maximum tillering" />
                      <StageItem code="30-39" name="Stem Elongation" description="Panicle initiation to booting" />
                      <StageItem code="51-59" name="Heading" description="Panicle emergence" />
                      <StageItem code="61-69" name="Flowering" description="Anthesis" />
                      <StageItem code="71-89" name="Grain Filling" description="Milk to hard dough" />
                      <StageItem code="92-99" name="Maturity" description="Ripening to harvest" />
                    </>
                  )}
                  {selectedCrop === 'wheat' && (
                    <>
                      <StageItem code="00-09" name="Germination" description="Dry seed to emergence" />
                      <StageItem code="10-19" name="Leaf Development" description="First to 9+ leaves" />
                      <StageItem code="21-29" name="Tillering" description="Main shoot and tillers" />
                      <StageItem code="30-39" name="Stem Elongation" description="Node development" />
                      <StageItem code="41-49" name="Booting" description="Flag leaf to boot swollen" />
                      <StageItem code="51-59" name="Heading" description="Ear emergence" />
                      <StageItem code="61-69" name="Flowering" description="Anthesis" />
                      <StageItem code="71-89" name="Grain Development" description="Milk to hard dough" />
                    </>
                  )}
                  {selectedCrop === 'maize' && (
                    <>
                      <StageItem code="VE" name="Emergence" description="Coleoptile visible" />
                      <StageItem code="V1-V6" name="Early Vegetative" description="1-6 leaves with collar" />
                      <StageItem code="V7-V12" name="Mid Vegetative" description="Rapid growth phase" />
                      <StageItem code="VT" name="Tasseling" description="Tassel fully visible" />
                      <StageItem code="R1" name="Silking" description="Silks visible" />
                      <StageItem code="R2-R4" name="Grain Fill" description="Blister to dough" />
                      <StageItem code="R5-R6" name="Maturity" description="Dent to black layer" />
                    </>
                  )}
                  {!['rice', 'wheat', 'maize'].includes(selectedCrop) && (
                    <p className="text-muted-foreground text-sm">
                      Growth stage data for {selectedCrop} coming soon
                    </p>
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

function StageItem({ code, name, description }: { code: string; name: string; description: string }) {
  return (
    <div className="flex items-center gap-3 p-2 rounded-lg bg-muted/50">
      <Badge variant="outline" className="font-mono">{code}</Badge>
      <div>
        <p className="font-medium">{name}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

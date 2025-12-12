/**
 * Plant Vision Strategy Page
 * 
 * Explains the multi-tier approach to plant disease detection
 * and provides access to available detection methods.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Eye,
  Brain,
  Cloud,
  Users,
  Microscope,
  Lightbulb,
  Upload,
  ExternalLink,
  CheckCircle,
  Clock,
  Beaker,
  Leaf,
  AlertTriangle,
  Info,
} from 'lucide-react';

interface DetectionMethod {
  id: string;
  name: string;
  tier: number;
  status: 'available' | 'coming_soon' | 'research';
  accuracy: string;
  coverage: string;
  description: string;
  pros: string[];
  cons: string[];
}

const DETECTION_METHODS: DetectionMethod[] = [
  {
    id: 'heuristic',
    name: 'Color Heuristics',
    tier: 0,
    status: 'available',
    accuracy: '40-60%',
    coverage: 'Basic symptoms only',
    description: 'Simple color-based detection for obvious symptoms like yellowing, browning, or spots.',
    pros: ['Works offline', 'No API costs', 'Instant results'],
    cons: ['Low accuracy', 'Many false positives', 'Cannot identify specific diseases'],
  },
  {
    id: 'external_api',
    name: 'External AI APIs',
    tier: 1,
    status: 'available',
    accuracy: '70-85%',
    coverage: '~50 crops, ~100 diseases',
    description: 'Integration with PlantNet, Plant.id, or Google Cloud Vision for disease identification.',
    pros: ['Good accuracy', 'No training needed', 'Broad coverage'],
    cons: ['Requires internet', 'API costs', 'Limited to their training data'],
  },

  {
    id: 'transfer_learning',
    name: 'Transfer Learning Models',
    tier: 2,
    status: 'coming_soon',
    accuracy: '80-92%',
    coverage: '10 priority crops',
    description: 'Fine-tuned models for priority crops using MobileNet/EfficientNet base with public datasets.',
    pros: ['High accuracy for target crops', 'Works offline once downloaded', 'Customizable'],
    cons: ['Limited crop coverage', 'Requires training data', 'Model size ~20-50MB'],
  },
  {
    id: 'community',
    name: 'Community-Trained Models',
    tier: 3,
    status: 'coming_soon',
    accuracy: '85-95%',
    coverage: 'User-contributed crops',
    description: 'Models trained on user-contributed images with expert verification.',
    pros: ['Covers regional varieties', 'Continuously improving', 'Community ownership'],
    cons: ['Requires critical mass of data', 'Quality depends on contributions', 'Verification overhead'],
  },
  {
    id: 'few_shot',
    name: 'Few-Shot Learning',
    tier: 4,
    status: 'research',
    accuracy: '60-80%',
    coverage: 'Any disease with 5-10 examples',
    description: 'Experimental approach to identify new diseases with minimal training examples.',
    pros: ['Rapid adaptation', 'Handles rare diseases', 'Scalable to new crops'],
    cons: ['Research stage', 'Lower accuracy', 'Requires careful validation'],
  },
  {
    id: 'symptom_decomposition',
    name: 'Symptom Decomposition',
    tier: 4,
    status: 'research',
    accuracy: 'Variable',
    coverage: 'Universal symptoms',
    description: 'Detect visual symptoms (chlorosis, necrosis, lesions) rather than specific diseases.',
    pros: ['Generalizes across crops', 'Interpretable', 'Aids diagnosis'],
    cons: ['Cannot name specific disease', 'Requires expert interpretation', 'Research stage'],
  },
];

const PRIORITY_CROPS = [
  { name: 'Rice', diseases: 12, images_needed: 5000, status: 'collecting' },
  { name: 'Wheat', diseases: 10, images_needed: 4000, status: 'collecting' },
  { name: 'Maize', diseases: 8, images_needed: 3500, status: 'planned' },
  { name: 'Soybean', diseases: 6, images_needed: 2500, status: 'planned' },
  { name: 'Cotton', diseases: 8, images_needed: 3000, status: 'planned' },
  { name: 'Tomato', diseases: 10, images_needed: 4000, status: 'planned' },
  { name: 'Potato', diseases: 7, images_needed: 3000, status: 'planned' },
  { name: 'Groundnut', diseases: 5, images_needed: 2000, status: 'planned' },
];

const PUBLIC_DATASETS = [
  { name: 'PlantVillage', crops: 38, images: 87000, url: 'https://plantvillage.psu.edu/' },
  { name: 'PlantDoc', crops: 13, images: 2598, url: 'https://github.com/pratikkayal/PlantDoc-Dataset' },
  { name: 'Rice Disease Dataset', crops: 1, images: 5932, url: 'https://www.kaggle.com/datasets/minhhuy2810/rice-diseases-image-dataset' },
  { name: 'Wheat Disease Dataset', crops: 1, images: 3000, url: 'https://www.kaggle.com/datasets/olyadgetch/wheat-disease-detection' },
];


export function PlantVisionStrategy() {
  const [selectedMethod, setSelectedMethod] = useState<string>('external_api');

  const getStatusBadge = (status: DetectionMethod['status']) => {
    switch (status) {
      case 'available':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Available</Badge>;
      case 'coming_soon':
        return <Badge className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />Coming Soon</Badge>;
      case 'research':
        return <Badge className="bg-purple-100 text-purple-800"><Beaker className="h-3 w-3 mr-1" />Research</Badge>;
    }
  };

  const getCropStatusBadge = (status: string) => {
    switch (status) {
      case 'collecting':
        return <Badge className="bg-blue-100 text-blue-800">Collecting Data</Badge>;
      case 'training':
        return <Badge className="bg-yellow-100 text-yellow-800">Training</Badge>;
      case 'available':
        return <Badge className="bg-green-100 text-green-800">Model Available</Badge>;
      default:
        return <Badge variant="secondary">Planned</Badge>;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Eye className="h-6 w-6" />
          Plant Vision Strategy
        </h1>
        <p className="text-muted-foreground">
          Multi-tier approach to plant disease detection at scale
        </p>
      </div>

      {/* The Challenge */}
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            The Scale of the Challenge
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4 text-center">
            <div className="p-3 bg-white rounded-lg">
              <p className="text-2xl font-bold text-amber-600">7,000+</p>
              <p className="text-sm text-muted-foreground">Cultivated Species</p>
            </div>
            <div className="p-3 bg-white rounded-lg">
              <p className="text-2xl font-bold text-amber-600">10,000+</p>
              <p className="text-sm text-muted-foreground">Plant Pathogens</p>
            </div>
            <div className="p-3 bg-white rounded-lg">
              <p className="text-2xl font-bold text-amber-600">Millions</p>
              <p className="text-sm text-muted-foreground">Visual Variations</p>
            </div>
            <div className="p-3 bg-white rounded-lg">
              <p className="text-2xl font-bold text-amber-600">~87K</p>
              <p className="text-sm text-muted-foreground">Largest Public Dataset</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-amber-800">
            <Info className="h-4 w-4 inline mr-1" />
            No single organization has solved universal plant disease detection. 
            We take a pragmatic, tiered approach focusing on what's achievable today 
            while building toward more comprehensive solutions.
          </p>
        </CardContent>
      </Card>

      <Tabs defaultValue="methods" className="space-y-4">
        <TabsList>
          <TabsTrigger value="methods">Detection Methods</TabsTrigger>
          <TabsTrigger value="priority">Priority Crops</TabsTrigger>
          <TabsTrigger value="datasets">Public Datasets</TabsTrigger>
          <TabsTrigger value="contribute">Contribute</TabsTrigger>
        </TabsList>


        {/* Detection Methods Tab */}
        <TabsContent value="methods">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Method List */}
            <Card>
              <CardHeader>
                <CardTitle>Available Methods</CardTitle>
                <CardDescription>
                  From simple heuristics to cutting-edge research
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {DETECTION_METHODS.map((method) => (
                  <div
                    key={method.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedMethod === method.id ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
                    }`}
                    onClick={() => setSelectedMethod(method.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">Tier {method.tier}</Badge>
                        <span className="font-medium">{method.name}</span>
                      </div>
                      {getStatusBadge(method.status)}
                    </div>
                    <p className="text-sm text-muted-foreground">{method.description}</p>
                    <div className="flex gap-4 mt-2 text-xs">
                      <span>Accuracy: <strong>{method.accuracy}</strong></span>
                      <span>Coverage: <strong>{method.coverage}</strong></span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Method Details */}
            <Card>
              <CardHeader>
                <CardTitle>
                  {DETECTION_METHODS.find(m => m.id === selectedMethod)?.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(() => {
                  const method = DETECTION_METHODS.find(m => m.id === selectedMethod);
                  if (!method) return null;
                  return (
                    <div className="space-y-4">
                      <p>{method.description}</p>
                      
                      <div>
                        <h4 className="font-medium text-green-700 mb-2">Advantages</h4>
                        <ul className="space-y-1">
                          {method.pros.map((pro, i) => (
                            <li key={i} className="flex items-center gap-2 text-sm">
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              {pro}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h4 className="font-medium text-red-700 mb-2">Limitations</h4>
                        <ul className="space-y-1">
                          {method.cons.map((con, i) => (
                            <li key={i} className="flex items-center gap-2 text-sm">
                              <AlertTriangle className="h-4 w-4 text-red-500" />
                              {con}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {method.status === 'available' && (
                        <Button className="w-full">
                          <Eye className="h-4 w-4 mr-2" />
                          Use This Method
                        </Button>
                      )}
                      {method.status === 'coming_soon' && (
                        <Button variant="outline" className="w-full" disabled>
                          <Clock className="h-4 w-4 mr-2" />
                          Coming Soon
                        </Button>
                      )}
                      {method.status === 'research' && (
                        <Button variant="outline" className="w-full" disabled>
                          <Beaker className="h-4 w-4 mr-2" />
                          In Research
                        </Button>
                      )}
                    </div>
                  );
                })()}
              </CardContent>
            </Card>
          </div>
        </TabsContent>


        {/* Priority Crops Tab */}
        <TabsContent value="priority">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Leaf className="h-5 w-5" />
                Priority Crops for Model Training
              </CardTitle>
              <CardDescription>
                We're focusing on crops most relevant to our users. Help us by contributing images!
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                {PRIORITY_CROPS.map((crop) => (
                  <div key={crop.name} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{crop.name}</span>
                      {getCropStatusBadge(crop.status)}
                    </div>
                    <div className="text-sm text-muted-foreground space-y-1">
                      <p>{crop.diseases} diseases to cover</p>
                      <p>~{crop.images_needed.toLocaleString()} images needed</p>
                    </div>
                    <Button variant="outline" size="sm" className="w-full mt-3">
                      <Upload className="h-4 w-4 mr-1" />
                      Contribute
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Public Datasets Tab */}
        <TabsContent value="datasets">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cloud className="h-5 w-5" />
                Public Datasets
              </CardTitle>
              <CardDescription>
                Existing datasets we can leverage for transfer learning
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {PUBLIC_DATASETS.map((dataset) => (
                  <div key={dataset.name} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <p className="font-medium">{dataset.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {dataset.crops} crops • {dataset.images.toLocaleString()} images
                      </p>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a href={dataset.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4 mr-1" />
                        View
                      </a>
                    </Button>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">Why These Aren't Enough</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Combined: ~100K images covering ~50 crops</li>
                  <li>• Reality: 7,000+ crops with 10,000+ diseases</li>
                  <li>• Missing: Regional varieties, environmental variations</li>
                  <li>• Quality: Lab conditions ≠ field conditions</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Contribute Tab */}
        <TabsContent value="contribute">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  How You Can Help
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2">1. Contribute Images</h4>
                  <p className="text-sm text-muted-foreground">
                    Upload photos of diseased plants from your fields. Include crop name, 
                    suspected disease, and location.
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2">2. Verify Labels</h4>
                  <p className="text-sm text-muted-foreground">
                    If you're a plant pathologist, help verify disease labels on 
                    community-contributed images.
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2">3. Report Errors</h4>
                  <p className="text-sm text-muted-foreground">
                    When the AI gets it wrong, report the error with the correct diagnosis. 
                    This improves future accuracy.
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2">4. Share Regional Knowledge</h4>
                  <p className="text-sm text-muted-foreground">
                    Document diseases specific to your region that may not be in 
                    global databases.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5" />
                  The Long-Term Vision
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  Building a truly universal plant disease detector requires:
                </p>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <Brain className="h-4 w-4 mt-0.5 text-purple-500" />
                    <span><strong>Few-shot learning</strong> — Identify new diseases with just 5-10 examples</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Microscope className="h-4 w-4 mt-0.5 text-blue-500" />
                    <span><strong>Symptom decomposition</strong> — Detect symptoms, not just diseases</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Cloud className="h-4 w-4 mt-0.5 text-cyan-500" />
                    <span><strong>Multi-modal fusion</strong> — Combine visual + weather + soil data</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Users className="h-4 w-4 mt-0.5 text-green-500" />
                    <span><strong>Federated learning</strong> — Train on distributed data without centralizing</span>
                  </li>
                </ul>
                <div className="p-4 bg-purple-50 rounded-lg mt-4">
                  <p className="text-sm text-purple-800">
                    <strong>This is a research frontier.</strong> We're not just building software — 
                    we're contributing to agricultural science. Your data and feedback 
                    help push the boundaries of what's possible.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default PlantVisionStrategy;

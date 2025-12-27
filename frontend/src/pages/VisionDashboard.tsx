import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Brain, Database, Upload, Play, TrendingUp, 
  FolderOpen, Image, Layers, Sparkles, ArrowRight,
  CheckCircle2, Clock, AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface Dataset {
  id: string;
  name: string;
  crop: string;
  status: string;
  image_count: number;
  annotated_count: number;
  quality_score: number;
  updated_at: string;
}

interface Model {
  id: string;
  name: string;
  crop: string;
  accuracy: number;
  status: string;
  downloads: number;
}

export function VisionDashboard() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [datasetsRes, modelsRes] = await Promise.all([
        fetch('/api/v2/vision/datasets'),
        fetch('/api/v2/vision/models'),
      ]);
      
      if (datasetsRes.ok) {
        const data = await datasetsRes.json();
        setDatasets(data.datasets || []);
      }
      if (modelsRes.ok) {
        const data = await modelsRes.json();
        setModels(data.models || []);
      }
    } catch (error) {
      console.error('Failed to fetch vision data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
      case 'deployed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'draft':
      case 'training':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const totalImages = datasets.reduce((sum, d) => sum + d.image_count, 0);
  const totalAnnotated = datasets.reduce((sum, d) => sum + d.annotated_count, 0);
  const deployedModels = models.filter(m => m.status === 'deployed').length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6" />
            AI Plant Vision Training Ground
          </h1>
          <p className="text-muted-foreground">
            Train custom AI models on your plant image datasets
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/plant-vision">
              <Play className="h-4 w-4 mr-2" />
              Live Inference
            </Link>
          </Button>
          <Button asChild>
            <Link to="/vision/datasets">
              <Database className="h-4 w-4 mr-2" />
              Manage Datasets
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <Database className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{datasets.length}</p>
                <p className="text-xs text-muted-foreground">Datasets</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <Image className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalImages.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">Total Images</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <Layers className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{models.length}</p>
                <p className="text-xs text-muted-foreground">Models</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                <Sparkles className="h-5 w-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{deployedModels}</p>
                <p className="text-xs text-muted-foreground">Deployed</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-4">
        <Link to="/vision/datasets">
          <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <FolderOpen className="h-5 w-5 text-blue-600" />
                </div>
                <CardTitle className="text-lg">Create Dataset</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Organize images into datasets for training custom models
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/vision/datasets">
          <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                  <Upload className="h-5 w-5 text-green-600" />
                </div>
                <CardTitle className="text-lg">Upload Images</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Add images to existing datasets with metadata
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/plant-vision">
          <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                  <Play className="h-5 w-5 text-purple-600" />
                </div>
                <CardTitle className="text-lg">Run Inference</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Test models with real-time plant image analysis
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Recent Datasets & Models */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Datasets */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Datasets</CardTitle>
              <CardDescription>Your training datasets</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/vision/datasets">
                View All <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <p className="text-muted-foreground text-sm">Loading...</p>
            ) : datasets.length === 0 ? (
              <div className="text-center py-8">
                <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-muted-foreground">No datasets yet</p>
                <Button variant="link" asChild>
                  <Link to="/vision/datasets">Create your first dataset</Link>
                </Button>
              </div>
            ) : (
              datasets.slice(0, 4).map((dataset) => (
                <div key={dataset.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(dataset.status)}
                      <span className="font-medium">{dataset.name}</span>
                      <Badge variant="outline" className="text-xs">{dataset.crop}</Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                      <span>{dataset.image_count} images</span>
                      <span>{dataset.annotated_count} annotated</span>
                    </div>
                    <Progress 
                      value={dataset.quality_score} 
                      className="h-1 mt-2" 
                    />
                  </div>
                  <Badge variant={dataset.status === 'ready' ? 'default' : 'secondary'}>
                    {dataset.status}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Models */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Available Models</CardTitle>
              <CardDescription>Pre-trained and custom models</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/vision/datasets">
                View All <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <p className="text-muted-foreground text-sm">Loading...</p>
            ) : models.length === 0 ? (
              <div className="text-center py-8">
                <Layers className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-muted-foreground">No models available</p>
              </div>
            ) : (
              models.slice(0, 4).map((model) => (
                <div key={model.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(model.status)}
                      <span className="font-medium">{model.name}</span>
                      <Badge variant="outline" className="text-xs">{model.crop}</Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" />
                        {(model.accuracy * 100).toFixed(1)}% accuracy
                      </span>
                      <span>{model.downloads} downloads</span>
                    </div>
                  </div>
                  <Badge variant={model.status === 'deployed' ? 'default' : 'secondary'}>
                    {model.status}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Workflow Guide */}
      <Card>
        <CardHeader>
          <CardTitle>Training Workflow</CardTitle>
          <CardDescription>Steps to train your custom plant vision model</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4">
            <div className="flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 font-bold">1</div>
              <div>
                <p className="font-medium">Create Dataset</p>
                <p className="text-sm text-muted-foreground">Define classes and organize images</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 text-green-600 font-bold">2</div>
              <div>
                <p className="font-medium">Upload & Annotate</p>
                <p className="text-sm text-muted-foreground">Add images with labels</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-600 font-bold">3</div>
              <div>
                <p className="font-medium">Train Model</p>
                <p className="text-sm text-muted-foreground">Transfer learning from base models</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-orange-100 dark:bg-orange-900 text-orange-600 font-bold">4</div>
              <div>
                <p className="font-medium">Deploy & Use</p>
                <p className="text-sm text-muted-foreground">Run inference in the field</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

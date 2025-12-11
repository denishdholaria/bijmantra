import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { 
  Tag, Square, Hexagon, Circle, ArrowLeft, Save,
  ChevronLeft, ChevronRight, Check, X, RotateCcw,
  ZoomIn, ZoomOut, Move
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Dataset {
  id: string;
  name: string;
  classes: string[];
  image_count: number;
  annotated_count: number;
}

interface ImageItem {
  id: string;
  filename: string;
  url: string;
  annotation?: {
    label?: string;
    boxes?: Array<{ x: number; y: number; width: number; height: number; label: string }>;
  };
}

type AnnotationTool = 'select' | 'classification' | 'bbox' | 'polygon';

export function VisionAnnotate() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [images, setImages] = useState<ImageItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTool, setActiveTool] = useState<AnnotationTool>('classification');
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [zoom, setZoom] = useState(1);
  const [annotations, setAnnotations] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (datasetId) {
      fetchData();
    }
  }, [datasetId]);

  const fetchData = async () => {
    try {
      const [datasetRes, imagesRes] = await Promise.all([
        fetch(`/api/v2/vision/datasets/${datasetId}`),
        fetch(`/api/v2/vision/datasets/${datasetId}/images?limit=100`),
      ]);
      
      if (datasetRes.ok) {
        const data = await datasetRes.json();
        setDataset(data.dataset);
        if (data.dataset.classes.length > 0) {
          setSelectedClass(data.dataset.classes[0]);
        }
      }
      if (imagesRes.ok) {
        const data = await imagesRes.json();
        // Generate demo images if none exist
        if (data.images.length === 0) {
          const demoImages = Array.from({ length: 10 }, (_, i) => ({
            id: `img-demo-${i}`,
            filename: `sample_${i + 1}.jpg`,
            url: `https://picsum.photos/seed/${datasetId}-${i}/640/480`,
            annotation: i < 5 ? { label: 'healthy' } : undefined,
          }));
          setImages(demoImages);
        } else {
          setImages(data.images);
        }
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const currentImage = images[currentIndex];
  const progress = dataset ? (dataset.annotated_count / dataset.image_count) * 100 : 0;

  const handleClassify = (label: string) => {
    if (!currentImage) return;
    
    setAnnotations({
      ...annotations,
      [currentImage.id]: { label },
    });
    
    // Auto-advance to next image
    if (currentIndex < images.length - 1) {
      setTimeout(() => setCurrentIndex(currentIndex + 1), 300);
    }
  };

  const handleSaveAnnotations = async () => {
    // In a real app, this would save to the backend
    alert(`Saved ${Object.keys(annotations).length} annotations`);
  };

  const handlePrevious = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
  };

  const handleNext = () => {
    if (currentIndex < images.length - 1) setCurrentIndex(currentIndex + 1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') handlePrevious();
    if (e.key === 'ArrowRight') handleNext();
    if (e.key >= '1' && e.key <= '9' && dataset) {
      const index = parseInt(e.key) - 1;
      if (index < dataset.classes.length) {
        handleClassify(dataset.classes[index]);
      }
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <p className="text-muted-foreground">Loading annotation tool...</p>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="container mx-auto p-6">
        <p className="text-destructive">Dataset not found</p>
        <Button asChild className="mt-4">
          <Link to="/vision/datasets">Back to Datasets</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col" onKeyDown={handleKeyDown} tabIndex={0}>
      {/* Header */}
      <div className="border-b p-4 flex items-center justify-between bg-background">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/vision/datasets"><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <div>
            <h1 className="font-semibold">{dataset.name}</h1>
            <p className="text-sm text-muted-foreground">
              Image {currentIndex + 1} of {images.length}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-48">
            <Progress value={progress} className="h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {dataset.annotated_count} / {dataset.image_count} annotated
            </p>
          </div>
          <Button onClick={handleSaveAnnotations}>
            <Save className="h-4 w-4 mr-2" />
            Save ({Object.keys(annotations).length})
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Toolbar */}
        <div className="w-16 border-r bg-muted/30 p-2 flex flex-col gap-2">
          <Button
            variant={activeTool === 'select' ? 'default' : 'ghost'}
            size="icon"
            onClick={() => setActiveTool('select')}
            title="Select (V)"
          >
            <Move className="h-4 w-4" />
          </Button>
          <Button
            variant={activeTool === 'classification' ? 'default' : 'ghost'}
            size="icon"
            onClick={() => setActiveTool('classification')}
            title="Classification (C)"
          >
            <Tag className="h-4 w-4" />
          </Button>
          <Button
            variant={activeTool === 'bbox' ? 'default' : 'ghost'}
            size="icon"
            onClick={() => setActiveTool('bbox')}
            title="Bounding Box (B)"
          >
            <Square className="h-4 w-4" />
          </Button>
          <Button
            variant={activeTool === 'polygon' ? 'default' : 'ghost'}
            size="icon"
            onClick={() => setActiveTool('polygon')}
            title="Polygon (P)"
          >
            <Hexagon className="h-4 w-4" />
          </Button>
          <div className="flex-1" />
          <Button variant="ghost" size="icon" onClick={() => setZoom(z => Math.min(z + 0.25, 3))}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setZoom(z => Math.max(z - 0.25, 0.5))}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setZoom(1)}>
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 flex items-center justify-center bg-muted/20 overflow-auto p-4">
          {currentImage ? (
            <div 
              className="relative bg-black rounded-lg overflow-hidden shadow-lg"
              style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
            >
              <img
                src={currentImage.url}
                alt={currentImage.filename}
                className="max-w-full max-h-[70vh] object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'https://via.placeholder.com/640x480?text=Image+Not+Found';
                }}
              />
              {/* Annotation overlay would go here */}
            </div>
          ) : (
            <p className="text-muted-foreground">No images to annotate</p>
          )}
        </div>

        {/* Right Panel */}
        <div className="w-72 border-l bg-background p-4 overflow-y-auto">
          <Tabs defaultValue="classes">
            <TabsList className="w-full">
              <TabsTrigger value="classes" className="flex-1">Classes</TabsTrigger>
              <TabsTrigger value="info" className="flex-1">Info</TabsTrigger>
            </TabsList>

            <TabsContent value="classes" className="space-y-4 mt-4">
              <div className="space-y-2">
                <p className="text-sm font-medium">Select Class</p>
                <p className="text-xs text-muted-foreground">
                  Click a class or press 1-9 to annotate
                </p>
              </div>
              
              <div className="space-y-2">
                {dataset.classes.map((cls, index) => {
                  const currentAnnotation = annotations[currentImage?.id] as { label?: string } | undefined;
                  const isSelected = currentAnnotation?.label === cls || 
                    currentImage?.annotation?.label === cls;
                  return (
                    <Button
                      key={cls}
                      variant={isSelected ? 'default' : 'outline'}
                      className="w-full justify-start"
                      onClick={() => handleClassify(cls)}
                    >
                      <span className="w-6 h-6 rounded bg-muted flex items-center justify-center text-xs mr-2">
                        {index + 1}
                      </span>
                      {cls}
                      {isSelected && <Check className="h-4 w-4 ml-auto" />}
                    </Button>
                  );
                })}
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm font-medium mb-2">Current Annotation</p>
                {annotations[currentImage?.id] || currentImage?.annotation ? (
                  <Badge>
                    {(annotations[currentImage?.id] as { label?: string })?.label || currentImage?.annotation?.label}
                  </Badge>
                ) : (
                  <p className="text-sm text-muted-foreground">Not annotated</p>
                )}
              </div>
            </TabsContent>

            <TabsContent value="info" className="space-y-4 mt-4">
              {currentImage && (
                <>
                  <div>
                    <p className="text-sm font-medium">Filename</p>
                    <p className="text-sm text-muted-foreground">{currentImage.filename}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Image ID</p>
                    <p className="text-sm text-muted-foreground font-mono">{currentImage.id}</p>
                  </div>
                </>
              )}
            </TabsContent>
          </Tabs>

          {/* Keyboard Shortcuts */}
          <Card className="mt-4">
            <CardHeader className="py-3">
              <CardTitle className="text-sm">Keyboard Shortcuts</CardTitle>
            </CardHeader>
            <CardContent className="text-xs space-y-1">
              <div className="flex justify-between">
                <span>Previous image</span>
                <kbd className="px-1 bg-muted rounded">←</kbd>
              </div>
              <div className="flex justify-between">
                <span>Next image</span>
                <kbd className="px-1 bg-muted rounded">→</kbd>
              </div>
              <div className="flex justify-between">
                <span>Select class</span>
                <kbd className="px-1 bg-muted rounded">1-9</kbd>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Footer Navigation */}
      <div className="border-t p-4 flex items-center justify-between bg-background">
        <Button variant="outline" onClick={handlePrevious} disabled={currentIndex === 0}>
          <ChevronLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>
        
        <div className="flex items-center gap-2">
          {images.slice(Math.max(0, currentIndex - 3), currentIndex + 4).map((img, i) => {
            const actualIndex = Math.max(0, currentIndex - 3) + i;
            const isAnnotated = annotations[img.id] || img.annotation;
            return (
              <button
                key={img.id}
                onClick={() => setCurrentIndex(actualIndex)}
                className={`w-12 h-12 rounded border-2 overflow-hidden ${
                  actualIndex === currentIndex ? 'border-primary' : 'border-transparent'
                }`}
              >
                <div className="relative w-full h-full">
                  <img
                    src={img.url}
                    alt=""
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = 'https://via.placeholder.com/48';
                    }}
                  />
                  {isAnnotated && (
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-tl" />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        <Button variant="outline" onClick={handleNext} disabled={currentIndex === images.length - 1}>
          Next
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

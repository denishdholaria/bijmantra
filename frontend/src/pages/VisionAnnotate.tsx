import { useState, useEffect, useRef } from 'react';
import { Link, useParams } from 'react-router-dom';
import { 
  Tag, Square, Hexagon, ArrowLeft, Save,
  ChevronLeft, ChevronRight, Check, RotateCcw,
  ZoomIn, ZoomOut, Move, AlertCircle, RefreshCw, X
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { VisionService, VisionDataset, VisionImage } from '@/services/VisionService';

interface Box {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
}

type AnnotationTool = 'select' | 'classification' | 'bbox' | 'polygon';

export function VisionAnnotate() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [dataset, setDataset] = useState<VisionDataset | null>(null);
  const [images, setImages] = useState<VisionImage[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTool, setActiveTool] = useState<AnnotationTool>('bbox');
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [zoom, setZoom] = useState(1);

  // Annotation state
  const [annotations, setAnnotations] = useState<Record<string, Box[]>>({});
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{x: number, y: number} | null>(null);
  const [currentBox, setCurrentBox] = useState<Box | null>(null);
  const [imgLoaded, setImgLoaded] = useState(false);
  const imageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (datasetId) {
      fetchData();
    }
  }, [datasetId]);

  const fetchData = async () => {
    setError(null);
    setLoading(true);
    try {
      if (!datasetId) return;
      const datasetData = await VisionService.getDataset(datasetId);
      setDataset(datasetData.dataset);
      
      if (datasetData.dataset.classes.length > 0) {
        setSelectedClass(datasetData.dataset.classes[0]);
      }

      const imagesData = await VisionService.getDatasetImages(datasetId);
      setImages(imagesData.images || []);

      // Load annotations for existing images if any (assuming API supports it)
      // For now, we initialize from image.annotation if present
      const initialAnnotations: Record<string, Box[]> = {};
      imagesData.images.forEach(img => {
        if (img.annotation && img.annotation.boxes) {
           initialAnnotations[img.id] = img.annotation.boxes;
        }
      });
      setAnnotations(initialAnnotations);

    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('Failed to load annotation data. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const currentImage = images[currentIndex];
  const progress = dataset ? (dataset.annotated_count / dataset.image_count) * 100 : 0;

  const handleSaveAnnotations = async () => {
    if (!dataset || !currentImage) return;
    const boxes = annotations[currentImage.id] || [];
    try {
       await VisionService.saveBoundingBox(dataset.id, currentImage.id, boxes);
       alert(`Saved ${boxes.length} boxes for image ${currentImage.filename}`);
       // Update dataset annotated count (optimistically)
       // fetchDataset(); // or just update local state
    } catch (e) {
       console.error(e);
       alert('Failed to save annotations');
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
  };

  const handleNext = () => {
    if (currentIndex < images.length - 1) setCurrentIndex(currentIndex + 1);
  };

  // Canvas Handlers
  const getCoordinates = (e: React.MouseEvent) => {
    if (!imageRef.current) return { x: 0, y: 0 };
    const rect = imageRef.current.getBoundingClientRect();
    const scaleX = (imageRef.current.naturalWidth || 1) / rect.width;
    const scaleY = (imageRef.current.naturalHeight || 1) / rect.height;

    // Calculate position relative to image element
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    return { x, y };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (activeTool !== 'bbox' || !imageRef.current) return;
    e.preventDefault();
    const { x, y } = getCoordinates(e);
    setIsDrawing(true);
    setStartPoint({ x, y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDrawing || !startPoint || !imageRef.current) return;
    e.preventDefault();
    const { x, y } = getCoordinates(e);

    const width = Math.abs(x - startPoint.x);
    const height = Math.abs(y - startPoint.y);
    const boxX = Math.min(x, startPoint.x);
    const boxY = Math.min(y, startPoint.y);

    setCurrentBox({ x: boxX, y: boxY, width, height, label: selectedClass });
  };

  const handleMouseUp = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    setStartPoint(null);

    if (currentBox && currentImage) {
      const currentBoxes = annotations[currentImage.id] || [];
      setAnnotations({
         ...annotations,
         [currentImage.id]: [...currentBoxes, currentBox]
      });
    }
    setCurrentBox(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') handlePrevious();
    if (e.key === 'ArrowRight') handleNext();
    if (e.key >= '1' && e.key <= '9' && dataset) {
      const index = parseInt(e.key) - 1;
      if (index < dataset.classes.length) {
        setSelectedClass(dataset.classes[index]);
      }
    }
  };

  if (loading) return <div className="container mx-auto p-6">Loading...</div>;
  if (error || !dataset) return <div className="container mx-auto p-6 text-red-500">{error || 'Dataset not found'}</div>;

  return (
    <div className="h-screen flex flex-col" onKeyDown={handleKeyDown} tabIndex={0}>
      {/* Header */}
      <div className="border-b p-4 flex items-center justify-between bg-background">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label="Back to datasets">
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
          </div>
          <Button onClick={handleSaveAnnotations}>
            <Save className="h-4 w-4 mr-2" />
            Save
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Toolbar */}
        <div className="w-16 border-r bg-muted/30 p-2 flex flex-col gap-2">
          <Button variant={activeTool === 'select' ? 'default' : 'ghost'} size="icon" onClick={() => setActiveTool('select')} title="Select"><Move className="h-4 w-4" /></Button>
          <Button variant={activeTool === 'classification' ? 'default' : 'ghost'} size="icon" onClick={() => setActiveTool('classification')} title="Classify"><Tag className="h-4 w-4" /></Button>
          <Button variant={activeTool === 'bbox' ? 'default' : 'ghost'} size="icon" onClick={() => setActiveTool('bbox')} title="BBox"><Square className="h-4 w-4" /></Button>
          <div className="flex-1" />
          <Button variant="ghost" size="icon" onClick={() => setZoom(z => Math.min(z + 0.25, 3))}><ZoomIn className="h-4 w-4" /></Button>
          <Button variant="ghost" size="icon" onClick={() => setZoom(z => Math.max(z - 0.25, 0.5))}><ZoomOut className="h-4 w-4" /></Button>
          <Button variant="ghost" size="icon" onClick={() => setZoom(1)}><RotateCcw className="h-4 w-4" /></Button>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 flex items-center justify-center bg-muted/20 overflow-auto p-4 select-none">
          {currentImage ? (
            <div 
              className="relative inline-block shadow-lg bg-black"
              style={{ transform: `scale(${zoom})`, transformOrigin: 'center', cursor: activeTool === 'bbox' ? 'crosshair' : 'default' }}
            >
              <img
                ref={imageRef}
                src={currentImage.url}
                alt={currentImage.filename}
                className="max-w-[70vw] max-h-[70vh] object-contain block pointer-events-auto"
                onLoad={() => setImgLoaded(true)}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                draggable={false}
              />
              {imgLoaded && (
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none"
                  viewBox={`0 0 ${imageRef.current?.naturalWidth || 100} ${imageRef.current?.naturalHeight || 100}`}
                >
                  {(annotations[currentImage.id] || []).map((box, i) => (
                    <g key={i}>
                      <rect
                        x={box.x} y={box.y} width={box.width} height={box.height}
                        fill="rgba(0, 255, 0, 0.2)" stroke="lime" strokeWidth="2"
                        vectorEffect="non-scaling-stroke"
                      />
                      <text x={box.x} y={box.y > 20 ? box.y - 5 : box.y + 20} fill="lime" fontSize="20" fontWeight="bold" style={{ textShadow: '1px 1px 1px black' }}>
                        {box.label}
                      </text>
                    </g>
                  ))}
                  {currentBox && (
                    <rect
                      x={currentBox.x} y={currentBox.y} width={currentBox.width} height={currentBox.height}
                      fill="rgba(255, 255, 0, 0.2)" stroke="yellow" strokeWidth="2" strokeDasharray="5,5"
                      vectorEffect="non-scaling-stroke"
                    />
                  )}
                </svg>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground">No images to annotate</p>
          )}
        </div>

        {/* Right Panel */}
        <div className="w-72 border-l bg-background p-4">
          <Tabs defaultValue="classes">
            <TabsList className="w-full">
              <TabsTrigger value="classes" className="flex-1">Classes</TabsTrigger>
              <TabsTrigger value="boxes" className="flex-1">Annotations</TabsTrigger>
            </TabsList>

            <TabsContent value="classes" className="space-y-2 mt-4">
              <p className="text-xs text-muted-foreground mb-2">Selected Class: <Badge>{selectedClass}</Badge></p>
              {dataset.classes.map((cls, index) => (
                <Button
                  key={cls}
                  variant={selectedClass === cls ? 'default' : 'outline'}
                  className="w-full justify-start"
                  onClick={() => setSelectedClass(cls)}
                >
                  <span className="w-6 h-6 rounded bg-muted flex items-center justify-center text-xs mr-2">{index + 1}</span>
                  {cls}
                </Button>
              ))}
            </TabsContent>

            <TabsContent value="boxes" className="space-y-2 mt-4">
               {currentImage && annotations[currentImage.id]?.map((box, i) => (
                 <div key={i} className="flex items-center justify-between p-2 border rounded">
                    <span className="text-sm">{box.label}</span>
                    <Button
                      variant="ghost" size="icon" className="h-6 w-6 text-destructive"
                      onClick={() => {
                         const newBoxes = annotations[currentImage.id].filter((_, idx) => idx !== i);
                         setAnnotations({ ...annotations, [currentImage.id]: newBoxes });
                      }}
                    >
                       <X className="h-4 w-4" />
                    </Button>
                 </div>
               ))}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

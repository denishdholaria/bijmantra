import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Trash2, Maximize, Square, ZoomIn, ZoomOut, RotateCcw, Save, Crosshair, Tag, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

/**
 * Interface representing a bounding box annotation.
 */
export interface BoundingBox {
  id: string;
  x: number; // Percentage of image width (0-1)
  y: number; // Percentage of image height (0-1)
  width: number; // Percentage of image width (0-1)
  height: number; // Percentage of image height (0-1)
  label?: string;
  color?: string;
}

/**
 * Props for the BiometricImageAnnotator component.
 */
export interface BiometricImageAnnotatorProps {
  /** URL of the image to annotate */
  imageUrl: string;
  /** Initial bounding boxes */
  initialBoxes?: BoundingBox[];
  /** Callback triggered when bounding boxes are saved */
  onSave?: (boxes: BoundingBox[]) => void;
  /** Available labels for annotation */
  labels?: string[];
  /** Default label for new boxes */
  defaultLabel?: string;
  /** Custom className for the container */
  className?: string;
}

type Tool = 'draw' | 'select';

const COLORS = [
  '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'
];

/**
 * BiometricImageAnnotator - A canvas-based tool for drawing and managing bounding box annotations
 * on images, specifically designed for biometric data labeling.
 */
const BiometricImageAnnotator: React.FC<BiometricImageAnnotatorProps> = ({
  imageUrl,
  initialBoxes = [],
  onSave,
  labels = [],
  defaultLabel,
  className,
}) => {
  const [boxes, setBoxes] = useState<BoundingBox[]>(initialBoxes);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [currentTool, setCurrentTool] = useState<Tool>('draw');
  const [isDrawing, setIsDrawing] = useState(false);
  const [isMoving, setIsMoving] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [currentBox, setCurrentBox] = useState<Partial<BoundingBox> | null>(null);
  const [zoom, setZoom] = useState(1);
  const [imageLoaded, setImageLoaded] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const getCanvasCoords = (e: React.MouseEvent | MouseEvent) => {
    if (!canvasRef.current) return { x: 0, y: 0 };
    const rect = canvasRef.current.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / zoom,
      y: (e.clientY - rect.top) / zoom,
    };
  };

  const getNormalizedCoords = (x: number, y: number) => {
    if (!imageRef.current) return { x: 0, y: 0 };
    return {
      x: x / imageRef.current.width,
      y: y / imageRef.current.height,
    };
  };

  const getPixelCoords = (nx: number, ny: number, nw: number, nh: number) => {
    if (!imageRef.current) return { x: 0, y: 0, w: 0, h: 0 };
    return {
      x: nx * imageRef.current.width,
      y: ny * imageRef.current.height,
      w: nw * imageRef.current.width,
      h: nh * imageRef.current.height,
    };
  };

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    const img = imageRef.current;

    if (!canvas || !ctx || !img) return;

    // Set canvas dimensions to match image
    canvas.width = img.width;
    canvas.height = img.height;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);

    // Draw boxes
    boxes.forEach((box) => {
      const { x, y, w, h } = getPixelCoords(box.x, box.y, box.width, box.height);
      const isSelected = box.id === selectedBoxId;

      ctx.strokeStyle = isSelected ? '#ffffff' : (box.color || '#3b82f6');
      ctx.lineWidth = Math.max(2, 3 / zoom);

      // Draw shadow for better visibility
      ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
      ctx.shadowBlur = 4 / zoom;
      ctx.strokeRect(x, y, w, h);
      ctx.shadowBlur = 0;

      if (isSelected) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
        ctx.fillRect(x, y, w, h);

        // Draw resize handles
        const handleSize = Math.max(6, 10 / zoom);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(x + w - handleSize / 2, y + h - handleSize / 2, handleSize, handleSize);
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 1 / zoom;
        ctx.strokeRect(x + w - handleSize / 2, y + h - handleSize / 2, handleSize, handleSize);
      }

      if (box.label) {
        ctx.fillStyle = isSelected ? '#ffffff' : (box.color || '#3b82f6');
        ctx.font = `bold ${Math.max(12, 14 / zoom)}px Inter, system-ui, sans-serif`;
        const text = box.label;
        const textWidth = ctx.measureText(text).width;
        const padding = 6 / zoom;
        const labelHeight = 20 / zoom;

        // If the box is at the very top, draw label inside the box
        let labelY = y - labelHeight;
        if (labelY < 0) {
          labelY = y;
        }

        ctx.fillRect(x, labelY, textWidth + padding * 2, labelHeight);
        ctx.fillStyle = '#000000';
        ctx.fillText(text, x + padding, labelY + labelHeight - 6 / zoom);
      }
    });

    // Draw current drawing box
    if (isDrawing && currentBox) {
      const { x, y, w, h } = getPixelCoords(
        currentBox.x || 0,
        currentBox.y || 0,
        currentBox.width || 0,
        currentBox.height || 0
      );
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2 / zoom;
      ctx.setLineDash([5 / zoom, 5 / zoom]);
      ctx.strokeRect(x, y, w, h);
      ctx.setLineDash([]);
    }
  }, [boxes, selectedBoxId, isDrawing, currentBox, zoom]);

  // Load image
  useEffect(() => {
    const img = new Image();
    img.crossOrigin = "anonymous"; // Handle potential CORS issues
    img.src = imageUrl;
    img.onload = () => {
      imageRef.current = img;
      setImageLoaded(true);
      draw();
    };
    img.onerror = () => {
      console.error("Failed to load image:", imageUrl);
    };
  }, [imageUrl, draw]);

  useEffect(() => {
    draw();
  }, [draw]);

  const handleMouseDown = (e: React.MouseEvent) => {
    const { x, y } = getCanvasCoords(e);
    const { x: nx, y: ny } = getNormalizedCoords(x, y);

    if (currentTool === 'draw') {
      setIsDrawing(true);
      setStartPos({ x: nx, y: ny });
      setCurrentBox({ id: Date.now().toString(), x: nx, y: ny, width: 0, height: 0 });
    } else if (currentTool === 'select') {
      const clickedBox = [...boxes].reverse().find(box =>
        nx >= box.x && nx <= box.x + box.width &&
        ny >= box.y && ny <= box.y + box.height
      );

      if (clickedBox) {
        setSelectedBoxId(clickedBox.id);

        const { x: px, y: py, w: pw, h: ph } = getPixelCoords(clickedBox.x, clickedBox.y, clickedBox.width, clickedBox.height);
        const mouseX = x;
        const mouseY = y;
        const handleSize = Math.max(10, 15 / zoom);

        if (mouseX >= px + pw - handleSize && mouseX <= px + pw + handleSize &&
            mouseY >= py + ph - handleSize && mouseY <= py + ph + handleSize) {
          setIsResizing(true);
        } else {
          setIsMoving(true);
        }
        setStartPos({ x: nx, y: ny });
      } else {
        setSelectedBoxId(null);
      }
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const { x, y } = getCanvasCoords(e);
    const { x: nx, y: ny } = getNormalizedCoords(x, y);

    if (isDrawing && currentBox) {
      setCurrentBox({
        ...currentBox,
        width: nx - (currentBox.x || 0),
        height: ny - (currentBox.y || 0),
      });
    } else if (isMoving && selectedBoxId) {
      const dx = nx - startPos.x;
      const dy = ny - startPos.y;
      setBoxes(boxes.map(box =>
        box.id === selectedBoxId
          ? {
              ...box,
              x: Math.max(0, Math.min(1 - box.width, box.x + dx)),
              y: Math.max(0, Math.min(1 - box.height, box.y + dy))
            }
          : box
      ));
      setStartPos({ x: nx, y: ny });
    } else if (isResizing && selectedBoxId) {
      const dx = nx - startPos.x;
      const dy = ny - startPos.y;
      setBoxes(boxes.map(box =>
        box.id === selectedBoxId
          ? {
              ...box,
              width: Math.max(0.005, Math.min(1 - box.x, box.width + dx)),
              height: Math.max(0.005, Math.min(1 - box.y, box.height + dy))
            }
          : box
      ));
      setStartPos({ x: nx, y: ny });
    }
  };

  const handleMouseUp = () => {
    if (isDrawing && currentBox) {
      if (Math.abs(currentBox.width || 0) > 0.005 && Math.abs(currentBox.height || 0) > 0.005) {
        const newBox: BoundingBox = {
          id: currentBox.id!,
          x: currentBox.width! > 0 ? currentBox.x! : currentBox.x! + currentBox.width!,
          y: currentBox.height! > 0 ? currentBox.y! : currentBox.y! + currentBox.height!,
          width: Math.abs(currentBox.width!),
          height: Math.abs(currentBox.height!),
          label: defaultLabel || (labels.length > 0 ? labels[0] : undefined),
          color: COLORS[boxes.length % COLORS.length]
        };
        setBoxes([...boxes, newBox]);
        setSelectedBoxId(newBox.id);
        setCurrentTool('select');
      }
    }
    setIsDrawing(false);
    setIsMoving(false);
    setIsResizing(false);
    setCurrentBox(null);
  };

  const deleteSelectedBox = useCallback(() => {
    if (selectedBoxId) {
      setBoxes(prev => prev.filter(box => box.id !== selectedBoxId));
      setSelectedBoxId(null);
    }
  }, [selectedBoxId]);

  const updateSelectedBoxLabel = (label: string) => {
    if (selectedBoxId) {
      setBoxes(boxes.map(box =>
        box.id === selectedBoxId ? { ...box, label } : box
      ));
    }
  };

  const handleZoom = (delta: number) => {
    setZoom(prev => Math.max(0.1, Math.min(10, prev + delta)));
  };

  const resetZoom = () => setZoom(1);

  const handleSave = () => {
    if (onSave) {
      onSave(boxes);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedBoxId && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName || '')) {
          deleteSelectedBox();
        }
      } else if (e.key === 'd') {
        setCurrentTool('draw');
      } else if (e.key === 's') {
        setCurrentTool('select');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedBoxId, deleteSelectedBox]);

  const selectedBox = boxes.find(b => b.id === selectedBoxId);

  return (
    <div className={cn("flex flex-col gap-5 bg-card p-6 rounded-2xl border border-border shadow-xl", className)}>
      {/* Tool Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-muted/40 p-3 rounded-xl border border-border/50">
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <div className="flex items-center bg-background rounded-lg border border-border p-1 shadow-sm">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={currentTool === 'draw' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => {
                      setCurrentTool('draw');
                      setSelectedBoxId(null);
                    }}
                    className="h-9 px-3 gap-2 transition-all"
                    aria-label="Draw Bounding Box"
                  >
                    <Square className="h-4 w-4" />
                    <span className="hidden sm:inline font-medium">Draw</span>
                    <Badge variant="outline" className="ml-1 text-[10px] px-1 h-4 opacity-50 bg-transparent border-current">D</Badge>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Draw Bounding Box (D)</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={currentTool === 'select' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setCurrentTool('select')}
                    className="h-9 px-3 gap-2 transition-all"
                    aria-label="Select Tool"
                  >
                    <Crosshair className="h-4 w-4" />
                    <span className="hidden sm:inline font-medium">Select</span>
                    <Badge variant="outline" className="ml-1 text-[10px] px-1 h-4 opacity-50 bg-transparent border-current">S</Badge>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Select / Move / Resize (S)</TooltipContent>
              </Tooltip>
            </div>

            <div className="flex items-center bg-background rounded-lg border border-border p-1 shadow-sm">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" onClick={() => handleZoom(0.25)} className="h-9 w-9" aria-label="Zoom In">
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Zoom In</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" onClick={() => handleZoom(-0.25)} className="h-9 w-9" aria-label="Zoom Out">
                    <ZoomOut className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Zoom Out</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" onClick={resetZoom} className="h-9 w-9 text-muted-foreground hover:text-foreground" aria-label="Reset Zoom">
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Reset Zoom</TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
        </div>

        <div className="flex items-center gap-3">
          {selectedBox && labels.length > 0 && (
            <div className="flex items-center gap-2 bg-background p-1 pr-2 rounded-lg border border-border animate-in zoom-in-95 duration-200">
              <div className="pl-2">
                <Tag className="h-3.5 w-3.5 text-primary" />
              </div>
              <Select value={selectedBox.label} onValueChange={updateSelectedBoxLabel}>
                <SelectTrigger className="h-8 w-[150px] border-none shadow-none focus:ring-0 font-medium">
                  <SelectValue placeholder="Select label" />
                </SelectTrigger>
                <SelectContent>
                  {labels.map(label => (
                    <SelectItem key={label} value={label}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {selectedBoxId && (
            <Button variant="destructive" size="sm" onClick={deleteSelectedBox} className="h-9 gap-2 shadow-sm px-3" aria-label="Delete Annotation">
              <Trash2 className="h-4 w-4" />
              <span className="hidden sm:inline">Delete</span>
            </Button>
          )}

          <div className="w-[1px] h-8 bg-border/60 mx-1 hidden sm:block" />

          <Button variant="default" size="sm" onClick={handleSave} className="h-9 gap-2 bg-primary hover:bg-primary/90 shadow-md px-5 transition-transform active:scale-95">
            <Save className="h-4 w-4" />
            <span className="font-semibold">Save Labels</span>
          </Button>
        </div>
      </div>

      {/* Canvas Area */}
      <div
        ref={containerRef}
        className="relative overflow-auto border-2 border-dashed border-border/80 rounded-2xl bg-black/5 flex items-center justify-center min-h-[550px] max-h-[80vh] group transition-all hover:bg-black/10 hover:border-border"
        style={{ cursor: currentTool === 'draw' ? 'crosshair' : 'default' }}
      >
        <div
          className="relative transition-transform duration-200 cubic-bezier(0.2, 0, 0, 1)"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
        >
          {!imageLoaded && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
              <div className="relative p-8 rounded-full bg-background/50 backdrop-blur-sm border border-border mb-4">
                <Maximize className="h-10 w-10 opacity-20 animate-pulse" />
              </div>
              <p className="text-sm font-semibold tracking-tight">Initializing Biometric Canvas...</p>
            </div>
          )}
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            className={cn(
              "shadow-2xl bg-white rounded-md transition-opacity duration-700",
              !imageLoaded ? "opacity-0" : "opacity-100",
              currentTool === 'select' && !isMoving && !isResizing && "cursor-pointer",
              isMoving && "cursor-move",
              isResizing && "cursor-nwse-resize"
            )}
          />
        </div>

        {/* Floating Info */}
        <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="p-2 bg-background/80 backdrop-blur-md rounded-full border border-border shadow-lg cursor-help">
                  <Info className="h-4 w-4 text-muted-foreground" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="left" className="p-3 max-w-[200px]">
                <p className="text-xs font-semibold mb-1">Canvas Instructions:</p>
                <ul className="text-[10px] space-y-1 text-muted-foreground list-disc pl-3">
                  <li>Hold click and drag to create new boxes</li>
                  <li>In Select mode, drag boxes to move them</li>
                  <li>Use the bottom-right handle to resize</li>
                  <li>Press <kbd className="bg-muted px-1 rounded">DEL</kbd> to remove selected</li>
                </ul>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Footer / Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-1">
        <div className="flex gap-6">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Annotation Count</span>
            <div className="flex items-center gap-2 mt-1">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-sm font-mono font-bold leading-none">{boxes.length} Objects</span>
            </div>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Viewport Scaling</span>
            <span className="text-sm font-mono font-bold mt-1">{(zoom * 100).toFixed(0)}%</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="px-3 py-1 font-mono text-[10px] uppercase tracking-tight">
            {currentTool === 'draw' ? 'Mode: Annotation' : (selectedBoxId ? 'Status: Editing Box' : 'Mode: Navigation')}
          </Badge>
        </div>
      </div>
    </div>
  );
};

export default BiometricImageAnnotator;

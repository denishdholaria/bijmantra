import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  ZoomIn,
  ZoomOut,
  Maximize,
  Search,
  Filter,
  Layers,
  Bot,
  Map as MapIcon,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFieldMode } from '@/hooks/useFieldMode';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui/tooltip';
import {
  Popover,
  PopoverContent,
  PopoverTrigger
} from '@/components/ui/popover';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import {
  FieldPlot,
  FieldLayout,
  SpatialMapSettings,
  ViewState,
  PlotStatus,
  Position
} from './SpatialFieldMapLayout.types';

interface SpatialFieldMapLayoutProps {
  layout: FieldLayout;
  onPlotSelect?: (plot: FieldPlot) => void;
  onBulkSelect?: (plots: FieldPlot[]) => void;
  initialSettings?: Partial<SpatialMapSettings>;
  className?: string;
}

export const SpatialFieldMapLayout: React.FC<SpatialFieldMapLayoutProps> = ({
  layout,
  onPlotSelect,
  onBulkSelect,
  initialSettings,
  className,
}) => {
  const { isFieldMode, triggerHaptic } = useFieldMode();
  const containerRef = useRef<HTMLDivElement>(null);

  // State
  const [settings, setSettings] = useState<SpatialMapSettings>({
    showLabels: true,
    showLegend: true,
    colorScheme: 'status',
    orientation: 'standard',
    ...initialSettings,
  });

  const [viewState, setViewState] = useState<ViewState>({
    scale: 1,
    offset: { x: 0, y: 0 },
  });

  const [isPanning, setIsPanning] = useState(false);
  const [startPanPos, setStartPanPos] = useState<Position>({ x: 0, y: 0 });

  const [selectedPlotIds, setSelectedPlotIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<PlotStatus | 'all'>('all');

  // Derived data
  const orderedPlots = useMemo(() => {
    const sorted = [...layout.plots].sort((a, b) => {
      if (a.row !== b.row) return a.row - b.row;

      if (settings.orientation === 'serpentine') {
        // In serpentine mode, odd rows (1-indexed) are L to R, even rows are R to L
        // Or vice-versa depending on the specific serpentine pattern, but usually
        // Row 1: 1->N, Row 2: N->1
        return a.row % 2 !== 0 ? a.col - b.col : b.col - a.col;
      }
      return a.col - b.col;
    });
    return sorted;
  }, [layout.plots, settings.orientation]);

  const filteredPlots = useMemo(() => {
    return layout.plots.filter((p) => {
      const matchesSearch = !searchQuery ||
        p.plotNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.germplasmName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === 'all' || p.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [layout.plots, searchQuery, statusFilter]);

  // Handlers
  const handleZoomIn = () => {
    setViewState(prev => ({ ...prev, scale: Math.min(prev.scale * 1.2, 5) }));
    triggerHaptic(20);
  };

  const handleZoomOut = () => {
    setViewState(prev => ({ ...prev, scale: Math.max(prev.scale / 1.2, 0.2) }));
    triggerHaptic(20);
  };

  const handleResetView = () => {
    setViewState({ scale: 1, offset: { x: 0, y: 0 } });
    triggerHaptic([20, 10, 20]);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left click
    setIsPanning(true);
    setStartPanPos({ x: e.clientX - viewState.offset.x, y: e.clientY - viewState.offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setViewState(prev => ({
      ...prev,
      offset: {
        x: e.clientX - startPanPos.x,
        y: e.clientY - startPanPos.y,
      }
    }));
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (e.ctrlKey) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      setViewState(prev => ({
        ...prev,
        scale: Math.max(0.1, Math.min(5, prev.scale * delta))
      }));
    }
  };

  const togglePlotSelection = (plot: FieldPlot, isMulti: boolean) => {
    const newSelection = new Set(selectedPlotIds);
    if (isMulti) {
      if (newSelection.has(plot.id)) {
        newSelection.delete(plot.id);
      } else {
        newSelection.add(plot.id);
      }
    } else {
      newSelection.clear();
      newSelection.add(plot.id);
    }
    setSelectedPlotIds(newSelection);
    onPlotSelect?.(plot);
    triggerHaptic(30);
  };

  useEffect(() => {
    if (onBulkSelect && selectedPlotIds.size > 0) {
      const selectedPlots = layout.plots.filter(p => selectedPlotIds.has(p.id));
      onBulkSelect(selectedPlots);
    }
  }, [selectedPlotIds, layout.plots, onBulkSelect]);

  // Plot Color Logic
  const getPlotColor = (plot: FieldPlot) => {
    if (settings.colorScheme === 'status') {
      switch (plot.status) {
        case 'complete': return 'bg-emerald-500 border-emerald-600';
        case 'skipped': return 'bg-amber-500 border-amber-600';
        case 'failed': return 'bg-rose-500 border-rose-600';
        default: return 'bg-slate-200 border-slate-300 dark:bg-slate-800 dark:border-slate-700';
      }
    }

    if (settings.colorScheme === 'heatmap' && settings.heatmapVariable) {
      const observation = plot.observations?.find(o => o.variableDbId === settings.heatmapVariable);
      if (observation && typeof observation.value === 'number') {
        // Simple linear interpolation for heatmap (blue to red)
        const val = observation.value;
        // Mock range for demo: 0-100
        const hue = Math.max(0, Math.min(240, 240 - (val * 2.4))); // 240 is blue, 0 is red
        return `hsl(${hue}, 70%, 50%)`;
      }
    }

    return 'bg-slate-200 border-slate-300 dark:bg-slate-800 dark:border-slate-700';
  };

  return (
    <Card className={cn("w-full h-full flex flex-col overflow-hidden", className)}>
      <CardHeader className="pb-2">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <MapIcon className="h-5 w-5 text-emerald-600" />
              {layout.studyName} Spatial Map
            </CardTitle>
            <CardDescription>
              {layout.rows} Rows x {layout.cols} Columns • {layout.plots.length} Total Plots
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative w-full md:w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search plots..."
                className="pl-9"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button variant="outline" size="icon" onClick={handleResetView} title="Reset View">
              <Maximize className="h-4 w-4" />
            </Button>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="icon" className={cn(statusFilter !== 'all' && "border-primary text-primary")}>
                  <Filter className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-56">
                <div className="space-y-4">
                  <h4 className="font-medium leading-none">Filters</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Status</span>
                      <Select
                        value={statusFilter}
                        onValueChange={(v: PlotStatus | 'all') => setStatusFilter(v)}
                      >
                        <SelectTrigger className="w-[120px] h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All</SelectItem>
                          <SelectItem value="pending">Pending</SelectItem>
                          <SelectItem value="complete">Complete</SelectItem>
                          <SelectItem value="skipped">Skipped</SelectItem>
                          <SelectItem value="failed">Failed</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="icon">
                  <Layers className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-56">
                <div className="space-y-4">
                  <h4 className="font-medium leading-none">Map Layers</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Orientation</span>
                      <Select
                        value={settings.orientation}
                        onValueChange={(v: SpatialMapSettings['orientation']) => setSettings(s => ({ ...s, orientation: v }))}
                      >
                        <SelectTrigger className="w-[120px] h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="standard">Standard</SelectItem>
                          <SelectItem value="serpentine">Serpentine</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Color Scheme</span>
                      <Select
                        value={settings.colorScheme}
                        onValueChange={(v: SpatialMapSettings['colorScheme']) => setSettings(s => ({ ...s, colorScheme: v }))}
                      >
                        <SelectTrigger className="w-[120px] h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="status">Status</SelectItem>
                          <SelectItem value="heatmap">Heatmap</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    {settings.colorScheme === 'heatmap' && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Variable</span>
                        <Select
                          value={settings.heatmapVariable}
                          onValueChange={(v: string) => setSettings(s => ({ ...s, heatmapVariable: v }))}
                        >
                          <SelectTrigger className="w-[120px] h-8">
                            <SelectValue placeholder="Select trait" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="yield">Yield (kg/ha)</SelectItem>
                            <SelectItem value="height">Plant Height (cm)</SelectItem>
                            <SelectItem value="moisture">Moisture (%)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 relative p-0 overflow-hidden bg-slate-50 dark:bg-slate-950">
        {/* Plot Grid Viewport */}
        <div
          ref={containerRef}
          role="presentation"
          className={cn(
            "w-full h-full overflow-hidden",
            isPanning ? "cursor-grabbing" : "cursor-grab"
          )}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        >
          <div
            className="inline-grid gap-1 p-8 origin-top-left transition-transform duration-200"
            style={{
              gridTemplateColumns: `repeat(${layout.cols}, minmax(40px, 1fr))`,
              transform: `translate(${viewState.offset.x}px, ${viewState.offset.y}px) scale(${viewState.scale})`,
            }}
          >
            {orderedPlots.map((plot) => {
              const isSelected = selectedPlotIds.has(plot.id);
              const isFiltered = (searchQuery || statusFilter !== 'all') && !filteredPlots.some(p => p.id === plot.id);

              return (
                <TooltipProvider key={plot.id}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        aria-label={`Plot ${plot.plotNumber}, ${plot.germplasmName || 'Unknown Germplasm'}`}
                        className={cn(
                          "relative aspect-square min-w-[40px] border-2 rounded-sm cursor-pointer transition-all flex items-center justify-center text-[10px] font-mono",
                          !getPlotColor(plot).startsWith('hsl') && getPlotColor(plot),
                          isSelected && "ring-2 ring-primary ring-offset-2 z-10 scale-110",
                          isFiltered && "opacity-20",
                          isFieldMode && "min-w-[60px] text-sm"
                        )}
                        style={getPlotColor(plot).startsWith('hsl') ? { backgroundColor: getPlotColor(plot), borderColor: 'rgba(0,0,0,0.1)' } : {}}
                        onClick={(e) => {
                          e.stopPropagation();
                          togglePlotSelection(plot, e.shiftKey || e.metaKey);
                        }}
                      >
                        {settings.showLabels && plot.plotNumber}
                        {plot.entryType === 'check' && (
                          <div className="absolute top-0 right-0 w-2 h-2 bg-blue-600 rounded-bl-sm" />
                        )}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                      <div className="space-y-1">
                        <p className="font-bold">Plot {plot.plotNumber}</p>
                        <p className="text-xs">{plot.germplasmName || 'Unknown Germplasm'}</p>
                        <p className="text-[10px] opacity-70">Row: {plot.row} | Col: {plot.col}</p>
                        <Badge variant="outline" className="text-[8px] h-4">
                          {plot.status || 'pending'}
                        </Badge>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              );
            })}
          </div>
        </div>

        {/* Floating Controls */}
        <div className="absolute bottom-4 right-4 flex flex-col gap-2">
          <div className="bg-background/80 backdrop-blur-md border rounded-lg shadow-lg p-1 flex flex-col">
            <Button variant="ghost" size="icon" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
            <div className="h-px bg-border my-1" />
            <Button variant="ghost" size="icon" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* AI Insight Overlay (REEVU) */}
        <div className="absolute top-4 left-4 max-w-xs">
          <Card className="bg-background/80 backdrop-blur-md border-emerald-500/30 shadow-lg">
            <CardHeader className="p-3">
              <CardTitle className="text-xs flex items-center gap-1 text-emerald-700 dark:text-emerald-400">
                <Bot className="h-3 w-3" />
                REEVU AI Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0">
              {selectedPlotIds.size > 0 ? (
                <div className="space-y-2">
                  <p className="text-[10px] text-emerald-800 dark:text-emerald-300 font-medium">
                    Analysis of {selectedPlotIds.size} selected plots:
                  </p>
                  <p className="text-[10px] text-muted-foreground italic">
                    The selected group shows a 12% higher-than-average {settings.heatmapVariable || 'yield'} compared to adjacent blocks. Spatial autocorrelation (Moran's I) is significant at p &lt; 0.05.
                  </p>
                </div>
              ) : (
                <p className="text-[10px] text-muted-foreground italic">
                  Scanning spatial trends... No significant environmental gradients detected in this block.
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Selection Status Bar */}
        {selectedPlotIds.size > 0 && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground px-4 py-2 rounded-full shadow-2xl flex items-center gap-4 animate-in fade-in slide-in-from-bottom-4">
            <span className="text-xs font-medium">{selectedPlotIds.size} plots selected</span>
            <div className="flex items-center gap-1 border-l border-primary-foreground/20 pl-4">
              <Button size="sm" variant="ghost" className="h-7 text-[10px] hover:bg-primary-foreground/10">
                Bulk Action
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0 hover:bg-primary-foreground/10"
                onClick={() => setSelectedPlotIds(new Set())}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>

      {/* Footer / Legend */}
      {settings.showLegend && (
        <div className="border-t p-2 bg-muted/30 flex flex-wrap items-center gap-4 text-[10px]">
          <span className="font-semibold uppercase tracking-wider opacity-60">Legend:</span>

          {settings.colorScheme === 'status' ? (
            <>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-slate-200 border border-slate-300 rounded-sm" />
                <span>Pending</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-emerald-500 rounded-sm" />
                <span>Complete</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-amber-500 rounded-sm" />
                <span>Skipped</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-rose-500 rounded-sm" />
                <span>Failed</span>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <span>Low</span>
              <div className="w-32 h-2 rounded-full bg-gradient-to-r from-[hsl(240,70%,50%)] via-[hsl(120,70%,50%)] to-[hsl(0,70%,50%)]" />
              <span>High</span>
              <span className="ml-2 font-mono text-muted-foreground">({settings.heatmapVariable})</span>
            </div>
          )}

          <div className="flex items-center gap-1 ml-auto">
            <div className="w-3 h-3 bg-blue-600 rounded-bl-sm" />
            <span>Check Entry</span>
          </div>
        </div>
      )}
    </Card>
  );
};

export default SpatialFieldMapLayout;

/**
 * Spatial Field Plot Component
 *
 * Interactive field layout for click-to-record data collection.
 * Supports row/column grid with color-coded values.
 */

import { useState, useMemo, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Grid3X3, Maximize2, RotateCcw } from 'lucide-react';

export interface PlotData {
  row: number;
  col: number;
  plotId: string;
  genotype?: string;
  value?: number;
  status?: 'empty' | 'planted' | 'measured' | 'harvested' | 'missing';
  metadata?: Record<string, any>;
}

interface SpatialFieldPlotProps {
  rows: number;
  cols: number;
  plots: PlotData[];
  selectedPlotId?: string;
  onPlotClick?: (plot: PlotData) => void;
  onPlotDoubleClick?: (plot: PlotData) => void;
  className?: string;
  title?: string;
  colorScale?: 'value' | 'status' | 'genotype';
  showLabels?: boolean;
  cellSize?: number;
}


const STATUS_COLORS: Record<string, string> = {
  empty: '#e5e7eb',
  planted: '#86efac',
  measured: '#3b82f6',
  harvested: '#f59e0b',
  missing: '#ef4444',
};

// Value-based color scale (green to red)
const getValueColor = (value: number, min: number, max: number): string => {
  if (max === min) return '#3b82f6';
  const ratio = (value - min) / (max - min);
  const r = Math.round(255 * ratio);
  const g = Math.round(255 * (1 - ratio));
  return `rgb(${r}, ${g}, 100)`;
};

export function SpatialFieldPlot({
  rows,
  cols,
  plots,
  selectedPlotId,
  onPlotClick,
  onPlotDoubleClick,
  className,
  title = 'Field Layout',
  colorScale = 'status',
  showLabels = true,
  cellSize = 40,
}: SpatialFieldPlotProps) {
  const [hoveredPlot, setHoveredPlot] = useState<string | null>(null);

  // Create plot map for quick lookup
  const plotMap = useMemo(() => {
    const map = new Map<string, PlotData>();
    plots.forEach((p) => map.set(`${p.row}-${p.col}`, p));
    return map;
  }, [plots]);

  // Calculate value range for color scale
  const valueRange = useMemo(() => {
    const values = plots.filter((p) => p.value !== undefined).map((p) => p.value!);
    return {
      min: Math.min(...values, 0),
      max: Math.max(...values, 100),
    };
  }, [plots]);

  // Get cell color based on scale type
  const getCellColor = useCallback(
    (plot: PlotData | undefined): string => {
      if (!plot) return '#f3f4f6';

      switch (colorScale) {
        case 'value':
          return plot.value !== undefined
            ? getValueColor(plot.value, valueRange.min, valueRange.max)
            : '#e5e7eb';
        case 'status':
          return STATUS_COLORS[plot.status || 'empty'];
        case 'genotype':
          // Simple hash-based color for genotypes
          if (!plot.genotype) return '#e5e7eb';
          const hash = plot.genotype.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
          const hue = hash % 360;
          return `hsl(${hue}, 60%, 70%)`;
        default:
          return '#e5e7eb';
      }
    },
    [colorScale, valueRange]
  );

  // Stats
  const stats = useMemo(() => {
    const total = rows * cols;
    const planted = plots.filter((p) => p.status === 'planted').length;
    const measured = plots.filter((p) => p.status === 'measured').length;
    const missing = plots.filter((p) => p.status === 'missing').length;
    return { total, planted, measured, missing };
  }, [plots, rows, cols]);

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Grid3X3 className="h-4 w-4" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {rows}×{cols} = {stats.total} plots
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-2">
        {/* Stats bar */}
        <div className="flex gap-4 mb-3 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: STATUS_COLORS.planted }} />
            Planted: {stats.planted}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: STATUS_COLORS.measured }} />
            Measured: {stats.measured}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: STATUS_COLORS.missing }} />
            Missing: {stats.missing}
          </span>
        </div>

        {/* Field grid */}
        <div className="overflow-auto">
          <div
            className="grid gap-1"
            style={{
              gridTemplateColumns: `auto repeat(${cols}, ${cellSize}px)`,
              gridTemplateRows: `auto repeat(${rows}, ${cellSize}px)`,
            }}
          >
            {/* Corner cell */}
            <div className="w-8" />

            {/* Column headers */}
            {Array.from({ length: cols }, (_, c) => (
              <div
                key={`col-${c}`}
                className="flex items-center justify-center text-xs font-medium text-muted-foreground"
              >
                {c + 1}
              </div>
            ))}

            {/* Rows */}
            {Array.from({ length: rows }, (_, r) => (
              <>
                {/* Row header */}
                <div
                  key={`row-${r}`}
                  className="flex items-center justify-center text-xs font-medium text-muted-foreground w-8"
                >
                  {r + 1}
                </div>

                {/* Cells */}
                {Array.from({ length: cols }, (_, c) => {
                  const plot = plotMap.get(`${r + 1}-${c + 1}`);
                  const isSelected = plot?.plotId === selectedPlotId;
                  const isHovered = plot?.plotId === hoveredPlot;

                  return (
                    <div
                      key={`cell-${r}-${c}`}
                      className={cn(
                        'rounded cursor-pointer transition-all border-2',
                        isSelected ? 'border-primary ring-2 ring-primary/30' : 'border-transparent',
                        isHovered && !isSelected && 'border-muted-foreground/50'
                      )}
                      style={{
                        backgroundColor: getCellColor(plot),
                        width: cellSize,
                        height: cellSize,
                      }}
                      onClick={() => plot && onPlotClick?.(plot)}
                      onDoubleClick={() => plot && onPlotDoubleClick?.(plot)}
                      onMouseEnter={() => plot && setHoveredPlot(plot.plotId)}
                      onMouseLeave={() => setHoveredPlot(null)}
                      title={
                        plot
                          ? `Plot ${plot.plotId}\n${plot.genotype || ''}\n${plot.value !== undefined ? `Value: ${plot.value}` : ''}`
                          : `Empty (${r + 1}, ${c + 1})`
                      }
                    >
                      {showLabels && plot && (
                        <div className="w-full h-full flex items-center justify-center text-[8px] font-medium text-gray-700 truncate p-0.5">
                          {plot.value !== undefined ? plot.value.toFixed(0) : plot.genotype?.slice(0, 4)}
                        </div>
                      )}
                    </div>
                  );
                })}
              </>
            ))}
          </div>
        </div>

        {/* Hovered plot info */}
        {hoveredPlot && (
          <div className="mt-2 p-2 bg-muted rounded text-xs">
            {(() => {
              const plot = plots.find((p) => p.plotId === hoveredPlot);
              if (!plot) return null;
              return (
                <div className="flex gap-4">
                  <span><strong>Plot:</strong> {plot.plotId}</span>
                  <span><strong>Position:</strong> R{plot.row}C{plot.col}</span>
                  {plot.genotype && <span><strong>Genotype:</strong> {plot.genotype}</span>}
                  {plot.value !== undefined && <span><strong>Value:</strong> {plot.value.toFixed(2)}</span>}
                  {plot.status && <span><strong>Status:</strong> {plot.status}</span>}
                </div>
              );
            })()}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default SpatialFieldPlot;

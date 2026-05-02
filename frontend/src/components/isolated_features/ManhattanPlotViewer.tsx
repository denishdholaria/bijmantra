import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Info, ZoomIn, ZoomOut, RefreshCw } from 'lucide-react';

/**
 * SNP Data Interface for Manhattan Plot
 */
export interface SNPData {
  markerName: string;
  chromosome: string;
  position: number;
  p_value: number;
  log_p?: number; // -log10(p-value)
}

/**
 * Component Props
 */
interface ManhattanPlotViewerProps {
  data: SNPData[];
  title?: string;
  threshold?: number;
  className?: string;
  onSNPClick?: (snp: SNPData) => void;
}

/**
 * Chromosome Information
 */
interface ChromosomeInfo {
  name: string;
  length: number;
  offset: number;
  color: string;
}

const CHROMOSOME_COLORS = [
  '#3b82f6', // blue-500
  '#60a5fa', // blue-400
];

export const ManhattanPlotViewer: React.FC<ManhattanPlotViewerProps> = ({
  data,
  title = "Manhattan Plot Viewer",
  threshold: initialThreshold = 5.0,
  className,
  onSNPClick
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [threshold, setThreshold] = useState(initialThreshold);
  const [hoveredSNP, setHoveredSNP] = useState<SNPData | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // 1. Process Data & Calculate Chromosome Offsets
  const { processedData, chromosomes, totalGenomicLength, maxLogP } = useMemo(() => {
    // Sort by chromosome and position
    const sortedData = [...data]
      .map(snp => ({
        ...snp,
        log_p: snp.log_p ?? -Math.log10(snp.p_value)
      }))
      .sort((a, b) => {
        const chrA = parseInt(a.chromosome) || 0;
        const chrB = parseInt(b.chromosome) || 0;
        if (chrA !== chrB) return chrA - chrB;
        return a.position - b.position;
      });

    const chrMap = new Map<string, { min: number; max: number }>();
    sortedData.forEach(snp => {
      const stats = chrMap.get(snp.chromosome) || { min: Infinity, max: -Infinity };
      stats.min = Math.min(stats.min, snp.position);
      stats.max = Math.max(stats.max, snp.position);
      chrMap.set(snp.chromosome, stats);
    });

    const chrs: ChromosomeInfo[] = [];
    let currentOffset = 0;

    // Convert map to sorted array of chromosomes
    const sortedChrNames = Array.from(chrMap.keys()).sort((a, b) => {
        const numA = parseInt(a);
        const numB = parseInt(b);
        if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
        return a.localeCompare(b);
    });

    sortedChrNames.forEach((name, index) => {
      const stats = chrMap.get(name)!;
      const length = stats.max - stats.min + 1000000; // Buffer
      chrs.push({
        name,
        length,
        offset: currentOffset,
        color: CHROMOSOME_COLORS[index % CHROMOSOME_COLORS.length]
      });
      currentOffset += length;
    });

    return {
      processedData: sortedData,
      chromosomes: chrs,
      totalGenomicLength: currentOffset,
      maxLogP: Math.max(...sortedData.map(d => d.log_p!), threshold + 2)
    };
  }, [data, threshold]);

  // 2. Rendering Logic
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set dimensions
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 40, right: 20, bottom: 40, left: 60 };
    const innerWidth = width - padding.left - padding.right;
    const innerHeight = height - padding.top - padding.bottom;

    // Clear
    ctx.clearRect(0, 0, width, height);

    // Draw Axes
    ctx.strokeStyle = '#94a3b8'; // slate-400
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();

    // Mapping Functions
    const getX = (chrName: string, pos: number) => {
      const chr = chromosomes.find(c => c.name === chrName);
      if (!chr) return padding.left;
      const genomicPos = chr.offset + pos;
      return padding.left + (genomicPos / totalGenomicLength) * innerWidth;
    };

    const getY = (logP: number) => {
      return padding.top + innerHeight - (logP / maxLogP) * innerHeight;
    };

    // Draw Chromosome Regions & Labels
    chromosomes.forEach((chr) => {
      const xStart = getX(chr.name, 0);
      const xEnd = getX(chr.name, chr.length);

      // Draw label
      ctx.fillStyle = '#64748b'; // slate-500
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(chr.name, (xStart + xEnd) / 2, height - padding.bottom + 15);
    });

    // Draw Significance Threshold
    const thresholdY = getY(threshold);
    ctx.strokeStyle = '#ef4444'; // red-500
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding.left, thresholdY);
    ctx.lineTo(width - padding.right, thresholdY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw SNPs
    processedData.forEach(snp => {
      const x = getX(snp.chromosome, snp.position);
      const y = getY(snp.log_p!);

      const chr = chromosomes.find(c => c.name === snp.chromosome);
      ctx.fillStyle = snp.log_p! >= threshold ? '#ef4444' : (chr?.color || '#3b82f6');

      ctx.beginPath();
      ctx.arc(x, y, snp.log_p! >= threshold ? 2.5 : 1.5, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw Y-axis labels
    ctx.fillStyle = '#64748b';
    ctx.textAlign = 'right';
    for (let i = 0; i <= maxLogP; i += 2) {
      const y = getY(i);
      ctx.fillText(i.toString(), padding.left - 10, y + 4);
    }

    // Y-axis Title
    ctx.save();
    ctx.translate(20, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillText('-log10(p-value)', 0, 0);
    ctx.restore();
  }, [chromosomes, totalGenomicLength, maxLogP, threshold, processedData]);

  useEffect(() => {
    render();

    const handleResize = () => render();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [render]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const padding = { top: 40, right: 20, bottom: 40, left: 60 };
    const innerWidth = rect.width - padding.left - padding.right;
    const innerHeight = rect.height - padding.top - padding.bottom;

    const getX = (chrName: string, pos: number) => {
        const chr = chromosomes.find(c => c.name === chrName);
        if (!chr) return padding.left;
        const genomicPos = chr.offset + pos;
        return padding.left + (genomicPos / totalGenomicLength) * innerWidth;
    };

    const getY = (logP: number) => {
        return padding.top + innerHeight - (logP / maxLogP) * innerHeight;
    };

    // Find nearest SNP (simple distance check)
    let nearest: SNPData | null = null;
    let minDist = 10; // Threshold pixels

    processedData.forEach(snp => {
      const x = getX(snp.chromosome, snp.position);
      const y = getY(snp.log_p!);
      const dist = Math.sqrt((x - mouseX) ** 2 + (y - mouseY) ** 2);
      if (dist < minDist) {
        minDist = dist;
        nearest = snp;
      }
    });

    if (nearest) {
      setHoveredSNP(nearest);
      setTooltipPos({ x: mouseX, y: mouseY });
    } else {
      setHoveredSNP(null);
    }
  };

  return (
    <Card className={cn("w-full h-full flex flex-col", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle className="text-xl font-bold">{title}</CardTitle>
          <div className="flex gap-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><Info size={12} /> Total SNPs: {data.length}</span>
            <span className="flex items-center gap-1"><Info size={12} /> Significant: {processedData.filter(s => s.log_p! >= threshold).length}</span>
          </div>
        </div>
        <div className="flex items-center gap-4 bg-muted/50 p-2 rounded-lg">
            <div className="flex flex-col gap-1 w-32">
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Threshold: {threshold.toFixed(1)}</span>
                <Slider
                    value={[threshold]}
                    min={0} max={10} step={0.1}
                    onValueChange={(val) => setThreshold(val[0])}
                />
            </div>
            <div className="flex gap-1">
                <Badge variant="outline" className="h-8 cursor-pointer hover:bg-muted"><ZoomIn size={14} /></Badge>
                <Badge variant="outline" className="h-8 cursor-pointer hover:bg-muted"><ZoomOut size={14} /></Badge>
                <Badge variant="outline" className="h-8 cursor-pointer hover:bg-muted" onClick={() => setThreshold(initialThreshold)}><RefreshCw size={14} /></Badge>
            </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 min-h-[400px] relative p-0" ref={containerRef}>
        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-crosshair"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredSNP(null)}
          onClick={() => hoveredSNP && onSNPClick?.(hoveredSNP)}
        />

        {hoveredSNP && (
          <div
            className="absolute z-10 bg-background/95 border shadow-lg rounded-md p-2 text-xs pointer-events-none backdrop-blur-sm"
            style={{
              left: tooltipPos.x + 15,
              top: tooltipPos.y - 10,
              maxWidth: '200px'
            }}
          >
            <div className="font-bold border-b pb-1 mb-1">{hoveredSNP.markerName}</div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              <span className="text-muted-foreground">Chr:</span>
              <span className="text-right">{hoveredSNP.chromosome}</span>
              <span className="text-muted-foreground">Pos:</span>
              <span className="text-right">{(hoveredSNP.position / 1000000).toFixed(2)} Mb</span>
              <span className="text-muted-foreground">-log10(P):</span>
              <span className="text-right font-mono font-bold text-primary">{hoveredSNP.log_p?.toFixed(4)}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ManhattanPlotViewer;

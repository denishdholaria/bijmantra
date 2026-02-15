/**
 * Pedigree Viewer Component
 *
 * Interactive pedigree tree visualization using D3.
 * Supports zoom, pan, and node selection.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  RotateCcw,
} from 'lucide-react';

export interface PedigreeNode {
  id: string;
  name: string;
  generation?: number;
  sex?: 'M' | 'F' | 'U';
  motherId?: string;
  fatherId?: string;
  metadata?: Record<string, any>;
}

interface PedigreeViewerProps {
  nodes: PedigreeNode[];
  selectedId?: string;
  onNodeSelect?: (node: PedigreeNode) => void;
  className?: string;
  title?: string;
  showControls?: boolean;
  colorByGeneration?: boolean;
}

// Generation colors
const GENERATION_COLORS = [
  '#3b82f6', // blue - current
  '#10b981', // green - parents
  '#f59e0b', // amber - grandparents
  '#8b5cf6', // purple - great-grandparents
  '#ec4899', // pink - older
  '#6b7280', // gray - ancient
];

// Sex colors
const SEX_COLORS = {
  M: '#3b82f6',
  F: '#ec4899',
  U: '#6b7280',
};

export function PedigreeViewer({
  nodes,
  selectedId,
  onNodeSelect,
  className,
  title = 'Pedigree',
  showControls = true,
  colorByGeneration = true,
}: PedigreeViewerProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Build tree structure
  const buildTree = useCallback(() => {
    const nodeMap = new Map<string, PedigreeNode & { children: string[]; level: number }>();
    
    // Initialize nodes
    nodes.forEach((node) => {
      nodeMap.set(node.id, { ...node, children: [], level: 0 });
    });

    // Build parent-child relationships
    nodes.forEach((node) => {
      if (node.motherId && nodeMap.has(node.motherId)) {
        nodeMap.get(node.motherId)!.children.push(node.id);
      }
      if (node.fatherId && nodeMap.has(node.fatherId)) {
        nodeMap.get(node.fatherId)!.children.push(node.id);
      }
    });

    // Calculate levels (generations)
    const calculateLevel = (id: string, visited = new Set<string>()): number => {
      if (visited.has(id)) return 0;
      visited.add(id);
      
      const node = nodeMap.get(id);
      if (!node) return 0;

      let maxParentLevel = -1;
      if (node.motherId && nodeMap.has(node.motherId)) {
        maxParentLevel = Math.max(maxParentLevel, calculateLevel(node.motherId, visited));
      }
      if (node.fatherId && nodeMap.has(node.fatherId)) {
        maxParentLevel = Math.max(maxParentLevel, calculateLevel(node.fatherId, visited));
      }

      node.level = maxParentLevel + 1;
      return node.level;
    };

    // Find root nodes (no parents) and calculate levels
    nodes.forEach((node) => {
      if (!node.motherId && !node.fatherId) {
        calculateLevel(node.id);
      }
    });

    // Recalculate for all nodes
    nodes.forEach((node) => calculateLevel(node.id));

    return nodeMap;
  }, [nodes]);

  // Layout calculation
  const calculateLayout = useCallback(() => {
    const nodeMap = buildTree();
    const levels: Map<number, string[]> = new Map();

    // Group by level
    nodeMap.forEach((node, id) => {
      const level = node.level;
      if (!levels.has(level)) {
        levels.set(level, []);
      }
      levels.get(level)!.push(id);
    });

    // Calculate positions
    const nodeWidth = 120;
    const nodeHeight = 50;
    const levelGap = 80;
    const nodeGap = 20;

    const positions: Map<string, { x: number; y: number }> = new Map();
    const maxLevel = Math.max(...Array.from(levels.keys()));

    levels.forEach((nodeIds, level) => {
      const totalWidth = nodeIds.length * nodeWidth + (nodeIds.length - 1) * nodeGap;
      const startX = -totalWidth / 2;

      nodeIds.forEach((id, index) => {
        positions.set(id, {
          x: startX + index * (nodeWidth + nodeGap) + nodeWidth / 2,
          y: (maxLevel - level) * (nodeHeight + levelGap),
        });
      });
    });

    return { nodeMap, positions, nodeWidth, nodeHeight };
  }, [buildTree]);

  const { nodeMap, positions, nodeWidth, nodeHeight } = calculateLayout();

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.2, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.2, 0.3));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  // Wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.max(0.3, Math.min(3, z * delta)));
  };

  // Export as SVG
  const handleExport = () => {
    if (!svgRef.current) return;
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pedigree.svg';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Get node color
  const getNodeColor = (node: PedigreeNode & { level: number }) => {
    if (colorByGeneration) {
      return GENERATION_COLORS[Math.min(node.level, GENERATION_COLORS.length - 1)];
    }
    return SEX_COLORS[node.sex || 'U'];
  };

  // Calculate SVG viewBox
  const allPositions = Array.from(positions.values());
  const minX = Math.min(...allPositions.map((p) => p.x)) - nodeWidth;
  const maxX = Math.max(...allPositions.map((p) => p.x)) + nodeWidth;
  const minY = Math.min(...allPositions.map((p) => p.y)) - nodeHeight;
  const maxY = Math.max(...allPositions.map((p) => p.y)) + nodeHeight;
  const viewWidth = maxX - minX + 100;
  const viewHeight = maxY - minY + 100;

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          {showControls && (
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomOut} aria-label="Zoom out">
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span className="text-xs text-muted-foreground w-12 text-center">
                {Math.round(zoom * 100)}%
              </span>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomIn} aria-label="Zoom in">
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleReset} aria-label="Reset view">
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleExport} aria-label="Export pedigree">
                <Download className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div
          ref={containerRef}
          className="relative overflow-hidden bg-muted/30 rounded-b-lg"
          style={{ height: 400, cursor: isDragging ? 'grabbing' : 'grab' }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        >
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            viewBox={`${minX - 50} ${minY - 50} ${viewWidth} ${viewHeight}`}
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transformOrigin: 'center',
            }}
          >
            {/* Draw edges */}
            {nodes.map((node) => {
              const pos = positions.get(node.id);
              if (!pos) return null;

              const edges = [];
              if (node.motherId) {
                const motherPos = positions.get(node.motherId);
                if (motherPos) {
                  edges.push(
                    <path
                      key={`${node.id}-mother`}
                      d={`M ${pos.x} ${pos.y - nodeHeight / 2} 
                          C ${pos.x} ${pos.y - nodeHeight / 2 - 40},
                            ${motherPos.x} ${motherPos.y + nodeHeight / 2 + 40},
                            ${motherPos.x} ${motherPos.y + nodeHeight / 2}`}
                      fill="none"
                      stroke="#ec4899"
                      strokeWidth={2}
                      opacity={0.6}
                    />
                  );
                }
              }
              if (node.fatherId) {
                const fatherPos = positions.get(node.fatherId);
                if (fatherPos) {
                  edges.push(
                    <path
                      key={`${node.id}-father`}
                      d={`M ${pos.x} ${pos.y - nodeHeight / 2} 
                          C ${pos.x} ${pos.y - nodeHeight / 2 - 40},
                            ${fatherPos.x} ${fatherPos.y + nodeHeight / 2 + 40},
                            ${fatherPos.x} ${fatherPos.y + nodeHeight / 2}`}
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      opacity={0.6}
                    />
                  );
                }
              }
              return edges;
            })}

            {/* Draw nodes */}
            {Array.from(nodeMap.entries()).map(([id, node]) => {
              const pos = positions.get(id);
              if (!pos) return null;

              const isSelected = selectedId === id;
              const color = getNodeColor(node);

              return (
                <g
                  key={id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={() => onNodeSelect?.(node)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect
                    x={-nodeWidth / 2}
                    y={-nodeHeight / 2}
                    width={nodeWidth}
                    height={nodeHeight}
                    rx={8}
                    fill={isSelected ? color : 'white'}
                    stroke={color}
                    strokeWidth={isSelected ? 3 : 2}
                  />
                  <text
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize={12}
                    fontWeight={isSelected ? 600 : 400}
                    fill={isSelected ? 'white' : '#1f2937'}
                  >
                    {node.name.length > 12 ? node.name.slice(0, 12) + '...' : node.name}
                  </text>
                  {node.sex && (
                    <text
                      x={nodeWidth / 2 - 12}
                      y={-nodeHeight / 2 + 12}
                      fontSize={10}
                      fill={SEX_COLORS[node.sex]}
                    >
                      {node.sex === 'M' ? '♂' : node.sex === 'F' ? '♀' : '?'}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div className="absolute bottom-2 left-2 bg-background/80 rounded p-2 text-xs">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded" style={{ backgroundColor: '#ec4899' }} />
              <span>Maternal</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded" style={{ backgroundColor: '#3b82f6' }} />
              <span>Paternal</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default PedigreeViewer;

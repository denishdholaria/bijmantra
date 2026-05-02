import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { PedigreeNode } from '@/lib/api-client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface RecursivePedigreeGraphProps {
  data: PedigreeNode | null;
  width?: number;
  height?: number;
  onNodeClick?: (node: PedigreeNode) => void;
}

interface D3Node extends PedigreeNode {
  children?: D3Node[];
}

type TreeNode = d3.HierarchyPointNode<D3Node>;

const transformToD3 = (node: PedigreeNode): D3Node => {
  const children: D3Node[] = [];
  if (node.sire) children.push(transformToD3(node.sire));
  if (node.dam) children.push(transformToD3(node.dam));

  return {
    ...node,
    children: children.length > 0 ? children : undefined,
  };
};

export function RecursivePedigreeGraph({
  data,
  width = 800,
  height = 800,
  onNodeClick,
}: RecursivePedigreeGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);

  const hierarchyData = useMemo(() => (data ? transformToD3(data) : null), [data]);

  useEffect(() => {
    if (!hierarchyData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const radius = Math.min(width, height) / 2 - 80;

    const tree = d3.tree<D3Node>()
      .size([2 * Math.PI, radius])
      .separation((a: d3.HierarchyNode<D3Node>, b: d3.HierarchyNode<D3Node>) => (a.parent === b.parent ? 1 : 2) / (a.depth || 1));

    const root = d3.hierarchy(hierarchyData);
    const treeData = tree(root);

    const g = svg.append('g');

    // Zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
        g.attr('transform', event.transform.toString());
      });

    zoomRef.current = zoom;
    svg.call(zoom);

    // Initial transform: Center the graph
    const initialTransform = d3.zoomIdentity
      .translate(width / 2, height / 2)
      .scale(0.8);
    svg.call(zoom.transform, initialTransform);

    // Links
    g.append('g')
      .attr('fill', 'none')
      .attr('stroke', '#94a3b8') // Slate-400
      .attr('stroke-opacity', 0.4)
      .attr('stroke-width', 1.5)
      .selectAll('path')
      .data(treeData.links())
      .join('path')
      .attr('d', d3.linkRadial<d3.HierarchyPointLink<D3Node>, d3.HierarchyPointNode<D3Node>>()
        .angle((d: TreeNode) => d.x)
        .radius((d: TreeNode) => d.y));

    // Nodes
    const node = g.append('g')
      .selectAll('g')
      .data(treeData.descendants())
      .join('g')
      .attr('transform', (d: TreeNode) => `
        rotate(${d.x * 180 / Math.PI - 90})
        translate(${d.y},0)
      `);

    node.append('circle')
      .attr('fill', (d: TreeNode) => d.depth === 0 ? '#10b981' : '#059669') // Emerald-500 for root, Emerald-600 for others
      .attr('r', (d: TreeNode) => d.depth === 0 ? 8 : 5)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .on('click', (_event: MouseEvent, d: TreeNode) => {
        onNodeClick?.(d.data);
      })
      .attr('class', 'cursor-pointer transition-all hover:r-7 hover:fill-emerald-400')
      .append('title')
      .text((d: TreeNode) => `${d.data.name || d.data.id}\nGeneration: ${d.data.generation || d.depth}`);

    node.append('text')
      .attr('dy', '0.31em')
      .attr('x', (d: TreeNode) => d.x < Math.PI ? 10 : -10)
      .attr('text-anchor', (d: TreeNode) => d.x < Math.PI ? 'start' : 'end')
      .attr('transform', (d: TreeNode) => d.x >= Math.PI ? 'rotate(180)' : null)
      .style('font-size', '12px')
      .style('font-family', 'sans-serif')
      .style('font-weight', (d: TreeNode) => d.depth === 0 ? 'bold' : 'normal')
      .attr('fill', 'currentColor')
      .text((d: TreeNode) => d.data.name || d.data.id)
      .clone(true).lower()
      .attr('stroke', 'white')
      .attr('stroke-width', 3);

  }, [hierarchyData, width, height, onNodeClick]);

  if (!data) {
    return (
      <Card className="flex items-center justify-center h-[600px] bg-muted/10 border-dashed">
        <p className="text-muted-foreground">No pedigree data available</p>
      </Card>
    );
  }

  const handleZoomIn = () => {
    if (svgRef.current && zoomRef.current) {
      d3.select<SVGSVGElement, unknown>(svgRef.current).transition().call(zoomRef.current.scaleBy, 1.2);
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current && zoomRef.current) {
      d3.select<SVGSVGElement, unknown>(svgRef.current).transition().call(zoomRef.current.scaleBy, 0.8);
    }
  };

  const handleReset = () => {
    if (svgRef.current && zoomRef.current) {
      const initialTransform = d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(0.8);
      d3.select<SVGSVGElement, unknown>(svgRef.current)
        .transition()
        .duration(750)
        .call(zoomRef.current.transform, initialTransform);
    }
  };

  return (
    <Card className="relative w-full h-[600px] overflow-hidden bg-background border" ref={containerRef}>
      <TooltipProvider>
        <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="secondary" size="icon" onClick={handleZoomIn} aria-label="Zoom In">
                <ZoomIn className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">Zoom In</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="secondary" size="icon" onClick={handleZoomOut} aria-label="Zoom Out">
                <ZoomOut className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">Zoom Out</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="secondary" size="icon" onClick={handleReset} aria-label="Reset View">
                <RotateCcw className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">Reset View</TooltipContent>
          </Tooltip>
        </div>
      </TooltipProvider>
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${width} ${height}`}
        className="cursor-grab active:cursor-grabbing"
      />
    </Card>
  );
}

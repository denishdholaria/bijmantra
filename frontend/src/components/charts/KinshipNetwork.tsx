/**
 * Kinship Network Graph Component
 *
 * Force-directed graph visualization for genetic relationships.
 * Uses ECharts graph for performance with large datasets.
 */

import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { EChartsWrapper } from './EChartsWrapper';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useTheme } from '@/hooks/useTheme';

export interface KinshipNode {
  id: string;
  name: string;
  group?: string;
  size?: number;
}

export interface KinshipEdge {
  source: string;
  target: string;
  value: number; // Kinship coefficient (0-1)
}

interface KinshipNetworkProps {
  nodes: KinshipNode[];
  edges: KinshipEdge[];
  selectedId?: string;
  onNodeClick?: (node: KinshipNode) => void;
  className?: string;
  title?: string;
  height?: number;
  minEdgeValue?: number;
}


// Group colors
const GROUP_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899',
  '#06b6d4', '#84cc16', '#f97316', '#6366f1', '#14b8a6',
];

export function KinshipNetwork({
  nodes,
  edges,
  selectedId,
  onNodeClick,
  className,
  title = 'Kinship Network',
  height = 500,
  minEdgeValue = 0.1,
}: KinshipNetworkProps) {
  const { isDark } = useTheme();

  // Filter edges by minimum value
  const filteredEdges = useMemo(
    () => edges.filter((e) => e.value >= minEdgeValue),
    [edges, minEdgeValue]
  );

  // Get unique groups
  const groups = useMemo(() => {
    const uniqueGroups = [...new Set(nodes.map((n) => n.group).filter(Boolean))];
    return uniqueGroups as string[];
  }, [nodes]);

  // Build ECharts option
  const option: EChartsOption = useMemo(() => {
    // Map groups to colors
    const groupColorMap = new Map<string, string>();
    groups.forEach((g, i) => {
      groupColorMap.set(g, GROUP_COLORS[i % GROUP_COLORS.length]);
    });

    // Create categories for legend
    const categories = groups.map((g, i) => ({
      name: g,
      itemStyle: { color: GROUP_COLORS[i % GROUP_COLORS.length] },
    }));

    // Transform nodes
    const graphNodes = nodes.map((n) => {
      const label: {
        show: boolean;
        position: 'top' | 'left' | 'right' | 'bottom' | 'inside' | 'insideLeft' | 'insideRight' | 'insideTop' | 'insideBottom' | 'insideTopLeft' | 'insideBottomLeft' | 'insideTopRight' | 'insideBottomRight';
        fontSize: number;
        color: string;
      } = {
        show: true,
        position: 'right',
        fontSize: 10,
        color: isDark ? '#e5e7eb' : '#374151',
      };
      return {
        id: n.id,
        name: n.name,
        symbolSize: n.size || 20,
        category: groups.indexOf(n.group || ''),
        itemStyle: {
          color: n.group ? groupColorMap.get(n.group) : '#6b7280',
          borderColor: selectedId === n.id ? '#fff' : undefined,
          borderWidth: selectedId === n.id ? 3 : 0,
        },
        label,
      }
    });

    // Transform edges
    const graphEdges = filteredEdges.map((e) => ({
      source: e.source,
      target: e.target,
      value: e.value,
      lineStyle: {
        width: Math.max(1, e.value * 5),
        opacity: 0.3 + e.value * 0.5,
        color: isDark ? '#6b7280' : '#9ca3af',
      },
    }));

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            return `<strong>${params.data.name}</strong>`;
          }
          if (params.dataType === 'edge') {
            return `${params.data.source} ↔ ${params.data.target}<br/>
                    Kinship: ${params.data.value.toFixed(3)}`;
          }
          return '';
        },
      },
      legend: groups.length > 0 ? {
        data: groups,
        top: 10,
        textStyle: { color: isDark ? '#e5e7eb' : '#374151' },
      } : undefined,
      series: [
        {
          type: 'graph' as const,
          layout: 'force',
          data: graphNodes,
          links: graphEdges,
          categories: categories.length > 0 ? categories : undefined,
          roam: true,
          draggable: true,
          force: {
            repulsion: 200,
            gravity: 0.1,
            edgeLength: [50, 200],
            layoutAnimation: true,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: { width: 4 },
          },
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
          },
          lineStyle: {
            curveness: 0.1,
          },
        },
      ],
    };
  }, [nodes, filteredEdges, groups, selectedId, isDark]);

  const handleClick = (params: any) => {
    if (params.dataType === 'node' && onNodeClick) {
      const node = nodes.find((n) => n.id === params.data.id);
      if (node) onNodeClick(node);
    }
  };

  // Stats
  const stats = useMemo(() => {
    const avgKinship = edges.length > 0
      ? edges.reduce((sum, e) => sum + e.value, 0) / edges.length
      : 0;
    const maxKinship = edges.length > 0
      ? Math.max(...edges.map((e) => e.value))
      : 0;
    return { avgKinship, maxKinship, edgeCount: filteredEdges.length };
  }, [edges, filteredEdges]);

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {nodes.length} individuals
            </Badge>
            <Badge variant="outline" className="text-xs">
              {stats.edgeCount} connections
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-2">
        <EChartsWrapper
          option={option}
          style={{ height }}
          onEvents={{ click: handleClick }}
          opts={{ renderer: 'canvas' }}
        />
        <div className="flex justify-between mt-2 text-xs text-muted-foreground px-2">
          <span>Avg kinship: {stats.avgKinship.toFixed(3)}</span>
          <span>Max kinship: {stats.maxKinship.toFixed(3)}</span>
          <span>Min threshold: {minEdgeValue}</span>
        </div>
      </CardContent>
    </Card>
  );
}

export default KinshipNetwork;

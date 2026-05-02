/**
 * AMMI Biplot Component
 *
 * Additive Main effects and Multiplicative Interaction biplot
 * for G×E (Genotype × Environment) analysis.
 */

import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { EChartsWrapper } from './EChartsWrapper';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTheme } from '@/hooks/useTheme';

export interface AMMIData {
  genotypes: {
    id: string;
    name: string;
    mean: number;
    pc1: number;
    pc2: number;
  }[];
  environments: {
    id: string;
    name: string;
    mean: number;
    pc1: number;
    pc2: number;
  }[];
  varianceExplained: {
    pc1: number;
    pc2: number;
  };
}

interface AMMIBiplotProps {
  data: AMMIData;
  className?: string;
  title?: string;
  height?: number;
  showMeanAxis?: boolean;
  onGenotypeClick?: (id: string) => void;
  onEnvironmentClick?: (id: string) => void;
}

export function AMMIBiplot({
  data,
  className,
  title = 'AMMI Biplot',
  height = 500,
  showMeanAxis = true,
  onGenotypeClick,
  onEnvironmentClick,
}: AMMIBiplotProps) {
  const { isDark } = useTheme();

  const option: EChartsOption = useMemo(() => {
    const { genotypes, environments, varianceExplained } = data;

    // Calculate axis ranges
    const allPC1 = [...genotypes.map((g) => g.pc1), ...environments.map((e) => e.pc1)];
    const allPC2 = [...genotypes.map((g) => g.pc2), ...environments.map((e) => e.pc2)];
    const pc1Range = Math.max(Math.abs(Math.min(...allPC1)), Math.abs(Math.max(...allPC1))) * 1.2;
    const pc2Range = Math.max(Math.abs(Math.min(...allPC2)), Math.abs(Math.max(...allPC2))) * 1.2;

    // Genotype scatter data
    const genotypeData = genotypes.map((g) => ({
      value: [g.pc1, g.pc2],
      name: g.name,
      id: g.id,
      mean: g.mean,
      itemStyle: { color: '#3b82f6' },
    }));

    // Environment scatter data
    const environmentData = environments.map((e) => ({
      value: [e.pc1, e.pc2],
      name: e.name,
      id: e.id,
      mean: e.mean,
      itemStyle: { color: '#10b981' },
    }));

    // Environment vectors (lines from origin)
    const envVectors = environments.map((e) => ({
      coords: [[0, 0], [e.pc1, e.pc2]],
      name: e.name,
    }));

    return {
      backgroundColor: 'transparent',
      title: {
        show: false,
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const { name, value, data } = params;
          return `<strong>${name}</strong><br/>
                  PC1: ${value[0].toFixed(3)}<br/>
                  PC2: ${value[1].toFixed(3)}<br/>
                  Mean: ${data.mean?.toFixed(2) || 'N/A'}`;
        },
      },
      legend: {
        data: ['Genotypes', 'Environments'],
        top: 10,
        textStyle: { color: isDark ? '#e5e7eb' : '#374151' },
      },
      grid: {
        left: 60,
        right: 40,
        top: 60,
        bottom: 60,
      },
      xAxis: {
        type: 'value',
        name: `PC1 (${varianceExplained.pc1.toFixed(1)}%)`,
        nameLocation: 'middle',
        nameGap: 35,
        min: -pc1Range,
        max: pc1Range,
        axisLine: { lineStyle: { color: isDark ? '#4b5563' : '#d1d5db' } },
        splitLine: { lineStyle: { color: isDark ? '#374151' : '#e5e7eb' } },
        axisLabel: { color: isDark ? '#9ca3af' : '#6b7280' },
        nameTextStyle: { color: isDark ? '#e5e7eb' : '#374151' },
      },
      yAxis: {
        type: 'value',
        name: `PC2 (${varianceExplained.pc2.toFixed(1)}%)`,
        nameLocation: 'middle',
        nameGap: 45,
        min: -pc2Range,
        max: pc2Range,
        axisLine: { lineStyle: { color: isDark ? '#4b5563' : '#d1d5db' } },
        splitLine: { lineStyle: { color: isDark ? '#374151' : '#e5e7eb' } },
        axisLabel: { color: isDark ? '#9ca3af' : '#6b7280' },
        nameTextStyle: { color: isDark ? '#e5e7eb' : '#374151' },
      },
      series: [
        // Reference lines (axes through origin)
        {
          type: 'line',
          data: [[-pc1Range, 0], [pc1Range, 0]],
          lineStyle: { color: isDark ? '#4b5563' : '#9ca3af', type: 'dashed', width: 1 },
          symbol: 'none',
          silent: true,
        },
        {
          type: 'line',
          data: [[0, -pc2Range], [0, pc2Range]],
          lineStyle: { color: isDark ? '#4b5563' : '#9ca3af', type: 'dashed', width: 1 },
          symbol: 'none',
          silent: true,
        },
        // Environment vectors
        {
          type: 'lines',
          coordinateSystem: 'cartesian2d',
          data: envVectors,
          lineStyle: {
            color: '#10b981',
            width: 1.5,
            opacity: 0.6,
          },
          effect: {
            show: false,
          },
          silent: true,
        },
        // Genotypes
        {
          name: 'Genotypes',
          type: 'scatter',
          data: genotypeData,
          symbolSize: 12,
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
            fontSize: 10,
            color: isDark ? '#93c5fd' : '#2563eb',
          },
          emphasis: {
            scale: 1.5,
            label: { fontWeight: 'bold' },
          },
        },
        // Environments
        {
          name: 'Environments',
          type: 'scatter',
          data: environmentData,
          symbolSize: 14,
          symbol: 'diamond',
          label: {
            show: true,
            position: 'top',
            formatter: '{b}',
            fontSize: 10,
            color: isDark ? '#6ee7b7' : '#059669',
          },
          emphasis: {
            scale: 1.5,
            label: { fontWeight: 'bold' },
          },
        },
      ],
    };
  }, [data, isDark]);

  const handleClick = (params: any) => {
    if (params.seriesName === 'Genotypes' && onGenotypeClick) {
      onGenotypeClick(params.data.id);
    } else if (params.seriesName === 'Environments' && onEnvironmentClick) {
      onEnvironmentClick(params.data.id);
    }
  };

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-2">
        <EChartsWrapper
          option={option}
          style={{ height }}
          onEvents={{ click: handleClick }}
          opts={{ renderer: 'canvas' }}
        />
        <div className="flex justify-center gap-6 mt-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-blue-500" />
            <span>Genotypes (circles)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rotate-45 bg-emerald-500" />
            <span>Environments (diamonds)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default AMMIBiplot;

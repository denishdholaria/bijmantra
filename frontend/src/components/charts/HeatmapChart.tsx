/**
 * Heatmap Chart Component
 * 
 * ECharts-based heatmap for correlation matrices, LD plots, etc.
 * Handles large datasets efficiently with WebGL rendering.
 */

import { useMemo } from 'react';
import { EChartsWrapper } from './EChartsWrapper';
import type { EChartsOption } from 'echarts';
import { useTheme } from '@/hooks/useTheme';

export interface HeatmapData {
  x: string[];
  y: string[];
  values: number[][]; // [row][col] format
}

interface HeatmapChartProps {
  data: HeatmapData;
  title?: string;
  colorRange?: [string, string, string]; // [low, mid, high]
  minValue?: number;
  maxValue?: number;
  showLabels?: boolean;
  height?: number | string;
  onCellClick?: (x: string, y: string, value: number) => void;
  className?: string;
}

export function HeatmapChart({
  data,
  title,
  colorRange = ['#3b82f6', '#fef3c7', '#ef4444'], // blue -> yellow -> red
  minValue,
  maxValue,
  showLabels = true,
  height = 400,
  onCellClick,
  className,
}: HeatmapChartProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Transform data for ECharts format: [x, y, value]
  const chartData = useMemo(() => {
    const result: [number, number, number][] = [];
    data.values.forEach((row, rowIdx) => {
      row.forEach((value, colIdx) => {
        result.push([colIdx, rowIdx, value]);
      });
    });
    return result;
  }, [data.values]);

  // Calculate min/max if not provided
  const [computedMin, computedMax] = useMemo(() => {
    const flatValues = data.values.flat();
    return [
      minValue ?? Math.min(...flatValues),
      maxValue ?? Math.max(...flatValues),
    ];
  }, [data.values, minValue, maxValue]);

  const option: EChartsOption = useMemo(() => ({
    title: title ? {
      text: title,
      left: 'center',
      textStyle: {
        color: isDark ? '#e5e7eb' : '#1f2937',
      },
    } : undefined,
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const [x, y, value] = params.data;
        return `${data.x[x]} × ${data.y[y]}<br/>Value: <strong>${value.toFixed(3)}</strong>`;
      },
    },
    grid: {
      top: title ? 60 : 20,
      bottom: 80,
      left: 100,
      right: 40,
    },
    xAxis: {
      type: 'category',
      data: data.x,
      splitArea: { show: true },
      axisLabel: {
        rotate: 45,
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: data.x.length > 20 ? 8 : 10,
      },
    },
    yAxis: {
      type: 'category',
      data: data.y,
      splitArea: { show: true },
      axisLabel: {
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: data.y.length > 20 ? 8 : 10,
      },
    },
    visualMap: {
      min: computedMin,
      max: computedMax,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      inRange: {
        color: colorRange,
      },
      textStyle: {
        color: isDark ? '#9ca3af' : '#6b7280',
      },
    },
    series: [{
      name: 'Heatmap',
      type: 'heatmap',
      data: chartData,
      label: {
        show: showLabels && data.x.length <= 15 && data.y.length <= 15,
        formatter: (params: any) => params.data[2].toFixed(2),
        fontSize: 9,
        color: isDark ? '#e5e7eb' : '#1f2937',
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
      },
    }],
  }), [data, chartData, title, colorRange, computedMin, computedMax, showLabels, isDark]);

  const handleClick = (params: any) => {
    if (onCellClick && params.data) {
      const [x, y, value] = params.data;
      onCellClick(data.x[x], data.y[y], value);
    }
  };

  return (
    <EChartsWrapper
      option={option}
      style={{ height, width: '100%' }}
      className={className}
      onEvents={{ click: handleClick }}
      opts={{ renderer: 'canvas' }}
    />
  );
}

export default HeatmapChart;

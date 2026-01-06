/**
 * Correlation Matrix Component
 * 
 * Specialized heatmap for trait correlations with significance indicators.
 */

import { useMemo } from 'react';
import { EChartsWrapper } from './EChartsWrapper';
import type { EChartsOption } from '@/lib/echarts';
import { useTheme } from '@/hooks/useTheme';

export interface CorrelationData {
  traits: string[];
  correlations: number[][]; // Symmetric matrix
  pValues?: number[][]; // Optional p-values for significance
}

interface CorrelationMatrixProps {
  data: CorrelationData;
  title?: string;
  significanceLevel?: number; // Default 0.05
  showValues?: boolean;
  height?: number | string;
  onCellClick?: (trait1: string, trait2: string, correlation: number, pValue?: number) => void;
  className?: string;
}

export function CorrelationMatrix({
  data,
  title = 'Trait Correlation Matrix',
  significanceLevel = 0.05,
  showValues = true,
  height = 500,
  onCellClick,
  className,
}: CorrelationMatrixProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Transform data for ECharts
  const chartData = useMemo(() => {
    const result: [number, number, number, boolean][] = [];
    data.correlations.forEach((row, rowIdx) => {
      row.forEach((value, colIdx) => {
        const isSignificant = data.pValues 
          ? data.pValues[rowIdx][colIdx] < significanceLevel 
          : true;
        result.push([colIdx, rowIdx, value, isSignificant]);
      });
    });
    return result;
  }, [data, significanceLevel]);

  const option: EChartsOption = useMemo(() => ({
    title: {
      text: title,
      left: 'center',
      textStyle: {
        color: isDark ? '#e5e7eb' : '#1f2937',
      },
    },
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const [x, y, value, isSignificant] = params.data;
        const trait1 = data.traits[x];
        const trait2 = data.traits[y];
        const pValue = data.pValues?.[y]?.[x];
        
        let html = `<strong>${trait1}</strong> × <strong>${trait2}</strong><br/>`;
        html += `r = ${value.toFixed(3)}`;
        if (pValue !== undefined) {
          html += `<br/>p = ${pValue < 0.001 ? '<0.001' : pValue.toFixed(3)}`;
          html += isSignificant ? ' ✓' : ' (ns)';
        }
        return html;
      },
    },
    grid: {
      top: 80,
      bottom: 100,
      left: 120,
      right: 60,
    },
    xAxis: {
      type: 'category',
      data: data.traits,
      splitArea: { show: true },
      axisLabel: {
        rotate: 45,
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: data.traits.length > 15 ? 9 : 11,
      },
    },
    yAxis: {
      type: 'category',
      data: data.traits,
      splitArea: { show: true },
      axisLabel: {
        color: isDark ? '#9ca3af' : '#6b7280',
        fontSize: data.traits.length > 15 ? 9 : 11,
      },
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      inRange: {
        color: ['#3b82f6', '#ffffff', '#ef4444'], // Blue (negative) -> White -> Red (positive)
      },
      textStyle: {
        color: isDark ? '#9ca3af' : '#6b7280',
      },
      text: ['Positive', 'Negative'],
    },
    series: [{
      name: 'Correlation',
      type: 'heatmap',
      data: chartData.map(([x, y, value, isSignificant]) => ({
        value: [x, y, value],
        itemStyle: {
          opacity: isSignificant ? 1 : 0.4,
        },
      })),
      label: {
        show: showValues && data.traits.length <= 12,
        formatter: (params: any) => {
          const value = params.data.value[2];
          return value.toFixed(2);
        },
        fontSize: 10,
        color: isDark ? '#e5e7eb' : '#1f2937',
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
      },
    }],
  }), [data, chartData, title, showValues, isDark]);

  const handleClick = (params: any) => {
    if (onCellClick && params.data) {
      const [x, y, value] = params.data.value;
      const pValue = data.pValues?.[y]?.[x];
      onCellClick(data.traits[x], data.traits[y], value, pValue);
    }
  };

  return (
    <EChartsWrapper
      option={option}
      style={{ height, width: '100%' }}
      className={className}
      onEvents={{ click: handleClick }}
    />
  );
}

export default CorrelationMatrix;

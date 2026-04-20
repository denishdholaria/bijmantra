/**
 * Scatter Plot Component
 *
 * ECharts-based scatter plot for PCA, GWAS Manhattan plots, etc.
 * Uses WebGL for large datasets (100K+ points).
 */

import { useMemo } from "react";
import { EChartsWrapper } from "./EChartsWrapper";
import type { EChartsOption } from "echarts";
import { useTheme } from "@/hooks/useTheme";

export interface ScatterPoint {
  x: number;
  y: number;
  label?: string;
  group?: string;
  size?: number;
  color?: string;
}

interface ScatterPlotProps {
  data: ScatterPoint[];
  title?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  showLegend?: boolean;
  colorByGroup?: boolean;
  height?: number | string;
  onPointClick?: (point: ScatterPoint) => void;
  className?: string;
}

// Color palette for groups
const GROUP_COLORS = [
  "#3b82f6",
  "#ef4444",
  "#22c55e",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#84cc16",
  "#f97316",
  "#6366f1",
];

export function ScatterPlot({
  data,
  title,
  xAxisLabel = "X",
  yAxisLabel = "Y",
  showLegend = true,
  colorByGroup = true,
  height = 400,
  onPointClick,
  className,
}: ScatterPlotProps) {
  const { isDark } = useTheme();

  // Group data by group field
  const groupedData = useMemo(() => {
    if (!colorByGroup) {
      return { All: data };
    }

    const groups: Record<string, ScatterPoint[]> = {};
    data.forEach((point) => {
      const group = point.group || "Unknown";
      if (!groups[group]) groups[group] = [];
      groups[group].push(point);
    });
    return groups;
  }, [data, colorByGroup]);

  // Create series for each group
  const series = useMemo(() => {
    return Object.entries(groupedData).map(([groupName, points], idx) => ({
      name: groupName,
      type: "scatter" as const,
      data: points.map((p) => ({
        value: [p.x, p.y],
        name: p.label,
        itemStyle: p.color ? { color: p.color } : undefined,
        symbolSize: p.size || 8,
      })),
      symbolSize: 8,
      itemStyle: {
        color: GROUP_COLORS[idx % GROUP_COLORS.length],
      },
      emphasis: {
        focus: "series" as const,
        itemStyle: {
          shadowBlur: 10,
          shadowColor: "rgba(0, 0, 0, 0.3)",
        },
      },
      // Use WebGL for large datasets
      large: points.length > 5000,
      largeThreshold: 5000,
    }));
  }, [groupedData]);

  const option: EChartsOption = useMemo(
    () => ({
      title: title
        ? {
            text: title,
            left: "center",
            textStyle: {
              color: isDark ? "#e5e7eb" : "#1f2937",
            },
          }
        : undefined,
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          const [x, y] = params.value;
          const label = params.name || "";
          return `${label ? `<strong>${label}</strong><br/>` : ""}${xAxisLabel}: ${x.toFixed(3)}<br/>${yAxisLabel}: ${y.toFixed(3)}`;
        },
      },
      legend:
        showLegend && Object.keys(groupedData).length > 1
          ? {
              top: title ? 30 : 10,
              textStyle: {
                color: isDark ? "#9ca3af" : "#6b7280",
              },
            }
          : undefined,
      grid: {
        top: title ? (showLegend ? 80 : 60) : showLegend ? 50 : 20,
        bottom: 60,
        left: 60,
        right: 40,
      },
      xAxis: {
        type: "value",
        name: xAxisLabel,
        nameLocation: "middle",
        nameGap: 30,
        nameTextStyle: {
          color: isDark ? "#9ca3af" : "#6b7280",
        },
        axisLabel: {
          color: isDark ? "#9ca3af" : "#6b7280",
        },
        splitLine: {
          lineStyle: {
            color: isDark ? "#374151" : "#e5e7eb",
          },
        },
      },
      yAxis: {
        type: "value",
        name: yAxisLabel,
        nameLocation: "middle",
        nameGap: 40,
        nameTextStyle: {
          color: isDark ? "#9ca3af" : "#6b7280",
        },
        axisLabel: {
          color: isDark ? "#9ca3af" : "#6b7280",
        },
        splitLine: {
          lineStyle: {
            color: isDark ? "#374151" : "#e5e7eb",
          },
        },
      },
      dataZoom: [
        {
          type: "inside",
          xAxisIndex: 0,
        },
        {
          type: "inside",
          yAxisIndex: 0,
        },
      ],
      toolbox: {
        feature: {
          dataZoom: {},
          restore: {},
          saveAsImage: {},
        },
        iconStyle: {
          borderColor: isDark ? "#9ca3af" : "#6b7280",
        },
      },
      series,
    }),
    [
      data,
      series,
      title,
      xAxisLabel,
      yAxisLabel,
      showLegend,
      groupedData,
      isDark,
    ]
  );

  const handleClick = (params: any) => {
    if (onPointClick && params.value) {
      const [x, y] = params.value;
      const point = data.find((p) => p.x === x && p.y === y);
      if (point) onPointClick(point);
    }
  };

  return (
    <EChartsWrapper
      key={`scatter-${data.length}-${Object.keys(groupedData).join("-")}`}
      option={option}
      style={{ height, width: "100%" }}
      className={className}
      onEvents={{ click: handleClick }}
      opts={{ renderer: "canvas" }}
      notMerge={true}
    />
  );
}

export default ScatterPlot;

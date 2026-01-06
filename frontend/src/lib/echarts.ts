/**
 * ECharts Modular Configuration
 * 
 * This module provides a tree-shaken ECharts setup that only includes
 * the chart types and components actually used in BijMantra.
 * 
 * Full ECharts: ~1,527 KB
 * Modular ECharts: ~400-600 KB (estimated)
 * 
 * Chart Types Used:
 * - HeatmapChart: Correlation matrices, LD plots
 * - ScatterChart: PCA plots, GWAS Manhattan plots, AMMI biplots
 * - LineChart: Live sensor data, time series
 * - GraphChart: Kinship networks, pedigree graphs
 * 
 * @see https://echarts.apache.org/handbook/en/basics/import#shrinking-bundle-size
 */

import * as echarts from 'echarts/core';

// Chart types
import { HeatmapChart } from 'echarts/charts';
import { ScatterChart } from 'echarts/charts';
import { LineChart } from 'echarts/charts';
import { GraphChart } from 'echarts/charts';

// Components
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  VisualMapComponent,
  VisualMapContinuousComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkLineComponent,
  MarkPointComponent,
} from 'echarts/components';

// Renderer - Canvas is smaller than SVG for most use cases
import { CanvasRenderer } from 'echarts/renderers';

// Register all components
echarts.use([
  // Charts
  HeatmapChart,
  ScatterChart,
  LineChart,
  GraphChart,
  // Components
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  VisualMapComponent,
  VisualMapContinuousComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkLineComponent,
  MarkPointComponent,
  // Renderer
  CanvasRenderer,
]);

// Re-export the configured echarts instance
export { echarts };

// Re-export types for convenience
export type { EChartsOption } from 'echarts';
export type { 
  HeatmapSeriesOption,
  ScatterSeriesOption,
  LineSeriesOption,
  GraphSeriesOption,
} from 'echarts/charts';

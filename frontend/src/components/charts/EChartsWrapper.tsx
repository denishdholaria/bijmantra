/**
 * ECharts Wrapper Component
 * 
 * Provides a consistent interface for ECharts across the application.
 * Uses tree-shaken ECharts imports — only the chart types and components
 * actually used in the app are bundled (~400KB savings vs full import).
 */

import { forwardRef } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import type { EChartsOption } from 'echarts';

// Renderers — canvas only (SVG not used in this app)
import { CanvasRenderer } from 'echarts/renderers';

// Chart types used across consumers
import { LineChart } from 'echarts/charts';
import { BarChart } from 'echarts/charts';
import { ScatterChart } from 'echarts/charts';
import { HeatmapChart as EChartsHeatmapChart } from 'echarts/charts';
import { GraphChart } from 'echarts/charts';
import { LinesChart } from 'echarts/charts';

// Components used in option configs
import { TitleComponent } from 'echarts/components';
import { TooltipComponent } from 'echarts/components';
import { LegendComponent } from 'echarts/components';
import { GridComponent } from 'echarts/components';
import { VisualMapComponent } from 'echarts/components';
import { DataZoomComponent } from 'echarts/components';
import { ToolboxComponent } from 'echarts/components';
import { MarkLineComponent } from 'echarts/components';

// Register all used modules
echarts.use([
  CanvasRenderer,
  LineChart, BarChart, ScatterChart, EChartsHeatmapChart, GraphChart, LinesChart,
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  VisualMapComponent, DataZoomComponent, ToolboxComponent, MarkLineComponent,
]);

interface EChartsWrapperProps {
  option: EChartsOption;
  style?: React.CSSProperties;
  className?: string;
  theme?: string | object;
  notMerge?: boolean;
  lazyUpdate?: boolean;
  showLoading?: boolean;
  loadingOption?: object;
  onEvents?: Record<string, (params: unknown) => void>;
  onChartReady?: (instance: unknown) => void;
  opts?: {
    devicePixelRatio?: number;
    renderer?: 'canvas' | 'svg';
    width?: number | 'auto' | null;
    height?: number | 'auto' | null;
    locale?: string;
  };
}

/**
 * ECharts component wrapper for consistent usage across the app.
 * Uses tree-shaken echarts via echarts-for-react/lib/core.
 */
export const EChartsWrapper = forwardRef<ReactEChartsCore, EChartsWrapperProps>(
  function EChartsWrapper(props, ref) {
    const {
      option,
      style,
      className,
      theme,
      notMerge = false,
      lazyUpdate = false,
      showLoading = false,
      loadingOption,
      onEvents,
      onChartReady,
      opts,
    } = props;

    return (
      <ReactEChartsCore
        ref={ref}
        echarts={echarts}
        option={option}
        style={style}
        className={className}
        theme={theme}
        notMerge={notMerge}
        lazyUpdate={lazyUpdate}
        showLoading={showLoading}
        loadingOption={loadingOption}
        onEvents={onEvents}
        onChartReady={onChartReady}
        opts={opts}
      />
    );
  }
);

export default EChartsWrapper;

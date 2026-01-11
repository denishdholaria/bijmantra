/**
 * ECharts Wrapper Component
 * 
 * Provides a consistent interface for ECharts across the application.
 * Uses the full ECharts library for stability in production builds.
 */

import { forwardRef } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

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
 */
export const EChartsWrapper = forwardRef<ReactECharts, EChartsWrapperProps>(
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
      <ReactECharts
        ref={ref}
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

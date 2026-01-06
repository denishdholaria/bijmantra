/**
 * ECharts Wrapper Component
 * 
 * This wrapper uses our modular ECharts configuration instead of the full library.
 * All chart components should use this wrapper instead of importing ReactECharts directly.
 * 
 * Savings: ~900KB from the bundle by only including used chart types.
 */

import { forwardRef } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { echarts } from '@/lib/echarts';
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
    width?: number | string;
    height?: number | string;
    locale?: string;
  };
}

/**
 * ECharts component using modular/tree-shaken echarts instance.
 * Use this instead of importing ReactECharts directly from 'echarts-for-react'.
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

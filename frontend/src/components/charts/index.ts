/**
 * Chart Components
 * 
 * High-performance charts for scientific data visualization.
 * Includes ECharts (WebGL for 100K+ points) and Recharts components.
 */

// ECharts-based components
export { HeatmapChart } from './HeatmapChart';
export type { HeatmapData } from './HeatmapChart';

export { ScatterPlot } from './ScatterPlot';
export type { ScatterPoint } from './ScatterPlot';

export { CorrelationMatrix } from './CorrelationMatrix';
export type { CorrelationData } from './CorrelationMatrix';

// Recharts-based components
export { TraitRadar } from './TraitRadar';

// Scientific visualization components
export { AMMIBiplot } from './AMMIBiplot';
export type { AMMIData } from './AMMIBiplot';

export { PedigreeViewer } from './PedigreeViewer';
export type { PedigreeNode } from './PedigreeViewer';

export { SpatialFieldPlot } from './SpatialFieldPlot';
export type { PlotData } from './SpatialFieldPlot';

export { KinshipNetwork } from './KinshipNetwork';
export type { KinshipNode, KinshipEdge } from './KinshipNetwork';

// Real-time streaming charts
export { LiveSensorChart } from './LiveSensorChart';

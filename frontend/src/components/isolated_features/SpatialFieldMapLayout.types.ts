/**
 * Spatial Field Map Types
 *
 * Based on BrAPI v2.1 specifications for Observation Units and Spatial Layouts.
 */

export type EntryType = 'check' | 'test' | 'filler' | 'border';

export type PlotStatus = 'pending' | 'complete' | 'skipped' | 'failed';

export interface Position {
  x: number;
  y: number;
}

export interface PlotObservation {
  variableDbId: string;
  variableName: string;
  value: string | number;
  timestamp?: string;
  collector?: string;
}

export interface FieldPlot {
  id: string;
  plotNumber: string;
  row: number;
  col: number;
  blockNumber?: number;
  replicate?: number;
  entryType?: EntryType;
  germplasmName?: string;
  germplasmDbId?: string;
  status?: PlotStatus;
  observations?: PlotObservation[];
  additionalInfo?: Record<string, unknown>;
}

export interface FieldLayout {
  studyDbId: string;
  studyName: string;
  rows: number;
  cols: number;
  plots: FieldPlot[];
}

export interface SpatialMapSettings {
  showLabels: boolean;
  showLegend: boolean;
  heatmapVariable?: string;
  colorScheme: 'status' | 'heatmap';
  orientation: 'standard' | 'serpentine';
}

export interface ViewState {
  scale: number;
  offset: Position;
}

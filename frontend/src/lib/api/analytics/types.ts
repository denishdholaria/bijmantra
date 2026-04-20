export interface GeneticGainData {
  year: number;
  gain: number;
  cumulative: number;
  target: number;
}

export interface HeritabilityData {
  trait: string;
  value: number;
  se?: number;
}

export interface SelectionResponseData {
  generation: number;
  mean: number;
  variance: number;
  selected: number;
}

export interface CorrelationMatrix {
  traits: string[];
  matrix: number[][];
}

export interface AnalyticsSummary {
  total_trials: number;
  active_studies: number;
  germplasm_entries: number;
  observations_this_month: number;
  genetic_gain_rate: number;
  data_quality_score: number;
  selection_intensity: number;
  breeding_cycle_days: number;
}

export interface QuickInsight {
  id: string;
  type: string;
  title: string;
  description: string;
  action_label?: string;
  action_route?: string;
  created_at: string;
}

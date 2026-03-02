import { ApiClientCore } from "./core/client";

export interface FertilizerRequest {
  crop: string;
  area: number;
  target_yield: number;
  soil_n: number;
  soil_p: number;
  soil_k: number;
}

export interface FertilizerResult {
  nitrogen_needed: number;
  phosphorus_needed: number;
  potassium_needed: number;
  urea: number;
  dap: number;
  mop: number;
  total_cost: number;
}

export interface TraitRequest {
  formula_id: string;
  inputs: number[];
}

export interface TraitResult {
  result: number;
  unit: string;
}

export interface PointData {
  x: number;
  y: number;
  value: number;
}

export interface InterpolationRequest {
  points: PointData[];
  resolution?: number;
  method?: string;
}

export interface InterpolationResult {
  grid_x: number[][];
  grid_y: number[][];
  grid_z: number[][];
  min_val: number;
  max_val: number;
}

export interface GrowthPredictionRequest {
  crop: string;
  planting_date: string;
  current_gdd: number;
}

export interface GrowthPredictionResult {
  current_stage: string;
  next_stage?: string;
  gdd_to_next?: number;
  days_to_next?: number;
  maturity_date?: string;
  progress: number;
}

export interface AllocationScenarioRequest {
  total_budget: number;
  categories: { name: string; weight?: number; amount?: number }[];
}

export interface AllocationResult {
  allocations: { name: string; amount: number; percent: number }[];
  remaining: number;
}

export interface ROICalculationRequest {
  total_cost: number;
  expected_revenue: number;
  initial_investment?: number;
  cash_flows?: number[];
  discount_rate?: number;
}

export interface ROICalculationResult {
  roi_percent: number;
  net_present_value?: number;
  benefit_cost_ratio: number;
}

export class CalculatorService {
  constructor(private client: ApiClientCore) {}

  async calculateROI(data: ROICalculationRequest) {
    return this.client.post<ROICalculationResult>("/api/v2/calculators/cost/roi", data);
  }

  async calculateFertilizer(data: FertilizerRequest) {
    return this.client.post<FertilizerResult>("/api/v2/calculators/fertilizer", data);
  }

  async calculateTrait(data: TraitRequest) {
    return this.client.post<TraitResult>("/api/v2/calculators/traits", data);
  }

  async interpolateYield(data: InterpolationRequest) {
    return this.client.post<InterpolationResult>("/api/v2/calculators/yield/interpolation", data);
  }

  async predictGrowth(data: GrowthPredictionRequest) {
    return this.client.post<GrowthPredictionResult>("/api/v2/calculators/growth", data);
  }

  async calculateAllocation(data: AllocationScenarioRequest) {
    return this.client.post<AllocationResult>("/api/v2/calculators/allocation", data);
  }
}

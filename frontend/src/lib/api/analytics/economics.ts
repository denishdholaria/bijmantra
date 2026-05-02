import { ApiClientCore } from "../core/client";

export interface ROICalculationRequest {
  total_cost: number;
  expected_revenue: number;
  initial_investment?: number;
  cash_flows?: number[];
  discount_rate?: number;
}

export interface ROICalculationResponse {
  roi_percent: number;
  net_present_value?: number;
  benefit_cost_ratio: number;
}

export interface CostBenefitCreate {
  organization_id: number;
  analysis_name: string;
  total_cost: number;
  expected_revenue: number;
  cash_flows?: number[];
}

export class EconomicsService {
  constructor(private client: ApiClientCore) {}

  async calculateROI(data: ROICalculationRequest) {
    return this.client.request<ROICalculationResponse>("/api/v2/economics/calculate-roi", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async createCostBenefitAnalysis(data: CostBenefitCreate) {
    return this.client.request<{ id: number; status: string; roi: number }>(
      "/api/v2/economics/cost-benefit",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  }
}

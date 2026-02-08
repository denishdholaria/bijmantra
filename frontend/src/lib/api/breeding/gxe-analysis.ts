import { ApiClientCore } from "../core/client";

export interface GxEDataInput {
  yield_matrix: number[][];
  genotype_names: string[];
  environment_names: string[];
}

export interface AMMIRequest extends GxEDataInput {
  n_components?: number;
}

export interface GGERequest extends GxEDataInput {
  n_components?: number;
  scaling?: number; // 0=symmetric, 1=genotype, 2=environment
}

export interface GxEResult {
  genotype_scores: Array<{
    name: string;
    pc1: number;
    pc2: number;
    mean: number;
  }>;
  environment_scores: Array<{
    name: string;
    pc1: number;
    pc2: number;
    mean: number;
  }>;
  variance_explained: number[];
  anova?: {
    source: string;
    df: number;
    ss: number;
    ms: number;
    f_value: number;
    p_value: number;
    variance_pct: number;
  }[];
}


export interface GxEFromDbRequest {
  study_db_ids: string[];
  trait_db_id: string;
  method: 'ammi' | 'gge' | 'finlay_wilkinson';
  n_components?: number;
  scaling?: number;
}

export class GxEAnalysisService {
  constructor(private client: ApiClientCore) {}

  async runAMMI(data: AMMIRequest): Promise<GxEResult> {
    return this.client.post<GxEResult>("/api/v2/gxe/ammi", data);
  }

  async runGGE(data: GGERequest): Promise<GxEResult> {
    return this.client.post<GxEResult>("/api/v2/gxe/gge", data);
  }

  async runFinlayWilkinson(data: GxEDataInput): Promise<{
    genotypes: Array<{
      name: string;
      mean: number;
      slope: number;
      intercept: number;
      r_squared: number;
      stability_class: string;
    }>;
  }> {
    return this.client.post<any>("/api/v2/gxe/finlay-wilkinson", data);
  }

  async analyzeFromDb(data: GxEFromDbRequest): Promise<any> {
    return this.client.post<any>("/api/v2/gxe/analyze-from-db", data);
  }

  async getMethods(): Promise<{
    methods: Array<{
      id: string;
      name: string;
      description: string;
    }>;
  }> {
    return this.client.get<any>("/api/v2/gxe/methods");
  }
}

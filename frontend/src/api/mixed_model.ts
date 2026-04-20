
import { analysisPost } from './analysisClient'

export interface MixedModelSolution {
  formula: string
  fixed_effects: Record<string, number>
  random_effects: Record<string, number>
  aic?: number
  bic?: number
}

export interface HeritabilityResult {
  heritability: number
  variance_components: {
    var_g: number
    var_e: number
    var_ge?: number
  }
}

export const mixedModelApi = {
  /**
   * Solve generic mixed model using formula interface
   * @param formula e.g. "yield ~ loc + year + (1|genotype)"
   * @param data_dict Dictionary of columns (arrays)
   */
  solveMixedModel: (data: { 
    formula: string; 
    data_dict: Record<string, (string | number)[]> 
  }): Promise<MixedModelSolution> =>
    analysisPost<MixedModelSolution>('/api/v2/analyze/mixed-model/solve', data),

  /**
   * Analyze multi-environment heritability
   */
  analyzeHeritability: (data: { 
    phenotypes: number[]; 
    environments: string[]; 
    genotypes: string[] 
  }): Promise<HeritabilityResult> =>
    analysisPost<HeritabilityResult>('/api/v2/analyze/mixed-model/heritability/multi-env', data),
}

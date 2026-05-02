
import { analysisPost } from './analysisClient'

export interface PCAResponse {
  coords: number[][]
  explained_variance: number[]
  components: number
}

export interface KinshipResponse {
  kinship_matrix: number[][]
  method: string
}

export const structureApi = {
  /**
   * Run PCA on genotype matrix
   * @param matrix n_samples x n_markers matrix (0,1,2 values)
   * @param components Number of components to return
   */
  pcaAnalysis: (data: { matrix: number[][]; components: number }): Promise<PCAResponse> =>
    analysisPost<PCAResponse>('/api/v2/analyze/structure/pca', data),

  /**
   * Calculate Kinship Matrix (IBS/GRM)
   * @param genotypes n_samples x n_markers matrix
   * @param method method name (default: vanraden)
   */
  kinshipAnalysis: (data: { genotypes: number[][]; method?: string }): Promise<KinshipResponse> =>
    analysisPost<KinshipResponse>('/api/v2/analyze/structure/kinship', data),
}

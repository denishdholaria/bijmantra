
import { analysisGet, analysisPost } from './analysisClient'

export interface CytoscapeElement {
  data: Record<string, any>
}

export interface CytoscapeGraph {
  nodes: CytoscapeElement[]
  edges: CytoscapeElement[]
}

export interface AMatrixResult {
  matrix: number[][]
  ids: string[]
}

export const pedigreeApi = {
  /**
   * Get Cytoscape.js compatible graph JSON
   * @param id Root Germplasm ID
   * @param depth Number of generations (default 3)
   * @param direction 'ancestors' | 'descendants' | 'both'
   */
  getVisualization: (
    id: string, 
    depth = 3, 
    direction: 'ancestors' | 'descendants' | 'both' = 'ancestors'
  ): Promise<CytoscapeGraph> =>
    analysisGet<CytoscapeGraph>(`/api/v2/pedigree/${id}/visualization`, { depth, direction }),

  /**
   * Calculate Numerator Relationship Matrix (A-Matrix)
   * @param records List of pedigree records
   */
  calculateAMatrix: (
    records: { id: string; parent_a?: string; parent_b?: string }[]
  ): Promise<AMatrixResult> =>
    analysisPost<AMatrixResult>('/api/v2/pedigree/matrix', records),
}

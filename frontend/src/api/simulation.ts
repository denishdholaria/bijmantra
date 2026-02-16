
import { analysisPost } from './analysisClient'

export interface CrossResponse {
  n_progeny: number
  offspring_dosages: number[][]
}

export interface GenerationResponse {
  generation: number
  n_offspring: number
  offspring_dosages: number[][] // List of unphased dosages (0,1,2)
}

export const simulationApi = {
  /**
   * Simulate a specific cross between two parents
   */
  simulateCross: (data: {
    parent_a_dosage: number[]
    parent_b_dosage: number[]
    n_progeny: number
    recombination_rate?: number
  }): Promise<CrossResponse> =>
    analysisPost<CrossResponse>('/api/v2/simulation/cross', data),

  /**
   * Advance a population by one generation
   */
  simulateGeneration: (data: {
    population_dosages: number[][]
    n_offspring: number
    recombination_rate?: number
    crossing_scheme?: 'random' | 'selfing'
  }): Promise<GenerationResponse> =>
    analysisPost<GenerationResponse>('/api/v2/simulation/generation', data),
}

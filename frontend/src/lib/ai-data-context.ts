/**
 * AI Data Context Engine
 * Provides AI with access to app data for intelligent analysis
 */

import { apiClient } from './api-client'

export interface DataContext {
  germplasm: any[]
  trials: any[]
  studies: any[]
  observations: any[]
  traits: any[]
  locations: any[]
  programs: any[]
  summary: string
}

class AIDataContextEngine {
  private cache: Partial<DataContext> = {}
  private cacheTimestamp: number = 0
  private cacheDuration = 5 * 60 * 1000 // 5 minutes

  /**
   * Get all relevant data context for AI
   */
  async getFullContext(): Promise<DataContext> {
    const now = Date.now()
    if (now - this.cacheTimestamp < this.cacheDuration && Object.keys(this.cache).length > 0) {
      return this.cache as DataContext
    }

    try {
      const [germplasm, trials, studies, observations, traits, locations, programs] = await Promise.all([
        this.fetchGermplasm(),
        this.fetchTrials(),
        this.fetchStudies(),
        this.fetchObservations(),
        this.fetchTraits(),
        this.fetchLocations(),
        this.fetchPrograms(),
      ])

      this.cache = {
        germplasm,
        trials,
        studies,
        observations,
        traits,
        locations,
        programs,
        summary: this.generateSummary({ germplasm, trials, studies, observations, traits, locations, programs }),
      }
      this.cacheTimestamp = now

      return this.cache as DataContext
    } catch (error) {
      console.error('Failed to fetch data context:', error)
      return this.getEmptyContext()
    }
  }

  /**
   * Get context for a specific entity type
   */
  async getContextFor(entityType: 'germplasm' | 'trials' | 'studies' | 'observations' | 'traits'): Promise<any[]> {
    switch (entityType) {
      case 'germplasm':
        return this.fetchGermplasm()
      case 'trials':
        return this.fetchTrials()
      case 'studies':
        return this.fetchStudies()
      case 'observations':
        return this.fetchObservations()
      case 'traits':
        return this.fetchTraits()
      default:
        return []
    }
  }

  /**
   * Format data context as a prompt-friendly string
   */
  formatForPrompt(context: DataContext, maxLength: number = 8000): string {
    let prompt = `## Current Breeding Data Context\n\n`
    prompt += `${context.summary}\n\n`

    // Add germplasm data
    if (context.germplasm.length > 0) {
      prompt += `### Germplasm (${context.germplasm.length} entries)\n`
      prompt += this.formatAsTable(context.germplasm.slice(0, 20), ['germplasmDbId', 'germplasmName', 'commonCropName', 'genus', 'species'])
      prompt += '\n\n'
    }

    // Add observations/phenotypic data
    if (context.observations.length > 0) {
      prompt += `### Phenotypic Observations (${context.observations.length} records)\n`
      prompt += this.formatAsTable(context.observations.slice(0, 30), ['observationUnitDbId', 'germplasmName', 'observationVariableName', 'value'])
      prompt += '\n\n'
    }

    // Add traits
    if (context.traits.length > 0) {
      prompt += `### Traits Being Measured (${context.traits.length})\n`
      prompt += this.formatAsTable(context.traits.slice(0, 15), ['observationVariableDbId', 'observationVariableName', 'trait.traitName'])
      prompt += '\n\n'
    }

    // Add trials
    if (context.trials.length > 0) {
      prompt += `### Active Trials (${context.trials.length})\n`
      prompt += this.formatAsTable(context.trials.slice(0, 10), ['trialDbId', 'trialName', 'programName'])
      prompt += '\n\n'
    }

    // Truncate if too long
    if (prompt.length > maxLength) {
      prompt = prompt.substring(0, maxLength) + '\n\n[Data truncated for length...]'
    }

    return prompt
  }

  /**
   * Get a quick summary of available data
   */
  async getQuickSummary(): Promise<string> {
    const context = await this.getFullContext()
    return context.summary
  }

  /**
   * Search for specific data
   */
  async searchData(query: string): Promise<any[]> {
    const context = await this.getFullContext()
    const results: any[] = []
    const lowerQuery = query.toLowerCase()

    // Search germplasm
    context.germplasm.forEach(g => {
      if (g.germplasmName?.toLowerCase().includes(lowerQuery) ||
          g.germplasmDbId?.toLowerCase().includes(lowerQuery)) {
        results.push({ type: 'germplasm', data: g })
      }
    })

    // Search trials
    context.trials.forEach(t => {
      if (t.trialName?.toLowerCase().includes(lowerQuery)) {
        results.push({ type: 'trial', data: t })
      }
    })

    return results.slice(0, 20)
  }

  // Private methods for fetching data
  private async fetchGermplasm(): Promise<any[]> {
    try {
      const response = await apiClient.getGermplasm(0, 100)
      return response?.result?.data || []
    } catch {
      return []
    }
  }

  private async fetchTrials(): Promise<any[]> {
    try {
      const response = await apiClient.getTrials(0, 50)
      return response?.result?.data || []
    } catch {
      return []
    }
  }

  private async fetchStudies(): Promise<any[]> {
    try {
      const response = await apiClient.getStudies(0, 50)
      return response?.result?.data || []
    } catch {
      return []
    }
  }

  private async fetchObservations(): Promise<any[]> {
    try {
      const response = await apiClient.getObservations(undefined, 0, 200)
      return response?.result?.data || []
    } catch {
      return []
    }
  }

  private async fetchTraits(): Promise<any[]> {
    try {
      const response = await apiClient.getObservationVariables(0, 50)
      return response?.result?.data || []
    } catch {
      return []
    }
  }

  private async fetchLocations(): Promise<any[]> {
    try {
      const response = await apiClient.getLocations(0, 50)
      return response?.result?.data || []
    } catch {
      return []
    }
  }

  private async fetchPrograms(): Promise<any[]> {
    try {
      const response = await apiClient.getPrograms(0, 50)
      return response?.result?.data || []
    } catch {
      return []
    }
  }

  private generateSummary(data: Omit<DataContext, 'summary'>): string {
    return `**Data Summary:**
- Germplasm entries: ${data.germplasm.length}
- Breeding programs: ${data.programs.length}
- Trials: ${data.trials.length}
- Studies: ${data.studies.length}
- Observations: ${data.observations.length}
- Traits measured: ${data.traits.length}
- Locations: ${data.locations.length}`
  }

  private formatAsTable(data: any[], columns: string[]): string {
    if (data.length === 0) return 'No data available.\n'

    // Get column values (handle nested properties like 'trait.traitName')
    const getValue = (obj: any, path: string): string => {
      const value = path.split('.').reduce((o, k) => o?.[k], obj)
      return value !== undefined && value !== null ? String(value) : '-'
    }

    // Create header
    let table = '| ' + columns.map(c => c.split('.').pop()).join(' | ') + ' |\n'
    table += '| ' + columns.map(() => '---').join(' | ') + ' |\n'

    // Create rows
    data.forEach(row => {
      table += '| ' + columns.map(c => getValue(row, c)).join(' | ') + ' |\n'
    })

    return table
  }

  private getEmptyContext(): DataContext {
    return {
      germplasm: [],
      trials: [],
      studies: [],
      observations: [],
      traits: [],
      locations: [],
      programs: [],
      summary: 'No data available. The backend server may not be running.',
    }
  }

  /**
   * Clear the cache
   */
  clearCache(): void {
    this.cache = {}
    this.cacheTimestamp = 0
  }
}

export const aiDataContext = new AIDataContextEngine()

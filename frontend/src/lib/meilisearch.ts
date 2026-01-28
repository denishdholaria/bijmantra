/**
 * Meilisearch Integration
 * Instant, typo-tolerant search across all breeding data
 * 
 * Updated Dec 2025:
 * - Federated multi-index search (v1.10+)
 * - Similar documents API (v1.9+)
 * - Ranking score threshold
 * - Geo search for locations
 */

import { MeiliSearch, Index, SearchResponse, SearchParams, MultiSearchParams } from 'meilisearch'

// Search result types
export interface GermplasmSearchResult {
  id: string
  germplasmDbId: string
  germplasmName: string
  accessionNumber?: string
  species?: string
  genus?: string
  subtaxa?: string
  instituteCode?: string
  biologicalStatus?: string
  countryOfOrigin?: string
  synonyms?: string[]
  pedigree?: string
  _rankingScore?: number
  [key: string]: unknown  // Index signature for Record<string, unknown> compatibility
}

export interface TraitSearchResult {
  id: string
  observationVariableDbId: string
  observationVariableName: string
  trait?: {
    traitName: string
    traitDescription?: string
    traitClass?: string
  }
  method?: {
    methodName: string
    methodDescription?: string
  }
  scale?: {
    scaleName: string
    dataType?: string
  }
  ontologyReference?: {
    ontologyName: string
  }
  _rankingScore?: number
}

export interface TrialSearchResult {
  id: string
  trialDbId: string
  trialName: string
  trialDescription?: string
  programName?: string
  locationName?: string
  startDate?: string
  endDate?: string
  active?: boolean
  trialType?: string
  _rankingScore?: number
}

export interface LocationSearchResult {
  id: string
  locationDbId: string
  locationName: string
  locationType?: string
  countryCode?: string
  countryName?: string
  instituteName?: string
  _geo?: {
    lat: number
    lng: number
  }
  _geoDistance?: number
  _rankingScore?: number
}

export interface ProgramSearchResult {
  id: string
  programDbId: string
  programName: string
  programDescription?: string
  objective?: string
  commonCropName?: string
  leadPerson?: string
  active?: boolean
  _rankingScore?: number
}

export interface StudySearchResult {
  id: string
  studyDbId: string
  studyName: string
  studyDescription?: string
  studyType?: string
  trialName?: string
  locationName?: string
  _rankingScore?: number
}

export interface UnifiedSearchResult {
  type: 'germplasm' | 'trait' | 'trial' | 'location' | 'program' | 'study'
  id: string
  title: string
  subtitle?: string
  description?: string
  path: string
  icon: string
  score?: number
}

export interface FederatedSearchResult {
  hits: Array<UnifiedSearchResult>
  query: string
  processingTimeMs: number
  estimatedTotalHits?: number
}

// Configuration
const MEILISEARCH_CONFIG = {
  host: import.meta.env.VITE_MEILISEARCH_HOST || 'http://localhost:7700',
  apiKey: import.meta.env.VITE_MEILISEARCH_API_KEY || '',
}

// Index names
export const INDEXES = {
  GERMPLASM: 'germplasm',
  TRAITS: 'traits',
  TRIALS: 'trials',
  LOCATIONS: 'locations',
  PROGRAMS: 'programs',
  STUDIES: 'studies',
} as const

// Icon mapping for unified results
const INDEX_ICONS: Record<string, string> = {
  germplasm: '🌱',
  traits: '🔬',
  trials: '🧪',
  locations: '📍',
  programs: '🎯',
  studies: '📊',
}

// Path mapping for unified results
const INDEX_PATHS: Record<string, (id: string) => string> = {
  germplasm: (id) => `/germplasm/${id}`,
  traits: (id) => `/traits/${id}`,
  trials: (id) => `/trials/${id}`,
  locations: (id) => `/locations/${id}`,
  programs: (id) => `/programs/${id}`,
  studies: (id) => `/studies/${id}`,
}

class MeilisearchService {
  private client: MeiliSearch | null = null
  private isConnected = false
  private connectionPromise: Promise<boolean> | null = null
  private version: string | null = null

  /**
   * Initialize connection to Meilisearch
   */
  async connect(): Promise<boolean> {
    if (this.isConnected) return true
    if (this.connectionPromise) return this.connectionPromise

    this.connectionPromise = this._doConnect()
    return this.connectionPromise
  }

  private async _doConnect(): Promise<boolean> {
    try {
      this.client = new MeiliSearch({
        host: MEILISEARCH_CONFIG.host,
        apiKey: MEILISEARCH_CONFIG.apiKey,
      })

      // Test connection and get version
      await this.client.health()
      const versionInfo = await this.client.getVersion()
      this.version = versionInfo.pkgVersion
      this.isConnected = true
      console.log(`[Meilisearch] Connected successfully (v${this.version})`)
      return true
    } catch (error) {
      console.warn('[Meilisearch] Connection failed, falling back to local search:', error)
      this.isConnected = false
      return false
    }
  }

  /**
   * Get an index
   */
  getIndex<T extends Record<string, unknown>>(indexName: string): Index<T> | null {
    if (!this.client) return null
    return this.client.index<T>(indexName)
  }

  /**
   * Get Meilisearch version
   */
  getVersion(): string | null {
    return this.version
  }

  /**
   * Search germplasm
   */
  async searchGermplasm(
    query: string,
    options?: SearchParams
  ): Promise<SearchResponse<GermplasmSearchResult>> {
    await this.connect()
    if (!this.client) {
      return { hits: [], query, processingTimeMs: 0, limit: 0, offset: 0, estimatedTotalHits: 0 }
    }

    const index = this.client.index<GermplasmSearchResult>(INDEXES.GERMPLASM)
    return index.search(query, {
      limit: 20,
      showRankingScore: true,
      attributesToHighlight: ['germplasmName', 'accessionNumber', 'species'],
      ...options,
    })
  }

  /**
   * Search traits/observation variables
   */
  async searchTraits(
    query: string,
    options?: SearchParams
  ): Promise<SearchResponse<TraitSearchResult>> {
    await this.connect()
    if (!this.client) {
      return { hits: [], query, processingTimeMs: 0, limit: 0, offset: 0, estimatedTotalHits: 0 }
    }

    const index = this.client.index<TraitSearchResult>(INDEXES.TRAITS)
    return index.search(query, {
      limit: 20,
      showRankingScore: true,
      attributesToHighlight: ['observationVariableName', 'trait.traitName'],
      ...options,
    })
  }

  /**
   * Search trials
   */
  async searchTrials(
    query: string,
    options?: SearchParams
  ): Promise<SearchResponse<TrialSearchResult>> {
    await this.connect()
    if (!this.client) {
      return { hits: [], query, processingTimeMs: 0, limit: 0, offset: 0, estimatedTotalHits: 0 }
    }

    const index = this.client.index<TrialSearchResult>(INDEXES.TRIALS)
    return index.search(query, {
      limit: 20,
      showRankingScore: true,
      attributesToHighlight: ['trialName', 'trialDescription'],
      ...options,
    })
  }

  /**
   * Search locations with optional geo filtering
   */
  async searchLocations(
    query: string,
    options?: SearchParams & { 
      nearLat?: number
      nearLng?: number
      radiusKm?: number 
    }
  ): Promise<SearchResponse<LocationSearchResult>> {
    await this.connect()
    if (!this.client) {
      return { hits: [], query, processingTimeMs: 0, limit: 0, offset: 0, estimatedTotalHits: 0 }
    }

    const index = this.client.index<LocationSearchResult>(INDEXES.LOCATIONS)
    const searchOptions: SearchParams = {
      limit: 20,
      showRankingScore: true,
      attributesToHighlight: ['locationName', 'countryName'],
      ...options,
    }

    // Add geo filter if coordinates provided
    if (options?.nearLat !== undefined && options?.nearLng !== undefined) {
      const radiusM = (options.radiusKm || 100) * 1000
      searchOptions.filter = `_geoRadius(${options.nearLat}, ${options.nearLng}, ${radiusM})`
      searchOptions.sort = [`_geoPoint(${options.nearLat}, ${options.nearLng}):asc`]
    }

    return index.search(query, searchOptions)
  }

  /**
   * Search programs
   */
  async searchPrograms(
    query: string,
    options?: SearchParams
  ): Promise<SearchResponse<ProgramSearchResult>> {
    await this.connect()
    if (!this.client) {
      return { hits: [], query, processingTimeMs: 0, limit: 0, offset: 0, estimatedTotalHits: 0 }
    }

    const index = this.client.index<ProgramSearchResult>(INDEXES.PROGRAMS)
    return index.search(query, {
      limit: 20,
      showRankingScore: true,
      attributesToHighlight: ['programName', 'programDescription'],
      ...options,
    })
  }

  /**
   * Search studies
   */
  async searchStudies(
    query: string,
    options?: SearchParams
  ): Promise<SearchResponse<StudySearchResult>> {
    await this.connect()
    if (!this.client) {
      return { hits: [], query, processingTimeMs: 0, limit: 0, offset: 0, estimatedTotalHits: 0 }
    }

    const index = this.client.index<StudySearchResult>(INDEXES.STUDIES)
    return index.search(query, {
      limit: 20,
      showRankingScore: true,
      attributesToHighlight: ['studyName', 'studyDescription'],
      ...options,
    })
  }

  /**
   * Federated search across multiple indexes (v1.10+ feature)
   * Merges results from all indexes into a single ranked response
   */
  async federatedSearch(
    query: string, 
    options?: {
      indexes?: string[]
      limit?: number
      scoreThreshold?: number
    }
  ): Promise<FederatedSearchResult> {
    await this.connect()
    if (!this.client || !query.trim()) {
      return { hits: [], query, processingTimeMs: 0 }
    }

    const targetIndexes = options?.indexes || Object.values(INDEXES)
    const limit = options?.limit || 20

    try {
      // Build multi-search queries
      const queries = targetIndexes.map(indexUid => ({
        indexUid,
        q: query,
        limit,
        showRankingScore: true,
        ...(options?.scoreThreshold && { rankingScoreThreshold: options.scoreThreshold }),
      }))

      // Try federated search first (v1.10+)
      try {
        const result = await this.client.multiSearch({
          queries,
          federation: { limit },
        } as MultiSearchParams)

        // Map federated results to unified format
        const hits = this.mapFederatedHits(result)
        return {
          hits,
          query,
          processingTimeMs: (result as any).processingTimeMs || 0,
          estimatedTotalHits: hits.length,
        }
      } catch {
        // Fallback to regular multi-search if federation not supported
        const result = await this.client.multiSearch({ queries })
        const hits = this.mapMultiSearchHits(result)
        return {
          hits,
          query,
          processingTimeMs: 0,
          estimatedTotalHits: hits.length,
        }
      }
    } catch (error) {
      console.error('[Meilisearch] Federated search failed:', error)
      return { hits: [], query, processingTimeMs: 0 }
    }
  }

  /**
   * Map federated search results to unified format
   */
  private mapFederatedHits(result: any): UnifiedSearchResult[] {
    const hits: UnifiedSearchResult[] = []
    
    // Federated results come in a single hits array with _federation metadata
    for (const hit of result.hits || []) {
      const indexName = hit._federation?.indexUid || 'unknown'
      const mapped = this.mapHitToUnified(hit, indexName)
      if (mapped) hits.push(mapped)
    }

    return hits
  }

  /**
   * Map multi-search results to unified format
   */
  private mapMultiSearchHits(result: any): UnifiedSearchResult[] {
    const hits: UnifiedSearchResult[] = []
    
    for (const indexResult of result.results || []) {
      const indexName = indexResult.indexUid
      for (const hit of indexResult.hits || []) {
        const mapped = this.mapHitToUnified(hit, indexName)
        if (mapped) hits.push(mapped)
      }
    }

    // Sort by ranking score
    hits.sort((a, b) => (b.score || 0) - (a.score || 0))
    return hits
  }

  /**
   * Map a single hit to unified format
   */
  private mapHitToUnified(hit: any, indexName: string): UnifiedSearchResult | null {
    const icon = INDEX_ICONS[indexName] || '📄'
    const pathFn = INDEX_PATHS[indexName]
    
    switch (indexName) {
      case 'germplasm':
        return {
          type: 'germplasm',
          id: hit.germplasmDbId,
          title: hit.germplasmName,
          subtitle: hit.accessionNumber,
          description: [hit.species, hit.countryOfOrigin].filter(Boolean).join(' • '),
          path: pathFn?.(hit.germplasmDbId) || `/germplasm/${hit.germplasmDbId}`,
          icon,
          score: hit._rankingScore,
        }
      case 'traits':
        return {
          type: 'trait',
          id: hit.observationVariableDbId,
          title: hit.observationVariableName,
          subtitle: hit.trait?.traitName,
          description: hit.method?.methodName,
          path: pathFn?.(hit.observationVariableDbId) || `/traits/${hit.observationVariableDbId}`,
          icon,
          score: hit._rankingScore,
        }
      case 'trials':
        return {
          type: 'trial',
          id: hit.trialDbId,
          title: hit.trialName,
          subtitle: hit.programName,
          description: hit.locationName,
          path: pathFn?.(hit.trialDbId) || `/trials/${hit.trialDbId}`,
          icon,
          score: hit._rankingScore,
        }
      case 'locations':
        return {
          type: 'location',
          id: hit.locationDbId,
          title: hit.locationName,
          subtitle: hit.locationType,
          description: hit.countryName,
          path: pathFn?.(hit.locationDbId) || `/locations/${hit.locationDbId}`,
          icon,
          score: hit._rankingScore,
        }
      case 'programs':
        return {
          type: 'program',
          id: hit.programDbId,
          title: hit.programName,
          subtitle: hit.commonCropName,
          description: hit.objective,
          path: pathFn?.(hit.programDbId) || `/programs/${hit.programDbId}`,
          icon,
          score: hit._rankingScore,
        }
      case 'studies':
        return {
          type: 'study',
          id: hit.studyDbId,
          title: hit.studyName,
          subtitle: hit.studyType,
          description: hit.locationName,
          path: pathFn?.(hit.studyDbId) || `/studies/${hit.studyDbId}`,
          icon,
          score: hit._rankingScore,
        }
      default:
        return null
    }
  }

  /**
   * Unified search across all indexes (legacy method)
   * Use federatedSearch for v1.10+ for better ranking
   */
  async searchAll(query: string, limit = 10): Promise<UnifiedSearchResult[]> {
    const result = await this.federatedSearch(query, { limit })
    return result.hits
  }

  /**
   * Get similar documents (v1.9+ feature)
   * Finds documents similar to the given document
   */
  async getSimilarDocuments<T extends Record<string, unknown>>(
    indexName: string,
    documentId: string,
    options?: {
      limit?: number
      filter?: string
    }
  ): Promise<SearchResponse<T>> {
    await this.connect()
    if (!this.client) {
      return { hits: [], query: '', processingTimeMs: 0, limit: 0, offset: 0, estimatedTotalHits: 0 }
    }

    const index = this.client.index<T>(indexName)
    
    try {
      // @ts-ignore - searchSimilarDocuments may not be in types yet
      return await index.searchSimilarDocuments(documentId, {
        limit: options?.limit || 10,
        showRankingScore: true,
        ...(options?.filter && { filter: options.filter }),
      })
    } catch (error) {
      console.warn('[Meilisearch] Similar documents not available:', error)
      return { hits: [], query: '', processingTimeMs: 0, limit: 0, offset: 0, estimatedTotalHits: 0 }
    }
  }

  /**
   * Get similar germplasm
   */
  async getSimilarGermplasm(
    germplasmDbId: string,
    options?: { limit?: number; sameSpecies?: boolean }
  ): Promise<GermplasmSearchResult[]> {
    const filter = options?.sameSpecies ? `species EXISTS` : undefined
    const result = await this.getSimilarDocuments<GermplasmSearchResult>(
      INDEXES.GERMPLASM,
      germplasmDbId,
      { limit: options?.limit, filter }
    )
    return result.hits
  }

  /**
   * Index documents (for admin/sync operations)
   */
  async indexDocuments<T extends Record<string, unknown>>(
    indexName: string,
    documents: T[],
    primaryKey?: string
  ): Promise<void> {
    await this.connect()
    if (!this.client) {
      throw new Error('Meilisearch not connected')
    }

    const index = this.client.index<T>(indexName)
    await index.addDocuments(documents, { primaryKey })
    console.log(`[Meilisearch] Indexed ${documents.length} documents to ${indexName}`)
  }

  /**
   * Configure index settings
   */
  async configureIndex(indexName: string, settings: {
    searchableAttributes?: string[]
    filterableAttributes?: string[]
    sortableAttributes?: string[]
    displayedAttributes?: string[]
    rankingRules?: string[]
    typoTolerance?: {
      enabled?: boolean
      minWordSizeForTypos?: { oneTypo?: number; twoTypos?: number }
    }
  }): Promise<void> {
    await this.connect()
    if (!this.client) {
      throw new Error('Meilisearch not connected')
    }

    const index = this.client.index(indexName)
    await index.updateSettings(settings)
    console.log(`[Meilisearch] Configured index ${indexName}`)
  }

  /**
   * Get index statistics
   */
  async getStats(): Promise<{
    databaseSize: number
    indexes: Record<string, { numberOfDocuments: number; isIndexing: boolean }>
    version: string | null
  }> {
    await this.connect()
    if (!this.client) {
      return { databaseSize: 0, indexes: {}, version: null }
    }

    try {
      const stats = await this.client.getStats()
      return {
        databaseSize: stats.databaseSize,
        indexes: Object.fromEntries(
          Object.entries(stats.indexes).map(([name, idx]) => [
            name,
            { numberOfDocuments: idx.numberOfDocuments, isIndexing: idx.isIndexing },
          ])
        ),
        version: this.version,
      }
    } catch (error) {
      console.error('[Meilisearch] Stats error:', error)
      return { databaseSize: 0, indexes: {}, version: this.version }
    }
  }

  /**
   * Check if connected
   */
  get connected(): boolean {
    return this.isConnected
  }
}

// Singleton instance
export const meilisearch = new MeilisearchService()

// React hook for Meilisearch
import { useState, useEffect, useRef, useCallback } from 'react'

export interface UseMeilisearchOptions {
  debounceMs?: number
  scoreThreshold?: number
  indexes?: string[]
}

export function useMeilisearch(initialQuery = '', options?: UseMeilisearchOptions) {
  const [query, setQuery] = useState(initialQuery)
  const [results, setResults] = useState<UnifiedSearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [version, setVersion] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const debounceMs = options?.debounceMs ?? 100

  // Check connection on mount
  useEffect(() => {
    meilisearch.connect().then((connected) => {
      setIsConnected(connected)
      if (connected) {
        setVersion(meilisearch.getVersion())
      }
    })
  }, [])

  // Debounced search
  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    if (!query.trim()) {
      setResults([])
      return
    }

    timeoutRef.current = setTimeout(async () => {
      setIsSearching(true)
      try {
        const searchResult = await meilisearch.federatedSearch(query, {
          indexes: options?.indexes,
          scoreThreshold: options?.scoreThreshold,
        })
        setResults(searchResult.hits)
      } finally {
        setIsSearching(false)
      }
    }, debounceMs)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [query, debounceMs, options?.indexes, options?.scoreThreshold])

  // Manual search function
  const search = useCallback(async (searchQuery: string) => {
    setIsSearching(true)
    try {
      const searchResult = await meilisearch.federatedSearch(searchQuery, {
        indexes: options?.indexes,
        scoreThreshold: options?.scoreThreshold,
      })
      setResults(searchResult.hits)
      return searchResult.hits
    } finally {
      setIsSearching(false)
    }
  }, [options?.indexes, options?.scoreThreshold])

  return {
    query,
    setQuery,
    results,
    isSearching,
    isConnected,
    version,
    search,
  }
}

/**
 * Hook for similar documents
 */
export function useSimilarDocuments<T extends Record<string, unknown>>(
  indexName: string,
  documentId: string | null,
  options?: { limit?: number; filter?: string }
) {
  const [results, setResults] = useState<T[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (!documentId) {
      setResults([])
      return
    }

    setIsLoading(true)
    meilisearch
      .getSimilarDocuments<T>(indexName, documentId, options)
      .then((response) => setResults(response.hits))
      .catch(() => setResults([]))
      .finally(() => setIsLoading(false))
  }, [indexName, documentId, options?.limit, options?.filter])

  return { results, isLoading }
}

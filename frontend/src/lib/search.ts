/**
 * Global Search Service
 * Foundation for instant search - can be upgraded to Meilisearch/Typesense
 * Currently uses client-side fuzzy search with IndexedDB caching
 */

interface SearchResult {
  id: string
  type: 'germplasm' | 'trial' | 'observation' | 'trait' | 'location' | 'person' | 'page'
  title: string
  subtitle?: string
  icon: string
  path: string
  score: number
  highlights?: { field: string; snippet: string }[]
}

interface SearchIndex {
  germplasm: SearchableItem[]
  trials: SearchableItem[]
  traits: SearchableItem[]
  locations: SearchableItem[]
  pages: SearchableItem[]
}

interface SearchableItem {
  id: string
  title: string
  subtitle?: string
  keywords?: string[]
  path: string
  type: SearchResult['type']
  icon: string
}

// Simple fuzzy matching score
function fuzzyScore(query: string, text: string): number {
  const queryLower = query.toLowerCase()
  const textLower = text.toLowerCase()
  
  // Exact match
  if (textLower === queryLower) return 100
  
  // Starts with
  if (textLower.startsWith(queryLower)) return 90
  
  // Contains
  if (textLower.includes(queryLower)) return 70
  
  // Fuzzy match (simple character matching)
  let score = 0
  let queryIndex = 0
  for (let i = 0; i < textLower.length && queryIndex < queryLower.length; i++) {
    if (textLower[i] === queryLower[queryIndex]) {
      score += 10
      queryIndex++
    }
  }
  
  // Bonus for matching all characters
  if (queryIndex === queryLower.length) {
    score += 20
  }
  
  return Math.min(score, 60)
}

class SearchService {
  private index: SearchIndex = {
    germplasm: [],
    trials: [],
    traits: [],
    locations: [],
    pages: [],
  }
  
  private isIndexed = false
  private indexPromise: Promise<void> | null = null

  /**
   * Initialize the search index
   */
  async initialize(): Promise<void> {
    if (this.isIndexed) return
    if (this.indexPromise) return this.indexPromise
    
    this.indexPromise = this._buildIndex()
    return this.indexPromise
  }

  private async _buildIndex(): Promise<void> {
    // In production, this would fetch from API or IndexedDB
    // For now, we'll index the navigation pages
    
    this.index.pages = [
      // Core
      { id: 'dashboard', title: 'Dashboard', path: '/dashboard', type: 'page', icon: '📊', keywords: ['home', 'overview'] },
      { id: 'programs', title: 'Programs', path: '/programs', type: 'page', icon: '🌾', keywords: ['breeding program'] },
      { id: 'trials', title: 'Trials', path: '/trials', type: 'page', icon: '🧪', keywords: ['experiment'] },
      { id: 'studies', title: 'Studies', path: '/studies', type: 'page', icon: '📈' },
      { id: 'locations', title: 'Locations', path: '/locations', type: 'page', icon: '📍', keywords: ['site', 'field'] },
      
      // Germplasm
      { id: 'germplasm', title: 'Germplasm', path: '/germplasm', type: 'page', icon: '🌱', keywords: ['accession', 'variety'] },
      { id: 'seedlots', title: 'Seed Lots', path: '/seedlots', type: 'page', icon: '📦', keywords: ['inventory'] },
      { id: 'crosses', title: 'Crosses', path: '/crosses', type: 'page', icon: '🧬', keywords: ['hybridization'] },
      
      // Phenotyping
      { id: 'traits', title: 'Traits', path: '/traits', type: 'page', icon: '🔬', keywords: ['variable'] },
      { id: 'observations', title: 'Observations', path: '/observations', type: 'page', icon: '📋', keywords: ['data'] },
      
      // Genomics
      { id: 'genomic-selection', title: 'Genomic Selection', path: '/genomic-selection', type: 'page', icon: '🧬', keywords: ['gs', 'gebv'] },
      { id: 'qtl-mapping', title: 'QTL Mapping', path: '/qtl-mapping', type: 'page', icon: '🎯', keywords: ['gwas'] },
      { id: 'genetic-diversity', title: 'Genetic Diversity', path: '/genetic-diversity', type: 'page', icon: '🌈' },
      
      // AI
      { id: 'ai-assistant', title: 'AI Assistant', path: '/ai-assistant', type: 'page', icon: '💬', keywords: ['chat', 'help'] },
      { id: 'plant-vision', title: 'Plant Vision', path: '/plant-vision', type: 'page', icon: '🌿', keywords: ['camera', 'disease'] },
      
      // Analytics
      { id: 'analytics', title: 'Analytics Dashboard', path: '/analytics', type: 'page', icon: '📊' },
      { id: 'visualization', title: 'Data Visualization', path: '/visualization', type: 'page', icon: '📈' },
      
      // WASM
      { id: 'wasm-genomics', title: 'WASM Genomics', path: '/wasm-genomics', type: 'page', icon: '⚡', keywords: ['rust', 'performance'] },
      { id: 'wasm-gblup', title: 'WASM GBLUP', path: '/wasm-gblup', type: 'page', icon: '📊' },
    ]
    
    this.isIndexed = true
    console.log('[Search] Index built with', this.index.pages.length, 'pages')
  }

  /**
   * Search across all indexed content
   */
  async search(query: string, options?: { limit?: number; types?: SearchResult['type'][] }): Promise<SearchResult[]> {
    await this.initialize()
    
    const limit = options?.limit || 10
    const types = options?.types || ['germplasm', 'trial', 'observation', 'trait', 'location', 'person', 'page']
    
    const results: SearchResult[] = []
    
    // Search pages
    if (types.includes('page')) {
      for (const item of this.index.pages) {
        const titleScore = fuzzyScore(query, item.title)
        const keywordScore = item.keywords 
          ? Math.max(...item.keywords.map(k => fuzzyScore(query, k)))
          : 0
        const score = Math.max(titleScore, keywordScore)
        
        if (score > 30) {
          results.push({
            id: item.id,
            type: 'page',
            title: item.title,
            subtitle: item.subtitle,
            icon: item.icon,
            path: item.path,
            score,
          })
        }
      }
    }
    
    // Sort by score and limit
    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
  }

  /**
   * Add items to the search index
   */
  addToIndex(type: keyof SearchIndex, items: SearchableItem[]): void {
    this.index[type] = [...this.index[type], ...items]
  }

  /**
   * Clear the search index
   */
  clearIndex(): void {
    this.index = {
      germplasm: [],
      trials: [],
      traits: [],
      locations: [],
      pages: [],
    }
    this.isIndexed = false
  }

  /**
   * Get search suggestions based on partial query
   */
  async getSuggestions(query: string, limit = 5): Promise<string[]> {
    const results = await this.search(query, { limit })
    return results.map(r => r.title)
  }
}

// Singleton instance
export const searchService = new SearchService()

// React hook for search
import { useState, useEffect, useRef } from 'react'

export function useSearch(initialQuery = '') {
  const [query, setQuery] = useState(initialQuery)
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    if (!query.trim()) {
      setResults([])
      return
    }

    // Debounce search
    timeoutRef.current = setTimeout(async () => {
      setIsSearching(true)
      try {
        const searchResults = await searchService.search(query)
        setResults(searchResults)
      } finally {
        setIsSearching(false)
      }
    }, 150)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [query])

  return {
    query,
    setQuery,
    results,
    isSearching,
  }
}

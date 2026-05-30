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

import { ApiClientCore } from "@/lib/api/core/client";

type SearchParamPrimitive = string | number | boolean;
type SearchParamValue =
  | SearchParamPrimitive
  | readonly SearchParamPrimitive[]
  | null
  | undefined;
type SearchParams = Record<string, SearchParamValue>;
type SearchResponse<T> = {
  hits: T[];
  query: string;
  processingTimeMs: number;
  limit: number;
  offset: number;
  estimatedTotalHits?: number;
};

// Search result types
export interface GermplasmSearchResult {
  id: string;
  germplasmDbId: string;
  germplasmName: string;
  accessionNumber?: string;
  species?: string;
  genus?: string;
  subtaxa?: string;
  instituteCode?: string;
  biologicalStatus?: string;
  countryOfOrigin?: string;
  synonyms?: string[];
  pedigree?: string;
  _rankingScore?: number;
  [key: string]: unknown; // Index signature for Record<string, unknown> compatibility
}

export interface TraitSearchResult {
  id: string;
  observationVariableDbId: string;
  observationVariableName: string;
  trait?: {
    traitName: string;
    traitDescription?: string;
    traitClass?: string;
  };
  method?: {
    methodName: string;
    methodDescription?: string;
  };
  scale?: {
    scaleName: string;
    dataType?: string;
  };
  ontologyReference?: {
    ontologyName: string;
  };
  _rankingScore?: number;
}

export interface TrialSearchResult {
  id: string;
  trialDbId: string;
  trialName: string;
  trialDescription?: string;
  programName?: string;
  locationName?: string;
  startDate?: string;
  endDate?: string;
  active?: boolean;
  trialType?: string;
  _rankingScore?: number;
}

export interface LocationSearchResult {
  id: string;
  locationDbId: string;
  locationName: string;
  locationType?: string;
  countryCode?: string;
  countryName?: string;
  instituteName?: string;
  _geo?: {
    lat: number;
    lng: number;
  };
  _geoDistance?: number;
  _rankingScore?: number;
}

export interface ProgramSearchResult {
  id: string;
  programDbId: string;
  programName: string;
  programDescription?: string;
  objective?: string;
  commonCropName?: string;
  leadPerson?: string;
  active?: boolean;
  _rankingScore?: number;
}

export interface StudySearchResult {
  id: string;
  studyDbId: string;
  studyName: string;
  studyDescription?: string;
  studyType?: string;
  trialName?: string;
  locationName?: string;
  _rankingScore?: number;
}

export interface UnifiedSearchResult {
  type: "germplasm" | "trait" | "trial" | "location" | "program" | "study";
  id: string;
  title: string;
  subtitle?: string;
  description?: string;
  path: string;
  icon: string;
  score?: number;
}

export interface FederatedSearchResult {
  hits: Array<UnifiedSearchResult>;
  query: string;
  processingTimeMs: number;
  estimatedTotalHits?: number;
}

type BackendSearchResponse<T> = Partial<SearchResponse<T>> & {
  results?: T[];
  total?: number;
};

type BackendUnifiedSearchResult = Omit<UnifiedSearchResult, "icon"> & {
  icon?: string;
};

type BackendFederatedSearchResponse = {
  query?: string;
  results?: BackendUnifiedSearchResult[];
  total?: number;
  processingTimeMs?: number;
};

type BackendStatsResponse = {
  connected: boolean;
  version: string | null;
  databaseSize?: number;
  indexes?: Record<string, { numberOfDocuments: number; isIndexing: boolean }>;
};

// Index names
export const INDEXES = {
  GERMPLASM: "germplasm",
  TRAITS: "traits",
  TRIALS: "trials",
  LOCATIONS: "locations",
  PROGRAMS: "programs",
  STUDIES: "studies",
} as const;

// Icon mapping for unified results
const INDEX_ICONS: Record<string, string> = {
  germplasm: "🌱",
  traits: "🔬",
  trials: "🧪",
  locations: "📍",
  programs: "🎯",
  studies: "📊",
};

// Path mapping for unified results
const INDEX_PATHS: Record<string, (id: string) => string> = {
  germplasm: (id) => `/germplasm/${id}`,
  traits: (id) => `/traits/${id}`,
  trials: (id) => `/trials/${id}`,
  locations: (id) => `/locations/${id}`,
  programs: (id) => `/programs/${id}`,
  studies: (id) => `/studies/${id}`,
};

class BackendSearchService {
  private client = new ApiClientCore();
  private isConnected = false;
  private connectionPromise: Promise<boolean> | null = null;
  private version: string | null = null;

  async connect(): Promise<boolean> {
    if (this.isConnected) return true;
    if (this.connectionPromise) return this.connectionPromise;

    this.connectionPromise = this._doConnect();
    return this.connectionPromise;
  }

  private async _doConnect(): Promise<boolean> {
    try {
      const stats = await this.client.get<BackendStatsResponse>(
        "/api/v2/search/stats",
      );

      this.version = stats.version;
      this.isConnected = stats.connected;
      return this.isConnected;
    } catch (error) {
      console.warn("[Search] Backend search facade unavailable:", error);
      this.isConnected = false;
      return false;
    } finally {
      this.connectionPromise = null;
    }
  }

  getVersion(): string | null {
    return this.version;
  }

  getIndex(_indexName: string): null {
    console.warn(
      "[Search] Direct browser Meilisearch index access is disabled.",
    );
    return null;
  }

  private buildUrl(
    endpoint: string,
    params: Record<string, SearchParamValue>,
  ): string {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") return;
      searchParams.set(
        key,
        Array.isArray(value) ? value.join(",") : String(value),
      );
    });

    const query = searchParams.toString();
    return query ? `${endpoint}?${query}` : endpoint;
  }

  private emptyResponse<T>(query: string, limit = 0): SearchResponse<T> {
    return {
      hits: [],
      query,
      processingTimeMs: 0,
      limit,
      offset: 0,
      estimatedTotalHits: 0,
    };
  }

  private async searchEndpoint<T>(
    endpoint: string,
    query: string,
    options?: SearchParams,
    extraParams: Record<string, SearchParamValue> = {},
  ): Promise<SearchResponse<T>> {
    const limit = Number(options?.limit ?? 20);
    const connected = await this.connect();
    if (!connected) return this.emptyResponse<T>(query, limit);

    try {
      const response = await this.client.get<BackendSearchResponse<T>>(
        this.buildUrl(endpoint, {
          q: query,
          limit,
          ...extraParams,
        }),
      );

      const hits = response.hits ?? response.results ?? [];
      return {
        ...response,
        hits,
        query: response.query ?? query,
        processingTimeMs: response.processingTimeMs ?? 0,
        limit,
        offset: response.offset ?? 0,
        estimatedTotalHits:
          response.estimatedTotalHits ?? response.total ?? hits.length,
      };
    } catch (error) {
      console.warn("[Search] Backend search request failed:", error);
      return this.emptyResponse<T>(query, limit);
    }
  }

  async searchGermplasm(
    query: string,
    options?: SearchParams,
  ): Promise<SearchResponse<GermplasmSearchResult>> {
    return this.searchEndpoint<GermplasmSearchResult>(
      "/api/v2/search/germplasm",
      query,
      options,
    );
  }

  async searchTraits(
    query: string,
    options?: SearchParams,
  ): Promise<SearchResponse<TraitSearchResult>> {
    return this.searchEndpoint<TraitSearchResult>(
      "/api/v2/search/traits",
      query,
      options,
    );
  }

  async searchTrials(
    query: string,
    options?: SearchParams,
  ): Promise<SearchResponse<TrialSearchResult>> {
    return this.searchEndpoint<TrialSearchResult>(
      "/api/v2/search/trials",
      query,
      options,
    );
  }

  async searchLocations(
    query: string,
    options?: SearchParams & {
      nearLat?: number;
      nearLng?: number;
      radiusKm?: number;
    },
  ): Promise<SearchResponse<LocationSearchResult>> {
    if (options?.nearLat !== undefined && options?.nearLng !== undefined) {
      return this.searchEndpoint<LocationSearchResult>(
        "/api/v2/search/geo/locations",
        query,
        options,
        {
          lat: options.nearLat,
          lng: options.nearLng,
          radius_km: options.radiusKm ?? 100,
        },
      );
    }

    return this.searchEndpoint<LocationSearchResult>(
      "/api/v2/search/locations",
      query,
      options,
    );
  }

  async searchPrograms(
    query: string,
    options?: SearchParams,
  ): Promise<SearchResponse<ProgramSearchResult>> {
    return this.searchEndpoint<ProgramSearchResult>(
      "/api/v2/search/programs",
      query,
      options,
    );
  }

  async searchStudies(
    query: string,
    options?: SearchParams,
  ): Promise<SearchResponse<StudySearchResult>> {
    return this.searchEndpoint<StudySearchResult>(
      "/api/v2/search/studies",
      query,
      options,
    );
  }

  async federatedSearch(
    query: string,
    options?: {
      indexes?: string[];
      limit?: number;
      scoreThreshold?: number;
    },
  ): Promise<FederatedSearchResult> {
    if (!query.trim()) return { hits: [], query, processingTimeMs: 0 };

    const limit = options?.limit ?? 20;
    const connected = await this.connect();
    if (!connected) return { hits: [], query, processingTimeMs: 0 };

    try {
      const response = await this.client.get<BackendFederatedSearchResponse>(
        this.buildUrl("/api/v2/search/federated", {
          q: query,
          limit,
          indexes: options?.indexes,
          score_threshold: options?.scoreThreshold,
        }),
      );

      const hits = (response.results ?? []).map((hit) =>
        this.mapBackendResult(hit),
      );
      return {
        hits,
        query: response.query ?? query,
        processingTimeMs: response.processingTimeMs ?? 0,
        estimatedTotalHits: response.total ?? hits.length,
      };
    } catch (error) {
      console.warn("[Search] Federated backend search failed:", error);
      return { hits: [], query, processingTimeMs: 0 };
    }
  }

  private mapBackendResult(
    hit: BackendUnifiedSearchResult,
  ): UnifiedSearchResult {
    const iconKey =
      {
        germplasm: "germplasm",
        trait: "traits",
        trial: "trials",
        location: "locations",
        program: "programs",
        study: "studies",
      }[hit.type] ?? hit.type;

    const pathFn = INDEX_PATHS[iconKey];
    return {
      type: hit.type,
      id: hit.id,
      title: hit.title,
      subtitle: hit.subtitle,
      description: hit.description,
      path: hit.path ?? pathFn?.(hit.id) ?? "/",
      icon: INDEX_ICONS[iconKey] ?? "📄",
      score: hit.score,
    };
  }

  async searchAll(query: string, limit = 10): Promise<UnifiedSearchResult[]> {
    const result = await this.federatedSearch(query, { limit });
    return result.hits;
  }

  async getSimilarDocuments<T extends Record<string, unknown>>(
    indexName: string,
    documentId: string,
    options?: {
      limit?: number;
      filter?: string;
    },
  ): Promise<SearchResponse<T>> {
    const connected = await this.connect();
    if (!connected) return this.emptyResponse<T>("", options?.limit ?? 10);

    try {
      const response = await this.client.get<{
        results?: T[];
        total?: number;
      }>(
        this.buildUrl(`/api/v2/search/similar/${indexName}/${documentId}`, {
          limit: options?.limit ?? 10,
          filter: options?.filter,
        }),
      );

      return {
        hits: response.results ?? [],
        query: "",
        processingTimeMs: 0,
        limit: options?.limit ?? 10,
        offset: 0,
        estimatedTotalHits: response.total ?? 0,
      };
    } catch (error) {
      console.warn("[Search] Similar documents request failed:", error);
      return this.emptyResponse<T>("", options?.limit ?? 10);
    }
  }

  async getSimilarGermplasm(
    germplasmDbId: string,
    options?: { limit?: number; sameSpecies?: boolean },
  ): Promise<GermplasmSearchResult[]> {
    const filter = options?.sameSpecies ? `species EXISTS` : undefined;
    const result = await this.getSimilarDocuments<GermplasmSearchResult>(
      INDEXES.GERMPLASM,
      germplasmDbId,
      { limit: options?.limit, filter },
    );
    return result.hits;
  }

  async indexDocuments<T extends Record<string, unknown>>(
    _indexName: string,
    _documents: T[],
    _primaryKey?: string,
  ): Promise<void> {
    throw new Error(
      "Search indexing is backend-only; browser clients may not write Meilisearch indexes.",
    );
  }

  async configureIndex(
    _indexName: string,
    _settings: Record<string, unknown>,
  ): Promise<void> {
    throw new Error(
      "Search index configuration is backend-only; browser clients may not mutate Meilisearch.",
    );
  }

  async getStats(): Promise<{
    databaseSize: number;
    indexes: Record<string, { numberOfDocuments: number; isIndexing: boolean }>;
    version: string | null;
  }> {
    try {
      const stats = await this.client.get<BackendStatsResponse>(
        "/api/v2/search/stats",
      );
      this.version = stats.version;
      this.isConnected = stats.connected;
      return {
        databaseSize: stats.databaseSize ?? 0,
        indexes: stats.indexes ?? {},
        version: this.version,
      };
    } catch (error) {
      console.warn("[Search] Search stats request failed:", error);
      this.isConnected = false;
      return { databaseSize: 0, indexes: {}, version: this.version };
    }
  }

  get connected(): boolean {
    return this.isConnected;
  }
}

// Singleton instance
export const meilisearch = new BackendSearchService();

// React hook for Meilisearch
import { useState, useEffect, useRef, useCallback } from "react";

export interface UseMeilisearchOptions {
  debounceMs?: number;
  scoreThreshold?: number;
  indexes?: string[];
}

export function useMeilisearch(
  initialQuery = "",
  options?: UseMeilisearchOptions,
) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<UnifiedSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [version, setVersion] = useState<string | null>(null);
  const timeoutRef = useRef<number | null>(null);

  const debounceMs = options?.debounceMs ?? 100;

  // Check connection on mount
  useEffect(() => {
    meilisearch.connect().then((connected) => {
      setIsConnected(connected);
      if (connected) {
        setVersion(meilisearch.getVersion());
      }
    });
  }, []);

  // Debounced search
  useEffect(() => {
    if (timeoutRef.current !== null) {
      clearTimeout(timeoutRef.current);
    }

    if (!query.trim()) {
      setResults([]);
      return;
    }

    timeoutRef.current = window.setTimeout(async () => {
      setIsSearching(true);
      try {
        const searchResult = await meilisearch.federatedSearch(query, {
          indexes: options?.indexes,
          scoreThreshold: options?.scoreThreshold,
        });
        setResults(searchResult.hits);
      } finally {
        setIsSearching(false);
      }
    }, debounceMs);

    return () => {
      if (timeoutRef.current !== null) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [query, debounceMs, options?.indexes, options?.scoreThreshold]);

  // Manual search function
  const search = useCallback(
    async (searchQuery: string) => {
      setIsSearching(true);
      try {
        const searchResult = await meilisearch.federatedSearch(searchQuery, {
          indexes: options?.indexes,
          scoreThreshold: options?.scoreThreshold,
        });
        setResults(searchResult.hits);
        return searchResult.hits;
      } finally {
        setIsSearching(false);
      }
    },
    [options?.indexes, options?.scoreThreshold],
  );

  return {
    query,
    setQuery,
    results,
    isSearching,
    isConnected,
    version,
    search,
  };
}

/**
 * Hook for similar documents
 */
export function useSimilarDocuments<T extends Record<string, unknown>>(
  indexName: string,
  documentId: string | null,
  options?: { limit?: number; filter?: string },
) {
  const [results, setResults] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const limit = options?.limit;
  const filter = options?.filter;

  useEffect(() => {
    let cancelled = false;

    async function loadSimilarDocuments() {
      await Promise.resolve();
      if (!documentId) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const response = await meilisearch.getSimilarDocuments<T>(
          indexName,
          documentId,
          { limit, filter },
        );
        if (!cancelled) setResults(response.hits);
      } catch {
        if (!cancelled) setResults([]);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void loadSimilarDocuments();
    return () => {
      cancelled = true;
    };
  }, [indexName, documentId, limit, filter]);

  return { results, isLoading };
}

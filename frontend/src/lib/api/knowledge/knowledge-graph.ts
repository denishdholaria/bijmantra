import type { ApiClientCore } from '../core/client';

import { buildQueryString } from './query';

export type KnowledgeGraphFacetMap = Record<string, number>;
export type KnowledgeGraphEdgeRecord = Record<string, unknown>;
export type KnowledgeGraphRetrievalDiagnosticsResponse = Record<string, unknown>;

export interface KnowledgeGraphFacetsResponse {
  source_asset_types?: KnowledgeGraphFacetMap;
  target_asset_types?: KnowledgeGraphFacetMap;
  relationship_types?: KnowledgeGraphFacetMap;
  [key: string]: unknown;
}

export interface KnowledgeGraphFacetFilters {
  source_asset_type?: string;
  target_asset_type?: string;
  relationship_type?: string;
}

export interface KnowledgeGraphListOptions extends KnowledgeGraphFacetFilters {
  limit?: number;
  offset?: number;
}

export interface KnowledgeGraphDiagnosticsOptions {
  limit?: number;
  offset?: number;
}

export class KnowledgeGraphService {
  constructor(private client: ApiClientCore) {}

  async getFacets(filters: KnowledgeGraphFacetFilters = {}) {
    const query = buildQueryString({
      source_asset_type: filters.source_asset_type,
      target_asset_type: filters.target_asset_type,
      relationship_type: filters.relationship_type,
    });

    return this.client.get<KnowledgeGraphFacetsResponse>(`/api/v2/knowledge-graph/facets${query}`);
  }

  async listEdges(options: KnowledgeGraphListOptions = {}) {
    const query = buildQueryString({
      limit: options.limit,
      offset: options.offset,
      source_asset_type: options.source_asset_type,
      target_asset_type: options.target_asset_type,
      relationship_type: options.relationship_type,
    });

    return this.client.get<KnowledgeGraphEdgeRecord[]>(`/api/v2/knowledge-graph/edges${query}`);
  }

  async getRetrievalDiagnostics(options: KnowledgeGraphDiagnosticsOptions = {}) {
    const query = buildQueryString({
      limit: options.limit,
      offset: options.offset,
    });

    return this.client.get<KnowledgeGraphRetrievalDiagnosticsResponse>(
      `/api/v2/knowledge-graph/retrieval-diagnostics${query}`,
    );
  }
}

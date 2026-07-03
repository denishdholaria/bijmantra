import { describe, expect, it, vi } from 'vitest';

import type { ApiClientCore } from '../core/client';

import { KnowledgeGraphService } from './knowledge-graph';

function makeClient() {
  return {
    get: vi.fn(),
  } as unknown as ApiClientCore & {
    get: ReturnType<typeof vi.fn>;
  };
}

describe('KnowledgeGraphService', () => {
  it('calls the facets endpoint with optional filters', async () => {
    const client = makeClient();
    client.get.mockResolvedValue({});
    const service = new KnowledgeGraphService(client);

    await service.getFacets({ source_asset_type: 'germplasm' });

    expect(client.get).toHaveBeenCalledWith(
      '/api/v2/knowledge-graph/facets?source_asset_type=germplasm',
    );
  });

  it('calls the edge inventory endpoint with pagination and filters', async () => {
    const client = makeClient();
    client.get.mockResolvedValue([]);
    const service = new KnowledgeGraphService(client);

    await service.listEdges({
      limit: 25,
      offset: 5,
      source_asset_type: 'study',
      relationship_type: 'observes',
    });

    expect(client.get).toHaveBeenCalledWith(
      '/api/v2/knowledge-graph/edges?limit=25&offset=5&source_asset_type=study&relationship_type=observes',
    );
  });

  it('calls retrieval diagnostics with pagination', async () => {
    const client = makeClient();
    client.get.mockResolvedValue({});
    const service = new KnowledgeGraphService(client);

    await service.getRetrievalDiagnostics({ limit: 25, offset: 10 });

    expect(client.get).toHaveBeenCalledWith(
      '/api/v2/knowledge-graph/retrieval-diagnostics?limit=25&offset=10',
    );
  });
});

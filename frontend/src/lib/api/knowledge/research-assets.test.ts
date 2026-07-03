import { describe, expect, it, vi } from 'vitest';

import type { ApiClientCore } from '../core/client';

import { ResearchAssetService } from './research-assets';

function makeClient() {
  return {
    get: vi.fn(),
  } as unknown as ApiClientCore & {
    get: ReturnType<typeof vi.fn>;
  };
}

describe('ResearchAssetService', () => {
  it('calls the FAIR metadata endpoint with asset filters', async () => {
    const client = makeClient();
    client.get.mockResolvedValue([]);
    const service = new ResearchAssetService(client);

    await service.listFairMetadata({ asset_type: 'study', limit: 25 });

    expect(client.get).toHaveBeenCalledWith('/api/v2/fair-metadata?limit=25&asset_type=study');
  });

  it('calls the federated registry endpoint with connector filters', async () => {
    const client = makeClient();
    client.get.mockResolvedValue([]);
    const service = new ResearchAssetService(client);

    await service.listFederatedAssets({
      connector_key: 'genesys',
      asset_kind: 'germplasm',
      limit: 25,
    });

    expect(client.get).toHaveBeenCalledWith(
      '/api/v2/federated-assets/registry?limit=25&connector_key=genesys&asset_kind=germplasm',
    );
  });

  it('calls the connector list endpoint', async () => {
    const client = makeClient();
    client.get.mockResolvedValue([]);
    const service = new ResearchAssetService(client);

    await service.listConnectors();

    expect(client.get).toHaveBeenCalledWith('/api/v2/federated-assets/connectors');
  });

  it('calls the sync receipts endpoint with filters', async () => {
    const client = makeClient();
    client.get.mockResolvedValue([]);
    const service = new ResearchAssetService(client);

    await service.listSyncReceipts({ connector_key: 'genesys', status: 'completed', limit: 25 });

    expect(client.get).toHaveBeenCalledWith(
      '/api/v2/federated-assets/receipts?limit=25&connector_key=genesys&status=completed',
    );
  });
});

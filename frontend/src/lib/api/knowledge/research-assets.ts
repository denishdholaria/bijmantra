import type { ApiClientCore } from '../core/client';

import { buildQueryString } from './query';

export type FairMetadataRecord = Record<string, unknown>;
export type FederatedAssetRecord = Record<string, unknown>;
export type FederatedConnectorRecord = Record<string, unknown>;
export type FederatedSyncReceiptRecord = Record<string, unknown>;

export interface ResearchAssetListOptions {
  limit?: number;
  offset?: number;
  asset_type?: string;
  connector_key?: string;
  asset_kind?: string;
  status?: string;
}

export class ResearchAssetService {
  constructor(private client: ApiClientCore) {}

  async listFairMetadata(options: ResearchAssetListOptions = {}) {
    const query = buildQueryString({
      limit: options.limit,
      offset: options.offset,
      asset_type: options.asset_type,
    });

    return this.client.get<FairMetadataRecord[]>(`/api/v2/fair-metadata${query}`);
  }

  async listFederatedAssets(options: ResearchAssetListOptions = {}) {
    const query = buildQueryString({
      limit: options.limit,
      offset: options.offset,
      connector_key: options.connector_key,
      asset_kind: options.asset_kind,
    });

    return this.client.get<FederatedAssetRecord[]>(`/api/v2/federated-assets/registry${query}`);
  }

  async listConnectors() {
    return this.client.get<FederatedConnectorRecord[]>('/api/v2/federated-assets/connectors');
  }

  async listSyncReceipts(options: ResearchAssetListOptions = {}) {
    const query = buildQueryString({
      limit: options.limit,
      offset: options.offset,
      connector_key: options.connector_key,
      status: options.status,
    });

    return this.client.get<FederatedSyncReceiptRecord[]>(
      `/api/v2/federated-assets/receipts${query}`,
    );
  }
}

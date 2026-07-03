import { describe, expect, it, vi } from 'vitest';

import {
  evaluateCapabilityAccess,
  resolveCapabilityManifest,
} from '@/framework/registry/capabilities';
import type { ApiClientCore } from '../core/client';

import {
  PlatformCapabilityService,
  capabilityInstallationsToAccessContext,
  currentCapabilityContextToAccessContext,
  type PlatformCapabilityInstallation,
} from './platform-capabilities';

function makeClient() {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  } as unknown as ApiClientCore & {
    get: ReturnType<typeof vi.fn>;
    post: ReturnType<typeof vi.fn>;
    put: ReturnType<typeof vi.fn>;
    delete: ReturnType<typeof vi.fn>;
  };
}

describe('PlatformCapabilityService', () => {
  it('calls the platform capability management endpoints', async () => {
    const client = makeClient();
    client.get.mockResolvedValue({});
    client.post.mockResolvedValue({});
    client.put.mockResolvedValue({});
    client.delete.mockResolvedValue({});
    const service = new PlatformCapabilityService(client);

    await service.listManifests();
    await service.listInstallations(7);
    await service.getCurrentUserContext();
    await service.getState('scientific_publishing_fair_exchange.research_asset_core', 7);
    await service.install('scientific_publishing_fair_exchange.research_asset_core', {
      granted_permissions: ['research_assets.read'],
      data_scopes: ['organization'],
    });
    await service.disable('scientific_publishing_fair_exchange.research_asset_core', 7);
    await service.bootstrapFirstWave({ organization_id: 7 });

    expect(client.get).toHaveBeenNthCalledWith(1, '/api/v2/system/capabilities/manifest');
    expect(client.get).toHaveBeenNthCalledWith(
      2,
      '/api/v2/system/capabilities/installations?organization_id=7',
    );
    expect(client.get).toHaveBeenNthCalledWith(
      3,
      '/api/v2/platform/capabilities/me',
    );
    expect(client.get).toHaveBeenNthCalledWith(
      4,
      '/api/v2/system/capabilities/scientific_publishing_fair_exchange.research_asset_core?organization_id=7',
    );
    expect(client.put).toHaveBeenCalledWith(
      '/api/v2/system/capabilities/scientific_publishing_fair_exchange.research_asset_core',
      {
        granted_permissions: ['research_assets.read'],
        data_scopes: ['organization'],
      },
    );
    expect(client.delete).toHaveBeenCalledWith(
      '/api/v2/system/capabilities/scientific_publishing_fair_exchange.research_asset_core?organization_id=7',
    );
    expect(client.post).toHaveBeenCalledWith('/api/v2/system/capabilities/bootstrap', {
      organization_id: 7,
    });
  });

  it('converts enabled installation rows into frontend capability access context', () => {
    const installations: PlatformCapabilityInstallation[] = [
      {
        capability_id: 'intelligence_fabric.knowledge_graph',
        organization_id: 7,
        enabled: true,
        lifecycle_state: 'installed',
        granted_permissions: ['intelligence.knowledge_graph.read'],
        data_scopes: ['organization', 'asset'],
      },
      {
        capability_id: 'scientific_publishing_fair_exchange.research_asset_core',
        organization_id: 7,
        enabled: false,
        lifecycle_state: 'disabled',
        granted_permissions: ['research_assets.read'],
        data_scopes: ['organization'],
      },
    ];

    const context = capabilityInstallationsToAccessContext(installations);

    expect(context).toEqual({
      installedCapabilities: ['intelligence_fabric.knowledge_graph'],
      grantedPermissions: ['intelligence.knowledge_graph.read'],
      dataScopes: ['organization', 'asset'],
    });

    const manifest = resolveCapabilityManifest('intelligence_fabric.knowledge_graph');
    expect(manifest).toBeDefined();
    const decision = evaluateCapabilityAccess(manifest!, context, {
      requiredPermission: 'intelligence.knowledge_graph.read',
      requiredDataScopes: ['organization'],
    });

    expect(decision.allowed).toBe(true);
  });

  it('converts current-user capability context into frontend access context', () => {
    const context = currentCapabilityContextToAccessContext({
      current_organization: { id: 7 },
      organization_id: 7,
      user_id: 43,
      installed_capability_ids: [
        'intelligence_fabric.knowledge_graph',
        'intelligence_fabric.knowledge_graph',
      ],
      enabled_capability_ids: [
        'intelligence_fabric.knowledge_graph',
        'intelligence_fabric.knowledge_graph',
      ],
      granted_permissions: [
        'intelligence.knowledge_graph.read',
        'intelligence.knowledge_graph.read',
      ],
      data_scopes: ['organization', 'asset', 'organization'],
      roles: ['knowledge_curator', 'knowledge_curator'],
      capability_decisions: [
        {
          capability_id: 'intelligence_fabric.knowledge_graph',
          allowed: true,
          reason: 'allowed',
          missing_permissions: [],
          missing_data_scopes: [],
        },
      ],
    });

    expect(context).toEqual({
      installedCapabilities: ['intelligence_fabric.knowledge_graph'],
      grantedPermissions: ['intelligence.knowledge_graph.read'],
      dataScopes: ['organization', 'asset'],
      roles: ['knowledge_curator'],
    });
  });
});

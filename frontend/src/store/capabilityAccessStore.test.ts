import { beforeEach, describe, expect, it, vi } from 'vitest';

import { apiClient } from '@/lib/api-client';
import { useCapabilityAccessStore } from './capabilityAccessStore';

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    platformCapabilityService: {
      getCurrentUserContext: vi.fn(),
      listInstallations: vi.fn(),
    },
  },
}));

describe('useCapabilityAccessStore', () => {
  beforeEach(() => {
    useCapabilityAccessStore.getState().reset();
    vi.clearAllMocks();
  });

  it('loads current-user capability context into app shell access context', async () => {
    vi.mocked(apiClient.platformCapabilityService.getCurrentUserContext).mockResolvedValue({
      current_organization: { id: 7 },
      organization_id: 7,
      user_id: 43,
      installed_capability_ids: [
        'intelligence_fabric.knowledge_graph',
        'scientific_publishing_fair_exchange.research_asset_core',
      ],
      enabled_capability_ids: [
        'intelligence_fabric.knowledge_graph',
      ],
      granted_permissions: ['intelligence.knowledge_graph.read'],
      data_scopes: ['organization', 'asset'],
      roles: ['knowledge_curator'],
      capability_decisions: [
        {
          capability_id: 'intelligence_fabric.knowledge_graph',
          allowed: true,
          reason: 'allowed',
          missing_permissions: [],
          missing_data_scopes: [],
        },
        {
          capability_id: 'scientific_publishing_fair_exchange.research_asset_core',
          allowed: false,
          reason: 'capability_not_installed',
          missing_permissions: [],
          missing_data_scopes: [],
        },
      ],
    });

    await useCapabilityAccessStore.getState().loadForOrganization(7);

    expect(apiClient.platformCapabilityService.getCurrentUserContext).toHaveBeenCalledWith();
    expect(apiClient.platformCapabilityService.listInstallations).not.toHaveBeenCalled();
    expect(useCapabilityAccessStore.getState()).toMatchObject({
      organizationId: 7,
      installations: [],
      isLoading: false,
      error: null,
      accessContext: {
        installedCapabilities: ['intelligence_fabric.knowledge_graph'],
        grantedPermissions: ['intelligence.knowledge_graph.read'],
        dataScopes: ['organization', 'asset'],
        roles: ['knowledge_curator'],
      },
    });
  });

  it('clears stale access context when loading fails', async () => {
    useCapabilityAccessStore.setState({
      organizationId: 7,
      accessContext: {
        installedCapabilities: ['intelligence_fabric.knowledge_graph'],
        grantedPermissions: ['intelligence.knowledge_graph.read'],
        dataScopes: ['organization'],
      },
    });
    vi.mocked(apiClient.platformCapabilityService.getCurrentUserContext).mockRejectedValue(
      new Error('capability endpoint unavailable'),
    );

    await useCapabilityAccessStore.getState().loadForOrganization(8);

    expect(useCapabilityAccessStore.getState()).toMatchObject({
      organizationId: 8,
      installations: [],
      accessContext: {
        installedCapabilities: [],
        grantedPermissions: [],
        dataScopes: [],
      },
      isLoading: false,
      error: 'capability endpoint unavailable',
    });
  });
});

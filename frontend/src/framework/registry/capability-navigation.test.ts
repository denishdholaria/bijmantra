import { describe, expect, it } from 'vitest';

import { capabilityInstallationsToAccessContext } from '@/lib/api/system/platform-capabilities';
import type { PlatformCapabilityInstallation } from '@/lib/api/system/platform-capabilities';

import {
  collectBlockedCapabilityNavigationNodes,
  evaluateCapabilityNavigationNode,
  filterNavigationTreeByCapabilityAccess,
} from './capability-navigation';
import type { CapabilityAccessContext } from './capabilities';
import { navigationTree } from './navigation-source';
import type { NavigationNode } from './navigation-source';

const fixtureNavigation: NavigationNode[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: '/dashboard',
  },
  {
    id: 'knowledge-graph',
    label: 'Knowledge Graph',
    path: '/knowledge-graph',
  },
  {
    id: 'data',
    label: 'Data',
    path: '/data',
    children: [
      {
        id: 'federated-assets',
        label: 'Federated Assets',
        path: '/data/federated-assets',
        parentPath: '/data',
      },
    ],
  },
  {
    id: 'knowledge',
    label: 'Knowledge',
    path: '/knowledge',
    children: [
      {
        id: 'research-assets',
        label: 'Research Assets',
        path: '/knowledge/research-assets',
        parentPath: '/knowledge',
      },
    ],
  },
];

function flattenPaths(tree: NavigationNode[]): string[] {
  const paths: string[] = [];

  function visit(nodes: NavigationNode[]): void {
    for (const node of nodes) {
      paths.push(node.path);

      if (node.children) {
        visit(node.children);
      }
    }
  }

  visit(tree);
  return paths;
}

describe('capability navigation', () => {
  it('keeps unprotected navigation while hiding capability routes that are not installed', () => {
    const context: CapabilityAccessContext = {
      installedCapabilities: [],
      grantedPermissions: [],
    };

    const filtered = filterNavigationTreeByCapabilityAccess(fixtureNavigation, context);
    const paths = flattenPaths(filtered);

    expect(paths).toContain('/dashboard');
    expect(paths).toContain('/data');
    expect(paths).toContain('/knowledge');
    expect(paths).not.toContain('/knowledge-graph');
    expect(paths).not.toContain('/data/federated-assets');
    expect(paths).not.toContain('/knowledge/research-assets');
  });

  it('allows installed capability routes without scattering install checks through shell code', () => {
    const context: CapabilityAccessContext = {
      installedCapabilities: ['intelligence_fabric.knowledge_graph'],
      grantedPermissions: [],
    };

    const filtered = filterNavigationTreeByCapabilityAccess(fixtureNavigation, context);
    const paths = flattenPaths(filtered);

    expect(paths).toContain('/knowledge-graph');
    expect(paths).not.toContain('/data/federated-assets');
  });

  it('treats disabled installation rows as unavailable navigation capabilities', () => {
    const installations: PlatformCapabilityInstallation[] = [
      {
        capability_id: 'intelligence_fabric.knowledge_graph',
        organization_id: 7,
        enabled: true,
        lifecycle_state: 'installed',
        granted_permissions: [],
        data_scopes: [],
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

    const filtered = filterNavigationTreeByCapabilityAccess(
      fixtureNavigation,
      capabilityInstallationsToAccessContext(installations),
    );
    const paths = flattenPaths(filtered);

    expect(paths).toContain('/knowledge-graph');
    expect(paths).not.toContain('/knowledge/research-assets');
  });

  it('reports blocked capability navigation decisions for diagnostics and tests', () => {
    const blocked = collectBlockedCapabilityNavigationNodes(fixtureNavigation, {
      installedCapabilities: [],
      grantedPermissions: [],
    });

    expect(blocked.map(decision => decision.path)).toEqual([
      '/knowledge-graph',
      '/data/federated-assets',
      '/knowledge/research-assets',
    ]);
    expect(blocked[0]?.reason).toBe('capability_not_installed');
  });

  it('can enforce route-level capability permissions when navigation declares them', () => {
    const node: NavigationNode = {
      id: 'knowledge-graph',
      label: 'Knowledge Graph',
      path: '/knowledge-graph',
      requiredPermissions: ['intelligence.knowledge_graph.read'],
    };

    const denied = evaluateCapabilityNavigationNode(node, {
      installedCapabilities: ['intelligence_fabric.knowledge_graph'],
      grantedPermissions: [],
    });
    const allowed = evaluateCapabilityNavigationNode(node, {
      installedCapabilities: ['intelligence_fabric.knowledge_graph'],
      grantedPermissions: ['intelligence.knowledge_graph.read'],
    });

    expect(denied.allowed).toBe(false);
    expect(denied.reason).toBe('missing_permission');
    expect(denied.missingPermissions).toEqual(['intelligence.knowledge_graph.read']);
    expect(allowed.allowed).toBe(true);
  });

  it('can enforce Accession Passport permission metadata on navigation nodes', () => {
    const node: NavigationNode = {
      id: 'accessions',
      label: 'Accession Search',
      path: '/seed-bank/accessions',
      requiredPermissions: ['germplasm.read'],
    };

    const denied = evaluateCapabilityNavigationNode(node, {
      installedCapabilities: ['germplasm_global_seed_registry.accession_passport'],
      grantedPermissions: [],
      dataScopes: ['organization', 'accession'],
    });
    const allowed = evaluateCapabilityNavigationNode(node, {
      installedCapabilities: ['germplasm_global_seed_registry.accession_passport'],
      grantedPermissions: ['germplasm.read'],
      dataScopes: ['organization', 'accession'],
    });

    expect(denied.allowed).toBe(false);
    expect(denied.reason).toBe('missing_permission');
    expect(denied.missingPermissions).toEqual(['germplasm.read']);
    expect(allowed.allowed).toBe(true);
  });

  it('can enforce Accession Passport data-scope metadata on navigation nodes', () => {
    const node: NavigationNode = {
      id: 'accessions',
      label: 'Accession Search',
      path: '/seed-bank/accessions',
      requiredPermissions: ['germplasm.read'],
      requiredDataScopes: ['organization', 'accession'],
    };

    const denied = evaluateCapabilityNavigationNode(node, {
      installedCapabilities: ['germplasm_global_seed_registry.accession_passport'],
      grantedPermissions: ['germplasm.read'],
      dataScopes: ['organization'],
    });
    const allowed = evaluateCapabilityNavigationNode(node, {
      installedCapabilities: ['germplasm_global_seed_registry.accession_passport'],
      grantedPermissions: ['germplasm.read'],
      dataScopes: ['organization', 'accession'],
    });

    expect(denied.allowed).toBe(false);
    expect(denied.reason).toBe('missing_data_scope');
    expect(denied.missingDataScopes).toEqual(['accession']);
    expect(allowed.allowed).toBe(true);
  });

  it('filters first-wave capability app entries from the actual navigation tree', () => {
    const withoutInstall = flattenPaths(filterNavigationTreeByCapabilityAccess(navigationTree, {
      installedCapabilities: [],
      grantedPermissions: [],
      dataScopes: [],
    }));
    const withInstall = flattenPaths(filterNavigationTreeByCapabilityAccess(navigationTree, {
      installedCapabilities: [
        'intelligence_fabric.knowledge_graph',
        'scientific_publishing_fair_exchange.research_asset_core',
        'germplasm_global_seed_registry.accession_passport',
      ],
      grantedPermissions: [],
      dataScopes: [],
    }));

    expect(withoutInstall).not.toContain('/knowledge-graph');
    expect(withoutInstall).not.toContain('/knowledge/research-assets');
    expect(withoutInstall).not.toContain('/data/federated-assets');
    expect(withoutInstall).not.toContain('/germplasm');
    expect(withoutInstall).not.toContain('/seed-bank/accessions');
    expect(withoutInstall).not.toContain('/seed-bank/mcpd');
    expect(withInstall).toContain('/knowledge-graph');
    expect(withInstall).toContain('/knowledge/research-assets');
    expect(withInstall).toContain('/data/federated-assets');
    expect(withInstall).toContain('/germplasm');
    expect(withInstall).toContain('/seed-bank/accessions');
    expect(withInstall).toContain('/seed-bank/mcpd');
  });
});

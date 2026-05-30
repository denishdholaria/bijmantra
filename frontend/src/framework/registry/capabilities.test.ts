import { describe, expect, it } from 'vitest';

import {
  capabilitiesForBackendRoute,
  capabilitiesForFrontendRoute,
  capabilityManifests,
  evaluateCapabilityAccess,
  resolveCapabilityManifest,
  routePatternMatches,
} from './capabilities';

describe('capability registry', () => {
  it('declares the Knowledge Graph capability for frontend ownership', () => {
    const manifest = resolveCapabilityManifest('intelligence_fabric.knowledge_graph');

    expect(manifest).toBeDefined();
    expect(manifest?.ownerDomain).toBe('intelligence');
    expect(manifest?.frontendRoutes).toContain('/knowledge-graph');
    expect(manifest?.requiredPermissions).toContain('intelligence.knowledge_graph.read');
  });

  it('declares the ResearchAsset core capability for FAIR exchange ownership', () => {
    const manifest = resolveCapabilityManifest('scientific_publishing_fair_exchange.research_asset_core');

    expect(manifest).toBeDefined();
    expect(manifest?.ownerDomain).toBe('knowledge');
    expect(manifest?.standards).toContain('FAIR');
    expect(manifest?.standards).toContain('BrAPI v2.1');
    expect(manifest?.backendRoutes).toContain('/api/v2/federated-assets/*');
    expect(manifest?.requiredPermissions).toContain('research_assets.promote_fair');
  });

  it('matches exact and wildcard route patterns', () => {
    expect(routePatternMatches('/knowledge-graph', '/knowledge-graph')).toBe(true);
    expect(routePatternMatches('/api/v2/knowledge-graph/*', '/api/v2/knowledge-graph')).toBe(true);
    expect(routePatternMatches('/api/v2/knowledge-graph/*', '/api/v2/knowledge-graph/edges')).toBe(true);
    expect(routePatternMatches('/api/v2/knowledge-graph/*', '/api/v2/knowledge')).toBe(false);
  });

  it('resolves capability manifests by frontend and backend routes', () => {
    expect(capabilitiesForFrontendRoute('/knowledge-graph').map(capability => capability.id)).toEqual([
      'intelligence_fabric.knowledge_graph',
    ]);
    expect(capabilitiesForBackendRoute('/api/v2/knowledge-graph/edges').map(capability => capability.id)).toEqual([
      'intelligence_fabric.knowledge_graph',
    ]);
    expect(capabilitiesForBackendRoute('/api/v2/federated-assets/registry').map(capability => capability.id)).toEqual([
      'scientific_publishing_fair_exchange.research_asset_core',
    ]);
  });

  it('keeps app capability ids globally unique', () => {
    const ids = capabilityManifests.map(capability => capability.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('evaluates frontend capability access from install state, permissions, and data scopes', () => {
    const manifest = resolveCapabilityManifest('intelligence_fabric.knowledge_graph');
    expect(manifest).toBeDefined();

    const decision = evaluateCapabilityAccess(
      manifest!,
      {
        installedCapabilities: ['intelligence_fabric.knowledge_graph'],
        grantedPermissions: ['intelligence.knowledge_graph.read'],
        dataScopes: ['organization', 'asset'],
      },
      {
        requiredPermission: 'intelligence.knowledge_graph.read',
        requiredDataScopes: ['organization'],
      },
    );

    expect(decision.allowed).toBe(true);
    expect(decision.reason).toBe('allowed');
  });

  it('rejects frontend capability access when the app is not installed', () => {
    const manifest = resolveCapabilityManifest('intelligence_fabric.knowledge_graph');
    expect(manifest).toBeDefined();

    const decision = evaluateCapabilityAccess(
      manifest!,
      {
        installedCapabilities: [],
        grantedPermissions: ['intelligence.knowledge_graph.read'],
      },
      { requiredPermission: 'intelligence.knowledge_graph.read' },
    );

    expect(decision.allowed).toBe(false);
    expect(decision.reason).toBe('capability_not_installed');
  });

  it('rejects frontend capability access when permission or data scope is missing', () => {
    const manifest = resolveCapabilityManifest('intelligence_fabric.knowledge_graph');
    expect(manifest).toBeDefined();

    const missingPermission = evaluateCapabilityAccess(
      manifest!,
      {
        installedCapabilities: ['intelligence_fabric.knowledge_graph'],
        grantedPermissions: [],
      },
      { requiredPermission: 'intelligence.knowledge_graph.read' },
    );
    const missingScope = evaluateCapabilityAccess(
      manifest!,
      {
        installedCapabilities: ['intelligence_fabric.knowledge_graph'],
        grantedPermissions: ['intelligence.knowledge_graph.read'],
        dataScopes: ['organization'],
      },
      {
        requiredPermission: 'intelligence.knowledge_graph.read',
        requiredDataScopes: ['organization', 'evidence'],
      },
    );

    expect(missingPermission.reason).toBe('missing_permission');
    expect(missingPermission.missingPermissions).toEqual(['intelligence.knowledge_graph.read']);
    expect(missingScope.reason).toBe('missing_data_scope');
    expect(missingScope.missingDataScopes).toEqual(['evidence']);
  });
});

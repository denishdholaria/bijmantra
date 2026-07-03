import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import {
  capabilitiesForBackendRoute,
  capabilitiesForFrontendRoute,
  capabilityManifests,
  evaluateCapabilityAccess,
  resolveCapabilityManifest,
  routePatternMatches,
} from './capabilities';

const seedOpsRouteSource = () => readFileSync(
  join(process.cwd(), 'src/routes/seed_ops.tsx'),
  'utf8',
);

const breedingRouteSource = () => readFileSync(
  join(process.cwd(), 'src/routes/breeding.tsx'),
  'utf8',
);

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
    expect(manifest?.lifecycle).toBe('active');
    expect(manifest?.standards).toContain('FAIR');
    expect(manifest?.standards).toContain('BrAPI v2.1');
    expect(manifest?.backendRoutes).toContain('/api/v2/federated-assets/*');
    expect(manifest?.requiredPermissions).toContain('research_assets.promote_fair');
  });

  it('declares the Accession Passport capability for MCPD exchange ownership', () => {
    const manifest = resolveCapabilityManifest('germplasm_global_seed_registry.accession_passport');

    expect(manifest).toBeDefined();
    expect(manifest?.ownerDomain).toBe('germplasm');
    expect(manifest?.lifecycle).toBe('active');
    expect(manifest?.standards).toContain('MCPD');
    expect(manifest?.frontendRoutes).toEqual(expect.arrayContaining([
      '/germplasm',
      '/germplasm/*',
      '/germplasm-passport',
      '/germplasm-search',
      '/seed-bank/accessions',
      '/seed-bank/accessions/*',
      '/seed-bank/mcpd',
    ]));
    expect(manifest?.backendRoutes).toContain('/api/v2/seed-bank/*');
    expect(manifest?.requiredPermissions).toContain('germplasm.read');
    expect(manifest?.requiredPermissions).toContain('germplasm.passport.manage');
    expect(manifest?.dataScopes).toContain('organization');
    expect(manifest?.dataScopes).toContain('accession');
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
    expect(capabilitiesForFrontendRoute('/seed-bank/mcpd').map(capability => capability.id)).toEqual([
      'germplasm_global_seed_registry.accession_passport',
    ]);
    expect(capabilitiesForFrontendRoute('/seed-bank/accessions').map(capability => capability.id)).toEqual([
      'germplasm_global_seed_registry.accession_passport',
    ]);
    expect(capabilitiesForFrontendRoute('/seed-bank/accessions/ACC-100').map(capability => capability.id)).toEqual([
      'germplasm_global_seed_registry.accession_passport',
    ]);
    expect(capabilitiesForFrontendRoute('/germplasm/GID-42/edit').map(capability => capability.id)).toEqual([
      'germplasm_global_seed_registry.accession_passport',
    ]);
    expect(capabilitiesForFrontendRoute('/germplasm-passport').map(capability => capability.id)).toEqual([
      'germplasm_global_seed_registry.accession_passport',
    ]);
    expect(capabilitiesForFrontendRoute('/germplasm-search').map(capability => capability.id)).toEqual([
      'germplasm_global_seed_registry.accession_passport',
    ]);
    expect(capabilitiesForBackendRoute('/api/v2/seed-bank/mcpd/template').map(capability => capability.id)).toEqual([
      'germplasm_global_seed_registry.accession_passport',
    ]);
  });

  it('protects the MCPD seed-bank route with the Accession Passport capability', () => {
    const source = seedOpsRouteSource();

    expect(source).toContain("path: '/seed-bank/mcpd'");
    expect(source).toContain('wrapCapability(SeedBankMCPD');
    expect(source).toContain("capabilityId: 'germplasm_global_seed_registry.accession_passport'");
    expect(source).toContain("requiredPermission: 'germplasm.read'");
    expect(source).toContain("requiredDataScopes: ['organization', 'accession']");
  });

  it('protects accession seed-bank routes with the Accession Passport capability', () => {
    const source = seedOpsRouteSource();

    expect(source).toContain("path: '/seed-bank/accessions'");
    expect(source).toContain('wrapCapability(SeedBankAccessions');
    expect(source).toContain('wrapCapability(SeedBankAccessionNew');
    expect(source).toContain('wrapCapability(SeedBankAccessionDetail');
    expect(source).toContain("capabilityId: 'germplasm_global_seed_registry.accession_passport'");
    expect(source).toContain("requiredPermission: 'germplasm.read'");
    expect(source).toContain("requiredDataScopes: ['organization', 'accession']");
  });

  it('protects germplasm passport routes with the Accession Passport capability', () => {
    const source = breedingRouteSource();

    expect(source).toContain("path: '/germplasm'");
    expect(source).toContain('wrapCapability(Germplasm');
    expect(source).toContain('wrapCapability(GermplasmForm');
    expect(source).toContain('wrapCapability(GermplasmDetail');
    expect(source).toContain('wrapCapability(GermplasmEdit');
    expect(source).toContain('wrapCapability(GermplasmPassport');
    expect(source).toContain('wrapCapability(GermplasmSearch');
    expect(source).toContain("capabilityId: 'germplasm_global_seed_registry.accession_passport'");
    expect(source).toContain("requiredPermission: 'germplasm.read'");
    expect(source).toContain("requiredDataScopes: ['organization', 'accession']");
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

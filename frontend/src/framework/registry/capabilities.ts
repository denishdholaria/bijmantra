export type CapabilityLifecycle = 'active' | 'planned' | 'proposed';

export interface CapabilityManifest {
  id: string;
  title: string;
  dominion: string;
  ownerDomain: string;
  supportingDomains: string[];
  lifecycle: CapabilityLifecycle;
  standards: string[];
  frontendRoutes: string[];
  backendRoutes: string[];
  dataScopes: string[];
  requiredPermissions: string[];
  suggestedRoles: string[];
  auditEvents: string[];
}

export type CapabilityAccessReason =
  | 'allowed'
  | 'capability_not_installed'
  | 'missing_permission'
  | 'missing_data_scope';

export interface CapabilityAccessContext {
  installedCapabilities: string[];
  grantedPermissions: string[];
  dataScopes?: string[];
  roles?: string[];
}

export interface CapabilityAccessDecision {
  allowed: boolean;
  reason: CapabilityAccessReason;
  capabilityId: string;
  missingPermissions: string[];
  missingDataScopes: string[];
}

export const capabilityManifests: CapabilityManifest[] = [
  {
    id: 'intelligence_fabric.knowledge_graph',
    title: 'Cross-Domain Knowledge Graph',
    dominion: 'intelligence_fabric',
    ownerDomain: 'intelligence',
    supportingDomains: [
      'breeding',
      'germplasm',
      'phenotyping',
      'field_operations',
      'commercial',
      'knowledge',
    ],
    lifecycle: 'active',
    standards: ['FAIR', 'JSON-LD', 'Schema.org', 'W3C PROV'],
    frontendRoutes: ['/knowledge-graph'],
    backendRoutes: ['/api/v2/knowledge-graph/*'],
    dataScopes: ['organization', 'asset', 'evidence', 'provenance'],
    requiredPermissions: ['intelligence.knowledge_graph.read', 'intelligence.knowledge_graph.write'],
    suggestedRoles: ['scientist', 'knowledge_curator', 'research_lead'],
    auditEvents: ['knowledge_graph.edge_created', 'knowledge_graph.evidence_retrieved'],
  },
  {
    id: 'scientific_publishing_fair_exchange.research_asset_core',
    title: 'Federated Research Asset Core',
    dominion: 'scientific_publishing_fair_exchange',
    ownerDomain: 'knowledge',
    supportingDomains: [
      'intelligence',
      'breeding',
      'phenotyping',
      'field_operations',
      'germplasm',
      'commercial',
    ],
    lifecycle: 'planned',
    standards: ['FAIR', 'JSON-LD', 'Schema.org', 'W3C PROV', 'DataCite DOI', 'BrAPI v2.1', 'Crop Ontology'],
    frontendRoutes: ['/data/federated-assets', '/knowledge/research-assets'],
    backendRoutes: ['/api/v2/fair-metadata/*', '/api/v2/federated-assets/*'],
    dataScopes: ['organization', 'asset', 'provenance', 'license', 'identifier', 'connector', 'evidence'],
    requiredPermissions: ['research_assets.read', 'research_assets.register', 'research_assets.promote_fair'],
    suggestedRoles: ['data_steward', 'knowledge_curator', 'research_lead', 'scientist'],
    auditEvents: [
      'federated_connector_upsert',
      'federated_connector_dry_run',
      'federated_asset_register',
      'federated_asset_promote_fair',
    ],
  },
];

function normalizeRoutePath(routePath: string): string {
  const normalized = routePath.split('?', 1)[0]?.replace(/\/+/g, '/') ?? '/';
  if (normalized === '/') return normalized;
  return normalized.replace(/\/+$/, '');
}

export function routePatternMatches(pattern: string, routePath: string): boolean {
  const normalizedPattern = normalizeRoutePath(pattern);
  const normalizedPath = normalizeRoutePath(routePath);

  if (normalizedPattern.endsWith('/*')) {
    const prefix = normalizedPattern.slice(0, -2);
    return normalizedPath === prefix || normalizedPath.startsWith(`${prefix}/`);
  }

  return normalizedPath === normalizedPattern;
}

export function resolveCapabilityManifest(capabilityId: string): CapabilityManifest | undefined {
  return capabilityManifests.find(capability => capability.id === capabilityId);
}

export function capabilitiesForFrontendRoute(routePath: string): CapabilityManifest[] {
  return capabilityManifests.filter(capability =>
    capability.frontendRoutes.some(pattern => routePatternMatches(pattern, routePath)),
  );
}

export function capabilitiesForBackendRoute(routePath: string): CapabilityManifest[] {
  return capabilityManifests.filter(capability =>
    capability.backendRoutes.some(pattern => routePatternMatches(pattern, routePath)),
  );
}

export function evaluateCapabilityAccess(
  capability: CapabilityManifest,
  context: CapabilityAccessContext,
  options: {
    requiredPermission?: string;
    requiredDataScopes?: string[];
  } = {},
): CapabilityAccessDecision {
  if (!context.installedCapabilities.includes(capability.id)) {
    return {
      allowed: false,
      reason: 'capability_not_installed',
      capabilityId: capability.id,
      missingPermissions: [],
      missingDataScopes: [],
    };
  }

  const missingPermissions = options.requiredPermission && !context.grantedPermissions.includes(options.requiredPermission)
    ? [options.requiredPermission]
    : [];
  if (missingPermissions.length > 0) {
    return {
      allowed: false,
      reason: 'missing_permission',
      capabilityId: capability.id,
      missingPermissions,
      missingDataScopes: [],
    };
  }

  const grantedDataScopes = context.dataScopes ?? [];
  const missingDataScopes = (options.requiredDataScopes ?? []).filter(
    dataScope => !grantedDataScopes.includes(dataScope),
  );
  if (missingDataScopes.length > 0) {
    return {
      allowed: false,
      reason: 'missing_data_scope',
      capabilityId: capability.id,
      missingPermissions: [],
      missingDataScopes,
    };
  }

  return {
    allowed: true,
    reason: 'allowed',
    capabilityId: capability.id,
    missingPermissions: [],
    missingDataScopes: [],
  };
}

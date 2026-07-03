import type {
  CapabilityAccessContext,
  CapabilityAccessDecision,
  CapabilityAccessReason,
  CapabilityManifest,
} from './capabilities';
import { capabilitiesForFrontendRoute, evaluateCapabilityAccess } from './capabilities';
import type { NavigationNode } from './navigation-source';

export type CapabilityNavigationDecisionReason = CapabilityAccessReason;

export interface CapabilityNavigationNodeDecision {
  nodeId: string;
  path: string;
  capabilityIds: string[];
  allowed: boolean;
  reason: CapabilityNavigationDecisionReason;
  blockedCapabilities: string[];
  missingPermissions: string[];
  missingDataScopes: string[];
}

function evaluateRouteCapability(
  node: NavigationNode,
  capability: CapabilityManifest,
  context: CapabilityAccessContext,
): CapabilityAccessDecision {
  const routePermissions = (node.requiredPermissions ?? []).filter(permission =>
    capability.requiredPermissions.includes(permission),
  );
  const routeDataScopes = (node.requiredDataScopes ?? []).filter(dataScope =>
    capability.dataScopes.includes(dataScope),
  );

  if (routePermissions.length === 0) {
    return evaluateCapabilityAccess(capability, context, {
      requiredDataScopes: routeDataScopes,
    });
  }

  for (const requiredPermission of routePermissions) {
    const decision = evaluateCapabilityAccess(capability, context, {
      requiredPermission,
      requiredDataScopes: routeDataScopes,
    });
    if (!decision.allowed) {
      return decision;
    }
  }

  return evaluateCapabilityAccess(capability, context, {
    requiredDataScopes: routeDataScopes,
  });
}

export function evaluateCapabilityNavigationNode(
  node: NavigationNode,
  context: CapabilityAccessContext,
): CapabilityNavigationNodeDecision {
  const capabilities = capabilitiesForFrontendRoute(node.path);

  if (capabilities.length === 0) {
    return {
      nodeId: node.id,
      path: node.path,
      capabilityIds: [],
      allowed: true,
      reason: 'allowed',
      blockedCapabilities: [],
      missingPermissions: [],
      missingDataScopes: [],
    };
  }

  const decisions = capabilities.map(capability => evaluateRouteCapability(node, capability, context));
  const denied = decisions.find(decision => !decision.allowed);

  if (!denied) {
    return {
      nodeId: node.id,
      path: node.path,
      capabilityIds: capabilities.map(capability => capability.id),
      allowed: true,
      reason: 'allowed',
      blockedCapabilities: [],
      missingPermissions: [],
      missingDataScopes: [],
    };
  }

  return {
    nodeId: node.id,
    path: node.path,
    capabilityIds: capabilities.map(capability => capability.id),
    allowed: false,
    reason: denied.reason,
    blockedCapabilities: decisions
      .filter(decision => !decision.allowed)
      .map(decision => decision.capabilityId),
    missingPermissions: decisions.flatMap(decision => decision.missingPermissions),
    missingDataScopes: decisions.flatMap(decision => decision.missingDataScopes),
  };
}

export function collectCapabilityNavigationDecisions(
  tree: NavigationNode[],
  context: CapabilityAccessContext,
): CapabilityNavigationNodeDecision[] {
  const decisions: CapabilityNavigationNodeDecision[] = [];

  function visit(nodes: NavigationNode[]): void {
    for (const node of nodes) {
      decisions.push(evaluateCapabilityNavigationNode(node, context));

      if (node.children && node.children.length > 0) {
        visit(node.children);
      }
    }
  }

  visit(tree);
  return decisions;
}

export function collectBlockedCapabilityNavigationNodes(
  tree: NavigationNode[],
  context: CapabilityAccessContext,
): CapabilityNavigationNodeDecision[] {
  return collectCapabilityNavigationDecisions(tree, context).filter(decision => !decision.allowed);
}

export function filterNavigationTreeByCapabilityAccess(
  tree: NavigationNode[],
  context: CapabilityAccessContext,
): NavigationNode[] {
  function filterNodes(nodes: NavigationNode[]): NavigationNode[] {
    return nodes.flatMap(node => {
      const decision = evaluateCapabilityNavigationNode(node, context);
      if (!decision.allowed) {
        return [];
      }

      return [
        {
          ...node,
          children: node.children ? filterNodes(node.children) : undefined,
        },
      ];
    });
  }

  return filterNodes(tree);
}

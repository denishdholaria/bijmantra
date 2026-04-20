/**
 * Workspace Service
 * 
 * Business logic for workspace operations.
 * Metadata lives in workspaces.ts, logic lives here.
 */

import type { 
  Workspace, 
  WorkspaceId, 
  WorkspaceModule, 
  ModuleId,
  CrossAccessConfig 
} from '@/types/workspace';
import { workspaces, workspaceModules, crossAccessPages } from '../workspaces';

/**
 * Get a workspace by ID
 */
export function getWorkspace(id: WorkspaceId): Workspace | undefined {
  return workspaces.find(w => w.id === id);
}

/**
 * Get all workspaces
 */
export function getAllWorkspaces(): Workspace[] {
  return workspaces;
}

/**
 * Get modules for a specific workspace
 */
export function getWorkspaceModules(workspaceId: WorkspaceId): WorkspaceModule[] {
  return workspaceModules.filter(m => m.workspaces.includes(workspaceId));
}

/**
 * Get a module by ID
 */
export function getModule(moduleId: ModuleId): WorkspaceModule | undefined {
  return workspaceModules.find(m => m.id === moduleId);
}

/**
 * Check if a route is accessible from a workspace
 */
export function isRouteInWorkspace(route: string, workspaceId: WorkspaceId): boolean {
  // Check direct module pages
  const modules = getWorkspaceModules(workspaceId);
  for (const module of modules) {
    if (module.pages.some(p => p.route === route || route.startsWith(p.route.replace(':id', '')))) {
      return true;
    }
  }
  
  // Check cross-access pages
  const crossAccess = crossAccessPages.find(c => c.route === route);
  if (crossAccess) {
    return crossAccess.primaryWorkspace === workspaceId || 
           crossAccess.additionalWorkspaces.includes(workspaceId);
  }
  
  // Global pages are always accessible
  const globalModule = workspaceModules.find(m => m.id === 'global');
  if (globalModule?.pages.some(p => p.route === route)) {
    return true;
  }
  
  return false;
}

/**
 * Get the primary workspace for a route
 */
export function getPrimaryWorkspaceForRoute(route: string): WorkspaceId | null {
  // Check cross-access first
  const crossAccess = crossAccessPages.find(c => c.route === route);
  if (crossAccess) {
    return crossAccess.primaryWorkspace;
  }
  
  // Find first workspace that contains this route
  for (const workspace of workspaces) {
    const modules = getWorkspaceModules(workspace.id);
    for (const module of modules) {
      if (module.pages.some(p => p.route === route || route.startsWith(p.route.replace(':id', '')))) {
        return workspace.id;
      }
    }
  }
  
  return null;
}

/**
 * Get all routes for a workspace
 */
export function getWorkspaceRoutes(workspaceId: WorkspaceId): string[] {
  const modules = getWorkspaceModules(workspaceId);
  const routes: string[] = [];
  
  for (const module of modules) {
    for (const page of module.pages) {
      routes.push(page.route);
    }
  }
  
  // Add cross-access routes
  for (const crossAccess of crossAccessPages) {
    if (crossAccess.additionalWorkspaces.includes(workspaceId) && !routes.includes(crossAccess.route)) {
      routes.push(crossAccess.route);
    }
  }
  
  return routes;
}

/**
 * Get workspace statistics
 */
export function getWorkspaceStats(workspaceId: WorkspaceId): { pageCount: number; moduleCount: number } {
  const modules = getWorkspaceModules(workspaceId);
  const pageCount = modules.reduce((sum, m) => sum + m.pages.length, 0);
  return { pageCount, moduleCount: modules.length };
}

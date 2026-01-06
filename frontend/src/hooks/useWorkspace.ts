/**
 * Workspace Management Hook
 * 
 * Enhanced hook for Gateway-Workspace Architecture.
 * Provides workspace switching, filtering, and navigation helpers.
 * 
 * @see docs/confidential/archieve/GATEWAY-WORKSPACE.md for full specification
 */

import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { divisions } from '@/framework/registry/divisions';
import { 
  getAllWorkspaces, 
  getWorkspace, 
  getWorkspaceModules,
  isRouteInWorkspace,
  getWorkspaceRoutes,
} from '@/framework/registry/workspaces';
import { 
  useWorkspaceStore,
  useActiveWorkspace,
  useShouldShowGateway,
} from '@/store/workspaceStore';
import type { Division } from '@/framework/registry/types';
import type { WorkspaceId, Workspace, WorkspaceModule } from '@/types/workspace';

// Re-export types for convenience
export type { WorkspaceId, Workspace, WorkspaceModule };

// Legacy type alias for backward compatibility
export type WorkspaceType = WorkspaceId;

// Legacy workspace definitions for backward compatibility
export const WORKSPACES = getAllWorkspaces().map(w => ({
  id: w.id as WorkspaceType,
  name: w.name,
  description: w.description,
  icon: w.icon,
  color: w.color,
  divisionIds: getDivisionIdsForWorkspace(w.id),
}));

/**
 * Map workspace modules to division IDs for backward compatibility
 */
function getDivisionIdsForWorkspace(workspaceId: WorkspaceId): string[] {
  const moduleToDiv: Record<string, string[]> = {
    'core': ['plant-sciences', 'home'],
    'germplasm': ['plant-sciences'],
    'phenotyping': ['plant-sciences'],
    'genotyping': ['plant-sciences'],
    'seed-bank': ['seed-bank'],
    'environment': ['environment'],
    'sensors': ['sensor-networks'],
    'lab-testing': ['seed-commerce'],
    'processing': ['seed-commerce'],
    'inventory': ['seed-commerce'],
    'dispatch': ['seed-commerce'],
    'traceability': ['seed-commerce'],
    'dus-testing': ['seed-commerce'],
    'licensing': ['seed-commerce'],
    'space-research': ['space-research'],
    'ai-vision': ['plant-sciences'],
    'analytics': ['plant-sciences', 'home'],
    'analysis-tools': ['plant-sciences'],
    'settings': ['settings'],
    'users-teams': ['settings'],
    'integrations': ['settings'],
    'system': ['settings'],
    'tools': ['tools'],
    'developer': ['settings'],
    'global': ['home', 'knowledge'],
  };
  
  const workspace = getWorkspace(workspaceId);
  if (!workspace) return [];
  
  const divIds = new Set<string>();
  for (const moduleId of workspace.modules) {
    const divs = moduleToDiv[moduleId] || [];
    divs.forEach(d => divIds.add(d));
  }
  
  // Always include home and knowledge
  divIds.add('home');
  divIds.add('knowledge');
  
  return Array.from(divIds);
}

/**
 * Main workspace hook - provides all workspace functionality
 */
export function useWorkspace() {
  const navigate = useNavigate();
  
  // Store state
  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId);
  const preferences = useWorkspaceStore(state => state.preferences);
  const hasSelectedWorkspace = useWorkspaceStore(state => state.hasSelectedWorkspace);
  const setActiveWorkspace = useWorkspaceStore(state => state.setActiveWorkspace);
  const setDefaultWorkspace = useWorkspaceStore(state => state.setDefaultWorkspace);
  const clearDefaultWorkspace = useWorkspaceStore(state => state.clearDefaultWorkspace);
  const dismissGateway = useWorkspaceStore(state => state.dismissGateway);
  const resetGateway = useWorkspaceStore(state => state.resetGateway);
  
  // Derived state
  const activeWorkspace = useActiveWorkspace();
  const shouldShowGateway = useShouldShowGateway();
  const allWorkspaces = useMemo(() => getAllWorkspaces(), []);
  
  // Current workspace (for backward compatibility)
  const currentWorkspace = activeWorkspaceId || 'breeding';
  const workspace = activeWorkspace || getWorkspace('breeding')!;
  
  // Filter divisions based on current workspace
  const filteredDivisions = useMemo((): Division[] => {
    if (!activeWorkspaceId) return divisions;
    
    const divisionIds = getDivisionIdsForWorkspace(activeWorkspaceId);
    const allowedIds = new Set(divisionIds);
    return divisions.filter(d => allowedIds.has(d.id));
  }, [activeWorkspaceId]);
  
  // Get modules for current workspace
  const workspaceModules = useMemo(() => {
    if (!activeWorkspaceId) return [];
    return getWorkspaceModules(activeWorkspaceId);
  }, [activeWorkspaceId]);
  
  // Check if a division is visible in current workspace
  const isDivisionVisible = useCallback((divisionId: string) => {
    if (!activeWorkspaceId) return true;
    const divisionIds = getDivisionIdsForWorkspace(activeWorkspaceId);
    return divisionIds.includes(divisionId);
  }, [activeWorkspaceId]);
  
  // Check if a route is accessible in current workspace
  const isRouteAccessible = useCallback((route: string) => {
    if (!activeWorkspaceId) return true;
    return isRouteInWorkspace(route, activeWorkspaceId);
  }, [activeWorkspaceId]);
  
  // Set workspace and navigate to landing page
  const setWorkspace = useCallback((workspaceId: WorkspaceId, navigateToLanding = true) => {
    setActiveWorkspace(workspaceId);
    
    if (navigateToLanding) {
      const ws = getWorkspace(workspaceId);
      if (ws) {
        navigate(ws.landingRoute);
      }
    }
  }, [setActiveWorkspace, navigate]);
  
  // Switch workspace (alias for setWorkspace)
  const switchWorkspace = useCallback((workspaceId: WorkspaceId) => {
    setWorkspace(workspaceId, true);
  }, [setWorkspace]);
  
  // Set as default and switch
  const setAsDefaultAndSwitch = useCallback((workspaceId: WorkspaceId) => {
    setDefaultWorkspace(workspaceId);
    setWorkspace(workspaceId, true);
  }, [setDefaultWorkspace, setWorkspace]);
  
  // Get workspace routes
  const getRoutes = useCallback((workspaceId?: WorkspaceId) => {
    const wsId = workspaceId || activeWorkspaceId;
    if (!wsId) return [];
    return getWorkspaceRoutes(wsId);
  }, [activeWorkspaceId]);

  return {
    // State
    currentWorkspace: currentWorkspace as WorkspaceType,
    activeWorkspaceId,
    workspace,
    activeWorkspace,
    workspaces: allWorkspaces,
    preferences,
    hasSelectedWorkspace,
    shouldShowGateway,
    
    // Filtered data
    filteredDivisions,
    workspaceModules,
    
    // Actions
    setWorkspace,
    switchWorkspace,
    setActiveWorkspace,
    setDefaultWorkspace,
    setAsDefaultAndSwitch,
    clearDefaultWorkspace,
    dismissGateway,
    resetGateway,
    
    // Queries
    isDivisionVisible,
    isRouteAccessible,
    getRoutes,
    
    // Computed
    isAdmin: activeWorkspaceId === 'admin',
    isBrAPIWorkspace: activeWorkspace?.isBrAPIAligned ?? false,
  };
}

export default useWorkspace;

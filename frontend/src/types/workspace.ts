/**
 * Workspace Type Definitions
 * 
 * Gateway-Workspace Architecture for multi-pathway navigation.
 * Users choose their workspace based on role/work, with BrAPI modules intact.
 * 
 * @see docs/gupt/archieve/GATEWAY-WORKSPACE.md for full specification
 */

/**
 * Workspace identifiers - the 5 main pathways
 */
export type WorkspaceId = 
  | 'breeding'    // Plant Breeding - BrAPI aligned
  | 'seed-ops'    // Seed Industry - Lab, processing, dispatch
  | 'research'    // Innovation Lab - Space, AI, analytics
  | 'genebank'    // Gene Bank - Conservation, vaults, exchange
  | 'admin';      // Administration - System management

/**
 * Module identifiers within workspaces
 * Maps to BrAPI modules and custom modules
 */
export type ModuleId = 
  // BrAPI Core Modules (Plant Breeding)
  | 'core'
  | 'germplasm'
  | 'phenotyping'
  | 'genotyping'
  // Seed Industry Modules
  | 'lab-testing'
  | 'processing'
  | 'inventory'
  | 'dispatch'
  | 'traceability'
  | 'dus-testing'
  | 'licensing'
  // Innovation Lab Modules
  | 'space-research'
  | 'ai-vision'
  | 'analytics'
  | 'analysis-tools'
  // Gene Bank Modules
  | 'seed-bank'
  | 'environment'
  | 'sensors'
  // Administration Modules
  | 'settings'
  | 'users-teams'
  | 'integrations'
  | 'system'
  | 'tools'
  | 'developer'
  // Global (always accessible)
  | 'global';

/**
 * Workspace definition
 */
export interface Workspace {
  /** Unique identifier */
  id: WorkspaceId;
  
  /** Display name (internationally friendly) */
  name: string;
  
  /** Short description for gateway page */
  description: string;
  
  /** Longer description for tooltips/help */
  longDescription?: string;
  
  /** Lucide icon name */
  icon: string;
  
  /** Tailwind gradient classes for theming */
  color: string;
  
  /** Background color for cards */
  bgColor: string;
  
  /** Landing route after selection */
  landingRoute: string;
  
  /** Module IDs included in this workspace */
  modules: ModuleId[];
  
  /** Target user personas */
  targetUsers: string[];
  
  /** Estimated page count */
  pageCount: number;
  
  /** Whether this workspace uses BrAPI modules */
  isBrAPIAligned: boolean;
}

/**
 * Module definition within a workspace
 */
export interface WorkspaceModule {
  /** Unique identifier */
  id: ModuleId;
  
  /** Display name */
  name: string;
  
  /** Module description */
  description: string;
  
  /** Lucide icon name */
  icon: string;
  
  /** Base route for this module */
  route: string;
  
  /** Page routes within this module */
  pages: WorkspacePage[];
  
  /** Whether this is a BrAPI v2.1 compliant module */
  isBrAPI: boolean;
  
  /** Workspaces this module appears in */
  workspaces: WorkspaceId[];
}

/**
 * Page definition within a module
 */
export interface WorkspacePage {
  /** Unique identifier */
  id: string;
  
  /** Display name */
  name: string;
  
  /** Full route path */
  route: string;
  
  /** Whether this page appears in multiple workspaces */
  isCrossAccess?: boolean;
  
  /** Additional workspaces this page is accessible from */
  crossAccessWorkspaces?: WorkspaceId[];
}

/**
 * User workspace preferences (persisted)
 */
export interface WorkspacePreferences {
  /** User's default workspace */
  defaultWorkspace: WorkspaceId | null;
  
  /** Recently accessed workspaces (for quick switch) */
  recentWorkspaces: WorkspaceId[];
  
  /** Whether to show gateway on login */
  showGatewayOnLogin: boolean;
  
  /** Last accessed workspace */
  lastWorkspace: WorkspaceId | null;
  
  /** Timestamp of last workspace change */
  lastChanged: string | null;

  /** @deprecated Use themeStore instead. Kept for migration compatibility. */
  theme?: 'prakruti' | 'aerospace';
}

/**
 * Workspace context for components
 */
export interface WorkspaceContext {
  /** Currently active workspace */
  activeWorkspace: Workspace | null;
  
  /** User's workspace preferences */
  preferences: WorkspacePreferences;
  
  /** Whether user has selected a workspace this session */
  hasSelectedWorkspace: boolean;
  
  /** Whether gateway should be shown */
  shouldShowGateway: boolean;
}

/**
 * Cross-access configuration for pages that appear in multiple workspaces
 */
export interface CrossAccessConfig {
  /** Page route */
  route: string;
  
  /** Primary workspace (where page is "home") */
  primaryWorkspace: WorkspaceId;
  
  /** Additional workspaces where page is accessible */
  additionalWorkspaces: WorkspaceId[];
}

/**
 * Workspace statistics for dashboard/gateway display
 */
export interface WorkspaceStats {
  /** Workspace ID */
  workspaceId: WorkspaceId;
  
  /** Number of pages in workspace */
  pageCount: number;
  
  /** Number of modules in workspace */
  moduleCount: number;
  
  /** Recent activity count (optional) */
  recentActivity?: number;
  
  /** Pending items count (optional) */
  pendingItems?: number;
}

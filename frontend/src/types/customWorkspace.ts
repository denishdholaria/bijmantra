/**
 * Custom Workspace Types
 * 
 * Type definitions for user-defined custom workspaces.
 * Custom workspaces allow users to create personalized navigation
 * by selecting pages they use frequently.
 * 
 * @see docs/confidential/archieve/MyWorkspace.md for full specification
 */

/**
 * Available color themes for custom workspaces
 */
export type WorkspaceColor = 'green' | 'blue' | 'purple' | 'amber' | 'slate';

/**
 * Custom workspace created by user
 */
export interface CustomWorkspace {
  /** Unique identifier (UUID) */
  id: string;
  
  /** User-defined name */
  name: string;
  
  /** Optional description */
  description?: string;
  
  /** Lucide icon name */
  icon: string;
  
  /** Color theme */
  color: WorkspaceColor;
  
  /** Selected page IDs from the page registry */
  pageIds: string[];
  
  /** Template this was created from (if any) */
  templateId?: string;
  
  /** Timestamps */
  createdAt: string;
  updatedAt: string;
}

/**
 * Predefined template for quick workspace creation
 */
export interface WorkspaceTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: WorkspaceColor;
  pageIds: string[];
  targetRole: string;
  category: 'breeding' | 'seed-ops' | 'research' | 'genebank' | 'admin';
}

/**
 * Page definition for the picker
 */
export interface SelectablePage {
  id: string;
  name: string;
  route: string;
  moduleId: string;
  moduleName: string;
  icon?: string;
  description?: string;
}

/**
 * Module group for page picker
 */
export interface PageModule {
  id: string;
  name: string;
  icon: string;
  pages: SelectablePage[];
}

/**
 * Color configuration for workspace themes
 */
export const WORKSPACE_COLORS: Record<WorkspaceColor, {
  gradient: string;
  bg: string;
  border: string;
  text: string;
  badge: string;
}> = {
  green: {
    gradient: 'from-green-500 to-emerald-600',
    bg: 'bg-green-50 dark:bg-green-950/30',
    border: 'border-green-200 dark:border-green-800',
    text: 'text-green-700 dark:text-green-300',
    badge: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  },
  blue: {
    gradient: 'from-blue-500 to-indigo-600',
    bg: 'bg-blue-50 dark:bg-blue-950/30',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-700 dark:text-blue-300',
    badge: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  },
  purple: {
    gradient: 'from-purple-500 to-violet-600',
    bg: 'bg-purple-50 dark:bg-purple-950/30',
    border: 'border-purple-200 dark:border-purple-800',
    text: 'text-purple-700 dark:text-purple-300',
    badge: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  },
  amber: {
    gradient: 'from-amber-500 to-orange-600',
    bg: 'bg-amber-50 dark:bg-amber-950/30',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-700 dark:text-amber-300',
    badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  },
  slate: {
    gradient: 'from-slate-500 to-gray-600',
    bg: 'bg-slate-50 dark:bg-slate-950/30',
    border: 'border-slate-200 dark:border-slate-800',
    text: 'text-slate-700 dark:text-slate-300',
    badge: 'bg-slate-100 text-slate-700 dark:bg-slate-900/40 dark:text-slate-300',
  },
};

/**
 * Available icons for custom workspaces
 */
export const WORKSPACE_ICONS = [
  'Sprout', 'Wheat', 'Leaf', 'TreeDeciduous', 'Flower2',
  'FlaskConical', 'Microscope', 'Dna', 'TestTube', 'Beaker',
  'BarChart3', 'LineChart', 'PieChart', 'TrendingUp', 'Activity',
  'Factory', 'Building2', 'Warehouse', 'Package', 'Truck',
  'ClipboardList', 'FileText', 'FolderOpen', 'Database', 'Server',
  'Sun', 'CloudSun', 'Droplets', 'Thermometer', 'Wind',
  'Target', 'Crosshair', 'Focus', 'Zap', 'Rocket',
  'Users', 'UserCheck', 'Shield', 'Lock', 'Settings',
] as const;

/**
 * Limits for custom workspaces
 */
export const CUSTOM_WORKSPACE_LIMITS = {
  maxWorkspaces: 10,
  maxPagesPerWorkspace: 50,
  minPagesPerWorkspace: 1,
  maxNameLength: 50,
  maxDescriptionLength: 200,
} as const;

/**
 * Unified active-workspace context.
 *
 * The codebase has two workspace stores:
 *   - workspaceStore      → predefined workspaces (Breeding, Seed Bank, etc.)
 *   - customWorkspaceStore → user-created workspaces
 *
 * Both now enforce mutual exclusivity: activating one clears the other.
 * This module provides a single hook that returns whichever is currently
 * active, so components don't need to query both stores and implement
 * their own arbitration.
 *
 * Usage:
 *   const { activeWorkspace, activeWorkspaceType, isRouteAccessible } = useActiveWorkspaceContext();
 */

import { useWorkspaceStore } from './workspaceStore';
import { useCustomWorkspaceStore } from './customWorkspaceStore';
import { getWorkspace } from '@/framework/registry/workspaces';
import type { Workspace } from '@/types/workspace';
import type { CustomWorkspace } from '@/types/customWorkspace';

export type ActiveWorkspaceType = 'predefined' | 'custom' | 'none';

export interface ActiveWorkspaceContext {
  /** The active predefined workspace, or null */
  predefinedWorkspace: Workspace | null;
  /** The active custom workspace, or null */
  customWorkspace: CustomWorkspace | null;
  /** Which type is currently active */
  activeWorkspaceType: ActiveWorkspaceType;
  /** True if any workspace (predefined or custom) is active */
  hasActiveWorkspace: boolean;
  /**
   * Route accessibility check that respects whichever workspace is active.
   * Returns true when no workspace is active (unrestricted navigation).
   */
  isRouteAccessible: (route: string) => boolean;
}

/**
 * Single hook for workspace-aware route access and active workspace identity.
 * Replaces the pattern of calling both useWorkspaceStore and useCustomWorkspaceStore
 * and manually arbitrating between them.
 */
export function useActiveWorkspaceContext(): ActiveWorkspaceContext {
  const predefinedId = useWorkspaceStore((s) => s.activeWorkspaceId);
  const customId = useCustomWorkspaceStore((s) => s.activeCustomWorkspaceId);
  const customWorkspaces = useCustomWorkspaceStore((s) => s.customWorkspaces);
  const isRouteInPredefined = useWorkspaceStore((s) => s.isRouteAccessible);

  const predefinedWorkspace = predefinedId ? (getWorkspace(predefinedId) ?? null) : null;
  const customWorkspace = customId
    ? (customWorkspaces.find((w) => w.id === customId) ?? null)
    : null;

  const activeWorkspaceType: ActiveWorkspaceType =
    predefinedWorkspace ? 'predefined' : customWorkspace ? 'custom' : 'none';

  const isRouteAccessible = (route: string): boolean => {
    if (activeWorkspaceType === 'none') return true;
    if (activeWorkspaceType === 'predefined') return isRouteInPredefined(route);
    // Custom workspace: check if the route's page ID is in the workspace's page list.
    // Page IDs in custom workspaces are stored as route paths.
    return customWorkspace!.pageIds.includes(route);
  };

  return {
    predefinedWorkspace,
    customWorkspace,
    activeWorkspaceType,
    hasActiveWorkspace: activeWorkspaceType !== 'none',
    isRouteAccessible,
  };
}

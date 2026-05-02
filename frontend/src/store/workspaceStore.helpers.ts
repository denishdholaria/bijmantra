import type { WorkspaceId, WorkspacePreferences } from '@/types/workspace';
import type { WorkspacePreferences as ApiWorkspacePreferences } from '@/lib/api/system/workspace';
import { z } from 'zod';

// Zod schema for validating workspace IDs from the backend
const WorkspaceIdSchema = z.string().refine(
  (id) => {
    // Valid workspace IDs are defined in the registry — this is a runtime check
    // that the backend didn't return a workspace ID that no longer exists.
    // For now, accept any non-empty string; stricter validation can be added later.
    return id.trim().length > 0;
  },
  { message: 'Workspace ID must be a non-empty string' }
);

export const MAX_RECENT_WORKSPACES = 5;

export const initialWorkspacePreferences: WorkspacePreferences = {
  defaultWorkspace: null,
  recentWorkspaces: [],
  showGatewayOnLogin: true,
  lastWorkspace: null,
  lastChanged: null,
};

export function updateRecentWorkspaces(
  recentWorkspaces: WorkspaceId[],
  workspaceId: WorkspaceId,
): WorkspaceId[] {
  return [
    workspaceId,
    ...recentWorkspaces.filter(id => id !== workspaceId),
  ].slice(0, MAX_RECENT_WORKSPACES);
}

export function buildWorkspaceSelectionPreferences(
  preferences: WorkspacePreferences,
  workspaceId: WorkspaceId,
): WorkspacePreferences {
  return {
    ...preferences,
    lastWorkspace: workspaceId,
    lastChanged: new Date().toISOString(),
    recentWorkspaces: updateRecentWorkspaces(preferences.recentWorkspaces, workspaceId),
  };
}

export function buildDefaultWorkspacePreferences(
  preferences: WorkspacePreferences,
  workspaceId: WorkspaceId | null,
): WorkspacePreferences {
  return {
    ...preferences,
    defaultWorkspace: workspaceId,
    showGatewayOnLogin: workspaceId === null,
  };
}

export function mergeWorkspacePreferencesFromBackend(
  currentPreferences: WorkspacePreferences,
  backendPreferences: ApiWorkspacePreferences,
): WorkspacePreferences {
  // Validate workspace IDs from backend before storing them.
  // An invalid/unknown ID would cause getWorkspace(activeWorkspaceId) to return
  // null and silently break the workspace selector.
  const parseWorkspaceId = (raw: unknown): WorkspaceId | null => {
    if (raw === null || raw === undefined) return null;
    const result = WorkspaceIdSchema.safeParse(raw);
    if (!result.success) {
      console.warn('[workspaceStore] Invalid workspace ID from backend:', raw);
      return null;
    }
    return result.data as WorkspaceId;
  };

  const parseWorkspaceIdArray = (raw: unknown): WorkspaceId[] => {
    if (!Array.isArray(raw)) return [];
    return raw
      .map(parseWorkspaceId)
      .filter((id): id is WorkspaceId => id !== null);
  };

  return {
    ...currentPreferences,
    defaultWorkspace: parseWorkspaceId(backendPreferences.default_workspace),
    recentWorkspaces: parseWorkspaceIdArray(backendPreferences.recent_workspaces),
    showGatewayOnLogin: backendPreferences.show_gateway_on_login ?? true,
    lastWorkspace: parseWorkspaceId(backendPreferences.last_workspace),
  };
}

export function shouldShowWorkspaceGateway({
  preferences,
  hasSelectedWorkspace,
  isGatewayDismissed,
}: {
  preferences: WorkspacePreferences;
  hasSelectedWorkspace: boolean;
  isGatewayDismissed: boolean;
}): boolean {
  if (isGatewayDismissed) {
    return false;
  }

  if (hasSelectedWorkspace) {
    return false;
  }

  if (preferences.showGatewayOnLogin) {
    return true;
  }

  if (preferences.defaultWorkspace) {
    return false;
  }

  return true;
}
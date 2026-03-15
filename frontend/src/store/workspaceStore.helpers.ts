import type { WorkspaceId, WorkspacePreferences } from '@/types/workspace';
import type { WorkspacePreferences as ApiWorkspacePreferences } from '@/lib/api/system/workspace';

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
  return {
    ...currentPreferences,
    defaultWorkspace: backendPreferences.default_workspace as WorkspaceId | null,
    recentWorkspaces: (backendPreferences.recent_workspaces || []) as WorkspaceId[],
    showGatewayOnLogin: backendPreferences.show_gateway_on_login ?? true,
    lastWorkspace: backendPreferences.last_workspace as WorkspaceId | null,
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
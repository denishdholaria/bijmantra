import type { WorkspaceId, WorkspacePreferences } from '@/types/workspace';
import { apiClient } from '@/lib/api-client';
import {
  mergeWorkspacePreferencesFromBackend,
} from './workspaceStore.helpers';

export async function recordWorkspacePreferenceSwitch(workspaceId: WorkspaceId): Promise<void> {
  await apiClient.workspacePreferencesService.recordWorkspaceSwitch(workspaceId);
}

export async function persistDefaultWorkspacePreference(workspaceId: WorkspaceId | null): Promise<void> {
  if (workspaceId) {
    await apiClient.workspacePreferencesService.setDefaultWorkspace(workspaceId);
    return;
  }

  await apiClient.workspacePreferencesService.clearDefaultWorkspace();
}

export async function syncWorkspacePreferencesToBackend(
  preferences: WorkspacePreferences,
): Promise<void> {
  await apiClient.workspacePreferencesService.updatePreferences({
    default_workspace: preferences.defaultWorkspace,
    recent_workspaces: preferences.recentWorkspaces,
    show_gateway_on_login: preferences.showGatewayOnLogin,
    last_workspace: preferences.lastWorkspace,
  });
}

export async function loadWorkspacePreferencesFromBackend(
  currentPreferences: WorkspacePreferences,
): Promise<WorkspacePreferences | null> {
  const response = await apiClient.workspacePreferencesService.getPreferences();

  if (response.status !== 'success' || !response.data) {
    return null;
  }

  return mergeWorkspacePreferencesFromBackend(currentPreferences, response.data);
}
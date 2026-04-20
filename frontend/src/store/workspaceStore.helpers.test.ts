import { describe, expect, it, vi } from 'vitest';
import type { WorkspacePreferences } from '@/types/workspace';
import {
  buildDefaultWorkspacePreferences,
  buildWorkspaceSelectionPreferences,
  initialWorkspacePreferences,
  mergeWorkspacePreferencesFromBackend,
  shouldShowWorkspaceGateway,
  updateRecentWorkspaces,
} from './workspaceStore.helpers';

describe('workspaceStore helpers', () => {
  it('keeps recent workspaces unique and capped', () => {
    const recent = updateRecentWorkspaces(
      ['breeding', 'seed-ops', 'research', 'genebank', 'admin'],
      'research',
    );

    expect(recent).toEqual(['research', 'breeding', 'seed-ops', 'genebank', 'admin']);
  });

  it('updates selection preferences with last workspace and timestamp', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-12T12:00:00.000Z'));

    const preferences = buildWorkspaceSelectionPreferences(initialWorkspacePreferences, 'breeding');

    expect(preferences.lastWorkspace).toBe('breeding');
    expect(preferences.lastChanged).toBe('2026-03-12T12:00:00.000Z');
    expect(preferences.recentWorkspaces).toEqual(['breeding']);

    vi.useRealTimers();
  });

  it('toggles gateway visibility when default workspace changes', () => {
    const withDefault = buildDefaultWorkspacePreferences(initialWorkspacePreferences, 'admin');
    const withoutDefault = buildDefaultWorkspacePreferences(withDefault, null);

    expect(withDefault.showGatewayOnLogin).toBe(false);
    expect(withDefault.defaultWorkspace).toBe('admin');
    expect(withoutDefault.showGatewayOnLogin).toBe(true);
    expect(withoutDefault.defaultWorkspace).toBeNull();
  });

  it('merges backend preferences into the local shape', () => {
    const current: WorkspacePreferences = {
      ...initialWorkspacePreferences,
      lastChanged: '2026-03-11T00:00:00.000Z',
    };

    const merged = mergeWorkspacePreferencesFromBackend(current, {
      user_id: 1,
      default_workspace: 'research',
      recent_workspaces: ['research', 'breeding'],
      show_gateway_on_login: false,
      last_workspace: 'research',
      updated_at: '2026-03-12T00:00:00.000Z',
    });

    expect(merged).toEqual({
      ...current,
      defaultWorkspace: 'research',
      recentWorkspaces: ['research', 'breeding'],
      showGatewayOnLogin: false,
      lastWorkspace: 'research',
    });
  });

  it('computes gateway visibility from session and preference state', () => {
    expect(
      shouldShowWorkspaceGateway({
        preferences: initialWorkspacePreferences,
        hasSelectedWorkspace: false,
        isGatewayDismissed: false,
      }),
    ).toBe(true);

    expect(
      shouldShowWorkspaceGateway({
        preferences: initialWorkspacePreferences,
        hasSelectedWorkspace: true,
        isGatewayDismissed: false,
      }),
    ).toBe(false);

    expect(
      shouldShowWorkspaceGateway({
        preferences: buildDefaultWorkspacePreferences(initialWorkspacePreferences, 'breeding'),
        hasSelectedWorkspace: false,
        isGatewayDismissed: false,
      }),
    ).toBe(false);
  });
});
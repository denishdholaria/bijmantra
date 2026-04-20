/**
 * Workspace Store (Zustand)
 * 
 * Manages workspace state for the Gateway-Workspace Architecture.
 * Persists user preferences to localStorage and syncs with backend.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { 
  WorkspaceId, 
  Workspace, 
  WorkspacePreferences 
} from '@/types/workspace';
import { 
  getWorkspace, 
  getAllWorkspaces,
  getWorkspaceModules,
  isRouteInWorkspace 
} from '@/framework/registry/workspaces';
import {
  buildDefaultWorkspacePreferences,
  buildWorkspaceSelectionPreferences,
  initialWorkspacePreferences,
  shouldShowWorkspaceGateway,
  updateRecentWorkspaces,
} from './workspaceStore.helpers';
import {
  loadWorkspacePreferencesFromBackend,
  persistDefaultWorkspacePreference,
  recordWorkspacePreferenceSwitch,
  syncWorkspacePreferencesToBackend,
} from './workspacePreferencesSync';

// ============================================================================
// Types
// ============================================================================

interface WorkspaceState {
  // Current state
  activeWorkspaceId: WorkspaceId | null;
  preferences: WorkspacePreferences;
  hasSelectedWorkspace: boolean;
  isGatewayDismissed: boolean;
  isSyncing: boolean;
  
  // Computed (derived from state)
  activeWorkspace: Workspace | null;
  
  // Actions
  setActiveWorkspace: (workspaceId: WorkspaceId) => void;
  setDefaultWorkspace: (workspaceId: WorkspaceId | null) => void;
  clearDefaultWorkspace: () => void;
  dismissGateway: () => void;
  resetGateway: () => void;
  addToRecentWorkspaces: (workspaceId: WorkspaceId) => void;
  /** @deprecated Use themeStore instead */
  setTheme: (theme: 'light' | 'dark') => void;
  syncWithBackend: () => Promise<void>;
  loadFromBackend: () => Promise<void>;
  
  // Queries
  isRouteAccessible: (route: string) => boolean;
  shouldShowGateway: () => boolean;
}

// ============================================================================
// Initial State
// ============================================================================

// ============================================================================
// Store
// ============================================================================

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      // Initial state
      activeWorkspaceId: null,
      preferences: initialWorkspacePreferences,
      hasSelectedWorkspace: false,
      isGatewayDismissed: false,
      isSyncing: false,
      
      // Computed
      get activeWorkspace() {
        const { activeWorkspaceId } = get();
        return activeWorkspaceId ? getWorkspace(activeWorkspaceId) ?? null : null;
      },

      // Actions
      setActiveWorkspace: (workspaceId: WorkspaceId) => {
        const workspace = getWorkspace(workspaceId);
        if (!workspace) {
          console.warn(`Workspace not found: ${workspaceId}`);
          return;
        }
        
        set((state) => ({
          activeWorkspaceId: workspaceId,
          hasSelectedWorkspace: true,
          isGatewayDismissed: true,
          preferences: buildWorkspaceSelectionPreferences(state.preferences, workspaceId),
        }));
        
        // Sync with backend (fire and forget)
        recordWorkspacePreferenceSwitch(workspaceId).catch(console.error);
      },
      
      setDefaultWorkspace: (workspaceId: WorkspaceId | null) => {
        set((state) => ({
          preferences: buildDefaultWorkspacePreferences(state.preferences, workspaceId),
        }));
        
        // Sync with backend
        persistDefaultWorkspacePreference(workspaceId).catch(console.error);
      },
      
      clearDefaultWorkspace: () => {
        set((state) => ({
          preferences: buildDefaultWorkspacePreferences(state.preferences, null),
        }));
        
        // Sync with backend
        persistDefaultWorkspacePreference(null).catch(console.error);
      },
      
      dismissGateway: () => {
        set({ isGatewayDismissed: true });
      },
      
      resetGateway: () => {
        set({ 
          isGatewayDismissed: false,
          hasSelectedWorkspace: false,
        });
      },
      
      addToRecentWorkspaces: (workspaceId: WorkspaceId) => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            recentWorkspaces: updateRecentWorkspaces(state.preferences.recentWorkspaces, workspaceId),
          },
        }));
      },

      /** @deprecated Use themeStore instead */
      setTheme: (_theme: 'light' | 'dark') => {
        // No-op: Theme is now managed by themeStore
        console.warn('workspaceStore.setTheme is deprecated. Use themeStore instead.');
      },
      
      // Sync local state to backend
      syncWithBackend: async () => {
        const { preferences, isSyncing } = get();
        if (isSyncing) return;
        
        set({ isSyncing: true });
        try {
          await syncWorkspacePreferencesToBackend(preferences);
        } catch (error) {
          console.error('Failed to sync workspace preferences:', error);
        } finally {
          set({ isSyncing: false });
        }
      },
      
      // Load preferences from backend
      loadFromBackend: async () => {
        const { isSyncing } = get();
        if (isSyncing) return;
        
        set({ isSyncing: true });
        try {
          const backendPreferences = await loadWorkspacePreferencesFromBackend(get().preferences);
          if (backendPreferences) {
            set((state) => ({
              preferences: backendPreferences,
              // If user has a default workspace and hasn't selected one this session, use it
              activeWorkspaceId: state.activeWorkspaceId || 
                backendPreferences.defaultWorkspace,
            }));
          }
        } catch (error) {
          console.error('Failed to load workspace preferences:', error);
        } finally {
          set({ isSyncing: false });
        }
      },
      
      // Queries
      isRouteAccessible: (route: string) => {
        const { activeWorkspaceId } = get();
        if (!activeWorkspaceId) return true; // No workspace = all routes accessible
        return isRouteInWorkspace(route, activeWorkspaceId);
      },
      
      shouldShowGateway: () => {
        const { preferences, hasSelectedWorkspace, isGatewayDismissed } = get();

        return shouldShowWorkspaceGateway({
          preferences,
          hasSelectedWorkspace,
          isGatewayDismissed,
        });
      },
    }),
    {
      name: 'bijmantra-workspace',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        activeWorkspaceId: state.activeWorkspaceId,
        preferences: state.preferences,
      }),
    }
  )
);

// ============================================================================
// Selectors (for performance optimization)
// ============================================================================

export const selectActiveWorkspace = (state: WorkspaceState) => 
  state.activeWorkspaceId ? getWorkspace(state.activeWorkspaceId) : null;

export const selectActiveWorkspaceId = (state: WorkspaceState) => 
  state.activeWorkspaceId;

export const selectPreferences = (state: WorkspaceState) => 
  state.preferences;

export const selectDefaultWorkspace = (state: WorkspaceState) => 
  state.preferences.defaultWorkspace;

export const selectRecentWorkspaces = (state: WorkspaceState) => 
  state.preferences.recentWorkspaces;

export const selectShouldShowGateway = (state: WorkspaceState) => 
  state.shouldShowGateway();

// ============================================================================
// Hooks (convenience wrappers)
// ============================================================================

/**
 * Hook to get the active workspace with all its data
 */
export function useActiveWorkspace(): Workspace | null {
  const activeWorkspaceId = useWorkspaceStore(selectActiveWorkspaceId);
  return activeWorkspaceId ? getWorkspace(activeWorkspaceId) ?? null : null;
}

/**
 * Hook to get workspace modules for the active workspace
 */
export function useActiveWorkspaceModules() {
  const activeWorkspaceId = useWorkspaceStore(selectActiveWorkspaceId);
  if (!activeWorkspaceId) return [];
  return getWorkspaceModules(activeWorkspaceId);
}

/**
 * Hook to check if a route is accessible in the current workspace
 */
export function useIsRouteAccessible(route: string): boolean {
  const isRouteAccessible = useWorkspaceStore((state) => state.isRouteAccessible);
  return isRouteAccessible(route);
}

/**
 * Hook to get all workspaces
 */
export function useAllWorkspaces(): Workspace[] {
  return getAllWorkspaces();
}

/**
 * Hook to check if gateway should be shown
 */
export function useShouldShowGateway(): boolean {
  return useWorkspaceStore(selectShouldShowGateway);
}

// ============================================================================
// Actions (for use outside React components)
// ============================================================================

export const workspaceActions = {
  setActiveWorkspace: (workspaceId: WorkspaceId) => 
    useWorkspaceStore.getState().setActiveWorkspace(workspaceId),
  
  setDefaultWorkspace: (workspaceId: WorkspaceId | null) => 
    useWorkspaceStore.getState().setDefaultWorkspace(workspaceId),
  
  clearDefaultWorkspace: () => 
    useWorkspaceStore.getState().clearDefaultWorkspace(),
  
  dismissGateway: () => 
    useWorkspaceStore.getState().dismissGateway(),
  
  resetGateway: () => 
    useWorkspaceStore.getState().resetGateway(),
  
  getActiveWorkspace: () => {
    const state = useWorkspaceStore.getState();
    return state.activeWorkspaceId ? getWorkspace(state.activeWorkspaceId) : null;
  },
  
  shouldShowGateway: () => 
    useWorkspaceStore.getState().shouldShowGateway(),
  
  syncWithBackend: () =>
    useWorkspaceStore.getState().syncWithBackend(),
  
  loadFromBackend: () =>
    useWorkspaceStore.getState().loadFromBackend(),
};

export default useWorkspaceStore;

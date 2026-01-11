/**
 * Workspace Store (Zustand)
 * 
 * Manages workspace state for the Gateway-Workspace Architecture.
 * Persists user preferences to localStorage and syncs with backend.
 * 
 * @see docs/gupt/archieve/GATEWAY-WORKSPACE.md for full specification
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
import { workspacePreferencesAPI } from '@/lib/api-client';

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
  setTheme: (theme: 'prakruti' | 'aerospace') => void;
  syncWithBackend: () => Promise<void>;
  loadFromBackend: () => Promise<void>;
  
  // Queries
  isRouteAccessible: (route: string) => boolean;
  shouldShowGateway: () => boolean;
}

// ============================================================================
// Initial State
// ============================================================================

const initialPreferences: WorkspacePreferences = {
  defaultWorkspace: null,
  recentWorkspaces: [],
  showGatewayOnLogin: true,
  lastWorkspace: null,
  lastChanged: null,
  theme: 'aerospace', // Default to Aerospace for testing
};

// ============================================================================
// Store
// ============================================================================

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      // Initial state
      activeWorkspaceId: null,
      preferences: initialPreferences,
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
          preferences: {
            ...state.preferences,
            lastWorkspace: workspaceId,
            lastChanged: new Date().toISOString(),
            recentWorkspaces: [
              workspaceId,
              ...state.preferences.recentWorkspaces.filter(w => w !== workspaceId),
            ].slice(0, 5), // Keep last 5
          },
        }));
        
        // Sync with backend (fire and forget)
        workspacePreferencesAPI.recordWorkspaceSwitch(workspaceId).catch(console.error);
      },
      
      setDefaultWorkspace: (workspaceId: WorkspaceId | null) => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            defaultWorkspace: workspaceId,
            showGatewayOnLogin: workspaceId === null,
          },
        }));
        
        // Sync with backend
        if (workspaceId) {
          workspacePreferencesAPI.setDefaultWorkspace(workspaceId).catch(console.error);
        } else {
          workspacePreferencesAPI.clearDefaultWorkspace().catch(console.error);
        }
      },
      
      clearDefaultWorkspace: () => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            defaultWorkspace: null,
            showGatewayOnLogin: true,
          },
        }));
        
        // Sync with backend
        workspacePreferencesAPI.clearDefaultWorkspace().catch(console.error);
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
            recentWorkspaces: [
              workspaceId,
              ...state.preferences.recentWorkspaces.filter(w => w !== workspaceId),
            ].slice(0, 5),
          },
        }));
      },

      setTheme: (theme: 'prakruti' | 'aerospace') => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            theme,
          },
        }));
      },
      
      // Sync local state to backend
      syncWithBackend: async () => {
        const { preferences, isSyncing } = get();
        if (isSyncing) return;
        
        set({ isSyncing: true });
        try {
          await workspacePreferencesAPI.updatePreferences({
            default_workspace: preferences.defaultWorkspace,
            recent_workspaces: preferences.recentWorkspaces,
            show_gateway_on_login: preferences.showGatewayOnLogin,
            last_workspace: preferences.lastWorkspace,
          });
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
          const response = await workspacePreferencesAPI.getPreferences();
          if (response.status === 'success' && response.data) {
            const backendPrefs = response.data;
            set((state) => ({
              preferences: {
                ...state.preferences,
                defaultWorkspace: backendPrefs.default_workspace as WorkspaceId | null,
                recentWorkspaces: (backendPrefs.recent_workspaces || []) as WorkspaceId[],
                showGatewayOnLogin: backendPrefs.show_gateway_on_login ?? true,
                lastWorkspace: backendPrefs.last_workspace as WorkspaceId | null,
              },
              // If user has a default workspace and hasn't selected one this session, use it
              activeWorkspaceId: state.activeWorkspaceId || 
                (backendPrefs.default_workspace as WorkspaceId | null),
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
        
        // Don't show if already dismissed this session
        if (isGatewayDismissed) return false;
        
        // Don't show if user has already selected a workspace this session
        if (hasSelectedWorkspace) return false;
        
        // Show if user wants to see gateway on login
        if (preferences.showGatewayOnLogin) return true;
        
        // Don't show if user has a default workspace
        if (preferences.defaultWorkspace) return false;
        
        return true;
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

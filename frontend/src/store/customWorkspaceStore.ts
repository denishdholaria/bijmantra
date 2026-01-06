/**
 * Custom Workspace Store (Zustand)
 * 
 * Manages user-defined custom workspaces with LocalStorage persistence.
 * Custom workspaces allow users to create personalized navigation
 * by selecting pages they use frequently.
 * 
 * @see docs/confidential/archieve/MyWorkspace.md for full specification
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { CustomWorkspace, WorkspaceColor } from '@/types/customWorkspace';
import { CUSTOM_WORKSPACE_LIMITS } from '@/types/customWorkspace';

// ============================================================================
// Types
// ============================================================================

interface CustomWorkspaceState {
  // Data
  customWorkspaces: CustomWorkspace[];
  activeCustomWorkspaceId: string | null;
  
  // Actions
  createWorkspace: (workspace: Omit<CustomWorkspace, 'id' | 'createdAt' | 'updatedAt'>) => string | null;
  updateWorkspace: (id: string, updates: Partial<Omit<CustomWorkspace, 'id' | 'createdAt'>>) => boolean;
  deleteWorkspace: (id: string) => boolean;
  duplicateWorkspace: (id: string) => string | null;
  setActiveCustomWorkspace: (id: string | null) => void;
  clearActiveCustomWorkspace: () => void;
  
  // Page management
  addPageToWorkspace: (workspaceId: string, pageId: string) => boolean;
  removePageFromWorkspace: (workspaceId: string, pageId: string) => boolean;
  setPagesForWorkspace: (workspaceId: string, pageIds: string[]) => boolean;
  reorderPages: (workspaceId: string, pageIds: string[]) => boolean;
  
  // Queries
  getWorkspace: (id: string) => CustomWorkspace | undefined;
  getActiveCustomWorkspace: () => CustomWorkspace | null;
  isPageInActiveWorkspace: (pageId: string) => boolean;
  canCreateWorkspace: () => boolean;
  canAddPageToWorkspace: (workspaceId: string) => boolean;
}

// ============================================================================
// Helpers
// ============================================================================

function generateId(): string {
  return `cw_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 9)}`;
}

function now(): string {
  return new Date().toISOString();
}

// ============================================================================
// Store
// ============================================================================

export const useCustomWorkspaceStore = create<CustomWorkspaceState>()(
  persist(
    (set, get) => ({
      // Initial state
      customWorkspaces: [],
      activeCustomWorkspaceId: null,

      // Create a new custom workspace
      createWorkspace: (workspace) => {
        const { customWorkspaces } = get();
        
        // Check limits
        if (customWorkspaces.length >= CUSTOM_WORKSPACE_LIMITS.maxWorkspaces) {
          console.warn(`Cannot create workspace: max ${CUSTOM_WORKSPACE_LIMITS.maxWorkspaces} workspaces allowed`);
          return null;
        }
        
        if (workspace.pageIds.length > CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace) {
          console.warn(`Cannot create workspace: max ${CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace} pages allowed`);
          return null;
        }
        
        if (workspace.pageIds.length < CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace) {
          console.warn(`Cannot create workspace: min ${CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace} page required`);
          return null;
        }
        
        const id = generateId();
        const timestamp = now();
        
        const newWorkspace: CustomWorkspace = {
          ...workspace,
          id,
          createdAt: timestamp,
          updatedAt: timestamp,
        };
        
        set((state) => ({
          customWorkspaces: [...state.customWorkspaces, newWorkspace],
        }));
        
        return id;
      },

      // Update an existing workspace
      updateWorkspace: (id, updates) => {
        const { customWorkspaces } = get();
        const index = customWorkspaces.findIndex(w => w.id === id);
        
        if (index === -1) {
          console.warn(`Workspace not found: ${id}`);
          return false;
        }
        
        // Validate page count if updating pages
        if (updates.pageIds) {
          if (updates.pageIds.length > CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace) {
            console.warn(`Cannot update workspace: max ${CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace} pages allowed`);
            return false;
          }
          if (updates.pageIds.length < CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace) {
            console.warn(`Cannot update workspace: min ${CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace} page required`);
            return false;
          }
        }
        
        set((state) => ({
          customWorkspaces: state.customWorkspaces.map(w =>
            w.id === id
              ? { ...w, ...updates, updatedAt: now() }
              : w
          ),
        }));
        
        return true;
      },

      // Delete a workspace
      deleteWorkspace: (id) => {
        const { customWorkspaces, activeCustomWorkspaceId } = get();
        
        if (!customWorkspaces.some(w => w.id === id)) {
          console.warn(`Workspace not found: ${id}`);
          return false;
        }
        
        set((state) => ({
          customWorkspaces: state.customWorkspaces.filter(w => w.id !== id),
          // Clear active if deleting the active workspace
          activeCustomWorkspaceId: state.activeCustomWorkspaceId === id 
            ? null 
            : state.activeCustomWorkspaceId,
        }));
        
        return true;
      },

      // Duplicate a workspace
      duplicateWorkspace: (id) => {
        const { customWorkspaces } = get();
        const source = customWorkspaces.find(w => w.id === id);
        
        if (!source) {
          console.warn(`Workspace not found: ${id}`);
          return null;
        }
        
        if (customWorkspaces.length >= CUSTOM_WORKSPACE_LIMITS.maxWorkspaces) {
          console.warn(`Cannot duplicate: max ${CUSTOM_WORKSPACE_LIMITS.maxWorkspaces} workspaces allowed`);
          return null;
        }
        
        const newId = generateId();
        const timestamp = now();
        
        const duplicate: CustomWorkspace = {
          ...source,
          id: newId,
          name: `${source.name} (Copy)`,
          templateId: undefined, // Clear template reference
          createdAt: timestamp,
          updatedAt: timestamp,
        };
        
        set((state) => ({
          customWorkspaces: [...state.customWorkspaces, duplicate],
        }));
        
        return newId;
      },

      // Set active custom workspace
      setActiveCustomWorkspace: (id) => {
        if (id !== null) {
          const { customWorkspaces } = get();
          if (!customWorkspaces.some(w => w.id === id)) {
            console.warn(`Workspace not found: ${id}`);
            return;
          }
        }
        
        set({ activeCustomWorkspaceId: id });
      },

      // Clear active custom workspace
      clearActiveCustomWorkspace: () => {
        set({ activeCustomWorkspaceId: null });
      },

      // Add a page to a workspace
      addPageToWorkspace: (workspaceId, pageId) => {
        const { customWorkspaces } = get();
        const workspace = customWorkspaces.find(w => w.id === workspaceId);
        
        if (!workspace) {
          console.warn(`Workspace not found: ${workspaceId}`);
          return false;
        }
        
        if (workspace.pageIds.includes(pageId)) {
          return true; // Already exists
        }
        
        if (workspace.pageIds.length >= CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace) {
          console.warn(`Cannot add page: max ${CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace} pages allowed`);
          return false;
        }
        
        set((state) => ({
          customWorkspaces: state.customWorkspaces.map(w =>
            w.id === workspaceId
              ? { ...w, pageIds: [...w.pageIds, pageId], updatedAt: now() }
              : w
          ),
        }));
        
        return true;
      },

      // Remove a page from a workspace
      removePageFromWorkspace: (workspaceId, pageId) => {
        const { customWorkspaces } = get();
        const workspace = customWorkspaces.find(w => w.id === workspaceId);
        
        if (!workspace) {
          console.warn(`Workspace not found: ${workspaceId}`);
          return false;
        }
        
        if (workspace.pageIds.length <= CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace) {
          console.warn(`Cannot remove page: min ${CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace} page required`);
          return false;
        }
        
        set((state) => ({
          customWorkspaces: state.customWorkspaces.map(w =>
            w.id === workspaceId
              ? { ...w, pageIds: w.pageIds.filter(p => p !== pageId), updatedAt: now() }
              : w
          ),
        }));
        
        return true;
      },

      // Set all pages for a workspace
      setPagesForWorkspace: (workspaceId, pageIds) => {
        const { customWorkspaces } = get();
        
        if (!customWorkspaces.some(w => w.id === workspaceId)) {
          console.warn(`Workspace not found: ${workspaceId}`);
          return false;
        }
        
        if (pageIds.length > CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace) {
          console.warn(`Cannot set pages: max ${CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace} pages allowed`);
          return false;
        }
        
        if (pageIds.length < CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace) {
          console.warn(`Cannot set pages: min ${CUSTOM_WORKSPACE_LIMITS.minPagesPerWorkspace} page required`);
          return false;
        }
        
        // Remove duplicates
        const uniquePageIds = [...new Set(pageIds)];
        
        set((state) => ({
          customWorkspaces: state.customWorkspaces.map(w =>
            w.id === workspaceId
              ? { ...w, pageIds: uniquePageIds, updatedAt: now() }
              : w
          ),
        }));
        
        return true;
      },

      // Reorder pages in a workspace
      reorderPages: (workspaceId, pageIds) => {
        const { customWorkspaces } = get();
        const workspace = customWorkspaces.find(w => w.id === workspaceId);
        
        if (!workspace) {
          console.warn(`Workspace not found: ${workspaceId}`);
          return false;
        }
        
        // Verify all pages exist in the workspace
        const existingPages = new Set(workspace.pageIds);
        const newPages = new Set(pageIds);
        
        if (existingPages.size !== newPages.size) {
          console.warn('Page count mismatch during reorder');
          return false;
        }
        
        for (const pageId of pageIds) {
          if (!existingPages.has(pageId)) {
            console.warn(`Page not in workspace: ${pageId}`);
            return false;
          }
        }
        
        set((state) => ({
          customWorkspaces: state.customWorkspaces.map(w =>
            w.id === workspaceId
              ? { ...w, pageIds, updatedAt: now() }
              : w
          ),
        }));
        
        return true;
      },

      // Get a workspace by ID
      getWorkspace: (id) => {
        return get().customWorkspaces.find(w => w.id === id);
      },

      // Get the active custom workspace
      getActiveCustomWorkspace: () => {
        const { customWorkspaces, activeCustomWorkspaceId } = get();
        if (!activeCustomWorkspaceId) return null;
        return customWorkspaces.find(w => w.id === activeCustomWorkspaceId) ?? null;
      },

      // Check if a page is in the active custom workspace
      isPageInActiveWorkspace: (pageId) => {
        const activeWorkspace = get().getActiveCustomWorkspace();
        if (!activeWorkspace) return true; // No filter when no custom workspace active
        return activeWorkspace.pageIds.includes(pageId);
      },

      // Check if user can create more workspaces
      canCreateWorkspace: () => {
        return get().customWorkspaces.length < CUSTOM_WORKSPACE_LIMITS.maxWorkspaces;
      },

      // Check if user can add more pages to a workspace
      canAddPageToWorkspace: (workspaceId) => {
        const workspace = get().customWorkspaces.find(w => w.id === workspaceId);
        if (!workspace) return false;
        return workspace.pageIds.length < CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace;
      },
    }),
    {
      name: 'bijmantra-custom-workspaces',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        customWorkspaces: state.customWorkspaces,
        activeCustomWorkspaceId: state.activeCustomWorkspaceId,
      }),
    }
  )
);

// ============================================================================
// Selectors
// ============================================================================

export const selectCustomWorkspaces = (state: CustomWorkspaceState) => 
  state.customWorkspaces;

export const selectActiveCustomWorkspaceId = (state: CustomWorkspaceState) => 
  state.activeCustomWorkspaceId;

export const selectActiveCustomWorkspace = (state: CustomWorkspaceState) => 
  state.getActiveCustomWorkspace();

export const selectCanCreateWorkspace = (state: CustomWorkspaceState) => 
  state.canCreateWorkspace();

// ============================================================================
// Hooks
// ============================================================================

/**
 * Hook to get all custom workspaces
 */
export function useCustomWorkspaces(): CustomWorkspace[] {
  return useCustomWorkspaceStore(selectCustomWorkspaces);
}

/**
 * Hook to get the active custom workspace
 */
export function useActiveCustomWorkspace(): CustomWorkspace | null {
  return useCustomWorkspaceStore((state) => state.getActiveCustomWorkspace());
}

/**
 * Hook to check if a custom workspace is active
 */
export function useIsCustomWorkspaceActive(): boolean {
  return useCustomWorkspaceStore((state) => state.activeCustomWorkspaceId !== null);
}

/**
 * Hook to check if user can create more workspaces
 */
export function useCanCreateWorkspace(): boolean {
  return useCustomWorkspaceStore(selectCanCreateWorkspace);
}

// ============================================================================
// Actions (for use outside React components)
// ============================================================================

export const customWorkspaceActions = {
  create: (workspace: Omit<CustomWorkspace, 'id' | 'createdAt' | 'updatedAt'>) =>
    useCustomWorkspaceStore.getState().createWorkspace(workspace),
  
  update: (id: string, updates: Partial<Omit<CustomWorkspace, 'id' | 'createdAt'>>) =>
    useCustomWorkspaceStore.getState().updateWorkspace(id, updates),
  
  delete: (id: string) =>
    useCustomWorkspaceStore.getState().deleteWorkspace(id),
  
  duplicate: (id: string) =>
    useCustomWorkspaceStore.getState().duplicateWorkspace(id),
  
  setActive: (id: string | null) =>
    useCustomWorkspaceStore.getState().setActiveCustomWorkspace(id),
  
  clearActive: () =>
    useCustomWorkspaceStore.getState().clearActiveCustomWorkspace(),
  
  addPage: (workspaceId: string, pageId: string) =>
    useCustomWorkspaceStore.getState().addPageToWorkspace(workspaceId, pageId),
  
  removePage: (workspaceId: string, pageId: string) =>
    useCustomWorkspaceStore.getState().removePageFromWorkspace(workspaceId, pageId),
  
  setPages: (workspaceId: string, pageIds: string[]) =>
    useCustomWorkspaceStore.getState().setPagesForWorkspace(workspaceId, pageIds),
  
  getAll: () =>
    useCustomWorkspaceStore.getState().customWorkspaces,
  
  get: (id: string) =>
    useCustomWorkspaceStore.getState().getWorkspace(id),
  
  getActive: () =>
    useCustomWorkspaceStore.getState().getActiveCustomWorkspace(),
};

export default useCustomWorkspaceStore;

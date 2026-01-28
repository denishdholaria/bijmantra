/**
 * Custom Workspace Hooks
 * 
 * Helper hooks for working with custom workspaces.
 * Provides convenient access to workspace data and actions.
 */

import { useMemo } from 'react';
import { useCustomWorkspaceStore } from '@/store/customWorkspaceStore';
import { workspaceModules } from '@/framework/registry/workspaces';
import type { CustomWorkspace, SelectablePage, PageModule } from '@/types/customWorkspace';

/**
 * Get all selectable pages grouped by module
 * Excludes global pages (always accessible)
 */
export function useSelectablePages(): PageModule[] {
  return useMemo(() => {
    return workspaceModules
      .filter(module => module.id !== 'global') // Exclude global pages
      .map(module => ({
        id: module.id,
        name: module.name,
        icon: module.icon,
        pages: module.pages.map(page => ({
          id: page.id,
          name: page.name,
          route: page.route,
          moduleId: module.id,
          moduleName: module.name,
        })),
      }));
  }, []);
}

/**
 * Get a flat list of all selectable pages
 */
export function useAllSelectablePages(): SelectablePage[] {
  const modules = useSelectablePages();
  return useMemo(() => {
    return modules.flatMap(module => module.pages);
  }, [modules]);
}

/**
 * Get page details by ID
 */
export function usePageById(pageId: string): SelectablePage | undefined {
  const allPages = useAllSelectablePages();
  return useMemo(() => {
    return allPages.find(p => p.id === pageId);
  }, [allPages, pageId]);
}

/**
 * Get pages for a custom workspace, grouped by module
 */
export function useWorkspacePages(workspaceId: string): PageModule[] {
  const workspace = useCustomWorkspaceStore(state => state.getWorkspace(workspaceId));
  const allModules = useSelectablePages();
  
  return useMemo(() => {
    if (!workspace) return [];
    
    const pageIdSet = new Set(workspace.pageIds);
    
    return allModules
      .map(module => ({
        ...module,
        pages: module.pages.filter(page => pageIdSet.has(page.id)),
      }))
      .filter(module => module.pages.length > 0);
  }, [workspace, allModules]);
}

/**
 * Get pages for the active custom workspace, grouped by module
 */
export function useActiveWorkspacePages(): PageModule[] {
  const activeWorkspace = useCustomWorkspaceStore(state => state.getActiveCustomWorkspace());
  const allModules = useSelectablePages();
  
  return useMemo(() => {
    if (!activeWorkspace) return [];
    
    const pageIdSet = new Set(activeWorkspace.pageIds);
    
    return allModules
      .map(module => ({
        ...module,
        pages: module.pages.filter(page => pageIdSet.has(page.id)),
      }))
      .filter(module => module.pages.length > 0);
  }, [activeWorkspace, allModules]);
}

/**
 * Check if a page is in a specific workspace
 */
export function useIsPageInWorkspace(workspaceId: string, pageId: string): boolean {
  const workspace = useCustomWorkspaceStore(state => state.getWorkspace(workspaceId));
  return workspace?.pageIds.includes(pageId) ?? false;
}

/**
 * Check if a page is in the active custom workspace
 */
export function useIsPageInActiveWorkspace(pageId: string): boolean {
  return useCustomWorkspaceStore(state => state.isPageInActiveWorkspace(pageId));
}

/**
 * Get workspace statistics
 */
export function useWorkspaceStats(workspaceId: string): {
  pageCount: number;
  moduleCount: number;
  modules: string[];
} {
  const workspacePages = useWorkspacePages(workspaceId);
  
  return useMemo(() => ({
    pageCount: workspacePages.reduce((sum, m) => sum + m.pages.length, 0),
    moduleCount: workspacePages.length,
    modules: workspacePages.map(m => m.name),
  }), [workspacePages]);
}

/**
 * Search pages by name
 */
export function useSearchPages(query: string): SelectablePage[] {
  const allPages = useAllSelectablePages();
  
  return useMemo(() => {
    if (!query.trim()) return allPages;
    
    const lowerQuery = query.toLowerCase();
    return allPages.filter(page => 
      page.name.toLowerCase().includes(lowerQuery) ||
      page.moduleName.toLowerCase().includes(lowerQuery)
    );
  }, [allPages, query]);
}

/**
 * Get module icon by ID
 */
export function useModuleIcon(moduleId: string): string {
  return useMemo(() => {
    const module = workspaceModules.find(m => m.id === moduleId);
    return module?.icon ?? 'File';
  }, [moduleId]);
}

/**
 * Hook for workspace CRUD operations with loading states
 */
export function useWorkspaceActions() {
  const store = useCustomWorkspaceStore();
  
  return {
    create: store.createWorkspace,
    update: store.updateWorkspace,
    delete: store.deleteWorkspace,
    duplicate: store.duplicateWorkspace,
    setActive: store.setActiveCustomWorkspace,
    clearActive: store.clearActiveCustomWorkspace,
    addPage: store.addPageToWorkspace,
    removePage: store.removePageFromWorkspace,
    setPages: store.setPagesForWorkspace,
    reorderPages: store.reorderPages,
  };
}

/**
 * Check if route is accessible in active custom workspace
 */
export function useIsRouteAccessibleInCustomWorkspace(route: string): boolean {
  const activeWorkspace = useCustomWorkspaceStore(state => state.getActiveCustomWorkspace());
  const allPages = useAllSelectablePages();
  
  return useMemo(() => {
    // No custom workspace active = all routes accessible
    if (!activeWorkspace) return true;
    
    // Find page by route
    const page = allPages.find(p => 
      p.route === route || 
      route.startsWith(p.route.replace(':id', ''))
    );
    
    // If page not found in selectable pages, it's a global page (always accessible)
    if (!page) return true;
    
    // Check if page is in the active workspace
    return activeWorkspace.pageIds.includes(page.id);
  }, [activeWorkspace, allPages, route]);
}

/**
 * Get the count of pages selected from each module
 */
export function useModuleSelectionCounts(selectedPageIds: string[]): Record<string, number> {
  const allModules = useSelectablePages();
  
  return useMemo(() => {
    const counts: Record<string, number> = {};
    const selectedSet = new Set(selectedPageIds);
    
    for (const module of allModules) {
      counts[module.id] = module.pages.filter(p => selectedSet.has(p.id)).length;
    }
    
    return counts;
  }, [allModules, selectedPageIds]);
}

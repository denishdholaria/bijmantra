/**
 * Navigation-Derived Surfaces
 * 
 * This module generates all navigation surfaces from the single source of truth
 * in navigation-source.ts. This eliminates duplication across routes, sidebars,
 * command palettes, and breadcrumbs.
 * 
 * Design Principles:
 * - Navigation truth derives from a single source
 * - Routes compose domain behavior, they don't own it
 * - Registries declare metadata, they don't accumulate logic
 */

import type { RouteObject } from 'react-router-dom';
import type { NavigationNode } from './navigation-source';
import { navigationTree } from './navigation-source';

// ============================================================================
// Types for Derived Surfaces
// ============================================================================

/**
 * Sidebar menu item structure
 */
export interface SidebarMenuItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  description?: string;
  parentPath?: string;
  divisionId?: string;
  children?: SidebarMenuItem[];
}

/**
 * Command palette item structure
 */
export interface CommandPaletteItem {
  id: string;
  title: string;
  subtitle?: string;
  route: string;
  icon?: string;
  keywords?: string[];
  divisionId?: string;
}

/**
 * Breadcrumb item structure
 */
export interface BreadcrumbItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
}

/**
 * Route metadata structure for generated routes
 */
export interface GeneratedRouteMetadata {
  id: string;
  path: string;
  label: string;
  divisionId?: string;
  requiredPermissions?: string[];
}

// ============================================================================
// 1. generateRoutesFromNavigation()
// ============================================================================

/**
 * Generates route configuration from the navigation tree.
 * 
 * This produces an array of route paths with metadata that can be used
 * to dynamically construct routes. The actual route components are loaded
 * separately by the route configuration.
 * 
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @returns Array of route metadata objects
 * 
 * @example
 * const routes = generateRoutesFromNavigation();
 * // Returns: [{ id: 'plant-sciences', path: '/programs', label: 'Plant Sciences', ... }, ...]
 */
export function generateRoutesFromNavigation(
  tree: NavigationNode[] = navigationTree
): GeneratedRouteMetadata[] {
  const routes: GeneratedRouteMetadata[] = [];

  function traverse(nodes: NavigationNode[]) {
    for (const node of nodes) {
      // Skip hidden nodes
      if (node.isHidden) continue;

      // Add this node as a route
      routes.push({
        id: node.id,
        path: node.path,
        label: node.label,
        divisionId: node.divisionId,
        requiredPermissions: node.requiredPermissions,
      });

      // Recursively process children
      if (node.children && node.children.length > 0) {
        traverse(node.children);
      }
    }
  }

  traverse(tree);
  return routes;
}

// ============================================================================
// 2. generateSidebarFromNavigation()
// ============================================================================

/**
 * Generates sidebar menu structure from the navigation tree.
 * 
 * This produces a hierarchical menu structure suitable for rendering
 * in the ShellSidebar component. The structure preserves the parent-child
 * relationships from the navigation tree.
 * 
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @param options - Optional filtering options
 * @returns Array of sidebar menu items
 * 
 * @example
 * const sidebar = generateSidebarFromNavigation();
 * // Returns: [{ id: 'plant-sciences', label: 'Plant Sciences', children: [...] }, ...]
 */
export function generateSidebarFromNavigation(
  tree: NavigationNode[] = navigationTree,
  options?: {
    divisionId?: string;
    includeHidden?: boolean;
    maxDepth?: number;
  }
): SidebarMenuItem[] {
  const { divisionId, includeHidden = false, maxDepth = 3 } = options || {};

  function transform(nodes: NavigationNode[], depth: number): SidebarMenuItem[] {
    if (depth > maxDepth) return [];

    return nodes
      .filter(node => {
        // Filter hidden nodes unless explicitly included
        if (!includeHidden && node.isHidden) return false;
        // Filter by division if specified
        if (divisionId && node.divisionId !== divisionId) return false;
        return true;
      })
      .map(node => ({
        id: node.id,
        label: node.label,
        path: node.path,
        icon: node.icon,
        description: node.description,
        parentPath: node.parentPath,
        divisionId: node.divisionId,
        children: node.children ? transform(node.children, depth + 1) : undefined,
      }));
  }

  return transform(tree, 1);
}

/**
 * Generates sidebar menu for a specific division.
 * This is useful when the sidebar should show only the active division's content.
 * 
 * @param divisionId - The division ID to filter by
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @returns Sidebar menu items for the specified division
 */
export function generateSidebarForDivision(
  divisionId: string,
  tree: NavigationNode[] = navigationTree
): SidebarMenuItem[] {
  // Find the division node
  const divisionNode = tree.find(node => node.id === divisionId || node.divisionId === divisionId);
  
  if (!divisionNode) {
    return [];
  }

  // Return the division's children as sidebar items
  return divisionNode.children?.map(node => ({
    id: node.id,
    label: node.label,
    path: node.path,
    icon: node.icon,
    description: node.description,
    parentPath: node.parentPath,
    divisionId: node.divisionId,
    children: node.children,
  })) || [];
}

// ============================================================================
// 3. generateCommandsFromNavigation()
// ============================================================================

/**
 * Generates command palette items from the navigation tree.
 * 
 * This produces a flat list of navigable items suitable for the command palette.
 * Each item includes keywords for fuzzy search. Hidden items are excluded.
 * 
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @returns Array of command palette items
 * 
 * @example
 * const commands = generateCommandsFromNavigation();
 * // Returns: [{ id: 'ld-analysis', title: 'LD Analysis', route: '/linkage-disequilibrium', ... }, ...]
 */
export function generateCommandsFromNavigation(
  tree: NavigationNode[] = navigationTree
): CommandPaletteItem[] {
  const commands: CommandPaletteItem[] = [];

  function traverse(nodes: NavigationNode[], parentLabel?: string) {
    for (const node of nodes) {
      // Skip hidden nodes
      if (node.isHidden) continue;

      // Build subtitle from parent context
      const subtitle = parentLabel 
        ? `${parentLabel} → ${node.label}`
        : node.description || node.divisionId;

      // Build keywords for search
      const keywords: string[] = [
        node.label,
        ...(node.keywords || []),
        ...(parentLabel ? [parentLabel] : []),
        ...(node.divisionId ? [node.divisionId] : []),
      ];

      // Add this node as a command
      commands.push({
        id: node.id,
        title: node.label,
        subtitle,
        route: node.path,
        icon: node.icon,
        keywords,
        divisionId: node.divisionId,
      });

      // Recursively process children
      if (node.children && node.children.length > 0) {
        traverse(node.children, node.label);
      }
    }
  }

  traverse(tree);
  return commands;
}

/**
 * Generates command palette items filtered by search query.
 * 
 * @param query - Search query string
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @returns Filtered array of command palette items
 */
export function searchCommands(
  query: string,
  tree: NavigationNode[] = navigationTree
): CommandPaletteItem[] {
  const allCommands = generateCommandsFromNavigation(tree);
  const normalizedQuery = query.toLowerCase().trim();

  if (!normalizedQuery) {
    return allCommands;
  }

  return allCommands.filter(command => {
    const searchableText = [
      command.title,
      command.subtitle,
      ...(command.keywords || []),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();

    return searchableText.includes(normalizedQuery);
  });
}

// ============================================================================
// 4. generateBreadcrumbsFromNavigation()
// ============================================================================

/**
 * Generates breadcrumb trail for a given path from the navigation tree.
 * 
 * This traverses the navigation tree to find the path and builds a breadcrumb
 * trail from root to the target node.
 * 
 * @param targetPath - The path to generate breadcrumbs for
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @returns Array of breadcrumb items from root to target, or empty array if not found
 * 
 * @example
 * const breadcrumbs = generateBreadcrumbsFromNavigation('/linkage-disequilibrium');
 * // Returns: [
 * //   { id: 'plant-sciences', label: 'Plant Sciences', path: '/programs' },
 * //   { id: 'genomics', label: 'Genomics', path: '/genetic-diversity' },
 * //   { id: 'linkage-disequilibrium', label: 'LD Analysis', path: '/linkage-disequilibrium' }
 * // ]
 */
export function generateBreadcrumbsFromNavigation(
  targetPath: string,
  tree: NavigationNode[] = navigationTree
): BreadcrumbItem[] {
  // Normalize the target path
  const normalizedTarget = targetPath.replace(/\/$/, '') || '/';

  function findPath(
    nodes: NavigationNode[],
    target: string,
    currentPath: BreadcrumbItem[]
  ): BreadcrumbItem[] | null {
    for (const node of nodes) {
      const nodePath = node.path.replace(/\/$/, '') || '/';

      // Add this node to the current path
      const newPath = [
        ...currentPath,
        {
          id: node.id,
          label: node.label,
          path: node.path,
          icon: node.icon,
        },
      ];

      // Check if this is the target
      if (nodePath === target) {
        return newPath;
      }

      // Recursively search children
      if (node.children && node.children.length > 0) {
        const result = findPath(node.children, target, newPath);
        if (result) {
          return result;
        }
      }
    }

    return null;
  }

  const result = findPath(tree, normalizedTarget, []);
  return result || [];
}

/**
 * Generates breadcrumbs with the division as the root.
 * This is useful for showing division-relative navigation.
 * 
 * @param targetPath - The path to generate breadcrumbs for
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @returns Breadcrumb items starting from the division root
 */
export function generateDivisionBreadcrumbs(
  targetPath: string,
  tree: NavigationNode[] = navigationTree
): BreadcrumbItem[] {
  const fullBreadcrumbs = generateBreadcrumbsFromNavigation(targetPath, tree);

  // If we have breadcrumbs and the first one is a division, return as-is
  if (fullBreadcrumbs.length > 0) {
    return fullBreadcrumbs;
  }

  return [];
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Finds a navigation node by path.
 * 
 * @param path - The path to search for
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @returns The navigation node if found, or undefined
 */
export function findNavigationNodeByPath(
  path: string,
  tree: NavigationNode[] = navigationTree
): NavigationNode | undefined {
  const normalizedPath = path.replace(/\/$/, '') || '/';

  function search(nodes: NavigationNode[]): NavigationNode | undefined {
    for (const node of nodes) {
      const nodePath = node.path.replace(/\/$/, '') || '/';

      if (nodePath === normalizedPath) {
        return node;
      }

      if (node.children) {
        const found = search(node.children);
        if (found) return found;
      }
    }
    return undefined;
  }

  return search(tree);
}

/**
 * Finds a navigation node by ID.
 * 
 * @param id - The ID to search for
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @returns The navigation node if found, or undefined
 */
export function findNavigationNodeById(
  id: string,
  tree: NavigationNode[] = navigationTree
): NavigationNode | undefined {
  function search(nodes: NavigationNode[]): NavigationNode | undefined {
    for (const node of nodes) {
      if (node.id === id) {
        return node;
      }

      if (node.children) {
        const found = search(node.children);
        if (found) return found;
      }
    }
    return undefined;
  }

  return search(tree);
}

/**
 * Gets all navigation paths as a flat array.
 * Useful for route validation and sitemap generation.
 * 
 * Note: This function returns unique paths only. Some sections may share
 * paths with their parent division (e.g., dashboard/overview pages), which
 * is an intentional design pattern. Duplicates are filtered out.
 * 
 * @param tree - The navigation tree (defaults to the canonical navigationTree)
 * @param includeHidden - Whether to include hidden nodes (default: false)
 * @returns Array of unique paths in the navigation tree
 */
export function getAllNavigationPaths(
  tree: NavigationNode[] = navigationTree,
  includeHidden = false
): string[] {
  const pathSet = new Set<string>();

  function collect(nodes: NavigationNode[]) {
    for (const node of nodes) {
      if (includeHidden || !node.isHidden) {
        pathSet.add(node.path);
      }
      if (node.children) {
        collect(node.children);
      }
    }
  }

  collect(tree);
  return Array.from(pathSet);
}

// ============================================================================
// Pre-generated exports for convenience
// ============================================================================

/**
 * Pre-generated route metadata from the navigation tree.
 * Use this instead of calling generateRoutesFromNavigation() directly.
 */
export const derivedRoutes = generateRoutesFromNavigation();

/**
 * Pre-generated sidebar menu from the navigation tree.
 * Use this instead of calling generateSidebarFromNavigation() directly.
 */
export const derivedSidebar = generateSidebarFromNavigation();

/**
 * Pre-generated command palette items from the navigation tree.
 * Use this instead of calling generateCommandsFromNavigation() directly.
 */
export const derivedCommands = generateCommandsFromNavigation();

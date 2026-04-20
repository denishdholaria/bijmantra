import type { LucideIcon } from 'lucide-react';
import type { Division, DivisionSection, DivisionNavItem } from './types';
import { divisions } from './divisions';

/**
 * Universal Navigation Node.
 * Used as the single source of truth for generating routes, sidebars, command palettes, and breadcrumbs.
 */
export interface NavigationNode {
  id: string;
  label: string;
  path: string;
  icon?: string;
  description?: string;
  keywords?: string[];

  // Authorization & visibility
  requiredPermissions?: string[];
  isHidden?: boolean;

  // Hierarchy
  parentPath?: string;
  children?: NavigationNode[];

  // Integration
  divisionId?: string; // Links back to domain ownership
}

/**
 * Constructs the universal navigation tree from the canonical `divisions.ts` registry.
 * This resolves the duplication between `routes/`, `CommandPalette`, and `ShellSidebar`.
 */
export function buildNavigationTree(): NavigationNode[] {
  return divisions.map(div => {
    const divNode: NavigationNode = {
      id: div.id,
      label: div.name,
      path: div.route,
      icon: div.icon,
      description: div.description,
      requiredPermissions: div.requiredPermissions,
      divisionId: div.id,
      children: []
    };

    if (div.sections) {
      divNode.children = div.sections.map(sec => {
        const secPath = sec.isAbsolute ? sec.route : `${div.route}${sec.route}`;
        const secNode: NavigationNode = {
          id: sec.id,
          label: sec.name,
          path: secPath,
          icon: sec.icon,
          description: sec.description,
          parentPath: div.route,
          divisionId: div.id,
          children: []
        };

        if (sec.items) {
          secNode.children = sec.items.map(item => {
            const itemPath = item.isAbsolute ? item.route : `${div.route}${item.route}`;
            return {
              id: item.id,
              label: item.name,
              path: itemPath,
              icon: item.icon,
              parentPath: secPath,
              divisionId: div.id
            };
          });
        }

        return secNode;
      });
    }

    return divNode;
  });
}

export const navigationTree = buildNavigationTree();

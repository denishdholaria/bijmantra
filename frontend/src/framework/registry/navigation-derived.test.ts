/**
 * Tests for navigation-derived.ts
 * 
 * These tests verify that the derived surface generators work correctly
 * with the navigation tree.
 */

import { describe, it, expect } from 'bun:test';
import {
  generateRoutesFromNavigation,
  generateSidebarFromNavigation,
  generateSidebarForDivision,
  generateCommandsFromNavigation,
  searchCommands,
  generateBreadcrumbsFromNavigation,
  generateDivisionBreadcrumbs,
  findNavigationNodeByPath,
  findNavigationNodeById,
  getAllNavigationPaths,
  derivedRoutes,
  derivedSidebar,
  derivedCommands,
} from './navigation-derived';
import { navigationTree } from './navigation-source';

describe('generateRoutesFromNavigation', () => {
  it('should generate routes from navigation tree', () => {
    const routes = generateRoutesFromNavigation();
    expect(routes.length).toBeGreaterThan(0);
  });

  it('should include division metadata in routes', () => {
    const routes = generateRoutesFromNavigation();
    const plantSciences = routes.find(r => r.id === 'plant-sciences');
    expect(plantSciences).toBeDefined();
    expect(plantSciences?.divisionId).toBe('plant-sciences');
  });

  it('should include child routes', () => {
    const routes = generateRoutesFromNavigation();
    const breeding = routes.find(r => r.id === 'breeding');
    expect(breeding).toBeDefined();
    expect(breeding?.path).toBe('/programs');
  });
});

describe('generateSidebarFromNavigation', () => {
  it('should generate sidebar menu from navigation tree', () => {
    const sidebar = generateSidebarFromNavigation();
    expect(sidebar.length).toBeGreaterThan(0);
  });

  it('should preserve hierarchy in sidebar', () => {
    const sidebar = generateSidebarFromNavigation();
    const plantSciences = sidebar.find(s => s.id === 'plant-sciences');
    expect(plantSciences).toBeDefined();
    expect(plantSciences?.children).toBeDefined();
    expect(plantSciences?.children?.length).toBeGreaterThan(0);
  });

  it('should filter by division when specified', () => {
    const sidebar = generateSidebarFromNavigation(navigationTree, {
      divisionId: 'plant-sciences',
    });
    // Should only include plant-sciences division
    expect(sidebar.every(s => s.divisionId === 'plant-sciences')).toBe(true);
  });

  it('should respect maxDepth option', () => {
    const sidebar = generateSidebarFromNavigation(navigationTree, {
      maxDepth: 1,
    });
    // At depth 1, children should be empty array (depth 2 is beyond maxDepth)
    expect(sidebar[0]?.children).toEqual([]);
  });
});

describe('generateSidebarForDivision', () => {
  it('should return sidebar items for a specific division', () => {
    const sidebar = generateSidebarForDivision('plant-sciences');
    expect(sidebar.length).toBeGreaterThan(0);
  });

  it('should return empty array for non-existent division', () => {
    const sidebar = generateSidebarForDivision('non-existent');
    expect(sidebar).toEqual([]);
  });
});

describe('generateCommandsFromNavigation', () => {
  it('should generate command palette items from navigation tree', () => {
    const commands = generateCommandsFromNavigation();
    expect(commands.length).toBeGreaterThan(0);
  });

  it('should include keywords for search', () => {
    const commands = generateCommandsFromNavigation();
    const plantSciences = commands.find(c => c.id === 'plant-sciences');
    expect(plantSciences?.keywords).toBeDefined();
    expect(plantSciences?.keywords?.length).toBeGreaterThan(0);
  });

  it('should build subtitle from parent context', () => {
    const commands = generateCommandsFromNavigation();
    // Find a nested item
    const ldAnalysis = commands.find(c => c.id === 'linkage-disequilibrium');
    expect(ldAnalysis).toBeDefined();
    expect(ldAnalysis?.subtitle).toContain('Genomics');
  });
});

describe('searchCommands', () => {
  it('should filter commands by query', () => {
    const results = searchCommands('genomics');
    expect(results.length).toBeGreaterThan(0);
    // Results should match the query in title, subtitle, or keywords
    const allMatch = results.every(c => {
      const searchText = [
        c.title,
        c.subtitle,
        ...(c.keywords || []),
      ].filter(Boolean).join(' ').toLowerCase();
      return searchText.includes('genomics');
    });
    expect(allMatch).toBe(true);
  });

  it('should return all commands for empty query', () => {
    const allCommands = generateCommandsFromNavigation();
    const results = searchCommands('');
    expect(results.length).toBe(allCommands.length);
  });
});

describe('generateBreadcrumbsFromNavigation', () => {
  it('should generate breadcrumbs for a valid path', () => {
    const breadcrumbs = generateBreadcrumbsFromNavigation('/programs');
    expect(breadcrumbs.length).toBeGreaterThan(0);
    expect(breadcrumbs[breadcrumbs.length - 1]?.path).toBe('/programs');
  });

  it('should return empty array for non-existent path', () => {
    const breadcrumbs = generateBreadcrumbsFromNavigation('/non-existent-path');
    expect(breadcrumbs).toEqual([]);
  });

  it('should build path from root to target', () => {
    const breadcrumbs = generateBreadcrumbsFromNavigation('/linkage-disequilibrium');
    expect(breadcrumbs.length).toBeGreaterThan(1);
    // First item should be a division
    expect(breadcrumbs[0]?.id).toBe('plant-sciences');
  });
});

describe('findNavigationNodeByPath', () => {
  it('should find node by path', () => {
    const node = findNavigationNodeByPath('/programs');
    expect(node).toBeDefined();
    expect(node?.id).toBe('plant-sciences');
  });

  it('should return undefined for non-existent path', () => {
    const node = findNavigationNodeByPath('/non-existent');
    expect(node).toBeUndefined();
  });
});

describe('findNavigationNodeById', () => {
  it('should find node by ID', () => {
    const node = findNavigationNodeById('plant-sciences');
    expect(node).toBeDefined();
    expect(node?.label).toBe('Plant Sciences');
  });

  it('should return undefined for non-existent ID', () => {
    const node = findNavigationNodeById('non-existent');
    expect(node).toBeUndefined();
  });
});

describe('getAllNavigationPaths', () => {
  it('should return all paths from navigation tree', () => {
    const paths = getAllNavigationPaths();
    expect(paths.length).toBeGreaterThan(0);
    expect(paths).toContain('/programs');
    expect(paths).toContain('/dashboard');
  });
});

describe('Pre-generated exports', () => {
  it('should export derivedRoutes', () => {
    expect(derivedRoutes.length).toBeGreaterThan(0);
  });

  it('should export derivedSidebar', () => {
    expect(derivedSidebar.length).toBeGreaterThan(0);
  });

  it('should export derivedCommands', () => {
    expect(derivedCommands.length).toBeGreaterThan(0);
  });
});

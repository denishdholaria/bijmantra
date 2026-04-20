import type { ReactNode } from 'react';
import { matchPath } from 'react-router-dom';
import type { RouteObject } from 'react-router-dom';

function normalizePath(path: string): string {
  if (!path) {
    return '/';
  }

  const normalized = path.replace(/\/+/g, '/');
  if (normalized === '/') {
    return normalized;
  }

  return normalized.replace(/\/+$/, '');
}

export function resolveRoutePath(basePath: string, routePath?: string): string {
  if (!routePath) {
    return normalizePath(basePath || '/');
  }

  if (routePath.startsWith('/')) {
    return normalizePath(routePath);
  }

  const normalizedBase = normalizePath(basePath || '/');
  if (normalizedBase === '/') {
    return normalizePath(`/${routePath}`);
  }

  return normalizePath(`${normalizedBase}/${routePath}`);
}

export function flattenRoutePaths(routes: RouteObject[]): Set<string> {
  const paths = new Set<string>();

  const walk = (nodes: RouteObject[], basePath = '') => {
    for (const node of nodes) {
      const nextBasePath = typeof node.path === 'string'
        ? resolveRoutePath(basePath, node.path)
        : resolveRoutePath(basePath);

      if (typeof node.path === 'string') {
        paths.add(nextBasePath);
      }

      if (node.children?.length) {
        walk(node.children, nextBasePath);
      }
    }
  };

  walk(routes);
  return paths;
}

export function findRouteElementByPath(path: string, routes: RouteObject[]): ReactNode | null {
  if (!path) {
    return null;
  }

  const normalizedPath = normalizePath(path);

  const walk = (nodes: RouteObject[], basePath = ''): ReactNode | null => {
    for (const node of nodes) {
      const nextBasePath = typeof node.path === 'string'
        ? resolveRoutePath(basePath, node.path)
        : resolveRoutePath(basePath);

      if (typeof node.path === 'string' && matchPath(nextBasePath, normalizedPath)) {
        return node.element ?? null;
      }

      if (node.children?.length) {
        const match = walk(node.children, nextBasePath);
        if (match) {
          return match;
        }
      }
    }

    return null;
  };

  return walk(routes);
}
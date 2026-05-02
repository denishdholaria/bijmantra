import { coreRoutes } from '@/routes/core';
import { RouteObject } from 'react-router-dom';

export interface SearchableItem {
  id: string;
  title: string;
  subtitle: string;
  path: string;
  category: 'App' | 'Action' | 'Page';
}

function extractRoutes(routes: RouteObject[], prefix = ''): SearchableItem[] {
  let items: SearchableItem[] = [];

  routes.forEach((route) => {
    if (route.path && route.path !== '/' && !route.path.includes('*')) {
      // Crude humanization of path
      const cleanPath = route.path.replace(':', '');
      const parts = cleanPath.split('/').filter(Boolean);
      const name = parts[parts.length - 1]
        .split('-')
        .map(w => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ');

      // Attempt to guess category
      const isAction = name.includes('New') || name.includes('Edit') || name.includes('Add');

      items.push({
        id: route.path,
        title: name || 'Home',
        subtitle: prefix + route.path,
        path: route.path,
        category: isAction ? 'Action' : 'Page'
      });
    }
  });

  return items;
}

export const DISCOVERED_ROUTES = extractRoutes(coreRoutes);

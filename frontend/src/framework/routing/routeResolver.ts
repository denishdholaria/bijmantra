import type { RouteObject } from 'react-router-dom';

// Import all route definitions
import { breedingRoutes } from '@/routes/breeding';
import { seedOpsRoutes } from '@/routes/seed_ops';
import { genomicsRoutes } from '@/routes/genomics';
import { commercialRoutes } from '@/routes/commercial';
import { cropSystemsRoutes } from '@/routes/crop_systems';
import { futureRoutes } from '@/routes/future';
import { adminRoutes } from '@/routes/admin';
import { aiRoutes } from '@/routes/ai';
import { coreRoutes } from '@/routes/core';
import { fieldRoutes } from '@/routes/field';
import { agronomyRoutes } from '@/divisions/agronomy/routes';
import { weatherRoutes } from '@/routes/weather';
import { findRouteElementByPath } from './routeTree';

// Consolidate all routes into a single search array
export const ALL_ROUTES: RouteObject[] = [
  ...coreRoutes,
  ...breedingRoutes,
  ...seedOpsRoutes,
  ...genomicsRoutes,
  ...commercialRoutes,
  ...cropSystemsRoutes,
  ...futureRoutes,
  ...adminRoutes,
  ...aiRoutes,
  ...fieldRoutes,
  ...agronomyRoutes,
  ...weatherRoutes,
];

/**
 * Resolves the component (element) for a given route path.
 * Leverages react-router-dom's matchPath to handle parameters (e.g. /programs/:id).
 */
export function resolveComponentForRoute(path: string): React.ReactNode | null {
  return findRouteElementByPath(path, ALL_ROUTES);
}

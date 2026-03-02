import { matchPath, RouteObject } from "react-router-dom";
import React from "react";

// Import all route definitions
import { breedingRoutes } from '@/routes/breeding';
import { seedOpsRoutes } from '@/routes/seed_ops';
import { genomicsRoutes } from '@/routes/genomics';
import { commercialRoutes } from '@/routes/commercial';
import { futureRoutes } from '@/routes/future';
import { adminRoutes } from '@/routes/admin';
import { aiRoutes } from '@/routes/ai';
import { coreRoutes } from '@/routes/core';
import { fieldRoutes } from '@/routes/field';

// Consolidate all routes into a single search array
export const ALL_ROUTES: RouteObject[] = [
  ...coreRoutes,
  ...breedingRoutes,
  ...seedOpsRoutes,
  ...genomicsRoutes,
  ...commercialRoutes,
  ...futureRoutes,
  ...adminRoutes,
  ...aiRoutes,
  ...fieldRoutes,
];

/**
 * Resolves the component (element) for a given route path.
 * Leverages react-router-dom's matchPath to handle parameters (e.g. /programs/:id).
 */
export function resolveComponentForRoute(path: string): React.ReactNode | null {
  if (!path) return null;

  // Find the matching route
  // We look for an exact match or a parameterized match
  const matchedRoute = ALL_ROUTES.find((route) => {
    if (route.path === path) return true;
    if (route.path && matchPath(route.path, path)) return true;
    return false;
  });

  return matchedRoute?.element || null;
}

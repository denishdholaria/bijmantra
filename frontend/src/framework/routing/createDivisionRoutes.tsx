/**
 * Parashakti Framework - Division Route Creator
 * 
 * Utility to create routes for divisions with proper protection and layout.
 * This allows gradual migration from the existing flat route structure.
 */

import { Suspense, lazy } from 'react';
import { RouteObject } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { ProtectedRoute } from '@/framework/auth';

/**
 * Loading fallback for lazy-loaded components
 */
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600" />
    </div>
  );
}

/**
 * Wrap a component with Layout and ProtectedRoute
 */
function withProtection(
  Component: React.ComponentType,
  options?: {
    requiredPermissions?: string[];
    requiredDivision?: string;
  }
) {
  return (
    <ProtectedRoute
      requiredPermissions={options?.requiredPermissions}
      requiredDivision={options?.requiredDivision}
    >
      <Layout>
        <Suspense fallback={<LoadingFallback />}>
          <Component />
        </Suspense>
      </Layout>
    </ProtectedRoute>
  );
}

/**
 * Create a protected route object
 */
export function createProtectedRoute(
  path: string,
  Component: React.ComponentType,
  options?: {
    requiredPermissions?: string[];
    requiredDivision?: string;
  }
): RouteObject {
  return {
    path,
    element: withProtection(Component, options),
  };
}

/**
 * Create routes for a division from a route config
 */
export function createDivisionRoutes(
  divisionId: string,
  routes: Array<{
    path: string;
    component: React.ComponentType;
    permissions?: string[];
  }>
): RouteObject[] {
  return routes.map(route => ({
    path: route.path,
    element: withProtection(route.component, {
      requiredPermissions: route.permissions,
      requiredDivision: divisionId,
    }),
  }));
}

/**
 * Create a lazy route (for code splitting)
 */
export function createLazyRoute(
  path: string,
  importFn: () => Promise<{ default: React.ComponentType }>,
  options?: {
    requiredPermissions?: string[];
    requiredDivision?: string;
  }
): RouteObject {
  const LazyComponent = lazy(importFn);
  return {
    path,
    element: withProtection(LazyComponent, options),
  };
}

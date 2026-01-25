/**
 * Integrations Division - Routes
 *
 * Division 8: Third-party API connections and external services.
 * Status: Active
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages - using default exports from local pages
const Dashboard = lazy(() => import('./pages/Dashboard'));

/**
 * Integrations Division Routes
 */
export const integrationsRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
];

export default integrationsRoutes;

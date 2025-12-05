/**
 * Commercial Division - Routes
 *
 * Division 6: Traceability, licensing, and ERP integration.
 * Status: Planned
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages - using default exports from local pages
const Dashboard = lazy(() => import('./pages/Dashboard'));

/**
 * Commercial Division Routes
 */
export const commercialRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
];

export default commercialRoutes;

/**
 * Space Research Division - Routes
 *
 * Division 7: Interplanetary agriculture and space agency collaborations.
 * Status: Visionary
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages - using default exports from local pages
const Dashboard = lazy(() => import('./pages/Dashboard'));

/**
 * Space Research Division Routes
 */
export const spaceResearchRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
];

export default spaceResearchRoutes;

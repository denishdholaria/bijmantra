/**
 * Sun-Earth Systems Division - Routes
 *
 * Division 4: Solar radiation, magnetic field monitoring, and space weather.
 * Status: Visionary
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages - using default exports from local pages
const Dashboard = lazy(() => import('./pages/Dashboard'));

/**
 * Sun-Earth Systems Division Routes
 */
export const sunEarthSystemsRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
];

export default sunEarthSystemsRoutes;

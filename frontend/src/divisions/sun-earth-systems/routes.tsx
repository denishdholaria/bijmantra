/**
 * Sun-Earth Systems Division - Routes
 *
 * Division 4: Solar radiation, magnetic field monitoring, and space weather.
 * Status: Active
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const SolarActivity = lazy(() => import('./pages/SolarActivity'));
const Photoperiod = lazy(() => import('./pages/Photoperiod'));
const UVIndex = lazy(() => import('./pages/UVIndex'));

/**
 * Sun-Earth Systems Division Routes
 */
export const sunEarthSystemsRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  { path: 'solar-activity', element: <SolarActivity /> },
  { path: 'photoperiod', element: <Photoperiod /> },
  { path: 'uv-index', element: <UVIndex /> },
];

export default sunEarthSystemsRoutes;

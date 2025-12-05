/**
 * Sensor Networks Division - Routes
 *
 * Division 5: IoT integration and environmental monitoring.
 * Status: Conceptual
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages - using default exports from local pages
const Dashboard = lazy(() => import('./pages/Dashboard'));

/**
 * Sensor Networks Division Routes
 */
export const sensorNetworksRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
];

export default sensorNetworksRoutes;

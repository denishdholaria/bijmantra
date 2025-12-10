/**
 * Sensor Networks Division - Routes
 *
 * Division 5: IoT integration and environmental monitoring.
 * Status: Active
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Devices = lazy(() => import('./pages/Devices'));
const LiveData = lazy(() => import('./pages/LiveData'));
const Alerts = lazy(() => import('./pages/Alerts'));

/**
 * Sensor Networks Division Routes
 */
export const sensorNetworksRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  { path: 'devices', element: <Devices /> },
  { path: 'live', element: <LiveData /> },
  { path: 'alerts', element: <Alerts /> },
];

export default sensorNetworksRoutes;

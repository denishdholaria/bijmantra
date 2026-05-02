/**
 * Sensor Networks Division - Routes
 *
 * Division 5: IoT integration and environmental monitoring.
 * Status: Active
 * 
 * Includes BrAPI IoT Extension endpoints:
 * - /brapi/v2/extensions/iot/devices
 * - /brapi/v2/extensions/iot/sensors
 * - /brapi/v2/extensions/iot/telemetry
 * - /brapi/v2/extensions/iot/aggregates
 * - /brapi/v2/extensions/iot/alerts
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Devices = lazy(() => import('./pages/Devices'));
const LiveData = lazy(() => import('./pages/LiveData'));
const Alerts = lazy(() => import('./pages/Alerts'));
const Telemetry = lazy(() => import('./pages/Telemetry'));
const Aggregates = lazy(() => import('./pages/Aggregates'));
const EnvironmentLink = lazy(() => import('./pages/EnvironmentLink'));

/**
 * Sensor Networks Division Routes
 */
export const sensorNetworksRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  { path: 'devices', element: <Devices /> },
  { path: 'live', element: <LiveData /> },
  { path: 'alerts', element: <Alerts /> },
  // BrAPI IoT Extension pages
  { path: 'telemetry', element: <Telemetry /> },
  { path: 'aggregates', element: <Aggregates /> },
  { path: 'environment-links', element: <EnvironmentLink /> },
];

export default sensorNetworksRoutes;

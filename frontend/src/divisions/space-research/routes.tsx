/**
 * Space Research Division - Routes
 *
 * Division 7: Interplanetary agriculture and space agency collaborations.
 * Status: Active
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const SpaceCrops = lazy(() => import('./pages/SpaceCrops'));
const Radiation = lazy(() => import('./pages/Radiation'));
const LifeSupport = lazy(() => import('./pages/LifeSupport'));

/**
 * Space Research Division Routes
 */
export const spaceResearchRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  { path: 'crops', element: <SpaceCrops /> },
  { path: 'radiation', element: <Radiation /> },
  { path: 'life-support', element: <LifeSupport /> },
];

export default spaceResearchRoutes;

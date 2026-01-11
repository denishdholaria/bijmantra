/**
 * Commercial Division - Routes
 *
 * Division 6: Traceability, licensing, DUS testing, and ERP integration.
 * Status: Active
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const DUSTrials = lazy(() => import('./pages/DUSTrials'));
const DUSCrops = lazy(() => import('./pages/DUSCrops'));
const DUSTrialDetail = lazy(() => import('./pages/DUSTrialDetail'));

/**
 * Commercial Division Routes
 */
export const commercialRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  // DUS Testing
  { path: 'dus', element: <DUSTrials /> },
  { path: 'dus/crops', element: <DUSCrops /> },
  { path: 'dus/trials/:trialId', element: <DUSTrialDetail /> },
];

export default commercialRoutes;

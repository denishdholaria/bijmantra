import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const SoilTests = lazy(() => import('./pages/SoilTests').then(m => ({ default: m.SoilTests })));
const SoilHealth = lazy(() => import('./pages/SoilHealth').then(m => ({ default: m.SoilHealth })));
const NutrientCalculator = lazy(() => import('./pages/NutrientCalculator').then(m => ({ default: m.NutrientCalculator })));
const CarbonTracker = lazy(() => import('./pages/CarbonTracker').then(m => ({ default: m.CarbonTracker })));

export const soilNutrientsRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  { path: 'soil-tests', element: <SoilTests /> },
  { path: 'soil-health', element: <SoilHealth /> },
  { path: 'prescriptions', element: <NutrientCalculator /> },
  { path: 'carbon', element: <CarbonTracker /> },
];

export default soilNutrientsRoutes;
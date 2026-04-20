import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

const CropIntelligenceDashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.CropIntelligenceDashboard })));
const CropSuitability = lazy(() => import('./pages/CropSuitability').then(m => ({ default: m.CropSuitability })));
const GDDTracker = lazy(() => import('./pages/GDDTracker').then(m => ({ default: m.GDDTracker })));
const CropCalendar = lazy(() => import('./pages/CropCalendar').then(m => ({ default: m.CropCalendar })));
const YieldPrediction = lazy(() => import('./pages/YieldPrediction').then(m => ({ default: m.YieldPrediction })));

export const cropIntelligenceRoutes: RouteObject[] = [
  { path: '', element: <CropIntelligenceDashboard /> },
  { path: 'dashboard', element: <CropIntelligenceDashboard /> },
  { path: 'crop-suitability', element: <CropSuitability /> },
  { path: 'gdd-tracker', element: <GDDTracker /> },
  { path: 'crop-calendar', element: <CropCalendar /> },
  { path: 'yield-prediction', element: <YieldPrediction /> },
];

export default cropIntelligenceRoutes;
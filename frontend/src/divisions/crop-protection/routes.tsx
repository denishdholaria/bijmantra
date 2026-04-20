import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

const CropProtectionDashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.CropProtectionDashboard })));
const PestObservations = lazy(() => import('./pages/PestObservations').then(m => ({ default: m.PestObservations })));
const DiseaseRiskForecast = lazy(() => import('./pages/DiseaseRiskForecast').then(m => ({ default: m.DiseaseRiskForecastPage })));
const SprayApplication = lazy(() => import('./pages/SprayApplication').then(m => ({ default: m.SprayApplication })));
const IPMStrategies = lazy(() => import('./pages/IPMStrategies').then(m => ({ default: m.IPMStrategies })));

export const cropProtectionRoutes: RouteObject[] = [
  { path: '', element: <CropProtectionDashboard /> },
  { path: 'dashboard', element: <CropProtectionDashboard /> },
  { path: 'pest-observations', element: <PestObservations /> },
  { path: 'disease-risk-forecast', element: <DiseaseRiskForecast /> },
  { path: 'spray-applications', element: <SprayApplication /> },
  { path: 'ipm-strategies', element: <IPMStrategies /> },
];

export default cropProtectionRoutes;
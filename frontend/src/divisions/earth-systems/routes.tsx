/**
 * Earth Systems Division - Routes
 *
 * Division 3: Climate, weather, and GIS platform.
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const WeatherForecast = lazy(() => import('./pages/WeatherForecast'));
const ClimateAnalysis = lazy(() => import('./pages/ClimateAnalysis'));
const FieldMap = lazy(() => import('./pages/FieldMap'));
const SoilData = lazy(() => import('./pages/SoilData'));
const GrowingDegrees = lazy(() => import('./pages/GrowingDegrees'));
const DroughtMonitor = lazy(() => import('./pages/DroughtMonitor'));
const InputLog = lazy(() => import('./pages/InputLog'));
const Irrigation = lazy(() => import('./pages/Irrigation'));
const YieldPrediction = lazy(() => import('./pages/YieldPrediction'));
const CarbonDashboard = lazy(() => import('./pages/CarbonDashboard').then(m => ({ default: m.CarbonDashboard })));
const SustainabilityMetrics = lazy(() => import('./pages/SustainabilityMetrics').then(m => ({ default: m.SustainabilityMetrics })));

/**
 * Earth Systems Division Routes
 */
export const earthSystemsRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  { path: 'weather', element: <WeatherForecast /> },
  { path: 'climate', element: <ClimateAnalysis /> },
  { path: 'map', element: <FieldMap /> },
  { path: 'soil', element: <SoilData /> },
  { path: 'inputs', element: <InputLog /> },
  { path: 'irrigation', element: <Irrigation /> },
  { path: 'gdd', element: <GrowingDegrees /> },
  { path: 'drought', element: <DroughtMonitor /> },
  { path: 'yield-prediction', element: <YieldPrediction /> },
  { path: 'carbon', element: <CarbonDashboard /> },
  { path: 'sustainability', element: <SustainabilityMetrics /> },
];

export default earthSystemsRoutes;

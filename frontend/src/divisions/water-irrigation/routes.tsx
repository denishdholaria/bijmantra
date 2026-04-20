import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const IrrigationSchedules = lazy(() => import('./pages/IrrigationSchedules').then(m => ({ default: m.IrrigationSchedules })));
const WaterBalance = lazy(() => import('./pages/WaterBalance').then(m => ({ default: m.WaterBalance })));
const SoilMoisture = lazy(() => import('./pages/SoilMoisture').then(m => ({ default: m.SoilMoisture })));

export const waterIrrigationRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  { path: 'schedules', element: <IrrigationSchedules /> },
  { path: 'balance', element: <WaterBalance /> },
  { path: 'moisture', element: <SoilMoisture /> },
];

export default waterIrrigationRoutes;
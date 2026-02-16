/**
 * Seed Operations Division - Routes
 *
 * Complete seed company workflow: LIMS, Processing, Inventory, Dispatch
 * Status: Active
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const LabSamples = lazy(() => import('./pages/LabSamples'));
const LabTesting = lazy(() => import('./pages/LabTesting'));
const Certificates = lazy(() => import('./pages/Certificates'));
const QualityGate = lazy(() => import('./pages/QualityGate'));
const ProcessingBatches = lazy(() => import('./pages/ProcessingBatches'));
const ProcessingStages = lazy(() => import('./pages/ProcessingStages'));
const SeedLots = lazy(() => import('./pages/SeedLots'));
const Warehouse = lazy(() => import('./pages/Warehouse'));
const StockAlerts = lazy(() => import('./pages/StockAlerts'));
const CreateDispatch = lazy(() => import('./pages/CreateDispatch'));
const DispatchHistory = lazy(() => import('./pages/DispatchHistory'));
const Firms = lazy(() => import('./pages/Firms'));
const TrackLot = lazy(() => import('./pages/TrackLot'));
const Lineage = lazy(() => import('./pages/Lineage'));
const Varieties = lazy(() => import('./pages/Varieties'));
const Agreements = lazy(() => import('./pages/Agreements'));

/**
 * Seed Operations Division Routes
 */
export const seedOperationsRoutes: RouteObject[] = [
  // Dashboard
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  
  // Lab Testing (LIMS)
  { path: 'samples', element: <LabSamples /> },
  { path: 'testing', element: <LabTesting /> },
  { path: 'certificates', element: <Certificates /> },
  
  // Processing
  { path: 'quality-gate', element: <QualityGate /> },
  { path: 'batches', element: <ProcessingBatches /> },
  { path: 'stages', element: <ProcessingStages /> },
  
  // Inventory
  { path: 'lots', element: <SeedLots /> },
  { path: 'warehouse', element: <Warehouse /> },
  { path: 'alerts', element: <StockAlerts /> },
  
  // Dispatch
  { path: 'dispatch', element: <CreateDispatch /> },
  { path: 'dispatch-history', element: <DispatchHistory /> },
  { path: 'firms', element: <Firms /> },
  
  // Traceability
  { path: 'track', element: <TrackLot /> },
  { path: 'lineage', element: <Lineage /> },
  
  // Licensing
  { path: 'varieties', element: <Varieties /> },
  { path: 'agreements', element: <Agreements /> },
];

export default seedOperationsRoutes;

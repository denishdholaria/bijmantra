/**
 * Seed Bank Division - Routes
 * 
 * Division 2: Genetic resources preservation and germplasm conservation.
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const SeedBankDashboard = lazy(() => import('./pages/Dashboard'));
const VaultManagement = lazy(() => import('./pages/VaultManagement'));
const Accessions = lazy(() => import('./pages/Accessions'));
const AccessionNew = lazy(() => import('./pages/AccessionNew'));
const AccessionDetail = lazy(() => import('./pages/AccessionDetail'));
const Conservation = lazy(() => import('./pages/Conservation'));
const GermplasmExchange = lazy(() => import('./pages/GermplasmExchange'));
const ViabilityTesting = lazy(() => import('./pages/ViabilityTesting'));
const RegenerationPlanning = lazy(() => import('./pages/RegenerationPlanning'));
const MCPDExchange = lazy(() => import('./pages/MCPDExchange'));
const GRINSearch = lazy(() => import('./pages/GRINSearch'));
const TaxonomyValidator = lazy(() => import('./pages/TaxonomyValidator'));
const MTAManagement = lazy(() => import('./pages/MTAManagement'));
const VaultMonitoring = lazy(() => import('./pages/VaultMonitoring'));
const OfflineDataEntry = lazy(() => import('./pages/OfflineDataEntry'));

/**
 * Seed Bank Division Routes
 */
export const seedBankRoutes: RouteObject[] = [
  { path: '', element: <SeedBankDashboard /> },
  { path: 'dashboard', element: <SeedBankDashboard /> },
  { path: 'vault', element: <VaultManagement /> },
  { path: 'accessions', element: <Accessions /> },
  { path: 'accessions/new', element: <AccessionNew /> },
  { path: 'accessions/:id', element: <AccessionDetail /> },
  { path: 'conservation', element: <Conservation /> },
  { path: 'exchange', element: <GermplasmExchange /> },
  { path: 'viability', element: <ViabilityTesting /> },
  { path: 'regeneration', element: <RegenerationPlanning /> },
  { path: 'mcpd', element: <MCPDExchange /> },
  { path: 'grin-search', element: <GRINSearch /> },
  { path: 'taxonomy', element: <TaxonomyValidator /> },
  { path: 'mta', element: <MTAManagement /> },
  { path: 'monitoring', element: <VaultMonitoring /> },
  { path: 'offline', element: <OfflineDataEntry /> },
];

export default seedBankRoutes;

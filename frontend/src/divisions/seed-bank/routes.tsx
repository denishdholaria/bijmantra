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
const AccessionDetail = lazy(() => import('./pages/AccessionDetail'));
const Conservation = lazy(() => import('./pages/Conservation'));
const GermplasmExchange = lazy(() => import('./pages/GermplasmExchange'));
const ViabilityTesting = lazy(() => import('./pages/ViabilityTesting'));
const RegenerationPlanning = lazy(() => import('./pages/RegenerationPlanning'));

/**
 * Seed Bank Division Routes
 */
export const seedBankRoutes: RouteObject[] = [
  { path: '', element: <SeedBankDashboard /> },
  { path: 'dashboard', element: <SeedBankDashboard /> },
  { path: 'vault', element: <VaultManagement /> },
  { path: 'accessions', element: <Accessions /> },
  { path: 'accessions/:id', element: <AccessionDetail /> },
  { path: 'conservation', element: <Conservation /> },
  { path: 'exchange', element: <GermplasmExchange /> },
  { path: 'viability', element: <ViabilityTesting /> },
  { path: 'regeneration', element: <RegenerationPlanning /> },
];

export default seedBankRoutes;

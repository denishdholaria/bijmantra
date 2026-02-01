import { lazy, Suspense } from 'react';
import { RouteObject } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/Layout';

// Seed Operations Division
const SeedOpsDashboard = lazy(() => import('@/divisions/seed-operations/pages/Dashboard'));
const SeedOpsLabSamples = lazy(() => import('@/divisions/seed-operations/pages/LabSamples'));
const SeedOpsLabTesting = lazy(() => import('@/divisions/seed-operations/pages/LabTesting'));
const SeedOpsCertificates = lazy(() => import('@/divisions/seed-operations/pages/Certificates'));
const SeedOpsQualityGate = lazy(() => import('@/divisions/seed-operations/pages/QualityGate'));
const SeedOpsBatches = lazy(() => import('@/divisions/seed-operations/pages/ProcessingBatches'));
const SeedOpsStages = lazy(() => import('@/divisions/seed-operations/pages/ProcessingStages'));
const SeedOpsLots = lazy(() => import('@/divisions/seed-operations/pages/SeedLots'));
const SeedOpsWarehouse = lazy(() => import('@/divisions/seed-operations/pages/Warehouse'));
const SeedOpsAlerts = lazy(() => import('@/divisions/seed-operations/pages/StockAlerts'));
const SeedOpsDispatch = lazy(() => import('@/divisions/seed-operations/pages/CreateDispatch'));
const SeedOpsDispatchHistory = lazy(() => import('@/divisions/seed-operations/pages/DispatchHistory'));
const SeedOpsFirms = lazy(() => import('@/divisions/seed-operations/pages/Firms'));
const SeedOpsTrack = lazy(() => import('@/divisions/seed-operations/pages/TrackLot'));
const SeedOpsLineage = lazy(() => import('@/divisions/seed-operations/pages/Lineage'));
const SeedOpsVarieties = lazy(() => import('@/divisions/seed-operations/pages/Varieties'));
const SeedOpsAgreements = lazy(() => import('@/divisions/seed-operations/pages/Agreements'));

// Core Seed Lot pages
const SeedLots = lazy(() => import('@/pages/SeedLots').then(m => ({ default: m.SeedLots })));
const SeedLotDetail = lazy(() => import('@/pages/SeedLotDetail').then(m => ({ default: m.SeedLotDetail })));
const SeedLotForm = lazy(() => import('@/pages/SeedLotForm').then(m => ({ default: m.SeedLotForm })));
const SeedInventory = lazy(() => import('@/pages/SeedInventory').then(m => ({ default: m.SeedInventory })));
const SeedRequest = lazy(() => import('@/pages/SeedRequest').then(m => ({ default: m.SeedRequest })));

// Seed Bank Division
const SeedBankDashboard = lazy(() => import('@/divisions/seed-bank/pages/Dashboard'));
const SeedBankVault = lazy(() => import('@/divisions/seed-bank/pages/VaultManagement'));
const SeedBankAccessions = lazy(() => import('@/divisions/seed-bank/pages/Accessions'));
const SeedBankAccessionNew = lazy(() => import('@/divisions/seed-bank/pages/AccessionNew'));
const SeedBankAccessionDetail = lazy(() => import('@/divisions/seed-bank/pages/AccessionDetail'));
const SeedBankConservation = lazy(() => import('@/divisions/seed-bank/pages/Conservation'));
const SeedBankExchange = lazy(() => import('@/divisions/seed-bank/pages/GermplasmExchange'));
const SeedBankViability = lazy(() => import('@/divisions/seed-bank/pages/ViabilityTesting'));
const SeedBankRegeneration = lazy(() => import('@/divisions/seed-bank/pages/RegenerationPlanning'));
const SeedBankMCPD = lazy(() => import('@/divisions/seed-bank/pages/MCPDExchange'));
const SeedBankGRINSearch = lazy(() => import('@/divisions/seed-bank/pages/GRINSearch'));
const SeedBankTaxonomy = lazy(() => import('@/divisions/seed-bank/pages/TaxonomyValidator'));
const SeedBankMTA = lazy(() => import('@/divisions/seed-bank/pages/MTAManagement'));
const SeedBankVaultMonitoring = lazy(() => import('@/divisions/seed-bank/pages/VaultMonitoring'));
const SeedBankOfflineEntry = lazy(() => import('@/divisions/seed-bank/pages/OfflineDataEntry'));
const GeneBank = lazy(() => import('@/pages/GeneBank').then(m => ({ default: m.GeneBank })));
const GermplasmCollection = lazy(() => import('@/pages/GermplasmCollection').then(m => ({ default: m.GermplasmCollection })));

const TraceabilityTimeline = lazy(() => import('@/components/ledger/TraceabilityTimeline'));

// Helper
const wrap = (Component: React.LazyExoticComponent<any> | React.ComponentType) => (
  <ProtectedRoute>
    <Layout>
      <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
        <Component />
      </Suspense>
    </Layout>
  </ProtectedRoute>
);

export const seedOpsRoutes: RouteObject[] = [
  // Seed Operations
  { path: '/seed-ops', element: wrap(SeedOpsDashboard) },
  { path: '/seed-ops/dashboard', element: wrap(SeedOpsDashboard) },
  { path: '/seed-ops/samples', element: wrap(SeedOpsLabSamples) },
  { path: '/seed-ops/testing', element: wrap(SeedOpsLabTesting) },
  { path: '/seed-ops/certificates', element: wrap(SeedOpsCertificates) },
  { path: '/seed-ops/quality-gate', element: wrap(SeedOpsQualityGate) },
  { path: '/seed-ops/batches', element: wrap(SeedOpsBatches) },
  { path: '/seed-ops/stages', element: wrap(SeedOpsStages) },
  { path: '/seed-ops/lots', element: wrap(SeedOpsLots) },
  { path: '/seed-ops/warehouse', element: wrap(SeedOpsWarehouse) },
  { path: '/seed-ops/alerts', element: wrap(SeedOpsAlerts) },
  { path: '/seed-ops/dispatch', element: wrap(SeedOpsDispatch) },
  { path: '/seed-ops/dispatch-history', element: wrap(SeedOpsDispatchHistory) },
  { path: '/seed-ops/firms', element: wrap(SeedOpsFirms) },
  { path: '/seed-ops/track', element: wrap(SeedOpsTrack) },
  { path: '/seed-ops/lineage', element: wrap(SeedOpsLineage) },
  { path: '/seed-ops/varieties', element: wrap(SeedOpsVarieties) },
  { path: '/seed-ops/agreements', element: wrap(SeedOpsAgreements) },

  // Core Seed Lots
  { path: '/seedlots', element: wrap(SeedLots) },
  { path: '/seedlots/new', element: wrap(SeedLotForm) },
  { path: '/seedlots/:id', element: wrap(SeedLotDetail) },
  { path: '/seedlots/:id/edit', element: wrap(SeedLotForm) },
  { path: '/inventory', element: wrap(SeedInventory) },
  { path: '/seedrequest', element: wrap(SeedRequest) },
  { path: '/traceability', element: wrap(TraceabilityTimeline) },

  // Seed Bank
  { path: '/seed-bank', element: wrap(SeedBankDashboard) },
  { path: '/seed-bank/dashboard', element: wrap(SeedBankDashboard) },
  { path: '/seed-bank/vault', element: wrap(SeedBankVault) },
  { path: '/seed-bank/accessions', element: wrap(SeedBankAccessions) },
  { path: '/seed-bank/accessions/new', element: wrap(SeedBankAccessionNew) },
  { path: '/seed-bank/accessions/:id', element: wrap(SeedBankAccessionDetail) },
  { path: '/seed-bank/conservation', element: wrap(SeedBankConservation) },
  { path: '/seed-bank/exchange', element: wrap(SeedBankExchange) },
  { path: '/seed-bank/viability', element: wrap(SeedBankViability) },
  { path: '/seed-bank/regeneration', element: wrap(SeedBankRegeneration) },
  { path: '/seed-bank/mcpd', element: wrap(SeedBankMCPD) },
  { path: '/seed-bank/grin-search', element: wrap(SeedBankGRINSearch) },
  { path: '/seed-bank/taxonomy', element: wrap(SeedBankTaxonomy) },
  { path: '/seed-bank/mta', element: wrap(SeedBankMTA) },
  { path: '/seed-bank/monitoring', element: wrap(SeedBankVaultMonitoring) },
  { path: '/seed-bank/offline', element: wrap(SeedBankOfflineEntry) },
  { path: '/genebank', element: wrap(GeneBank) },
  { path: '/collections', element: wrap(GermplasmCollection) },
];

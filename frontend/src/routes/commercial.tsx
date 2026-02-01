import { lazy, Suspense } from 'react';
import { RouteObject } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/Layout';

// Commercial Division - DUS Testing
const CommercialDashboard = lazy(() => import('@/divisions/commercial/pages/Dashboard'));
const DUSTrials = lazy(() => import('@/divisions/commercial/pages/DUSTrials'));
const DUSCrops = lazy(() => import('@/divisions/commercial/pages/DUSCrops'));
const DUSTrialDetail = lazy(() => import('@/divisions/commercial/pages/DUSTrialDetail'));

// Marketing & Sales
const MarketAnalysis = lazy(() => import('@/pages/MarketAnalysis').then(m => ({ default: m.MarketAnalysis })));
const StakeholderPortal = lazy(() => import('@/pages/StakeholderPortal').then(m => ({ default: m.StakeholderPortal })));
const VarietyRelease = lazy(() => import('@/pages/VarietyRelease').then(m => ({ default: m.VarietyRelease })));
const VarietyComparison = lazy(() => import('@/pages/VarietyComparison').then(m => ({ default: m.VarietyComparison })));

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

export const commercialRoutes: RouteObject[] = [
  // Commercial Dashboard
  { path: '/commercial', element: wrap(CommercialDashboard) },
  
  // DUS Testing
  { path: '/commercial/dus-trials', element: wrap(DUSTrials) },
  { path: '/commercial/dus-crops', element: wrap(DUSCrops) },
  { path: '/commercial/dus-trials/:id', element: wrap(DUSTrialDetail) },

  // Market & Release
  { path: '/market-analysis', element: wrap(MarketAnalysis) },
  { path: '/stakeholders', element: wrap(StakeholderPortal) },
  { path: '/variety-release', element: wrap(VarietyRelease) },
  { path: '/varietycomparison', element: wrap(VarietyComparison) },
  { path: '/variety-comparison', element: wrap(VarietyComparison) }, // Alias
];

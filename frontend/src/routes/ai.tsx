import { lazy, Suspense } from 'react';
import { RouteObject } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
// Lazy Layout import to prevent circular dependency
const Layout = lazy(() => import('@/components/Layout').then(m => ({ default: m.Layout })));

// AI Assistants
const VeenaChat = lazy(() => import('@/pages/VeenaChat').then(m => ({ default: m.VeenaChat })));
const ReevaChat = lazy(() => import('@/pages/ReevaChat').then(m => ({ default: m.ReevaChat })));
const DevGuru = lazy(() => import('@/pages/DevGuru').then(m => ({ default: m.DevGuru })));
const AIAssistant = lazy(() => import('@/pages/AIAssistant').then(m => ({ default: m.AIAssistant })));
const ChromeAI = lazy(() => import('@/pages/ChromeAI').then(m => ({ default: m.ChromeAI })));
const InsightsDashboard = lazy(() => import('@/pages/InsightsDashboard'));
const ApexAnalytics = lazy(() => import('@/pages/ApexAnalytics'));

// Computer Vision
const PlantVision = lazy(() => import('@/pages/PlantVision').then(m => ({ default: m.PlantVision })));
// const PlantVisionStrategy = lazy(() => import('@/pages/PlantVisionStrategy').then(m => ({ default: m.PlantVisionStrategy })));
const VisionDashboard = lazy(() => import('@/pages/VisionDashboard').then(m => ({ default: m.VisionDashboard })));
const VisionDatasets = lazy(() => import('@/pages/VisionDatasets').then(m => ({ default: m.VisionDatasets })));
const VisionTraining = lazy(() => import('@/pages/VisionTraining').then(m => ({ default: m.VisionTraining })));
const VisionRegistry = lazy(() => import('@/pages/VisionRegistry').then(m => ({ default: m.VisionRegistry })));
const VisionAnnotate = lazy(() => import('@/pages/VisionAnnotate').then(m => ({ default: m.VisionAnnotate })));

// Design Preview
const DesignPreview = lazy(() => import('@/pages/DesignPreview'));

// Helper
const wrap = (Component: React.LazyExoticComponent<any> | React.ComponentType) => (
  <ProtectedRoute>
    <Suspense fallback={null}>
      <Layout>
        <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
          <Component />
        </Suspense>
      </Layout>
    </Suspense>
  </ProtectedRoute>
);

export const aiRoutes: RouteObject[] = [
  // Assistants
  { 
    path: '/veena', 
    element: <ProtectedRoute>
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin h-8 w-8 border-4 border-amber-500 border-t-transparent rounded-full" /></div>}>
        <VeenaChat />
      </Suspense>
    </ProtectedRoute> 
  },
  { 
    path: '/reeva', 
    element: <ProtectedRoute>
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin h-8 w-8 border-4 border-violet-500 border-t-transparent rounded-full" /></div>}>
        <ReevaChat />
      </Suspense>
    </ProtectedRoute> 
  },
  { 
    path: '/devguru', 
    element: <ProtectedRoute>
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full" /></div>}>
        <DevGuru />
      </Suspense>
    </ProtectedRoute> 
  },
  { path: '/ai-assistant', element: wrap(AIAssistant) },
  { path: '/chrome-ai', element: wrap(ChromeAI) },
  { path: '/insights', element: wrap(InsightsDashboard) },
  { path: '/apex-analytics', element: wrap(ApexAnalytics) },

  // Vision
  { path: '/plant-vision', element: wrap(PlantVision) },
// { path: '/plant-vision/strategy', element: wrap(PlantVisionStrategy) },
  { path: '/ai-vision', element: wrap(VisionDashboard) },
  { path: '/ai-vision/datasets', element: wrap(VisionDatasets) },
  { path: '/ai-vision/training', element: wrap(VisionTraining) },
  { path: '/ai-vision/registry', element: wrap(VisionRegistry) },
  { 
    path: '/ai-vision/annotate/:datasetId', 
    element: <ProtectedRoute>
               <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                 <VisionAnnotate />
               </Suspense>
             </ProtectedRoute> 
  },

  // Design Preview
  { path: '/design-preview', element: wrap(DesignPreview) },
];

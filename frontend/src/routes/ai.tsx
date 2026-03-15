import { lazy, Suspense } from "react";
import { Navigate, RouteObject } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LEGACY_REEVU_ROUTE } from "@/lib/legacyReevu";

// Lazy Layout import to prevent circular dependency
const Layout = lazy(() =>
  import("@/components/Layout").then((m) => ({ default: m.Layout })),
);

// AI Assistants
const ReevuChat = lazy(() =>
  import("@/pages/ReevuChat").then((m) => ({ default: m.ReevuChat })),
);
const DevGuru = lazy(() =>
  import("@/pages/DevGuru").then((m) => ({ default: m.DevGuru })),
);
const ChromeAI = lazy(() =>
  import("@/pages/ChromeAI").then((m) => ({ default: m.ChromeAI })),
);
const InsightsDashboard = lazy(() => import("@/pages/InsightsDashboard"));
const ApexAnalytics = lazy(() => import("@/pages/ApexAnalytics"));

// Computer Vision
const PlantVision = lazy(() =>
  import("@/pages/PlantVision").then((m) => ({ default: m.PlantVision })),
);
// const PlantVisionStrategy = lazy(() => import('@/pages/PlantVisionStrategy').then(m => ({ default: m.PlantVisionStrategy })));
const VisionDashboard = lazy(() =>
  import("@/pages/VisionDashboard").then((m) => ({
    default: m.VisionDashboard,
  })),
);
const VisionDatasets = lazy(() =>
  import("@/pages/VisionDatasets").then((m) => ({ default: m.VisionDatasets })),
);
const VisionTraining = lazy(() =>
  import("@/pages/VisionTraining").then((m) => ({ default: m.VisionTraining })),
);
const VisionRegistry = lazy(() =>
  import("@/pages/VisionRegistry").then((m) => ({ default: m.VisionRegistry })),
);
const VisionAnnotate = lazy(() =>
  import("@/pages/VisionAnnotate").then((m) => ({ default: m.VisionAnnotate })),
);

// Design Preview
const DesignPreview = lazy(() => import("@/pages/DesignPreview"));

// Helper
const wrapInShellLayout = (
  Component: React.LazyExoticComponent<any> | React.ComponentType,
) => (
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

const wrapProtected = (
  Component: React.LazyExoticComponent<any> | React.ComponentType,
  fallback: React.ReactNode = <div className="p-8 text-center">Loading...</div>,
) => (
  <ProtectedRoute>
    <Suspense fallback={fallback}>
      <Component />
    </Suspense>
  </ProtectedRoute>
);

export const aiRoutes: RouteObject[] = [
  // Assistants
  {
    path: "/reevu",
    element: wrapProtected(
      ReevuChat,
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-emerald-500 border-t-transparent rounded-full" />
      </div>,
    ),
  },
  {
    path: LEGACY_REEVU_ROUTE,
    element: wrapProtected(
      ReevuChat,
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-amber-500 border-t-transparent rounded-full" />
      </div>,
    ),
  },
  {
    path: "/reeva",
    element: <Navigate to="/reevu" replace />,
  },
  {
    path: "/devguru",
    element: wrapProtected(
      DevGuru,
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full" />
      </div>,
    ),
  },
  { path: "/ai-assistant", element: <Navigate to="/reevu" replace /> },
  { path: "/chrome-ai", element: wrapInShellLayout(ChromeAI) },
  { path: "/insights", element: wrapInShellLayout(InsightsDashboard) },
  { path: "/apex-analytics", element: wrapInShellLayout(ApexAnalytics) },

  // Vision — Plant Vision AI Module
  { path: "/ai-vision", element: wrapInShellLayout(VisionDashboard) },
  { path: "/ai-vision/datasets", element: wrapInShellLayout(VisionDatasets) },
  { path: "/ai-vision/training", element: wrapInShellLayout(VisionTraining) },
  { path: "/ai-vision/registry", element: wrapInShellLayout(VisionRegistry) },
  { path: "/plant-vision", element: wrapInShellLayout(VisionDashboard) },
  { path: "/plant-vision/strategy", element: wrapInShellLayout(VisionDashboard) },
  { path: "/plant-vision/inference", element: wrapInShellLayout(PlantVision) },
  { path: "/plant-vision/datasets", element: wrapInShellLayout(VisionDatasets) },
  { path: "/plant-vision/training", element: wrapInShellLayout(VisionTraining) },
  { path: "/plant-vision/models", element: wrapInShellLayout(VisionRegistry) },
  {
    path: "/plant-vision/annotate/:datasetId",
    element: wrapProtected(VisionAnnotate),
  },

  // Design Preview
  { path: "/design-preview", element: wrapInShellLayout(DesignPreview) },
];

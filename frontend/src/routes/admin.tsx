import { lazy, Suspense } from 'react';
import { RouteObject } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
// Lazy Layout import to prevent circular dependency
const Layout = lazy(() => import('@/components/Layout').then(m => ({ default: m.Layout })));

const AdminDashboard = lazy(() => import('@/pages/workspaces/AdminDashboard'));
const UserManagement = lazy(() => import('@/pages/UserManagement').then(m => ({ default: m.UserManagement })));
const SystemSettings = lazy(() => import('@/pages/SystemSettings').then(m => ({ default: m.SystemSettings })));
const SystemHealth = lazy(() => import('@/pages/SystemHealth').then(m => ({ default: m.SystemHealth })));
const SecurityDashboard = lazy(() => import('@/pages/SecurityDashboard').then(m => ({ default: m.SecurityDashboard })));
const BackupRestore = lazy(() => import('@/pages/BackupRestore').then(m => ({ default: m.BackupRestore })));
const DataQuality = lazy(() => import('@/pages/DataQuality').then(m => ({ default: m.DataQuality })));
const ServerInfo = lazy(() => import('@/pages/ServerInfo').then(m => ({ default: m.ServerInfo })));
const AuditLog = lazy(() => import('@/pages/AuditLog').then(m => ({ default: m.AuditLog })));
const ImportExport = lazy(() => import('@/pages/ImportExport').then(m => ({ default: m.ImportExport })));
const DataDictionary = lazy(() => import('@/pages/DataDictionary').then(m => ({ default: m.DataDictionary })));
const DataValidation = lazy(() => import('@/pages/DataValidation').then(m => ({ default: m.DataValidation })));
const DataSync = lazy(() => import('@/pages/DataSync').then(m => ({ default: m.DataSync })));
const DataExportTemplates = lazy(() => import('@/pages/DataExportTemplates').then(m => ({ default: m.DataExportTemplates })));
const APIExplorer = lazy(() => import('@/pages/APIExplorer').then(m => ({ default: m.APIExplorer })));
const BatchOperations = lazy(() => import('@/pages/BatchOperations').then(m => ({ default: m.BatchOperations })));
const WorkflowAutomation = lazy(() => import('@/pages/WorkflowAutomation').then(m => ({ default: m.WorkflowAutomation })));
const LanguageSettings = lazy(() => import('@/pages/LanguageSettings').then(m => ({ default: m.LanguageSettings })));
const AISettings = lazy(() => import('@/pages/AISettings').then(m => ({ default: m.AISettings })));
const MobileApp = lazy(() => import('@/pages/MobileApp').then(m => ({ default: m.MobileApp })));
const OfflineMode = lazy(() => import('@/pages/OfflineMode').then(m => ({ default: m.OfflineMode })));
const TeamManagement = lazy(() => import('@/pages/TeamManagement').then(m => ({ default: m.TeamManagement })));
const ComplianceTracker = lazy(() => import('@/pages/ComplianceTracker').then(m => ({ default: m.ComplianceTracker })));
const CostAnalysis = lazy(() => import('@/pages/CostAnalysis').then(m => ({ default: m.CostAnalysis })));
const ProtocolLibrary = lazy(() => import('@/pages/ProtocolLibrary').then(m => ({ default: m.ProtocolLibrary })));
const ResourceAllocation = lazy(() => import('@/pages/ResourceAllocation').then(m => ({ default: m.ResourceAllocation })));
const ResourceCalendar = lazy(() => import('@/pages/ResourceCalendar').then(m => ({ default: m.ResourceCalendar })));
const BarcodeManagement = lazy(() => import('@/pages/BarcodeManagement'));
const BarcodeScanner = lazy(() => import('@/pages/BarcodeScanner').then(m => ({ default: m.BarcodeScanner })));

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

export const adminRoutes: RouteObject[] = [
  { path: '/admin/dashboard', element: wrap(AdminDashboard) },
  { path: '/users', element: wrap(UserManagement) },
  { path: '/system-settings', element: wrap(SystemSettings) },
  { path: '/system-health', element: wrap(SystemHealth) },
  { path: '/security', element: wrap(SecurityDashboard) },
  { path: '/backup', element: wrap(BackupRestore) },
  { path: '/dataquality', element: wrap(DataQuality) },
  { path: '/serverinfo', element: wrap(ServerInfo) },
  { path: '/auditlog', element: wrap(AuditLog) },
  { path: '/import-export', element: wrap(ImportExport) },
  { path: '/data-dictionary', element: wrap(DataDictionary) },
  { path: '/data-validation', element: wrap(DataValidation) },
  { path: '/data-sync', element: wrap(DataSync) },
  { path: '/export-templates', element: wrap(DataExportTemplates) },
  { path: '/api-explorer', element: wrap(APIExplorer) },
  { path: '/batch-operations', element: wrap(BatchOperations) },
  { path: '/workflows', element: wrap(WorkflowAutomation) },
  { path: '/languages', element: wrap(LanguageSettings) },
  { path: '/ai-settings', element: wrap(AISettings) },
  { path: '/mobile-app', element: wrap(MobileApp) },
  { path: '/offline', element: wrap(OfflineMode) },
  { path: '/team-management', element: wrap(TeamManagement) },
  { path: '/compliance', element: wrap(ComplianceTracker) },
  { path: '/cost-analysis', element: wrap(CostAnalysis) },
  { path: '/protocols', element: wrap(ProtocolLibrary) },
  { path: '/resource-allocation', element: wrap(ResourceAllocation) },
  { path: '/resource-calendar', element: wrap(ResourceCalendar) },
  { path: '/barcode', element: wrap(BarcodeManagement) },
  { path: '/scanner', element: wrap(BarcodeScanner) },
];

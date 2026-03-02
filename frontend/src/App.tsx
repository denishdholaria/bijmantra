import { Suspense } from 'react';
import { BrowserRouter as Router, useLocation, useRoutes } from 'react-router-dom';
import { ErrorBoundary, FallbackProps } from 'react-error-boundary';
import {
  breedingRoutes,
  seedOpsRoutes,
  genomicsRoutes,
  commercialRoutes,
  futureRoutes,
  adminRoutes,
  aiRoutes,
  coreRoutes,
  fieldRoutes,
  agronomyRoutes,
  weatherRoutes,
} from '@/routes';
import { BijMantraDesktop, SyncProvider } from '@/framework';
import { NotificationProvider } from '@/components/notifications/NotificationSystem';

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 m-4 max-w-lg mx-auto bg-white dark:bg-slate-900 shadow-xl border border-red-200 dark:border-red-900/50 rounded-xl relative z-[9999]">
      <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-full mb-4">
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-red-600 dark:text-red-400"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
      </div>
      <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-2">Application Error</h2>
      <p className="text-sm text-slate-600 dark:text-slate-400 break-words text-center mb-6">
        {error instanceof Error ? error.message : String(error)}
      </p>
      <button onClick={resetErrorBoundary} className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-6 py-2 rounded-lg transition-colors">
        Recover Session
      </button>
    </div>
  );
}

function PageSuspenseFallback() {
  return (
    <div className="flex items-center justify-center min-h-[50vh] w-full">
      <div className="flex flex-col items-center justify-center gap-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 dark:border-emerald-400"></div>
        <div className="text-sm text-slate-500 font-medium tracking-widest uppercase">Loading App Module...</div>
      </div>
    </div>
  );
}



function AppRoutes() {
  const element = useRoutes([
    ...coreRoutes,
    ...breedingRoutes,
    ...seedOpsRoutes,
    ...genomicsRoutes,
    ...commercialRoutes,
    ...futureRoutes,
    ...adminRoutes,
    ...aiRoutes,
    ...fieldRoutes,
    ...agronomyRoutes,
    ...weatherRoutes,
  ]);
  return element;
}

function AppLayout() {
  const location = useLocation();
  const isLogin = location.pathname === '/login';

  // Login page renders without shell
  if (isLogin) {
    return <AppRoutes />;
  }

  // Everything else renders inside the Web-OS Desktop Shell
  return (
    <BijMantraDesktop>
      <ErrorBoundary FallbackComponent={ErrorFallback} onReset={() => window.location.href = '/'}>
        <Suspense fallback={<PageSuspenseFallback />}>
          <AppRoutes />
        </Suspense>
      </ErrorBoundary>
    </BijMantraDesktop>
  );
}

function App() {
  return (
    <Router>
      <NotificationProvider>
        <SyncProvider>
          <AppLayout />
        </SyncProvider>
      </NotificationProvider>
    </Router>
  );
}

export default App;

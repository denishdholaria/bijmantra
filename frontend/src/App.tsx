import { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Navigate, useLocation, useRoutes } from 'react-router-dom';
import { ErrorBoundary, FallbackProps } from 'react-error-boundary';
import {
  breedingRoutes,
  seedOpsRoutes,
  genomicsRoutes,
  commercialRoutes,
  cropSystemsRoutes,
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
import { useAuthHydrated, useAuthStore } from '@/store/auth';

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div className="bg-shell-panel border-shell shadow-shell relative z-[9999] mx-auto m-4 flex max-w-lg flex-col items-center justify-center rounded-3xl border p-8 text-shell">
      <div className="mb-4 rounded-full bg-red-50 p-4 dark:bg-red-900/20">
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-red-600 dark:text-red-400"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
      </div>
      <h2 className="mb-2 text-xl font-bold text-shell">Application Error</h2>
      <p className="text-shell-muted mb-6 break-words text-center text-sm">
        {error instanceof Error ? error.message : String(error)}
      </p>
      <button type="button" onClick={resetErrorBoundary} className="rounded-2xl bg-prakruti-patta px-6 py-2 font-medium text-white transition-colors hover:bg-prakruti-patta-dark dark:bg-prakruti-patta dark:hover:bg-prakruti-patta-light dark:hover:text-prakruti-patta-dark">
        Recover Session
      </button>
    </div>
  );
}

function PageSuspenseFallback() {
  return (
    <div className="flex items-center justify-center min-h-[50vh] w-full">
      <div className="flex flex-col items-center justify-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-prakruti-patta dark:border-prakruti-patta-light"></div>
        <div className="text-shell-muted text-sm font-medium tracking-[0.3em] uppercase">Loading App Module...</div>
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
    ...cropSystemsRoutes,
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
  const hasHydrated = useAuthHydrated();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isAuthInitialized = useAuthStore((state) => state.isAuthInitialized);
  const isExternalAuthEnabled = useAuthStore((state) => state.isExternalAuthEnabled());
  const initializeAuth = useAuthStore((state) => state.initializeAuth);
  const loginWithIdentityProvider = useAuthStore((state) => state.loginWithIdentityProvider);
  const token = useAuthStore((state) => state.token);

  useEffect(() => {
    if (!hasHydrated) {
      return
    }

    if (isLogin && isExternalAuthEnabled) {
      return
    }

    void initializeAuth()
  }, [hasHydrated, initializeAuth, isExternalAuthEnabled, isLogin])

  useEffect(() => {
    if (isLogin || !hasHydrated || !isAuthInitialized || isAuthenticated || !isExternalAuthEnabled) {
      return
    }

    void loginWithIdentityProvider()
  }, [
    hasHydrated,
    isAuthInitialized,
    isAuthenticated,
    isExternalAuthEnabled,
    isLogin,
    loginWithIdentityProvider,
  ])

  // Login page renders without shell
  if (isLogin) {
    if (hasHydrated && isAuthInitialized && isAuthenticated && token) {
      return <Navigate to="/gateway" replace />;
    }

    return <AppRoutes />;
  }

  if (!hasHydrated || !isAuthInitialized) {
    return null;
  }

  if (!isAuthenticated || !token) {
    if (isExternalAuthEnabled) {
      return null;
    }

    return <Navigate to="/login" replace />;
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
          <div className="app-theme-bridge bg-page text-heading min-h-screen">
            <AppLayout />
          </div>
        </SyncProvider>
      </NotificationProvider>
    </Router>
  );
}

export default App;

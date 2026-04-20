import { lazy, Suspense } from 'react';
import type { ComponentType, LazyExoticComponent } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';

const Layout = lazy(() => import('@/components/Layout').then(m => ({ default: m.Layout })));

export function wrapWithAppShell(Component: LazyExoticComponent<any> | ComponentType) {
  return (
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
}
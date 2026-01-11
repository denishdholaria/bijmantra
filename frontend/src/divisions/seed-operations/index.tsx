/**
 * Seed Operations Division
 * 
 * Complete seed company workflow: LIMS, Processing, Inventory, Dispatch
 * Inspired by ProQRT patterns for seed industry operations.
 * Status: Active
 */

import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';

export default function SeedOperationsDivision() {
  return (
    <div className="seed-operations-division">
      <Suspense fallback={<LoadingFallback />}>
        <Outlet />
      </Suspense>
    </div>
  );
}

function LoadingFallback() {
  return (
    <div className="p-6 space-y-4">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-96" />
      <div className="grid md:grid-cols-4 gap-4 mt-6">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <div className="grid md:grid-cols-2 gap-4 mt-4">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}

export { seedOperationsRoutes } from './routes';

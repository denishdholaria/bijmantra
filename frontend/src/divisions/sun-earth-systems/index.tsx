/**
 * Sun-Earth Systems Division
 * 
 * Division 4: Solar radiation, magnetic field monitoring, and space weather.
 * Status: Visionary
 */

import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';

export default function SunEarthSystemsDivision() {
  return (
    <div className="sun-earth-systems-division">
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
      <div className="grid md:grid-cols-2 gap-4 mt-6">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    </div>
  );
}

export { sunEarthSystemsRoutes } from './routes';

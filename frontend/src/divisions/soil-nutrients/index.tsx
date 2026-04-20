import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';

export default function SoilNutrientsDivision() {
  return (
    <div className="soil-nutrients-division">
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
      <div className="grid gap-4 mt-6 md:grid-cols-2">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    </div>
  );
}

export { soilNutrientsRoutes } from './routes';
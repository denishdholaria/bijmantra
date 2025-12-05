/**
 * Plant Sciences Division
 * 
 * Main entry point for the Plant Sciences division.
 * This division covers breeding operations, genomics, molecular biology,
 * crop sciences, and soil/field environment.
 */

import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600" />
    </div>
  );
}

export default function PlantSciencesDivision() {
  return (
    <div className="plant-sciences-division">
      <Suspense fallback={<LoadingFallback />}>
        <Outlet />
      </Suspense>
    </div>
  );
}

// Re-export routes for use in main router
export { plantSciencesRoutes } from './routes';

/**
 * Phenomic Upload Page (Thin Adapter)
 * Routes to division-owned PhenomicUploadPanel
 * Part of Titanium Path convergence - pages are thin adapters only
 */

import { PhenomicUploadPanel } from '@/divisions/phenotyping/upload';

export function PhenomicUpload() {
  return <PhenomicUploadPanel />;
}

import { RouteObject } from 'react-router-dom';
import { FieldDashboard } from '@/pages/field/FieldDashboard';
import { FieldScan } from '@/pages/field/FieldScan';
import { FieldSync } from '@/pages/field/FieldSync';

export const fieldRoutes: RouteObject[] = [
  {
    path: '/field/dashboard',
    element: <FieldDashboard />
  },
  {
    path: '/field/scan',
    element: <FieldScan />
  },
  {
    path: '/field/sync',
    element: <FieldSync />
  }
];

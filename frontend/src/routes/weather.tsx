import { lazy, Suspense } from 'react';
import { RouteObject } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';

// Lazy load Layout to avoid circular/duplicate chunking
const Layout = lazy(() => import('@/components/Layout').then(m => ({ default: m.Layout })));

// Existing Pages
const Weather = lazy(() => import('@/pages/Weather').then(m => ({ default: m.Weather })));
const WeatherForecast = lazy(() => import('@/pages/WeatherForecast').then(m => ({ default: m.WeatherForecast })));

// New Pages
const WeatherStationManagement = lazy(() => import('@/pages/weather/WeatherStationManagement').then(m => ({ default: m.WeatherStationManagement })));

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

export const weatherRoutes: RouteObject[] = [
  { path: '/weather', element: wrap(Weather) },
  { path: '/weather-forecast', element: wrap(WeatherForecast) },
  { path: '/weather/stations', element: wrap(WeatherStationManagement) },
];

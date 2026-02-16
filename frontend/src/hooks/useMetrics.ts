/**
 * useMetrics - Single Source of Truth for Project Metrics
 * 
 * Fetches metrics from /api/v2/metrics which reads from /metrics.json (project root)
 * Use this hook anywhere you need to display project statistics.
 * 
 * FAILSAFE: If API fails, returns sensible defaults embedded in this file.
 */

import { useQuery } from '@tanstack/react-query';

const API_BASE = import.meta.env.VITE_API_URL || '';

// Failsafe defaults if API is unavailable
const FALLBACK_METRICS: AllMetrics = {
  lastUpdated: '2025-12-30',
  updatedBy: 'Fallback (API unavailable)',
  session: 0,
  version: {
    app: '1.0.0',
    brapi: '2.1',
    schema: '1.0.0',
  },
  pages: {
    total: 221,
    functional: 213,
    demo: 0,
    uiOnly: 0,
    removed: 12,
    note: 'Fallback data - API unavailable'
  },
  api: {
    totalEndpoints: 1370,
    brapiEndpoints: 201,
    brapiCoverage: 100,
    customEndpoints: 1169
  },
  database: {
    models: 106,
    migrations: 21,
    seeders: 15
  },
  modules: {
    total: 8,
    list: [
      { name: 'Breeding', pages: 35, endpoints: 120 },
      { name: 'Phenotyping', pages: 25, endpoints: 85 },
      { name: 'Genomics', pages: 35, endpoints: 107 },
      { name: 'Seed Bank', pages: 15, endpoints: 59 },
      { name: 'Environment', pages: 20, endpoints: 97 },
      { name: 'Seed Operations', pages: 22, endpoints: 96 },
      { name: 'Knowledge', pages: 5, endpoints: 35 },
      { name: 'Settings & Admin', pages: 35, endpoints: 79 }
    ]
  },
  workspaces: {
    total: 5,
    list: [
      { id: 'breeding', name: 'Plant Breeding', pages: 83 },
      { id: 'seed-ops', name: 'Seed Industry', pages: 22 },
      { id: 'research', name: 'Innovation Lab', pages: 28 },
      { id: 'genebank', name: 'Gene Bank', pages: 34 },
      { id: 'admin', name: 'Administration', pages: 25 }
    ]
  },
  build: {
    status: 'passing',
    pwaEntries: 116,
    sizeKB: 7960,
    sizeMB: '7.9MB'
  },
  milestones: {
    brapiComplete: '2025-12-23',
    gatewayComplete: '2025-12-26',
    prakrutiComplete: '2025-12-26',
    productionReady: '2025-12-25'
  },
  techStack: {
    frontend: ['React 18', 'TypeScript 5', 'Vite 5', 'Tailwind CSS', 'TanStack Query'],
    backend: ['Python 3.11', 'FastAPI', 'SQLAlchemy 2.0', 'Pydantic 2'],
    database: ['PostgreSQL 15', 'PostGIS', 'pgvector', 'Redis'],
    compute: ['Rust/WASM', 'Fortran']
  }
};

// Helper function for API calls
async function fetchMetrics<T>(endpoint: string): Promise<T> {
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch ${endpoint}`);
  }
  return response.json();
}

export interface PageMetrics {
  total: number;
  functional: number;
  demo: number;
  uiOnly: number;
  removed: number;
  note?: string;
}

export interface ApiMetrics {
  totalEndpoints: number;
  brapiEndpoints: number;
  brapiCoverage: number;
  customEndpoints: number;
}

export interface DatabaseMetrics {
  models: number;
  migrations: number;
  seeders: number;
}

export interface BuildMetrics {
  status: string;
  pwaEntries: number;
  sizeKB: number;
  sizeMB: string;
}

export interface ModuleInfo {
  name: string;
  pages: number;
  endpoints: number;
}

export interface WorkspaceInfo {
  id: string;
  name: string;
  pages: number;
}

export interface Milestones {
  brapiComplete: string;
  gatewayComplete: string;
  prakrutiComplete: string;
  productionReady: string;
}

export interface VersionInfo {
  app: string;
  brapi: string;
  schema: string;
  lastUpdated?: string;
}

export interface AllMetrics {
  lastUpdated: string;
  updatedBy: string;
  session: number;
  version?: VersionInfo;
  pages: PageMetrics;
  api: ApiMetrics;
  database: DatabaseMetrics;
  modules: {
    total: number;
    list: ModuleInfo[];
  };
  workspaces: {
    total: number;
    list: WorkspaceInfo[];
  };
  build: BuildMetrics;
  milestones: Milestones;
  techStack: {
    frontend: string[];
    backend: string[];
    database: string[];
    compute: string[];
  };
}

export interface MetricsSummary {
  pages: number;
  functionalPercent: number;
  endpoints: number;
  brapiCoverage: number;
  models: number;
  modules: number;
  workspaces: number;
  buildStatus: string;
}

// API functions
const metricsApi = {
  getAll: async (): Promise<AllMetrics> => {
    return fetchMetrics<AllMetrics>('/api/v2/metrics');
  },
  
  getSummary: async (): Promise<MetricsSummary> => {
    return fetchMetrics<MetricsSummary>('/api/v2/metrics/summary');
  },
  
  getPages: async (): Promise<PageMetrics> => {
    return fetchMetrics<PageMetrics>('/api/v2/metrics/pages');
  },
  
  getApi: async (): Promise<ApiMetrics> => {
    return fetchMetrics<ApiMetrics>('/api/v2/metrics/api');
  },
  
  getDatabase: async (): Promise<DatabaseMetrics> => {
    return fetchMetrics<DatabaseMetrics>('/api/v2/metrics/database');
  },
  
  getBuild: async (): Promise<BuildMetrics> => {
    return fetchMetrics<BuildMetrics>('/api/v2/metrics/build');
  },
  
  getModules: async () => {
    return fetchMetrics('/api/v2/metrics/modules');
  },
  
  getWorkspaces: async () => {
    return fetchMetrics('/api/v2/metrics/workspaces');
  },
  
  getMilestones: async (): Promise<Milestones> => {
    return fetchMetrics<Milestones>('/api/v2/metrics/milestones');
  },
  
  getTechStack: async () => {
    return fetchMetrics('/api/v2/metrics/tech-stack');
  },
  
  getVersion: async (): Promise<VersionInfo> => {
    return fetchMetrics<VersionInfo>('/api/v2/metrics/version');
  },
};

// Hooks with failsafe fallback data
export function useMetrics() {
  return useQuery({
    queryKey: ['metrics', 'all'],
    queryFn: metricsApi.getAll,
    staleTime: 5 * 60 * 1000, // 5 minutes
    placeholderData: FALLBACK_METRICS,
    retry: 2,
  });
}

export function useMetricsSummary() {
  const fallbackSummary: MetricsSummary = {
    pages: FALLBACK_METRICS.pages.total,
    functionalPercent: Math.round((FALLBACK_METRICS.pages.functional / FALLBACK_METRICS.pages.total) * 100),
    endpoints: FALLBACK_METRICS.api.totalEndpoints,
    brapiCoverage: FALLBACK_METRICS.api.brapiCoverage,
    models: FALLBACK_METRICS.database.models,
    modules: FALLBACK_METRICS.modules.total,
    workspaces: FALLBACK_METRICS.workspaces.total,
    buildStatus: FALLBACK_METRICS.build.status,
  };
  
  return useQuery({
    queryKey: ['metrics', 'summary'],
    queryFn: metricsApi.getSummary,
    staleTime: 5 * 60 * 1000,
    placeholderData: fallbackSummary,
    retry: 2,
  });
}

export function usePageMetrics() {
  return useQuery({
    queryKey: ['metrics', 'pages'],
    queryFn: metricsApi.getPages,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK_METRICS.pages,
    retry: 2,
  });
}

export function useApiMetrics() {
  return useQuery({
    queryKey: ['metrics', 'api'],
    queryFn: metricsApi.getApi,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK_METRICS.api,
    retry: 2,
  });
}

export function useDatabaseMetrics() {
  return useQuery({
    queryKey: ['metrics', 'database'],
    queryFn: metricsApi.getDatabase,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK_METRICS.database,
    retry: 2,
  });
}

export function useBuildMetrics() {
  return useQuery({
    queryKey: ['metrics', 'build'],
    queryFn: metricsApi.getBuild,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK_METRICS.build,
    retry: 2,
  });
}

export function useModuleMetrics() {
  return useQuery({
    queryKey: ['metrics', 'modules'],
    queryFn: metricsApi.getModules,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK_METRICS.modules,
    retry: 2,
  });
}

export function useWorkspaceMetrics() {
  return useQuery({
    queryKey: ['metrics', 'workspaces'],
    queryFn: metricsApi.getWorkspaces,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK_METRICS.workspaces,
    retry: 2,
  });
}

export function useMilestones() {
  return useQuery({
    queryKey: ['metrics', 'milestones'],
    queryFn: metricsApi.getMilestones,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK_METRICS.milestones,
    retry: 2,
  });
}

export function useTechStack() {
  return useQuery({
    queryKey: ['metrics', 'tech-stack'],
    queryFn: metricsApi.getTechStack,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK_METRICS.techStack,
    retry: 2,
  });
}

export function useVersion() {
  const fallbackVersion: VersionInfo = {
    app: '1.0.0',
    brapi: '2.1',
    schema: '1.0.0',
  };
  
  return useQuery({
    queryKey: ['metrics', 'version'],
    queryFn: metricsApi.getVersion,
    staleTime: 5 * 60 * 1000,
    placeholderData: fallbackVersion,
    retry: 2,
  });
}

// Export fallback for use in other components
export { FALLBACK_METRICS };

// Utility: Format percentage
export function formatPercent(value: number, total: number): string {
  return `${Math.round((value / total) * 100)}%`;
}

// Utility: Get status color
export function getStatusColor(percent: number): string {
  if (percent >= 90) return 'text-green-600';
  if (percent >= 70) return 'text-yellow-600';
  return 'text-red-600';
}

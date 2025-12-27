/**
 * useMetrics - Single Source of Truth for Project Metrics
 * 
 * Fetches metrics from /api/v2/metrics which reads from .kiro/metrics.json
 * Use this hook anywhere you need to display project statistics.
 */

import { useQuery } from '@tanstack/react-query';

const API_BASE = import.meta.env.VITE_API_URL || '';

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

export interface AllMetrics {
  lastUpdated: string;
  updatedBy: string;
  session: number;
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
};

// Hooks
export function useMetrics() {
  return useQuery({
    queryKey: ['metrics', 'all'],
    queryFn: metricsApi.getAll,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useMetricsSummary() {
  return useQuery({
    queryKey: ['metrics', 'summary'],
    queryFn: metricsApi.getSummary,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePageMetrics() {
  return useQuery({
    queryKey: ['metrics', 'pages'],
    queryFn: metricsApi.getPages,
    staleTime: 5 * 60 * 1000,
  });
}

export function useApiMetrics() {
  return useQuery({
    queryKey: ['metrics', 'api'],
    queryFn: metricsApi.getApi,
    staleTime: 5 * 60 * 1000,
  });
}

export function useDatabaseMetrics() {
  return useQuery({
    queryKey: ['metrics', 'database'],
    queryFn: metricsApi.getDatabase,
    staleTime: 5 * 60 * 1000,
  });
}

export function useBuildMetrics() {
  return useQuery({
    queryKey: ['metrics', 'build'],
    queryFn: metricsApi.getBuild,
    staleTime: 5 * 60 * 1000,
  });
}

export function useModuleMetrics() {
  return useQuery({
    queryKey: ['metrics', 'modules'],
    queryFn: metricsApi.getModules,
    staleTime: 5 * 60 * 1000,
  });
}

export function useWorkspaceMetrics() {
  return useQuery({
    queryKey: ['metrics', 'workspaces'],
    queryFn: metricsApi.getWorkspaces,
    staleTime: 5 * 60 * 1000,
  });
}

export function useMilestones() {
  return useQuery({
    queryKey: ['metrics', 'milestones'],
    queryFn: metricsApi.getMilestones,
    staleTime: 5 * 60 * 1000,
  });
}

export function useTechStack() {
  return useQuery({
    queryKey: ['metrics', 'tech-stack'],
    queryFn: metricsApi.getTechStack,
    staleTime: 5 * 60 * 1000,
  });
}

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

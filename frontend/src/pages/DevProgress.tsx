/**
 * DevProgress Page
 *
 * Displays development progress across divisions, features, and roadmap.
 * Shows Past (completed), Present (in-progress), and Future (planned) items.
 * Named "DevProgress" to distinguish from other progress tracking features
 * (e.g., breeding program progress, trial progress).
 * 
 * METRICS: Uses useMetrics() hook which reads from /metrics.json via /api/v2/metrics
 * This ensures all metrics come from the SINGLE SOURCE OF TRUTH.
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  CheckCircle2,
  Clock,
  Calendar,
  Layers,
  Code2,
  FileCode,
  Server,
  Cpu,
  Database,
  Rocket,
  TrendingUp,
} from 'lucide-react';
import { useMetrics, type AllMetrics } from '@/hooks/useMetrics';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ProgressData {
  summary: {
    total_endpoints: number;
    total_pages: number;
    total_divisions: number;
    completed_features: number;
    in_progress_features: number;
    planned_features: number;
    divisions_complete: number;
    last_updated: string;
  };
  divisions: Array<{
    id: string;
    name: string;
    status: string;
    progress: number;
    endpoints: number;
    pages: number;
    notes?: string;
  }>;
  recent_features: Array<{
    id: string;
    name: string;
    description: string;
    status: string;
    completed_date?: string;
    priority?: string;
    endpoints?: number;
    tags: string[];
  }>;
  roadmap: Array<{
    quarter: string;
    title: string;
    items: string[];
    status: string;
  }>;
  api_stats: {
    brapi_endpoints: number;
    custom_endpoints: number;
    total_endpoints: number;
  };
  tech_stack: {
    frontend: string[];
    backend: string[];
    database: string[];
    compute: string[];
  };
}


const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-green-500',
  'in-progress': 'bg-blue-500',
  planned: 'bg-amber-500',
  backlog: 'bg-gray-400',
};

const STATUS_BADGES: Record<string, { variant: 'default' | 'secondary' | 'outline'; label: string }> = {
  completed: { variant: 'default', label: '✅ Completed' },
  'in-progress': { variant: 'secondary', label: '🔄 In Progress' },
  planned: { variant: 'outline', label: '📋 Planned' },
  backlog: { variant: 'outline', label: '📝 Backlog' },
};

/**
 * Build fallback data from metrics structure.
 * This ensures fallback values match metrics.json schema.
 * Values here are defaults - actual data comes from /api/v2/progress
 */
function buildFallbackData(metrics?: AllMetrics): ProgressData {
  // Use metrics if available, otherwise use sensible defaults matching metrics.json
  const pages = metrics?.pages || { total: 220, functional: 207, demo: 0, uiOnly: 5 };
  const api = metrics?.api || { totalEndpoints: 1344, brapiEndpoints: 201, customEndpoints: 1143 };
  const modules = metrics?.modules || { total: 8, list: [] };
  const techStack = metrics?.techStack || {
    frontend: ['React 18', 'TypeScript 5', 'Tailwind CSS', 'shadcn/ui', 'TanStack Query', 'ECharts'],
    backend: ['Python 3.11', 'FastAPI', 'SQLAlchemy 2.0', 'Pydantic 2'],
    database: ['PostgreSQL 15', 'PostGIS', 'pgvector', 'Redis'],
    compute: ['Rust/WASM', 'Fortran'],
  };

  // Build divisions from modules
  const divisions = (modules.list || []).map((mod, i) => ({
    id: `div-${i + 1}`,
    name: mod.name,
    status: 'completed',
    progress: 100,
    endpoints: mod.endpoints,
    pages: mod.pages,
  }));

  return {
    summary: {
      total_endpoints: api.totalEndpoints,
      total_pages: pages.total,
      total_divisions: modules.total,
      completed_features: 7,
      in_progress_features: 0,
      planned_features: 0,
      divisions_complete: modules.total,
      last_updated: metrics?.lastUpdated || '2025-12-29',
    },
    divisions: divisions.length > 0 ? divisions : [
      { id: 'div-1', name: 'Breeding', status: 'completed', progress: 100, endpoints: 120, pages: 35 },
      { id: 'div-2', name: 'Phenotyping', status: 'completed', progress: 100, endpoints: 85, pages: 25 },
      { id: 'div-3', name: 'Genomics', status: 'completed', progress: 100, endpoints: 107, pages: 35 },
      { id: 'div-4', name: 'Seed Bank', status: 'completed', progress: 100, endpoints: 59, pages: 15 },
      { id: 'div-5', name: 'Environment', status: 'completed', progress: 100, endpoints: 97, pages: 20 },
      { id: 'div-6', name: 'Seed Operations', status: 'completed', progress: 100, endpoints: 96, pages: 22 },
      { id: 'div-7', name: 'Knowledge', status: 'completed', progress: 100, endpoints: 35, pages: 5 },
      { id: 'div-8', name: 'Settings & Admin', status: 'completed', progress: 100, endpoints: 79, pages: 35 },
    ],
    recent_features: [
      { id: 'feat-myworkspace', name: 'MyWorkspace Custom Workspaces', description: 'Users can create personalized workspaces with selected pages', status: 'completed', completed_date: '2025-12-29', tags: ['frontend', 'ux'] },
      { id: 'feat-gateway-refinements', name: 'Gateway Refinements', description: 'Auto-advance carousel, error boundary, sync loading state', status: 'completed', completed_date: '2025-12-29', tags: ['frontend', 'ux'] },
      { id: 'feat-admin-demo', name: 'Admin/Demo Separation', description: 'Server-determined is_demo flag, proper organization isolation', status: 'completed', completed_date: '2025-12-29', tags: ['backend', 'security'] },
      { id: 'feat-prakruti', name: 'Prakruti Design System', description: 'Complete design system with Hindi-named colors', status: 'completed', completed_date: '2025-12-26', tags: ['frontend', 'design'] },
      { id: 'feat-gateway', name: 'Gateway-Workspace Architecture', description: '5 workspaces, gateway page, sidebar filtering', status: 'completed', completed_date: '2025-12-26', tags: ['frontend', 'navigation'] },
      { id: 'feat-mock-migration', name: 'Mock Data Migration Complete', description: 'Zero in-memory mock data, all seeders working', status: 'completed', completed_date: '2025-12-26', tags: ['backend', 'database'] },
      { id: 'feat-brapi-100', name: 'BrAPI v2.1 100% Complete', description: 'All 201 BrAPI v2.1 endpoints implemented', status: 'completed', completed_date: '2025-12-23', endpoints: 201, tags: ['backend', 'brapi', 'milestone'] },
    ],
    roadmap: [
      { quarter: 'Q1 2026', title: 'Preview Phase & Early Adopters', items: ['Fix demo data pages', 'Real computation implementation', '80% test coverage', 'Production deployment'], status: 'in-progress' },
      { quarter: 'Q2 2026', title: 'Mobile & Offline', items: ['React Native mobile app', 'Enhanced offline sync', 'Voice data entry'], status: 'planned' },
      { quarter: 'Q3 2026', title: 'AI & Analytics', items: ['AI crop recommendations', 'Predictive analytics', 'Computer vision models'], status: 'planned' },
      { quarter: 'Q4 2026', title: 'Enterprise Features', items: ['Multi-tenant SaaS', 'Advanced RBAC', 'Custom reporting'], status: 'backlog' },
    ],
    api_stats: { 
      brapi_endpoints: api.brapiEndpoints, 
      custom_endpoints: api.customEndpoints, 
      total_endpoints: api.totalEndpoints 
    },
    tech_stack: techStack,
  };
}

function DevProgress() {
  const [activeTab, setActiveTab] = useState('overview');
  const [currentTime, setCurrentTime] = useState(new Date());

  // Live clock - updates every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch metrics from single source of truth
  const { data: metricsData } = useMetrics();

  const { data, isLoading } = useQuery<ProgressData>({
    queryKey: ['progress'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/v2/progress`);
      if (!response.ok) throw new Error('Failed to fetch progress data');
      return response.json();
    },
    retry: 1,
    staleTime: 60000, // Cache for 1 minute
  });

  // Build fallback from metrics (single source of truth)
  const fallbackData = buildFallbackData(metricsData);
  
  // Use API data if available, otherwise use metrics-based fallback
  const progressData = data || fallbackData;
  const isUsingFallback = !data;

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  const { summary, divisions, recent_features, roadmap, api_stats, tech_stack } = progressData;

  return (
    <div className="p-6 space-y-6">
      {/* Fallback Notice */}
      {isUsingFallback && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-3 text-center text-amber-700 text-sm">
            ⚠️ Backend unavailable — showing cached data. Start the backend for live updates.
          </CardContent>
        </Card>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <TrendingUp className="h-6 w-6" />
            Development Progress
          </h1>
          <p className="text-muted-foreground text-sm">
            Data from: {summary.last_updated} • Now: {currentTime.toLocaleString()}
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          Bijmantra preview-1
        </Badge>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <Server className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{summary.total_endpoints}</p>
                <p className="text-xs text-muted-foreground">API Endpoints</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <FileCode className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{summary.total_pages}+</p>
                <p className="text-xs text-muted-foreground">Frontend Pages</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <Layers className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{summary.divisions_complete}/{summary.total_divisions}</p>
                <p className="text-xs text-muted-foreground">Divisions Complete</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 dark:bg-amber-900 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{summary.completed_features}</p>
                <p className="text-xs text-muted-foreground">Features Done</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="divisions">Divisions</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
          <TabsTrigger value="roadmap">Roadmap</TabsTrigger>
          <TabsTrigger value="tech">Tech Stack</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Divisions Progress */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="h-4 w-4" />
                  Division Progress
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {divisions.slice(0, 6).map((div) => (
                  <div key={div.id} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>{div.name}</span>
                      <span className="text-muted-foreground">{div.progress}%</span>
                    </div>
                    <Progress value={div.progress} className="h-2" />
                  </div>
                ))}
                {divisions.length > 6 && (
                  <Button variant="ghost" size="sm" onClick={() => setActiveTab('divisions')}>
                    View all {divisions.length} divisions →
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Recent Features */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Rocket className="h-4 w-4" />
                  Recent Features
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {recent_features.slice(0, 5).map((feature) => (
                  <div key={feature.id} className="flex items-start gap-2 py-1">
                    <div className={`w-2 h-2 rounded-full mt-1.5 ${STATUS_COLORS[feature.status]}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{feature.name}</p>
                      <p className="text-xs text-muted-foreground truncate">{feature.description}</p>
                    </div>
                    {feature.completed_date && (
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {feature.completed_date}
                      </span>
                    )}
                  </div>
                ))}
                <Button variant="ghost" size="sm" onClick={() => setActiveTab('features')}>
                  View all features →
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* API Stats */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Code2 className="h-4 w-4" />
                API Statistics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-green-600">{api_stats.brapi_endpoints}</p>
                  <p className="text-xs text-muted-foreground">BrAPI Endpoints</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-blue-600">{api_stats.custom_endpoints}</p>
                  <p className="text-xs text-muted-foreground">Custom Endpoints</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{api_stats.total_endpoints}</p>
                  <p className="text-xs text-muted-foreground">Total Endpoints</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Divisions Tab */}
        <TabsContent value="divisions" className="space-y-4">
          <div className="grid gap-4">
            {divisions.map((div) => (
              <Card key={div.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${div.progress === 100 ? 'bg-green-500' : div.progress > 0 ? 'bg-blue-500' : 'bg-gray-400'}`} />
                      <h3 className="font-medium">{div.name}</h3>
                    </div>
                    <Badge variant={div.progress === 100 ? 'default' : 'secondary'}>
                      {div.progress}%
                    </Badge>
                  </div>
                  <Progress value={div.progress} className="h-2 mb-3" />
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Server className="h-3 w-3" />
                      {div.endpoints} endpoints
                    </span>
                    <span className="flex items-center gap-1">
                      <FileCode className="h-3 w-3" />
                      {div.pages} pages
                    </span>
                    {div.notes && (
                      <span className="text-xs italic">{div.notes}</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Features Tab */}
        <TabsContent value="features" className="space-y-4">
          {/* Feature Status Filter */}
          <div className="flex gap-2 flex-wrap">
            {Object.entries(STATUS_BADGES).map(([status, { variant, label }]) => {
              const count = recent_features.filter(f => f.status === status).length;
              return (
                <Badge key={status} variant={variant} className="cursor-default">
                  {label} ({count})
                </Badge>
              );
            })}
          </div>

          {/* Completed Features */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Completed (Past)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {recent_features.filter(f => f.status === 'completed').map((feature) => (
                <div key={feature.id} className="flex items-start gap-3 py-2 border-b last:border-0">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{feature.name}</span>
                      {feature.endpoints && feature.endpoints > 0 && (
                        <Badge variant="outline" className="text-xs">
                          {feature.endpoints} endpoints
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {feature.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {feature.completed_date && (
                        <span className="text-xs text-muted-foreground ml-auto">
                          {feature.completed_date}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* In Progress Features */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4 text-blue-500" />
                In Progress (Present)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {recent_features.filter(f => f.status === 'in-progress').length === 0 ? (
                <p className="text-sm text-muted-foreground py-2">No features currently in progress</p>
              ) : (
                recent_features.filter(f => f.status === 'in-progress').map((feature) => (
                  <div key={feature.id} className="flex items-start gap-3 py-2 border-b last:border-0">
                    <Clock className="h-4 w-4 text-blue-500 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{feature.name}</span>
                        {feature.priority && (
                          <Badge variant={feature.priority === 'high' ? 'destructive' : 'outline'} className="text-xs">
                            {feature.priority}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{feature.description}</p>
                      <div className="flex items-center gap-2 mt-1">
                        {feature.tags.map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Planned Features */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4 text-amber-500" />
                Planned (Future)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {recent_features.filter(f => f.status === 'planned').map((feature) => (
                <div key={feature.id} className="flex items-start gap-3 py-2 border-b last:border-0">
                  <Calendar className="h-4 w-4 text-amber-500 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{feature.name}</span>
                      {feature.priority && (
                        <Badge variant={feature.priority === 'high' ? 'destructive' : 'outline'} className="text-xs">
                          {feature.priority}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {feature.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Roadmap Tab */}
        <TabsContent value="roadmap" className="space-y-4">
          <div className="grid gap-4">
            {roadmap.map((item, index) => (
              <Card key={item.quarter} className={item.status === 'completed' ? 'border-green-200 dark:border-green-800' : ''}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                        item.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                        item.status === 'in-progress' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' :
                        'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                      }`}>
                        {index + 1}
                      </div>
                      <div>
                        <span className="text-muted-foreground text-sm">{item.quarter}</span>
                        <p className="font-medium">{item.title}</p>
                      </div>
                    </CardTitle>
                    <Badge variant={
                      item.status === 'completed' ? 'default' :
                      item.status === 'in-progress' ? 'secondary' : 'outline'
                    }>
                      {item.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1">
                    {item.items.map((task, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <div className={`w-1.5 h-1.5 rounded-full ${
                          item.status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                        }`} />
                        {task}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Tech Stack Tab */}
        <TabsContent value="tech" className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileCode className="h-4 w-4 text-blue-500" />
                  Frontend
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {tech_stack.frontend.map((tech) => (
                    <Badge key={tech} variant="secondary">{tech}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Server className="h-4 w-4 text-green-500" />
                  Backend
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {tech_stack.backend.map((tech) => (
                    <Badge key={tech} variant="secondary">{tech}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Database className="h-4 w-4 text-purple-500" />
                  Database
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {tech_stack.database.map((tech) => (
                    <Badge key={tech} variant="secondary">{tech}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-orange-500" />
                  Compute Engines
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {tech_stack.compute.map((tech) => (
                    <Badge key={tech} variant="secondary">{tech}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Architecture Overview */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Architecture Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground space-y-2">
                <p>Bijmantra is built on the Parashakti Framework — a modular architecture with offline capabilities designed for agricultural research.</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{summary.total_divisions}</p>
                    <p className="text-xs">Divisions</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{summary.total_endpoints}</p>
                    <p className="text-xs">API Endpoints</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{summary.total_pages}+</p>
                    <p className="text-xs">Frontend Pages</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">100%</p>
                    <p className="text-xs">Open Source</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export { DevProgress };

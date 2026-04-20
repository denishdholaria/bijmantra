/**
 * Admin Dashboard
 * 
 * Workspace-specific dashboard for Administration workspace.
 * Shows system health, user activity, audit summary, and pending tasks.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Link } from 'react-router-dom';
import { 
  Settings, Activity, Users, Shield,
  ArrowRight,
  Database, HardDrive, Clock, FileText, Bot, Cpu
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useHydratedSuperuserQueryAccess } from '@/store/auth';

interface ActivityLog {
  id: string;
  action: string;
  actor: string | null;
  timestamp: string;
  category: string;
}

type ServiceState = 'healthy' | 'degraded' | 'unavailable';

function formatRoutingLabel(value: string) {
  return value.replace(/_/g, ' ');
}

function normalizeServiceState(status?: string): ServiceState {
  if (!status) {
    return 'unavailable';
  }

  const normalized = status.toLowerCase();

  if (['healthy', 'connected', 'running', 'ok'].includes(normalized)) {
    return 'healthy';
  }

  if (['degraded', 'warning'].includes(normalized)) {
    return 'degraded';
  }

  return 'unavailable';
}

function getServiceBadgeClass(state: ServiceState) {
  if (state === 'healthy') {
    return 'bg-green-100 text-green-800';
  }

  if (state === 'degraded') {
    return 'bg-amber-100 text-amber-800';
  }

  return 'bg-slate-100 text-slate-800';
}

function getServiceLabel(state: ServiceState) {
  if (state === 'healthy') {
    return 'Healthy';
  }

  if (state === 'degraded') {
    return 'Degraded';
  }

  return 'Unavailable';
}

export function AdminDashboard() {
  const canQueryAdminRuntime = useHydratedSuperuserQueryAccess();

  // Fetch System Status
  const { data: statusData } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => apiClient.systemSettingsService.getSystemStatus()
  })

  // Fetch Team Stats (for active users)
  const { data: teamStats } = useQuery({
    queryKey: ['team-stats'],
    queryFn: () => apiClient.teamManagementService.getStats()
  })

  // Fetch Pending Invites count
  const { data: invitesData } = useQuery({
    queryKey: ['pending-invites'],
    queryFn: () => apiClient.teamManagementService.getInvites('pending')
  })

  // Fetch Storage/API Settings
  const { data: apiSettings } = useQuery({
    queryKey: ['api-settings'],
    queryFn: () => apiClient.systemSettingsService.getAPISettings()
  })

  // Fetch Recent Activity
  const { data: activityData } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: () => apiClient.auditLogService.getEntries({ limit: 5 })
  })

  const { data: aiHealth } = useQuery({
    queryKey: ['chat-health'],
    queryFn: () => apiClient.chatHealthService.getChatHealth(),
    enabled: canQueryAdminRuntime,
    retry: false,
  })

  const { data: aiMetrics } = useQuery({
    queryKey: ['chat-metrics'],
    queryFn: () => apiClient.chatHealthService.getChatMetrics(),
    enabled: canQueryAdminRuntime,
    retry: false,
  })

  const { data: aiDiagnostics } = useQuery({
    queryKey: ['chat-diagnostics'],
    queryFn: () => apiClient.chatHealthService.getChatDiagnostics(),
    enabled: canQueryAdminRuntime,
    retry: false,
  })

  const serviceHealth = statusData?.service_health ?? {}
  const normalizedServiceStates = Object.values(serviceHealth).map((status) => normalizeServiceState(status))
  const systemStatus: ServiceState = normalizedServiceStates.length === 0
    ? 'unavailable'
    : normalizedServiceStates.every((state) => state === 'healthy')
      ? 'healthy'
      : normalizedServiceStates.some((state) => state === 'degraded')
        ? 'degraded'
        : 'unavailable'
  const activeUsers = teamStats?.active_users || 0
  const pendingApprovals = invitesData?.length || 0
  const recentActivity = (activityData?.entries || []) as unknown as ActivityLog[]
  const aiRuntimeHealthy = aiHealth?.llm_enabled ?? false
  const aiLatencyP50Ms = aiMetrics?.latency?.total?.p50 ? Math.round(aiMetrics.latency.total.p50 * 1000) : null
  const topPolicyFlags = (aiDiagnostics?.policy_flags || []).slice(0, 3)
  const topRoutingDecisions = (aiDiagnostics?.routing_decisions || []).slice(0, 3)
  const safeFailureCount = (aiDiagnostics?.safe_failures || []).reduce((sum, item) => sum + item.count, 0)
  const providerLatencies = aiDiagnostics?.provider_latencies || []
  const providerStatuses = aiDiagnostics?.request_statuses || []
  const routingState = aiDiagnostics?.routing_state
  const uploadLimitMb = apiSettings?.max_upload_size ?? null
  const systemHealthCards = [
    {
      key: 'database',
      title: 'Database',
      description: 'Primary database connection',
      icon: Database,
      state: normalizeServiceState(serviceHealth.database),
    },
    {
      key: 'api_server',
      title: 'API Server',
      description: 'FastAPI runtime status',
      icon: Activity,
      state: normalizeServiceState(serviceHealth.api_server),
    },
    {
      key: 'task_queue',
      title: 'Task Queue',
      description: `Pending ${statusData?.task_queue?.pending ?? 0} • Running ${statusData?.task_queue?.running ?? 0}`,
      icon: Clock,
      state: normalizeServiceState(serviceHealth.task_queue),
    },
    {
      key: 'event_bus',
      title: 'Event Bus',
      description: `${statusData?.event_bus?.total_events ?? 0} active subscriptions`,
      icon: HardDrive,
      state: normalizeServiceState(serviceHealth.event_bus),
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="h-6 w-6 text-slate-600" />
            Administration Dashboard
          </h1>
          <p className="text-muted-foreground">
            System management, users, and configuration
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/users">
              <Users className="h-4 w-4 mr-2" />
              Manage Users
            </Link>
          </Button>
          <Button asChild>
            <Link to="/system-settings">
              <Settings className="h-4 w-4 mr-2" />
              System Settings
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className={systemStatus === 'healthy' ? 'border-green-200 bg-green-50/50 dark:bg-green-950/20' : systemStatus === 'degraded' ? 'border-amber-200 bg-amber-50/50 dark:bg-amber-950/20' : 'border-slate-200 bg-slate-50/50 dark:bg-slate-950/20'}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Activity className={`h-4 w-4 ${systemStatus === 'healthy' ? 'text-green-600' : systemStatus === 'degraded' ? 'text-amber-600' : 'text-slate-600'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{systemStatus}</div>
            <p className="text-xs text-muted-foreground">
              {systemStatus === 'healthy'
                ? 'All reported services are healthy'
                : systemStatus === 'degraded'
                  ? 'One or more reported services need attention'
                  : 'Live service status is not available'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeUsers}</div>
            <p className="text-xs text-muted-foreground">Online now</p>
          </CardContent>
        </Card>

        <Card className={pendingApprovals > 0 ? 'border-amber-200 bg-amber-50/50 dark:bg-amber-950/20' : ''}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            <Clock className={`h-4 w-4 ${pendingApprovals > 0 ? 'text-amber-600' : 'text-muted-foreground'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingApprovals}</div>
            <p className="text-xs text-muted-foreground">Awaiting action</p>
          </CardContent>
        </Card>

        <Card className={uploadLimitMb === null ? 'border-slate-200 bg-slate-50/50 dark:bg-slate-950/20' : ''}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Storage Telemetry</CardTitle>
            <HardDrive className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{uploadLimitMb === null ? 'Unavailable' : `${uploadLimitMb} MB`}</div>
            <p className="mt-2 text-xs text-muted-foreground">
              {uploadLimitMb === null ? 'Storage telemetry is not connected on this dashboard' : 'Current max upload limit from system settings'}
            </p>
          </CardContent>
        </Card>

        <Card className={aiRuntimeHealthy ? 'border-emerald-200 bg-emerald-50/50 dark:bg-emerald-950/20' : 'border-amber-200 bg-amber-50/50 dark:bg-amber-950/20'}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">AI Runtime</CardTitle>
            <Cpu className={`h-4 w-4 ${aiRuntimeHealthy ? 'text-emerald-600' : 'text-amber-600'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{aiHealth?.active_provider || 'unknown'}</div>
            <p className="text-xs text-muted-foreground">
              {aiHealth?.active_model || 'No active model'}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge className={aiRuntimeHealthy ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}>
                {aiRuntimeHealthy ? 'LLM Enabled' : 'Template Fallback'}
              </Badge>
              {aiLatencyP50Ms !== null ? <Badge variant="outline">P50 {aiLatencyP50Ms}ms</Badge> : null}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">System Health</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/system-health">
                  View Details <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Service status overview</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {systemHealthCards.map((service) => {
                const Icon = service.icon

                return (
                  <div key={service.key} className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50">
                    <div className="flex items-center gap-3">
                      <div className={`rounded-lg p-2 ${service.state === 'healthy' ? 'bg-green-100 dark:bg-green-900/30' : service.state === 'degraded' ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-slate-100 dark:bg-slate-900/30'}`}>
                        <Icon className={`h-4 w-4 ${service.state === 'healthy' ? 'text-green-600' : service.state === 'degraded' ? 'text-amber-600' : 'text-slate-600'}`} />
                      </div>
                      <div>
                        <div className="font-medium">{service.title}</div>
                        <div className="text-sm text-muted-foreground">
                          {service.state === 'unavailable' ? 'Detailed service telemetry is not available on this dashboard yet.' : service.description}
                        </div>
                      </div>
                    </div>
                    <Badge className={getServiceBadgeClass(service.state)}>{getServiceLabel(service.state)}</Badge>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Recent Activity</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/auditlog">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Audit log summary</CardDescription>
          </CardHeader>
            <CardContent>
             <div className="space-y-3">
               {(recentActivity || []).map((log) => (
                 <div key={log.id} className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                   <div>
                     <div className="font-medium">{log.action}</div>
                     <div className="text-sm text-muted-foreground">
                       {log.actor || 'System'} • {new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                     </div>
                   </div>
                   <Badge variant="outline">{log.category}</Badge>
                 </div>
               ))}
               {(!recentActivity || recentActivity.length === 0) && (
                 <div className="text-center py-4 text-muted-foreground">No recent activity</div>
               )}
             </div>
           </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">AI Diagnostics</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/ai-settings">
                View Runtime <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </div>
          <CardDescription>Routing, validation, and safe-failure signals for REEVU operators</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border p-4">
              <div className="text-sm font-medium text-muted-foreground">Request Outcomes</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {providerStatuses.length ? providerStatuses.map(item => (
                  <Badge key={item.status} variant="outline">
                    {item.status}: {item.count}
                  </Badge>
                )) : <span className="text-sm text-muted-foreground">No request telemetry yet</span>}
              </div>
              <div className="mt-3 text-sm text-muted-foreground">
                Safe failures observed: {safeFailureCount}
              </div>
            </div>

            <div className="rounded-lg border p-4">
              <div className="text-sm font-medium text-muted-foreground">Provider Latency</div>
              <div className="mt-3 space-y-2">
                {providerLatencies.length ? providerLatencies.map(item => (
                  <div key={item.provider} className="flex items-center justify-between text-sm">
                    <span className="font-medium capitalize">{item.provider}</span>
                    <span className="text-muted-foreground">P50 {Math.round(item.p50 * 1000)}ms</span>
                  </div>
                )) : <div className="text-sm text-muted-foreground">No provider latency samples yet</div>}
              </div>
            </div>

            <div className="rounded-lg border p-4">
              <div className="text-sm font-medium text-muted-foreground">Routing and Policy</div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge variant="outline">
                  {formatRoutingLabel(routingState?.selection_mode || 'priority_order')}
                </Badge>
                {routingState?.preferred_provider ? (
                  <Badge variant="outline">
                    preferred {routingState.preferred_provider}
                  </Badge>
                ) : null}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {topRoutingDecisions.length ? topRoutingDecisions.map(item => (
                  <Badge key={item.decision} variant="outline">
                    {formatRoutingLabel(item.decision)}: {item.count}
                  </Badge>
                )) : <span className="text-sm text-muted-foreground">No routing telemetry recorded</span>}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {topPolicyFlags.length ? topPolicyFlags.map(item => (
                  <Badge key={item.flag} className="bg-amber-100 text-amber-800">
                    {item.flag}: {item.count}
                  </Badge>
                )) : <span className="text-sm text-muted-foreground">No policy validation flags recorded</span>}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {(aiDiagnostics?.providers || []).map(item => (
                  <Badge key={item.provider} variant="outline">
                    {item.provider} {item.available ? 'ready' : 'offline'}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
          <CardDescription>Common administration tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/users">
                <Users className="h-5 w-5 mb-2" />
                <span>Add User</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/auditlog">
                <FileText className="h-5 w-5 mb-2" />
                <span>View Audit Log</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/backup">
                <Database className="h-5 w-5 mb-2" />
                <span>Backup Data</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/security">
                <Shield className="h-5 w-5 mb-2" />
                <span>Security Settings</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/ai-settings">
                <Bot className="h-5 w-5 mb-2" />
                <span>AI Configuration</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default AdminDashboard;

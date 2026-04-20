import { Cloud, RefreshCw } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

import type {
  DeveloperControlPlaneMem0HealthResponse,
  DeveloperControlPlaneMem0StatusResponse,
} from '../../api/mem0'

type Mem0TabState = 'idle' | 'loading' | 'ready' | 'error'

type Mem0DiagnosticsCardProps = {
  statusState: Mem0TabState
  statusRecord: DeveloperControlPlaneMem0StatusResponse | null
  statusError: string | null
  statusLastCheckedAt: string | null
  healthState: Mem0TabState
  healthRecord: DeveloperControlPlaneMem0HealthResponse | null
  healthError: string | null
  onRefreshDiagnostics: () => Promise<void> | void
}

function statusTone(state: Mem0TabState) {
  if (state === 'ready') {
    return 'border-emerald-200/80 bg-emerald-50/80 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-100'
  }

  if (state === 'loading') {
    return 'border-sky-200/80 bg-sky-50/80 text-sky-900 dark:border-sky-900/50 dark:bg-sky-950/20 dark:text-sky-100'
  }

  if (state === 'error') {
    return 'border-rose-200/80 bg-rose-50/80 text-rose-900 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-100'
  }

  return 'border-slate-200/80 bg-slate-50/80 text-slate-900 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-100'
}

function healthBadgeLabel(
  state: Mem0TabState,
  healthRecord: DeveloperControlPlaneMem0HealthResponse | null
) {
  if (state === 'loading') {
    return 'Probe Running'
  }
  if (state === 'error') {
    return 'Probe Failed'
  }
  if (state === 'ready' && healthRecord?.reachable) {
    return 'Cloud Reachable'
  }
  return 'Probe Pending'
}

export function Mem0DiagnosticsCard({
  statusState,
  statusRecord,
  statusError,
  statusLastCheckedAt,
  healthState,
  healthRecord,
  healthError,
  onRefreshDiagnostics,
}: Mem0DiagnosticsCardProps) {
  const readyLabel = statusRecord?.service.enabled
    ? statusRecord.service.configured
      ? 'Ready'
      : 'Config Pending'
    : 'Disabled'

  return (
    <Card className={statusTone(statusState)}>
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <Badge className="w-fit border border-slate-950/10 bg-slate-950 text-white dark:border-white/10 dark:bg-white/10 dark:text-white">
            Developer Cloud Memory
          </Badge>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Cloud className="h-5 w-5" />
            Mem0
          </CardTitle>
          <CardDescription className="max-w-3xl text-sm leading-6 text-current/80">
            {statusRecord?.purpose ??
              'Optional developer-only cloud memory for short project recall, outside the canonical REEVU runtime.'}
          </CardDescription>
        </div>
        <div className="flex items-center gap-3 text-sm text-current/80">
          <span>
            Last checked:{' '}
            {statusLastCheckedAt ? new Date(statusLastCheckedAt).toLocaleString() : 'Not checked yet'}
          </span>
          <Button type="button" variant="outline" size="sm" onClick={() => void onRefreshDiagnostics()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-current/90">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">{readyLabel}</Badge>
          <Badge variant="outline">{healthBadgeLabel(healthState, healthRecord)}</Badge>
          {statusRecord && <Badge variant="outline">{statusRecord.service.host}</Badge>}
          {statusRecord?.service.project_scoped && <Badge variant="outline">Project scoped</Badge>}
          {healthRecord?.latency_ms !== null && healthRecord?.latency_ms !== undefined && (
            <Badge variant="outline">{`${healthRecord.latency_ms} ms`}</Badge>
          )}
        </div>
        <p>{statusRecord?.detail ?? statusError ?? 'Status has not been sampled yet.'}</p>
        <p>
          {healthRecord?.detail ?? healthError ?? 'Cloud reachability has not been probed yet.'}
        </p>
      </CardContent>
    </Card>
  )
}
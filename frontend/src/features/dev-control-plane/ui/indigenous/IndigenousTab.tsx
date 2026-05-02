import type { ReactNode } from 'react'

import {
  AlertTriangle,
  BookOpen,
  Brain,
  GitBranch,
  Radar,
  RefreshCw,
  Route,
  Sparkles,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TabsContent } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

import type { DeveloperControlPlaneIndigenousBrainBriefResponse } from '../../api/activeBoard'

type IndigenousTabProps = {
  indigenousBrainState: 'idle' | 'loading' | 'ready' | 'error'
  indigenousBrainBrief: DeveloperControlPlaneIndigenousBrainBriefResponse | null
  indigenousBrainError: string | null
  indigenousBrainLastCheckedAt: string | null
  onRefresh: () => Promise<unknown> | void
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return 'Not sampled yet'
  }

  return new Date(value).toLocaleString()
}

function summaryTone(state: IndigenousTabProps['indigenousBrainState']) {
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

function blockerTone(severity: string) {
  if (severity === 'blocking') {
    return 'border-rose-300/60 bg-rose-50/80 text-rose-900 dark:border-rose-800/60 dark:bg-rose-950/20 dark:text-rose-100'
  }

  if (severity === 'watch') {
    return 'border-amber-300/60 bg-amber-50/80 text-amber-900 dark:border-amber-800/60 dark:bg-amber-950/20 dark:text-amber-100'
  }

  return 'border-sky-300/60 bg-sky-50/80 text-sky-900 dark:border-sky-800/60 dark:bg-sky-950/20 dark:text-sky-100'
}

function signalSummaryCard(title: string, value: string, description: string, icon: ReactNode) {
  return (
    <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
      <CardContent className="flex items-start gap-3 p-4">
        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 p-2 dark:border-white/10 dark:bg-slate-950/60">
          {icon}
        </div>
        <div>
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">{title}</div>
          <div className="mt-1 text-2xl font-semibold text-foreground">{value}</div>
          <div className="mt-1 text-sm text-muted-foreground">{description}</div>
        </div>
      </CardContent>
    </Card>
  )
}

export function IndigenousTab({
  indigenousBrainState,
  indigenousBrainBrief,
  indigenousBrainError,
  indigenousBrainLastCheckedAt,
  onRefresh,
}: IndigenousTabProps) {
  const brief = indigenousBrainBrief

  return (
    <TabsContent value="indigenous" className="space-y-4">
      <Card className={cn('overflow-hidden', summaryTone(indigenousBrainState))}>
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <Badge className="w-fit border border-slate-950/10 bg-slate-950 text-white dark:border-white/10 dark:bg-white/10 dark:text-white">
              Indigenous Brain
            </Badge>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Brain className="h-5 w-5" />
              Native World Model
            </CardTitle>
            <CardDescription className="max-w-3xl text-sm leading-6 text-current/80">
              {brief?.indigenous_brain.summary ??
                'Backend-native control-plane world model that fuses canonical planning, execution, runtime, learning, and optional project-brain signals.'}
            </CardDescription>
          </div>
          <div className="flex items-center gap-3 text-sm text-current/80">
            <span>Last checked: {formatTimestamp(indigenousBrainLastCheckedAt)}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => void onRefresh()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        {brief && (
          <CardContent className="space-y-3 text-sm text-current/90">
            <p>{brief.worldview_summary}</p>
            <p>{brief.indigenous_brain.authority_boundary}</p>
          </CardContent>
        )}
        {!brief && indigenousBrainError && (
          <CardContent className="text-sm text-current/90">{indigenousBrainError}</CardContent>
        )}
      </Card>

      {brief && (
        <>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {signalSummaryCard(
              'Active Lanes',
              String(brief.board.active_lane_count),
              brief.board.available
                ? `${brief.board.blocked_lane_count} blocked lane(s) in the canonical board.`
                : brief.board.detail ?? 'Shared board unavailable.',
              <GitBranch className="h-4 w-4 text-emerald-600" />
            )}
            {signalSummaryCard(
              'Queue Jobs',
              String(brief.queue.job_count),
              brief.queue.exists
                ? `${brief.queue.is_stale ? 'Stale' : 'Fresh'} queue at ${brief.queue.age_hours ?? 0}h.`
                : brief.queue.detail ?? 'Reviewed queue unavailable.',
              <Route className="h-4 w-4 text-sky-600" />
            )}
            {signalSummaryCard(
              'Missions',
              String(brief.missions.total_count),
              brief.missions.available
                ? `${brief.missions.escalation_count} escalation signal(s).`
                : brief.missions.detail ?? 'Mission-state unavailable.',
              <Radar className="h-4 w-4 text-violet-600" />
            )}
            {signalSummaryCard(
              'Learnings',
              String(brief.learnings.total_count),
              brief.learnings.available
                ? `${brief.project_brain.node_match_count} project-brain node match(es).`
                : brief.learnings.detail ?? 'Learning ledger unavailable.',
              <BookOpen className="h-4 w-4 text-amber-600" />
            )}
            {signalSummaryCard(
              'Mem0',
              brief.mem0.ready ? 'Ready' : brief.mem0.enabled ? 'Pending' : 'Disabled',
              brief.mem0.ready
                ? `${brief.mem0.project_scoped ? 'Project-scoped' : 'Global'} adapter at ${brief.mem0.host}.`
                : brief.mem0.detail ?? 'Optional external memory is not ready.',
              <Sparkles className="h-4 w-4 text-fuchsia-600" />
            )}
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
              <CardHeader>
                <CardTitle>Recommended Focus</CardTitle>
                <CardDescription>
                  The next canonical lane to move with the current evidence set.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                {brief.recommended_focus ? (
                  <>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline">{brief.recommended_focus.source}</Badge>
                      <Badge variant="outline">{brief.recommended_focus.status}</Badge>
                      <span className="font-medium text-foreground">
                        {brief.recommended_focus.lane_id}
                      </span>
                    </div>
                    <div className="text-base font-semibold text-foreground">
                      {brief.recommended_focus.title}
                    </div>
                    <p>{brief.recommended_focus.objective}</p>
                    <p>{brief.recommended_focus.reason}</p>
                    {brief.recommended_focus.dependencies.length > 0 && (
                      <div>
                        <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">
                          Dependencies
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {brief.recommended_focus.dependencies.map((dependency) => (
                            <Badge key={dependency} variant="secondary">
                              {dependency}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p>No active canonical lane is currently clean enough to recommend.</p>
                )}
              </CardContent>
            </Card>

            <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
              <CardHeader>
                <CardTitle>Project-Brain Enrichment</CardTitle>
                <CardDescription>
                  Optional associative recall from the Being BijMantra sidecar.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">
                    {brief.project_brain.available ? 'Connected' : 'Offline'}
                  </Badge>
                  <Badge variant="outline">{brief.project_brain.base_url}</Badge>
                </div>
                <p>Query: {brief.project_brain.query}</p>
                <p>
                  Sources {brief.project_brain.source_match_count}, projections{' '}
                  {brief.project_brain.projection_match_count}, nodes {brief.project_brain.node_match_count},
                  provenance trails {brief.project_brain.provenance_trail_count}.
                </p>
                {brief.project_brain.notable_source_paths.length > 0 && (
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">
                      Notable Sources
                    </div>
                    <div className="mt-2 space-y-1 text-foreground">
                      {brief.project_brain.notable_source_paths.map((path) => (
                        <div key={path}>{path}</div>
                      ))}
                    </div>
                  </div>
                )}
                {brief.project_brain.detail && <p>{brief.project_brain.detail}</p>}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
              <CardHeader>
                <CardTitle>Material Blockers</CardTitle>
                <CardDescription>
                  Evidence-backed blockers surfaced by the native world model.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {brief.blockers.length > 0 ? (
                  brief.blockers.map((blocker) => (
                    <div
                      key={blocker.key}
                      className={cn('rounded-2xl border p-4', blockerTone(blocker.severity))}
                    >
                      <div className="flex items-center gap-2 text-sm font-semibold">
                        <AlertTriangle className="h-4 w-4" />
                        {blocker.summary}
                      </div>
                      <div className="mt-2 text-sm opacity-90">{blocker.recommended_action}</div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-emerald-300/60 bg-emerald-50/80 p-4 text-sm text-emerald-900 dark:border-emerald-800/60 dark:bg-emerald-950/20 dark:text-emerald-100">
                    No material blockers are currently surfaced by the Indigenous Brain brief.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
              <CardHeader>
                <CardTitle>Still Missing</CardTitle>
                <CardDescription>
                  Remaining capability gaps exposed by the current evidence set.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                {brief.missing_capabilities.map((item) => (
                  <div
                    key={item}
                    className="flex items-start gap-2 rounded-2xl border border-slate-200/80 bg-slate-50/90 p-3 dark:border-white/10 dark:bg-slate-950/50"
                  >
                    <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-sky-500" />
                    <span>{item}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </TabsContent>
  )
}
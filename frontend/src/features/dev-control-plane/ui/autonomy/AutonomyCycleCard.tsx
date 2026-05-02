import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

import type {
  DeveloperControlPlaneAutonomyCycleAction,
  DeveloperControlPlaneAutonomyCycleOrderingSource,
  DeveloperControlPlaneCompletionWritePreparationResponse,
  DeveloperControlPlaneAutonomyCycleResponse,
  DeveloperControlPlaneMissionStateResponse,
} from '../../api/activeBoard'
import { getMissionSummaryForRuntimeLinkage } from '../missionLinking'
import {
  findAutonomyCycleCompletionWritePreparationForLane,
  getAutonomyActionCompletionWritePreparation,
} from './completionWritePreparation'

type AutonomyCycleCardProps = {
  state: 'idle' | 'loading' | 'ready' | 'missing' | 'error'
  record?: DeveloperControlPlaneAutonomyCycleResponse | null
  error?: string | null
  lastCheckedAt?: string | null
  missionStateState?: 'idle' | 'loading' | 'ready' | 'error'
  missionStateRecord?: DeveloperControlPlaneMissionStateResponse | null
  selectedLaneId?: string | null
  onSelectLane?: (laneId: string) => void
  onDraftLaneCompletionForLane?: (
    laneId: string,
    prepared?: DeveloperControlPlaneCompletionWritePreparationResponse | null
  ) => Promise<void> | void
}

type CompletionWriteBackAlignment = {
  state: 'ready' | 'pending' | 'unavailable' | 'already-closed'
  detail: string
  canPrepare: boolean
}

function formatTimestamp(value: string | null | undefined) {
  if (!value) {
    return 'Not available'
  }

  return new Date(value).toLocaleString()
}

function cycleTone(state: AutonomyCycleCardProps['state']) {
  return state === 'ready'
    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    : state === 'missing'
      ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
      : state === 'error'
        ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
        : state === 'loading'
          ? 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
          : 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function cycleLabel(state: AutonomyCycleCardProps['state']) {
  return state === 'ready' ? 'available' : state
}

function cycleDescription(state: AutonomyCycleCardProps['state'], hasActions: boolean) {
  if (state === 'ready' && hasActions) {
    return 'Latest bounded next-action synthesis from queue, runtime watchdog, and closeout evidence.'
  }

  if (state === 'ready') {
    return 'The autonomy-cycle artifact is present, but it is not currently proposing any next actions.'
  }

  if (state === 'missing') {
    return 'The tracked autonomy-cycle artifact has not been generated yet. Refresh queue status or run make autonomy-cycle.'
  }

  if (state === 'error') {
    return 'The autonomy-cycle artifact could not be loaded. Treat next-action synthesis as unavailable until the tracked artifact is readable again.'
  }

  if (state === 'loading') {
    return 'Refreshing the latest autonomy-cycle artifact.'
  }

  return 'Refresh queue status to load the current autonomy-cycle artifact.'
}

function completionWriteBackAlignmentTone(state: CompletionWriteBackAlignment['state']) {
  return state === 'ready'
    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    : state === 'already-closed'
      ? 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
      : state === 'unavailable'
        ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
        : 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
}

function resolveCompletionWriteBackAlignment(
  action: DeveloperControlPlaneAutonomyCycleAction,
  missionStateState: NonNullable<AutonomyCycleCardProps['missionStateState']>,
  missionStateRecord: DeveloperControlPlaneMissionStateResponse | null
): CompletionWriteBackAlignment {
  if (missionStateState === 'loading' || missionStateState === 'idle') {
    return {
      state: 'pending',
      detail:
        'Durable mission-state alignment is still loading. Keep explicit board write-back gated until the runtime mission snapshot is available.',
      canPrepare: false,
    }
  }

  if (missionStateState === 'error') {
    return {
      state: 'unavailable',
      detail:
        'Durable mission-state inspection is unavailable. Keep explicit board write-back gated until mission-state visibility recovers.',
      canPrepare: false,
    }
  }

  const missionSummary = getMissionSummaryForRuntimeLinkage({
    missionStateRecord,
    missionId: action.mission_id,
    sourceLaneId: action.source_lane_id,
    queueJobId: action.job_id,
  })

  if (!missionSummary) {
    return {
      state: 'pending',
      detail:
        'Stable closeout evidence exists, but no aligned durable mission snapshot is visible for this queue job and lane yet.',
      canPrepare: false,
    }
  }

  if (missionSummary.status === 'completed') {
    return {
      state: 'already-closed',
      detail: `Durable mission ${missionSummary.mission_id} is already completed, so explicit board closure appears to have been recorded.`,
      canPrepare: false,
    }
  }

  return {
    state: 'ready',
    detail: `Durable mission ${missionSummary.mission_id} is aligned to this queue job and lane and is still awaiting explicit board closure.`,
    canPrepare: true,
  }
}

function decisionMemoryOrderingDetail(
  orderingSource: DeveloperControlPlaneAutonomyCycleOrderingSource
) {
  if (orderingSource === 'canonical-learning-fallback') {
    return 'Next-action ordering is biased by broader lane-scope canonical learnings.'
  }

  return 'Next-action ordering is biased by exact runtime-scope canonical learnings.'
}

export function AutonomyCycleCard({
  state,
  record = null,
  error = null,
  lastCheckedAt = null,
  missionStateState = 'idle',
  missionStateRecord = null,
  selectedLaneId = null,
  onSelectLane,
  onDraftLaneCompletionForLane,
}: AutonomyCycleCardProps) {
  const nextActions = record?.next_actions ?? []
  const orderingSource = record?.next_action_ordering_source ?? 'artifact'
  const blockedJobs = record?.blocked_jobs ?? []
  const closeoutCandidates = record?.closeout_candidates ?? []
  const hasActions = nextActions.length > 0

  return (
    <div className="rounded-xl border border-border/60 bg-background/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Autonomy Cycle</div>
          <div className="mt-1 text-sm text-muted-foreground">
            {cycleDescription(state, hasActions)}
          </div>
        </div>
        <Badge className={cn('capitalize', cycleTone(state))}>{cycleLabel(state)}</Badge>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Next actions</div>
          <div className="mt-2 text-lg font-semibold text-foreground">
            {record?.next_action_count ?? 0}
          </div>
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Selected jobs</div>
          <div className="mt-2 text-lg font-semibold text-foreground">
            {record?.selected_job_count ?? 0}
          </div>
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Blocked jobs</div>
          <div className="mt-2 text-lg font-semibold text-foreground">
            {record?.blocked_job_count ?? 0}
          </div>
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Closeout candidates</div>
          <div className="mt-2 text-lg font-semibold text-foreground">
            {record?.closeout_candidate_count ?? 0}
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-2 text-sm text-muted-foreground">
        <div>
          Artifact path:{' '}
          <span className="font-mono text-foreground">{record?.artifact_path ?? 'Not available'}</span>
        </div>
        <div>
          Queue path:{' '}
          <span className="font-mono text-foreground">{record?.queue_path ?? 'Not available'}</span>
        </div>
        <div>
          Generated at: <span className="text-foreground">{formatTimestamp(record?.generated_at)}</span>
        </div>
        <div>
          Last checked: <span className="text-foreground">{formatTimestamp(lastCheckedAt)}</span>
        </div>
        <div>
          Watchdog signal:{' '}
          <span className="text-foreground">
            {record?.watchdog.exists
              ? record.watchdog.state_is_stale
                ? 'stale snapshot'
                : record.watchdog.gateway_healthy === false
                  ? 'gateway unhealthy'
                  : record.watchdog.total_alerts > 0
                    ? `${record.watchdog.total_alerts} alert(s)`
                    : 'healthy or idle'
              : 'not published'}
          </span>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">{error}</p>}

      {hasActions && (
        <div className="mt-4 space-y-3">
          {orderingSource !== 'artifact' && (
            <div className="rounded-lg border border-border/60 bg-background/60 px-3 py-3 text-sm text-muted-foreground">
              <div className="flex flex-wrap items-center gap-2">
                <Badge className="bg-sky-500/15 text-sky-700 dark:text-sky-300">memory-biased</Badge>
                <span>{decisionMemoryOrderingDetail(orderingSource)}</span>
              </div>
            </div>
          )}
          {nextActions.slice(0, 4).map((action, index) => {
            const completionWritePreparation = getAutonomyActionCompletionWritePreparation(action)
            const isPrepareWriteBackAction =
              action.action === 'prepare-completion-write-back' &&
              action.source_lane_id &&
              onDraftLaneCompletionForLane
            const alignment = isPrepareWriteBackAction
              ? resolveCompletionWriteBackAlignment(action, missionStateState, missionStateRecord)
              : null

            return (
              <div key={`${action.action}-${action.job_id ?? index}`} className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className="bg-sky-500/15 text-sky-700 dark:text-sky-300">{action.action}</Badge>
                  <span className="font-medium text-foreground">{action.title ?? action.job_id ?? 'Unnamed action'}</span>
                </div>
                {action.source_lane_id && (
                  <div className="mt-2 text-muted-foreground">
                    Lane: <span className="font-mono text-foreground">{action.source_lane_id}</span>
                  </div>
                )}
                {action.reason && <div className="mt-2 text-muted-foreground">{action.reason}</div>}
                {(action.receipt_path || action.state_path) && (
                  <div className="mt-2 text-muted-foreground">
                    <span className="font-mono text-foreground">{action.receipt_path ?? action.state_path}</span>
                  </div>
                )}

                {alignment ? (
                  <>
                    <div className="mt-3 rounded-lg border border-border/60 bg-background/60 px-3 py-3 text-muted-foreground">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs uppercase tracking-[0.22em] text-muted-foreground">
                          Mission alignment
                        </span>
                        <Badge className={completionWriteBackAlignmentTone(alignment.state)}>
                          {alignment.state}
                        </Badge>
                      </div>
                      <div className="mt-2 text-sm">{alignment.detail}</div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {onSelectLane && (
                        <Button
                          variant="outline"
                          className="h-8 px-3"
                          onClick={() => onSelectLane(action.source_lane_id!)}
                          disabled={action.source_lane_id === selectedLaneId}
                        >
                          {action.source_lane_id === selectedLaneId
                            ? `Lane ${action.source_lane_id} in focus`
                            : `Focus lane ${action.source_lane_id}`}
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        className="h-8 px-3"
                        onClick={() =>
                          void onDraftLaneCompletionForLane?.(
                            action.source_lane_id!,
                            completionWritePreparation
                          )
                        }
                        disabled={!alignment.canPrepare}
                      >
                        {alignment.canPrepare
                          ? action.source_lane_id === selectedLaneId
                            ? `Prepare board write-back for lane ${action.source_lane_id}`
                            : `Focus and prepare write-back for lane ${action.source_lane_id}`
                          : 'Mission alignment required'}
                      </Button>
                    </div>
                  </>
                ) : (
                  action.source_lane_id &&
                  onSelectLane && (
                    <div className="mt-3">
                      <Button
                        variant="outline"
                        className="h-8 px-3"
                        onClick={() => onSelectLane(action.source_lane_id!)}
                        disabled={action.source_lane_id === selectedLaneId}
                      >
                        {action.source_lane_id === selectedLaneId
                          ? `Lane ${action.source_lane_id} in focus`
                          : `Focus lane ${action.source_lane_id}`}
                      </Button>
                    </div>
                  )
                )}
              </div>
            )
          })}
        </div>
      )}

      {!hasActions && state === 'ready' && (
        <div className="mt-4 rounded-lg border border-border/60 bg-muted/20 px-3 py-3 text-sm text-muted-foreground">
          No synthesized next actions are currently visible from the tracked artifact.
        </div>
      )}

      {closeoutCandidates.length > 0 && (
        <div className="mt-4 rounded-lg border border-border/60 bg-muted/20 px-3 py-3 text-sm text-muted-foreground">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Closeout candidates</div>
          <div className="mt-3 space-y-3">
            {closeoutCandidates.slice(0, 2).map((candidate) => (
              (() => {
                const candidateCompletionWritePreparation = candidate.source_lane_id
                  ? findAutonomyCycleCompletionWritePreparationForLane(
                      record,
                      candidate.source_lane_id
                    )
                  : null

                return (
                  <div key={candidate.job_id} className="rounded-lg border border-border/60 bg-background/60 px-3 py-3">
                    <div className="font-medium text-foreground">{candidate.title ?? candidate.job_id}</div>
                    <div className="mt-1 text-muted-foreground">
                      Queue: {candidate.queue_status ?? 'unknown'} | Closeout: {candidate.closeout_status ?? 'unknown'}
                    </div>
                    {candidate.source_lane_id && (
                      <div className="mt-2 text-muted-foreground">
                        Lane: <span className="font-mono text-foreground">{candidate.source_lane_id}</span>
                      </div>
                    )}
                    {candidate.path && (
                      <div className="mt-2 text-muted-foreground">
                        <span className="font-mono text-foreground">{candidate.path}</span>
                      </div>
                    )}
                    {candidate.source_lane_id && onDraftLaneCompletionForLane && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {onSelectLane && (
                          <Button
                            variant="outline"
                            className="h-8 px-3"
                            onClick={() => onSelectLane(candidate.source_lane_id!)}
                            disabled={candidate.source_lane_id === selectedLaneId}
                          >
                            {candidate.source_lane_id === selectedLaneId
                              ? `Lane ${candidate.source_lane_id} in focus`
                              : `Focus lane ${candidate.source_lane_id}`}
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          className="h-8 px-3"
                          onClick={() =>
                            void onDraftLaneCompletionForLane(
                              candidate.source_lane_id!,
                              candidateCompletionWritePreparation
                            )
                          }
                        >
                          {candidate.source_lane_id === selectedLaneId
                            ? `Draft closeout for lane ${candidate.source_lane_id}`
                            : `Focus and draft closeout for lane ${candidate.source_lane_id}`}
                        </Button>
                      </div>
                    )}
                  </div>
                )
              })()
            ))}
          </div>
        </div>
      )}

      {blockedJobs.length > 0 && (
        <div className="mt-4 rounded-lg border border-border/60 bg-muted/20 px-3 py-3 text-sm text-muted-foreground">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Top blocked jobs</div>
          <div className="mt-3 space-y-3">
            {blockedJobs.slice(0, 2).map((job) => (
              <div key={job.job_id} className="rounded-lg border border-border/60 bg-background/60 px-3 py-3">
                <div className="font-medium text-foreground">{job.title}</div>
                <div className="mt-1 text-muted-foreground">{job.reason ?? 'blocked'}</div>
                {job.source_lane_id && (
                  <div className="mt-2 text-muted-foreground">
                    Lane: <span className="font-mono text-foreground">{job.source_lane_id}</span>
                  </div>
                )}
                {job.source_lane_id && onSelectLane && (
                  <div className="mt-3">
                    <Button
                      variant="outline"
                      className="h-8 px-3"
                      onClick={() => onSelectLane(job.source_lane_id!)}
                      disabled={job.source_lane_id === selectedLaneId}
                    >
                      {job.source_lane_id === selectedLaneId
                        ? `Lane ${job.source_lane_id} in focus`
                        : `Focus lane ${job.source_lane_id}`}
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

import type { DeveloperControlPlaneLearningLedgerResponse } from '../../api/activeBoard'
import type { DecisionMemoryResolution, DecisionMemoryState } from './useDecisionMemory'

type DecisionMemoryCardProps = {
  state: DecisionMemoryState
  record: DeveloperControlPlaneLearningLedgerResponse | null
  error: string | null
  lastCheckedAt: string | null
  scope: {
    sourceLaneId: string | null
    queueJobId: string | null
    linkedMissionId: string | null
  }
  resolution: DecisionMemoryResolution
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return 'Not available'
  }

  return new Date(value).toLocaleString()
}

function formatEntryTypeLabel(value: string) {
  return value
    .split('-')
    .filter(Boolean)
    .map((segment) => segment[0]?.toUpperCase() + segment.slice(1))
    .join(' ')
}

function formatSourceClassificationLabel(value: string) {
  return value
    .split('-')
    .filter(Boolean)
    .map((segment) => segment[0]?.toUpperCase() + segment.slice(1))
    .join(' ')
}

function formatLearningConfidence(score: number | null) {
  if (score === null) {
    return null
  }

  const normalizedScore = score <= 1 ? Math.round(score * 100) : Math.round(score)
  return `${normalizedScore}% confidence`
}

function decisionMemoryTone(state: DecisionMemoryState, hasEntries: boolean) {
  if (state === 'error') {
    return 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
  }

  if (state === 'loading') {
    return 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
  }

  if (state === 'ready' && hasEntries) {
    return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
  }

  if (state === 'ready') {
    return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
  }

  return 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function decisionMemoryLabel(state: DecisionMemoryState, hasEntries: boolean) {
  if (state === 'ready' && hasEntries) {
    return 'memory-informed'
  }

  if (state === 'ready') {
    return 'no matching memory'
  }

  return state
}

function decisionMemoryDescription(
  state: DecisionMemoryState,
  hasEntries: boolean,
  scope: DecisionMemoryCardProps['scope']
) {
  if (!scope.sourceLaneId && !scope.queueJobId && !scope.linkedMissionId) {
    return 'Select a lane or load runtime evidence before binding canonical learnings into the current autonomy decision.'
  }

  if (state === 'loading') {
    return 'Loading canonical learning entries for the selected lane, queue job, and durable mission scope.'
  }

  if (state === 'error') {
    return 'Decision memory is unavailable until the learning ledger can be read again.'
  }

  if (state === 'ready' && hasEntries) {
    return 'Current hidden-surface decision guidance is backed by matching canonical learning entries.'
  }

  if (state === 'ready') {
    return 'No matching canonical learning entries are currently linked to this decision scope.'
  }

  return 'Decision memory is standing by.'
}

function decisionMemoryLinkageLabel(resolution: DecisionMemoryResolution) {
  if (resolution.fallbackUsed) {
    return resolution.matchMode === 'lane-and-mission'
      ? 'lane and mission fallback'
      : resolution.matchMode === 'mission-only'
        ? 'mission-only fallback'
        : resolution.matchMode === 'queue-only'
          ? 'queue-only fallback'
          : 'broader lane fallback'
  }

  return 'exact runtime match'
}

function decisionMemoryLinkageTone(resolution: DecisionMemoryResolution) {
  return resolution.fallbackUsed
    ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
    : 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
}

function decisionMemoryLinkageDetail(resolution: DecisionMemoryResolution) {
  if (!resolution.fallbackUsed) {
    return 'Canonical learnings matched the current runtime scope directly.'
  }

  if (resolution.matchMode === 'lane-and-mission') {
    return 'No exact queue-linked learning matched, so decision memory widened to lane and mission scope.'
  }

  if (resolution.matchMode === 'mission-only') {
    return 'No exact queue-linked learning matched, so decision memory widened to mission scope.'
  }

  if (resolution.matchMode === 'queue-only') {
    return 'Lane linkage was unavailable, so decision memory widened to queue scope.'
  }

  return 'No exact runtime-linked learning matched, so decision memory widened to broader lane scope.'
}

export function DecisionMemoryCard({
  state,
  record,
  error,
  lastCheckedAt,
  scope,
  resolution,
}: DecisionMemoryCardProps) {
  const entries = record?.entries ?? []
  const hasEntries = entries.length > 0

  return (
    <div className="rounded-xl border border-border/60 bg-background/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Decision Memory</div>
          <div className="mt-1 text-sm text-muted-foreground">
            {decisionMemoryDescription(state, hasEntries, scope)}
          </div>
        </div>
        <Badge className={cn('capitalize', decisionMemoryTone(state, hasEntries))}>
          {decisionMemoryLabel(state, hasEntries)}
        </Badge>
      </div>

      {state === 'ready' && hasEntries && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Badge className={cn('capitalize', decisionMemoryLinkageTone(resolution))}>
            {decisionMemoryLinkageLabel(resolution)}
          </Badge>
          {resolution.fallbackUsed && (
            <span className="text-xs text-muted-foreground">
              {decisionMemoryLinkageDetail(resolution)}
            </span>
          )}
        </div>
      )}

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Matches</div>
          <div className="mt-2 text-lg font-semibold text-foreground">{record?.total_count ?? 0}</div>
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Lane scope</div>
          <div className="mt-2 text-sm font-mono text-foreground">{scope.sourceLaneId ?? 'Not scoped'}</div>
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Queue scope</div>
          <div className="mt-2 text-sm font-mono text-foreground">{scope.queueJobId ?? 'Not scoped'}</div>
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3">
          <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Last checked</div>
          <div className="mt-2 text-sm text-foreground">{formatTimestamp(lastCheckedAt)}</div>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">{error}</p>}

      {hasEntries && (
        <div className="mt-4 space-y-3">
          {entries.slice(0, 3).map((entry) => (
            <div
              key={entry.learning_entry_id}
              className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3 text-sm"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge className="bg-slate-500/15 text-slate-700 dark:text-slate-300">
                  {formatEntryTypeLabel(entry.entry_type)}
                </Badge>
                <Badge className="bg-sky-500/15 text-sky-700 dark:text-sky-300">
                  {formatSourceClassificationLabel(entry.source_classification)}
                </Badge>
                {formatLearningConfidence(entry.confidence_score) && (
                  <span className="text-xs text-muted-foreground">
                    {formatLearningConfidence(entry.confidence_score)}
                  </span>
                )}
              </div>
              <div className="mt-2 font-medium text-foreground">{entry.title}</div>
              <div className="mt-2 text-muted-foreground">{entry.summary}</div>
              <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                <div>
                  Mission: <span className="font-mono text-foreground">{entry.linked_mission_id ?? 'Not linked'}</span>
                </div>
                <div>
                  Queue job: <span className="font-mono text-foreground">{entry.queue_job_id ?? 'Not linked'}</span>
                </div>
                <div>
                  Approval receipt: <span className="text-foreground">{entry.approval_receipt_id ?? 'None'}</span>
                </div>
                <div>
                  Recorded: <span className="text-foreground">{formatTimestamp(entry.recorded_at)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
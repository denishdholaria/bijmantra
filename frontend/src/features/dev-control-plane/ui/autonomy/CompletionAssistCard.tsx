import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

import type {
  DeveloperControlPlaneCompletionWritePreparationResponse,
  DeveloperControlPlaneRuntimeCompletionAssistResponse,
} from '../../api/activeBoard'

type CompletionAssistCardProps = {
  state: 'idle' | 'loading' | 'ready' | 'missing' | 'error'
  record?: DeveloperControlPlaneRuntimeCompletionAssistResponse | null
  error?: string | null
  lastCheckedAt?: string | null
  selectedLaneId?: string | null
  onSelectLane?: (laneId: string) => void
  onDraftLaneCompletionForLane?: (
    laneId: string,
    prepared?: DeveloperControlPlaneCompletionWritePreparationResponse | null
  ) => Promise<void> | void
}

function formatTimestamp(value: string | null | undefined) {
  if (!value) {
    return 'Not available'
  }

  return new Date(value).toLocaleString()
}

function assistTone(state: CompletionAssistCardProps['state']) {
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

function assistLabel(state: CompletionAssistCardProps['state']) {
  return state === 'ready' ? 'available' : state
}

function assistDescription(
  state: CompletionAssistCardProps['state'],
  record: DeveloperControlPlaneRuntimeCompletionAssistResponse | null | undefined
) {
  if (state === 'ready' && record?.staged) {
    return 'Headless reviewed completion assist derived from the hidden runtime autonomy-cycle response.'
  }

  if (state === 'ready') {
    return 'The completion-assist artifact is present but does not currently stage an actionable reviewed write-back packet.'
  }

  if (state === 'missing') {
    return 'The tracked completion-assist artifact has not been staged yet. Run make autonomy-cycle with the hidden control-plane token configured to produce it.'
  }

  if (state === 'error') {
    return 'The completion-assist artifact could not be loaded. Treat the headless assist surface as unavailable until the tracked artifact is readable again.'
  }

  if (state === 'loading') {
    return 'Refreshing the latest headless completion-assist artifact.'
  }

  return 'Refresh queue status to inspect whether a headless reviewed completion assist has been staged.'
}

function getPreparedCompletionWrite(
  record: DeveloperControlPlaneRuntimeCompletionAssistResponse | null | undefined
): DeveloperControlPlaneCompletionWritePreparationResponse | null {
  const actionable = record?.actionable_completion_write
  if (!actionable) {
    return null
  }

  return {
    source_lane_id: actionable.sourceLaneId,
    queue_job_id: actionable.jobId,
    draft_source: actionable.draftSource,
    queue_status: actionable.queueStatus,
    closeout_receipt: actionable.closeoutReceipt,
    prepared_request: actionable.preparedRequest,
  }
}

export function CompletionAssistCard({
  state,
  record = null,
  error = null,
  lastCheckedAt = null,
  selectedLaneId = null,
  onSelectLane,
  onDraftLaneCompletionForLane,
}: CompletionAssistCardProps) {
  const actionable = record?.actionable_completion_write
  const sourceLaneId = actionable?.sourceLaneId ?? null
  const prepared = getPreparedCompletionWrite(record)

  return (
    <div className="rounded-xl border border-border/60 bg-background/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
            Completion Assist
          </div>
          <div className="mt-1 text-sm text-muted-foreground">
            {assistDescription(state, record)}
          </div>
        </div>
        <Badge className={cn('capitalize', assistTone(state))}>{assistLabel(state)}</Badge>
      </div>

      <div className="mt-4 space-y-2 text-sm text-muted-foreground">
        <div>
          Artifact path:{' '}
          <span className="font-mono text-foreground">{record?.artifact_path ?? 'Not available'}</span>
        </div>
        <div>
          Generated at: <span className="text-foreground">{formatTimestamp(record?.generated_at)}</span>
        </div>
        <div>
          Last checked: <span className="text-foreground">{formatTimestamp(lastCheckedAt)}</span>
        </div>
        <div>
          Explicit write required:{' '}
          <span className="text-foreground">{record?.explicit_write_required === false ? 'no' : 'yes'}</span>
        </div>
      </div>

      {record?.message && (
        <div className="mt-4 rounded-lg border border-border/60 bg-muted/20 px-3 py-3 text-sm text-muted-foreground">
          {record.message}
        </div>
      )}

      {actionable && (
        <div className="mt-4 rounded-lg border border-border/60 bg-muted/20 px-3 py-3 text-sm text-muted-foreground">
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="bg-sky-500/15 text-sky-700 dark:text-sky-300">
              {actionable.action}
            </Badge>
            <span className="font-medium text-foreground">{actionable.jobId}</span>
          </div>
          <div className="mt-3 space-y-2">
            <div>
              Lane: <span className="font-mono text-foreground">{actionable.sourceLaneId}</span>
            </div>
            <div>
              Draft source: <span className="text-foreground">{actionable.draftSource}</span>
            </div>
            <div>
              Queue hash:{' '}
              <span className="font-mono text-foreground">{actionable.queueStatus.queue_sha256}</span>
            </div>
            <div>
              Closeout status:{' '}
              <span className="text-foreground">{actionable.closeoutReceipt.closeout_status ?? 'Not available'}</span>
            </div>
            <div>
              Receipt path:{' '}
              <span className="font-mono text-foreground">{actionable.receiptPath ?? 'Not available'}</span>
            </div>
          </div>

          {(onSelectLane || onDraftLaneCompletionForLane) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {sourceLaneId && onSelectLane && (
                <Button
                  variant="outline"
                  className="h-8 px-3"
                  onClick={() => onSelectLane(sourceLaneId)}
                  disabled={sourceLaneId === selectedLaneId}
                >
                  {sourceLaneId === selectedLaneId
                    ? `Lane ${sourceLaneId} in focus`
                    : `Focus lane ${sourceLaneId}`}
                </Button>
              )}
              {sourceLaneId && prepared && onDraftLaneCompletionForLane && (
                <Button
                  variant="outline"
                  className="h-8 px-3"
                  onClick={() => void onDraftLaneCompletionForLane(sourceLaneId, prepared)}
                >
                  {sourceLaneId === selectedLaneId
                    ? `Draft from staged assist for lane ${sourceLaneId}`
                    : `Focus and draft staged assist for lane ${sourceLaneId}`}
                </Button>
              )}
            </div>
          )}
        </div>
      )}

      {error && <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">{error}</p>}
    </div>
  )
}
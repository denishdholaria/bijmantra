import { useMemo, useState } from 'react'
import { Activity, AlertTriangle, CheckCircle2, Circle, Loader2, ShieldCheck } from 'lucide-react'

import type { ReevuRunEvent } from '@/lib/reevu-chat-stream'
import { cn } from '@/lib/utils'

interface ReevuRunTimelineCardProps {
  events?: ReevuRunEvent[]
}

function formatLabel(value: string): string {
  return value
    .replace(/\./g, ' ')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, character => character.toUpperCase())
}

function statusClasses(status: string): string {
  const normalized = status.trim().toLowerCase()

  if (normalized === 'completed') {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-300'
  }

  if (normalized === 'failed' || normalized === 'safe_failure') {
    return 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-200'
  }

  return 'border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-300'
}

function EventIcon({ status }: { status: string }) {
  const normalized = status.trim().toLowerCase()

  if (normalized === 'completed') {
    return <CheckCircle2 className="h-3.5 w-3.5" />
  }

  if (normalized === 'failed' || normalized === 'safe_failure') {
    return <AlertTriangle className="h-3.5 w-3.5" />
  }

  if (normalized === 'started' || normalized === 'in_progress') {
    return <Loader2 className="h-3.5 w-3.5 animate-spin" />
  }

  return <Circle className="h-3.5 w-3.5" />
}

function eventMeta(event: ReevuRunEvent): string[] {
  const meta: string[] = []

  if (event.tool_name) {
    meta.push(event.tool_name)
  }

  if (event.domains_involved?.length) {
    meta.push(event.domains_involved.join(', '))
  }

  if (typeof event.evidence_count === 'number') {
    meta.push(`${event.evidence_count} evidence refs`)
  }

  if (typeof event.calculation_count === 'number') {
    meta.push(`${event.calculation_count} calculations`)
  }

  if (event.missing_evidence_signals?.length) {
    meta.push(`${event.missing_evidence_signals.length} evidence gaps`)
  }

  return meta
}

export function ReevuRunTimelineCard({ events }: ReevuRunTimelineCardProps) {
  const [expanded, setExpanded] = useState(false)
  const runEvents = events ?? []
  const latestEvent = runEvents[runEvents.length - 1]
  const visibleEvents = useMemo(
    () => (expanded ? runEvents : runEvents.slice(-5)),
    [expanded, runEvents],
  )

  if (runEvents.length === 0 || !latestEvent) {
    return null
  }

  return (
    <div className="mb-3 overflow-hidden rounded-2xl border border-emerald-200/70 bg-gradient-to-br from-emerald-50/90 via-white to-slate-50 shadow-sm dark:border-emerald-900/50 dark:from-emerald-950/20 dark:via-slate-950 dark:to-slate-900/70">
      <button
        type="button"
        onClick={() => setExpanded(previous => !previous)}
        className="flex w-full flex-wrap items-center justify-between gap-3 px-4 py-3 text-left"
        aria-label="Toggle REEVU run timeline"
      >
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm shadow-emerald-900/15">
            <Activity className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700 dark:text-emerald-300">
                ReevuRun
              </p>
              <span className={cn(
                'rounded-full border px-2 py-0.5 text-[10px] font-medium',
                statusClasses(latestEvent.status),
              )}>
                {formatLabel(latestEvent.status)}
              </span>
            </div>
            <p className="mt-1 truncate text-sm font-medium text-slate-900 dark:text-slate-100">
              {latestEvent.title || formatLabel(latestEvent.event)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400">
          <span className="rounded-full border border-slate-200 bg-white/70 px-2 py-1 dark:border-slate-800 dark:bg-slate-950/60">
            {runEvents.length} events
          </span>
          <span className="rounded-full border border-emerald-200 bg-white/70 px-2 py-1 text-emerald-700 dark:border-emerald-900 dark:bg-slate-950/60 dark:text-emerald-300">
            {expanded ? 'Collapse' : 'Inspect'}
          </span>
        </div>
      </button>

      <ol className="border-t border-emerald-100/80 px-4 py-3 dark:border-emerald-950/80">
        {visibleEvents.map((event, index) => {
          const meta = eventMeta(event)
          const eventKey = `${event.run_id ?? 'run'}-${event.event}-${event.status}-${event.ts ?? index}`

          return (
            <li key={eventKey} className="relative grid grid-cols-[1.25rem_1fr] gap-3 pb-3 last:pb-0">
              {index < visibleEvents.length - 1 && (
                <span className="absolute left-[0.42rem] top-5 h-[calc(100%-1rem)] w-px bg-emerald-200/80 dark:bg-emerald-900/80" />
              )}
              <span className={cn(
                'z-10 mt-0.5 flex h-5 w-5 items-center justify-center rounded-full border bg-white dark:bg-slate-950',
                statusClasses(event.status),
              )}>
                <EventIcon status={event.status} />
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {event.title || formatLabel(event.event)}
                  </p>
                  <span className="text-[10px] uppercase tracking-wide text-slate-400 dark:text-slate-500">
                    {formatLabel(event.event)}
                  </span>
                </div>
                {event.detail && (
                  <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                    {event.detail}
                  </p>
                )}
                {meta.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {meta.map(item => (
                      <span
                        key={`${eventKey}-${item}`}
                        className="rounded-full border border-slate-200 bg-white/70 px-2 py-0.5 text-[10px] text-slate-600 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-300"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </li>
          )
        })}
      </ol>

      {!expanded && runEvents.length > visibleEvents.length && (
        <div className="border-t border-emerald-100/80 px-4 py-2 text-center text-[11px] text-slate-500 dark:border-emerald-950/80 dark:text-slate-400">
          Showing latest {visibleEvents.length} of {runEvents.length} run events
        </div>
      )}

      {latestEvent.safe_failure && (
        <div className="border-t border-amber-100 bg-amber-50/70 px-4 py-2 text-xs text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/20 dark:text-amber-200">
          <ShieldCheck className="mr-1 inline h-3.5 w-3.5" />
          Safe-failure guardrail active: {latestEvent.safe_failure.error_category.replace(/_/g, ' ')}
        </div>
      )}
    </div>
  )
}

export default ReevuRunTimelineCard

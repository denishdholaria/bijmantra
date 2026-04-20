import { useMemo, useState } from 'react'

import type {
  ReevuPlanExecutionStep,
  ReevuPlanExecutionSummary,
  ReevuRetrievalAudit,
} from '@/lib/reevu-chat-stream'

interface ReevuExecutionTraceCardProps {
  retrievalAudit?: ReevuRetrievalAudit
  planExecutionSummary?: ReevuPlanExecutionSummary
}

function formatEntityValue(value: unknown): string {
  if (typeof value === 'boolean') {
    return value ? 'yes' : 'no'
  }

  if (Array.isArray(value)) {
    return value.join(', ')
  }

  if (value === null || value === undefined || value === '') {
    return 'n/a'
  }

  if (typeof value === 'object') {
    return JSON.stringify(value)
  }

  return String(value)
}

function formatLabel(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, character => character.toUpperCase())
}

function getRecordEntries(record?: Record<string, unknown>): Array<[string, unknown]> {
  return Object.entries(record ?? {}).filter(([, value]) => value !== undefined)
}

function getCountEntries(record?: Record<string, number>): Array<[string, number]> {
  return Object.entries(record ?? {}).filter(([, value]) => Number.isFinite(value))
}

function getStepStatusLabel(step: ReevuPlanExecutionStep): string {
  if (typeof step.status === 'string' && step.status.trim()) {
    return formatLabel(step.status)
  }

  return step.completed ? 'Completed' : 'Not Completed'
}

function getStepStatusClasses(step: ReevuPlanExecutionStep): string {
  const normalizedStatus = (step.status ?? '').trim().toLowerCase()

  if (step.completed || normalizedStatus === 'completed') {
    return 'rounded-full border border-emerald-200 px-2 py-1 text-emerald-700 dark:border-emerald-800 dark:text-emerald-300'
  }

  if (normalizedStatus === 'missing') {
    return 'rounded-full border border-amber-200 px-2 py-1 text-amber-700 dark:border-amber-800 dark:text-amber-300'
  }

  return 'rounded-full border border-slate-200 px-2 py-1 text-slate-600 dark:border-slate-700 dark:text-slate-300'
}

export function ReevuExecutionTraceCard({
  retrievalAudit,
  planExecutionSummary,
}: ReevuExecutionTraceCardProps) {
  const [expanded, setExpanded] = useState(false)
  const effectivePlanExecutionSummary = planExecutionSummary ?? retrievalAudit?.plan
  const hasRetrievalAudit = Boolean(retrievalAudit)
  const hasPlan = Boolean(effectivePlanExecutionSummary)

  const entityEntries = useMemo(
    () => Object.entries(retrievalAudit?.entities ?? {}).filter(([, value]) => value !== undefined),
    [retrievalAudit],
  )
  const planMetadataEntries = useMemo(
    () => getRecordEntries(effectivePlanExecutionSummary?.metadata),
    [effectivePlanExecutionSummary],
  )

  if (!hasRetrievalAudit && !hasPlan) {
    return null
  }

  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-white/85 shadow-sm dark:border-slate-800 dark:bg-slate-950/40">
      <button
        type="button"
        onClick={() => setExpanded(previous => !previous)}
        className="flex w-full flex-wrap items-center justify-between gap-3 px-4 py-3 text-left"
        aria-label="Toggle execution trace details"
      >
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700 dark:text-emerald-300">
            Execution Trace
          </div>
          <p className="mt-1 text-sm font-medium text-slate-900 dark:text-slate-100">
            REEVU execution audit for this response
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400">
          {retrievalAudit && (
            <span className="rounded-full border border-slate-200 px-2 py-1 dark:border-slate-700">
              Services: {retrievalAudit.services.length}
            </span>
          )}
          {effectivePlanExecutionSummary && (
            <span className="rounded-full border border-slate-200 px-2 py-1 dark:border-slate-700">
              Steps: {effectivePlanExecutionSummary.steps.length}
            </span>
          )}
          <span className="rounded-full border border-emerald-200 px-2 py-1 text-emerald-700 dark:border-emerald-800 dark:text-emerald-300">
            {expanded ? 'Hide details' : 'Show details'}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="grid gap-4 border-t border-slate-200/80 px-4 py-4 dark:border-slate-800/80 lg:grid-cols-2">
          {retrievalAudit && (
            <section className="space-y-3">
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">
                  Retrieval Services
                </h4>
                <ul className="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-200">
                  {retrievalAudit.services.map(service => (
                    <li key={service} className="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900/70">
                      {service}
                    </li>
                  ))}
                </ul>
              </div>

              {retrievalAudit.tables && retrievalAudit.tables.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">
                    Tables or sources
                  </h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {retrievalAudit.tables.map(table => (
                      <span
                        key={table}
                        className="rounded-full border border-slate-200 px-2 py-1 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300"
                      >
                        {table}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {entityEntries.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">
                    Resolved scope
                  </h4>
                  <dl className="mt-2 grid gap-2 text-sm">
                    {entityEntries.map(([key, value]) => (
                      <div
                        key={key}
                        className="grid gap-1 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900/70"
                      >
                        <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          {key.replace(/_/g, ' ')}
                        </dt>
                        <dd className="text-slate-700 dark:text-slate-200">{formatEntityValue(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              )}
            </section>
          )}

          {effectivePlanExecutionSummary && (
            <section className="space-y-3">
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">
                  Execution plan
                </h4>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span className="rounded-full border border-slate-200 px-2 py-1 dark:border-slate-700">
                    {effectivePlanExecutionSummary.is_compound ? 'Compound' : 'Single-domain'}
                  </span>
                  {effectivePlanExecutionSummary.domains_involved.map(domain => (
                    <span
                      key={domain}
                      className="rounded-full border border-emerald-200 px-2 py-1 text-emerald-700 dark:border-emerald-800 dark:text-emerald-300"
                    >
                      {domain}
                    </span>
                  ))}
                  {effectivePlanExecutionSummary.missing_domains?.map(domain => (
                    <span
                      key={`missing-${domain}`}
                      className="rounded-full border border-amber-200 px-2 py-1 text-amber-700 dark:border-amber-800 dark:text-amber-300"
                    >
                      Missing: {domain}
                    </span>
                  ))}
                </div>
              </div>

              {planMetadataEntries.length > 0 && (
                <div>
                  <h5 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Planner metadata
                  </h5>
                  <dl className="mt-2 grid gap-2 text-sm">
                    {planMetadataEntries.map(([key, value]) => (
                      <div
                        key={key}
                        className="grid gap-1 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900/70"
                      >
                        <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          {formatLabel(key)}
                        </dt>
                        <dd className="text-slate-700 dark:text-slate-200">{formatEntityValue(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              )}

              <ol className="space-y-2">
                {effectivePlanExecutionSummary.steps.map(step => {
                  const outputCountEntries = getCountEntries(step.output_counts)
                  const outputEntityEntries = getRecordEntries(step.output_entity_ids)
                  const outputMetadataEntries = getRecordEntries(step.output_metadata)

                  return (
                  <li key={step.step_id} className="rounded-lg bg-slate-50 px-3 py-3 dark:bg-slate-900/70">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                          {step.description}
                        </div>
                        <div className="mt-1 text-[11px] uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          {step.domain}
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 text-[11px]">
                        {step.deterministic && (
                          <span className="rounded-full border border-blue-200 px-2 py-1 text-blue-700 dark:border-blue-800 dark:text-blue-300">
                            Deterministic
                          </span>
                        )}
                        <span className={getStepStatusClasses(step)}>{getStepStatusLabel(step)}</span>
                      </div>
                    </div>

                    {step.prerequisites && step.prerequisites.length > 0 && (
                      <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                        Prerequisites: {step.prerequisites.join(', ')}
                      </div>
                    )}

                    {step.expected_outputs && step.expected_outputs.length > 0 && (
                      <div className="mt-3">
                        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          Expected outputs
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {step.expected_outputs.map(output => (
                            <span
                              key={`${step.step_id}-expected-${output}`}
                              className="rounded-full border border-slate-200 px-2 py-1 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300"
                            >
                              {output}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {step.actual_outputs && step.actual_outputs.length > 0 && (
                      <div className="mt-3">
                        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          Actual outputs
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {step.actual_outputs.map(output => (
                            <span
                              key={`${step.step_id}-actual-${output}`}
                              className="rounded-full border border-emerald-200 px-2 py-1 text-xs text-emerald-700 dark:border-emerald-800 dark:text-emerald-300"
                            >
                              {output}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {step.services && step.services.length > 0 && (
                      <div className="mt-3">
                        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          Services used
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {step.services.map(service => (
                            <span
                              key={`${step.step_id}-service-${service}`}
                              className="rounded-full border border-slate-200 px-2 py-1 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300"
                            >
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {step.compute_methods && step.compute_methods.length > 0 && (
                      <div className="mt-3">
                        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          Deterministic methods
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {step.compute_methods.map(method => (
                            <span
                              key={`${step.step_id}-method-${method}`}
                              className="rounded-full border border-blue-200 px-2 py-1 text-xs text-blue-700 dark:border-blue-800 dark:text-blue-300"
                            >
                              {method}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {step.missing_reason && (
                      <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50/70 px-3 py-2 text-xs text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/20 dark:text-amber-200">
                        <span className="font-semibold">Missing reason:</span> {step.missing_reason}
                      </div>
                    )}

                    {(outputCountEntries.length > 0 || outputEntityEntries.length > 0 || outputMetadataEntries.length > 0) && (
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        {outputCountEntries.length > 0 && (
                          <div>
                            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                              Output counts
                            </div>
                            <dl className="mt-2 grid gap-2 text-sm">
                              {outputCountEntries.map(([key, value]) => (
                                <div
                                  key={`${step.step_id}-count-${key}`}
                                  className="grid gap-1 rounded-lg border border-slate-200/80 px-3 py-2 dark:border-slate-800/80"
                                >
                                  <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                    {formatLabel(key)}
                                  </dt>
                                  <dd className="text-slate-700 dark:text-slate-200">{value}</dd>
                                </div>
                              ))}
                            </dl>
                          </div>
                        )}

                        {outputEntityEntries.length > 0 && (
                          <div>
                            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                              Sample entities
                            </div>
                            <dl className="mt-2 grid gap-2 text-sm">
                              {outputEntityEntries.map(([key, value]) => (
                                <div
                                  key={`${step.step_id}-entities-${key}`}
                                  className="grid gap-1 rounded-lg border border-slate-200/80 px-3 py-2 dark:border-slate-800/80"
                                >
                                  <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                    {formatLabel(key)}
                                  </dt>
                                  <dd className="text-slate-700 dark:text-slate-200">{formatEntityValue(value)}</dd>
                                </div>
                              ))}
                            </dl>
                          </div>
                        )}

                        {outputMetadataEntries.length > 0 && (
                          <div className={outputCountEntries.length > 0 && outputEntityEntries.length > 0 ? 'md:col-span-2' : ''}>
                            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                              Additional context
                            </div>
                            <dl className="mt-2 grid gap-2 text-sm sm:grid-cols-2">
                              {outputMetadataEntries.map(([key, value]) => (
                                <div
                                  key={`${step.step_id}-metadata-${key}`}
                                  className="grid gap-1 rounded-lg border border-slate-200/80 px-3 py-2 dark:border-slate-800/80"
                                >
                                  <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                    {formatLabel(key)}
                                  </dt>
                                  <dd className="text-slate-700 dark:text-slate-200">{formatEntityValue(value)}</dd>
                                </div>
                              ))}
                            </dl>
                          </div>
                        )}
                      </div>
                    )}
                  </li>
                  )
                })}
              </ol>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

export default ReevuExecutionTraceCard

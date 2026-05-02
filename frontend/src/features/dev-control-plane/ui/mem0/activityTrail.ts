export type Mem0ActivityKind = 'manual-note' | 'learning-capture' | 'mission-capture'
export type Mem0ActivityFilter = 'all' | Mem0ActivityKind

export type Mem0ActivityEntry = {
  id: string
  kind: Mem0ActivityKind
  title: string
  summary: string
  scopeLabel: string
  resultId: string | null
  recordedAt: string
}

export const MEM0_ACTIVITY_STORAGE_KEY = 'developer-control-plane-mem0-activity-trail'

export const mem0ActivityFilterOptions: Mem0ActivityFilter[] = [
  'all',
  'manual-note',
  'learning-capture',
  'mission-capture',
]

export function activityKindLabel(kind: Mem0ActivityKind) {
  if (kind === 'manual-note') {
    return 'Manual Note'
  }

  if (kind === 'learning-capture') {
    return 'Learning Capture'
  }

  return 'Mission Capture'
}

export function activityFilterLabel(filter: Mem0ActivityFilter) {
  if (filter === 'all') {
    return 'All Entries'
  }

  return `${activityKindLabel(filter)}s`
}

export function extractFirstResultId(result: Record<string, unknown>) {
  const results = result.results
  if (!Array.isArray(results)) {
    return null
  }

  const first = results[0]
  if (!first || typeof first !== 'object') {
    return null
  }

  return typeof (first as { id?: unknown }).id === 'string'
    ? (first as { id: string }).id
    : null
}

export function formatScopeLabel(scope: { user_id: string; app_id: string; run_id: string | null }) {
  if (scope.run_id) {
    return `${scope.user_id} · ${scope.app_id} · ${scope.run_id}`
  }
  return `${scope.user_id} · ${scope.app_id}`
}

export function buildActivitySummary(entry: Mem0ActivityEntry) {
  const lines = [
    `Mem0 ${activityKindLabel(entry.kind)}`,
    `Title: ${entry.title}`,
    `Summary: ${entry.summary}`,
    `Scope: ${entry.scopeLabel}`,
    `Recorded: ${entry.recordedAt}`,
  ]

  if (entry.resultId) {
    lines.push(`Result ID: ${entry.resultId}`)
  }

  return lines.join('\n')
}

export function buildVisibleActivitySummaries(
  entries: Mem0ActivityEntry[],
  filter: Mem0ActivityFilter
) {
  const lines = [`Mem0 ${activityFilterLabel(filter)}`]

  for (const entry of entries) {
    lines.push('')
    lines.push(buildActivitySummary(entry))
  }

  return lines.join('\n')
}
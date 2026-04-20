import { describe, expect, it } from 'vitest'

import {
  activityFilterLabel,
  activityKindLabel,
  buildActivitySummary,
  buildVisibleActivitySummaries,
  extractFirstResultId,
  formatScopeLabel,
  type Mem0ActivityEntry,
} from './activityTrail'

function createEntry(overrides: Partial<Mem0ActivityEntry> = {}): Mem0ActivityEntry {
  return {
    id: 'manual-note-1',
    kind: 'manual-note',
    title: 'Manual note: architecture',
    summary: 'Keep Mem0 separate from REEVU.',
    scopeLabel: 'bijmantra-dev · bijmantra-dev',
    resultId: 'mem-1',
    recordedAt: '2026-04-05T10:40:00.000Z',
    ...overrides,
  }
}

describe('activityTrail helpers', () => {
  it('returns human-readable labels for activity kinds and filters', () => {
    expect(activityKindLabel('manual-note')).toBe('Manual Note')
    expect(activityKindLabel('learning-capture')).toBe('Learning Capture')
    expect(activityKindLabel('mission-capture')).toBe('Mission Capture')

    expect(activityFilterLabel('all')).toBe('All Entries')
    expect(activityFilterLabel('manual-note')).toBe('Manual Notes')
    expect(activityFilterLabel('learning-capture')).toBe('Learning Captures')
    expect(activityFilterLabel('mission-capture')).toBe('Mission Captures')
  })

  it('formats scope labels and extracts result ids defensively', () => {
    expect(
      formatScopeLabel({ user_id: 'bijmantra-dev', app_id: 'mem0-app', run_id: 'run-1' })
    ).toBe('bijmantra-dev · mem0-app · run-1')
    expect(
      formatScopeLabel({ user_id: 'bijmantra-dev', app_id: 'mem0-app', run_id: null })
    ).toBe('bijmantra-dev · mem0-app')

    expect(extractFirstResultId({ results: [{ id: 'mem-1' }] })).toBe('mem-1')
    expect(extractFirstResultId({ results: [{ id: 123 }] })).toBeNull()
    expect(extractFirstResultId({ results: [] })).toBeNull()
    expect(extractFirstResultId({ results: 'not-an-array' })).toBeNull()
    expect(extractFirstResultId({})).toBeNull()
  })

  it('builds individual summaries with and without result ids', () => {
    const summaryWithResult = buildActivitySummary(createEntry())
    const summaryWithoutResult = buildActivitySummary(
      createEntry({ kind: 'mission-capture', resultId: null })
    )

    expect(summaryWithResult).toContain('Mem0 Manual Note')
    expect(summaryWithResult).toContain('Title: Manual note: architecture')
    expect(summaryWithResult).toContain('Summary: Keep Mem0 separate from REEVU.')
    expect(summaryWithResult).toContain('Scope: bijmantra-dev · bijmantra-dev')
    expect(summaryWithResult).toContain('Recorded: 2026-04-05T10:40:00.000Z')
    expect(summaryWithResult).toContain('Result ID: mem-1')

    expect(summaryWithoutResult).toContain('Mem0 Mission Capture')
    expect(summaryWithoutResult).not.toContain('Result ID:')
  })

  it('builds visible summaries with a filter-specific header and grouped entries', () => {
    const visibleSummary = buildVisibleActivitySummaries(
      [
        createEntry({
          id: 'learning-1',
          kind: 'learning-capture',
          title: 'Learning 1',
          summary: 'Learning summary 1',
          resultId: 'mem-learn-1',
        }),
        createEntry({
          id: 'learning-2',
          kind: 'learning-capture',
          title: 'Learning 2',
          summary: 'Learning summary 2',
          resultId: 'mem-learn-2',
        }),
      ],
      'learning-capture'
    )

    expect(visibleSummary).toContain('Mem0 Learning Captures')
    expect(visibleSummary).toContain('Title: Learning 1')
    expect(visibleSummary).toContain('Title: Learning 2')
    expect(visibleSummary).toContain('Result ID: mem-learn-1')
    expect(visibleSummary).toContain('Result ID: mem-learn-2')
  })
})
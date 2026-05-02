import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  MEM0_ACTIVITY_STORAGE_KEY,
  type Mem0ActivityEntry,
} from './activityTrail'
import {
  clipboardWriteText,
  resetMem0TestEnvironment,
  sonnerMocks,
} from './mem0TestHelpers'
import { useMem0ActivityTrail } from './useMem0ActivityTrail'

vi.mock('sonner', () => ({
  toast: sonnerMocks,
}))

function createEntry(overrides: Partial<Mem0ActivityEntry> = {}): Mem0ActivityEntry {
  return {
    id: 'manual-note-1',
    kind: 'manual-note',
    title: 'Manual note: architecture',
    summary: 'Keep Mem0 separate from REEVU.',
    scopeLabel: 'bijmantra-dev · bijmantra-dev',
    resultId: 'mem-seeded-1',
    recordedAt: '2026-04-05T10:40:00.000Z',
    ...overrides,
  }
}

describe('useMem0ActivityTrail', () => {
  beforeEach(() => {
    resetMem0TestEnvironment()
  })

  it('rehydrates valid session entries and ignores invalid seeded values', async () => {
    window.sessionStorage.setItem(
      MEM0_ACTIVITY_STORAGE_KEY,
      JSON.stringify([
        createEntry(),
        {
          id: 'broken-entry',
          kind: 'manual-note',
          title: 'Broken',
        },
      ])
    )

    const { result } = renderHook(() => useMem0ActivityTrail())

    await waitFor(() => {
      expect(result.current.activityTrail).toHaveLength(1)
    })

    expect(result.current.activityTrail[0]).toMatchObject({
      title: 'Manual note: architecture',
      resultId: 'mem-seeded-1',
    })
    expect(result.current.filteredActivityTrail).toHaveLength(1)

    act(() => {
      result.current.setActivityFilter('mission-capture')
    })

    expect(result.current.filteredActivityTrail).toHaveLength(0)

    act(() => {
      result.current.clearActivityTrail()
    })

    await waitFor(() => {
      expect(result.current.activityTrail).toHaveLength(0)
    })

    expect(window.sessionStorage.getItem(MEM0_ACTIVITY_STORAGE_KEY)).toBe('[]')
  })

  it('records activity entries, caps the trail at eight, persists them, and copies filtered summaries', async () => {
    const { result } = renderHook(() => useMem0ActivityTrail())

    await waitFor(() => {
      expect(result.current.activityTrail).toHaveLength(0)
    })

    act(() => {
      result.current.recordActivity({
        kind: 'manual-note',
        title: 'Manual note: decision',
        summary: 'Developer note',
        scopeLabel: 'scope-1',
        resultId: 'mem-1',
      })
      result.current.recordActivity({
        kind: 'learning-capture',
        title: 'Learning 1',
        summary: 'Learning summary 1',
        scopeLabel: 'scope-2',
        resultId: 'mem-learn-1',
      })
      result.current.recordActivity({
        kind: 'mission-capture',
        title: 'Mission 1',
        summary: 'Mission summary 1',
        scopeLabel: 'scope-3',
        resultId: 'mem-mission-1',
      })

      for (let index = 2; index <= 8; index += 1) {
        result.current.recordActivity({
          kind: 'learning-capture',
          title: `Learning ${index}`,
          summary: `Learning summary ${index}`,
          scopeLabel: `scope-${index + 2}`,
          resultId: `mem-learn-${index}`,
        })
      }
    })

    await waitFor(() => {
      expect(result.current.activityTrail).toHaveLength(8)
    })

    expect(result.current.activityTrail[0]?.title).toBe('Learning 8')
    expect(result.current.activityTrail.map((entry) => entry.title)).not.toContain('Manual note: decision')

    const persisted = JSON.parse(
      window.sessionStorage.getItem(MEM0_ACTIVITY_STORAGE_KEY) ?? '[]'
    ) as Mem0ActivityEntry[]
    expect(persisted).toHaveLength(8)

    act(() => {
      result.current.setActivityFilter('learning-capture')
    })

    expect(result.current.filteredActivityTrail).toHaveLength(7)
    expect(result.current.filteredActivityTrail.every((entry) => entry.kind === 'learning-capture')).toBe(true)

    await act(async () => {
      await result.current.copyVisibleActivitySummaries()
    })

    expect(clipboardWriteText).toHaveBeenCalledTimes(1)
    expect(String(clipboardWriteText.mock.calls[0]?.[0] ?? '')).toContain('Mem0 Learning Captures')
    expect(String(clipboardWriteText.mock.calls[0]?.[0] ?? '')).toContain('Learning 8')
    expect(String(clipboardWriteText.mock.calls[0]?.[0] ?? '')).not.toContain('Mission 1')
    expect(sonnerMocks.success).toHaveBeenCalledWith('Visible Mem0 summaries copied.')
  })

  it('copies individual summaries and reports clipboard failures explicitly', async () => {
    const { result } = renderHook(() => useMem0ActivityTrail())

    await waitFor(() => {
      expect(result.current.activityTrail).toHaveLength(0)
    })

    act(() => {
      result.current.recordActivity({
        kind: 'mission-capture',
        title: 'Mission closeout',
        summary: 'Mission evidence was captured into Mem0.',
        scopeLabel: 'bijmantra-dev · bijmantra-dev · run-1',
        resultId: 'mem-mission-1',
      })
    })

    await waitFor(() => {
      expect(result.current.activityTrail).toHaveLength(1)
    })

    await act(async () => {
      await result.current.copyActivitySummary(result.current.activityTrail[0]!)
    })

    expect(String(clipboardWriteText.mock.calls[0]?.[0] ?? '')).toContain('Mem0 Mission Capture')
    expect(String(clipboardWriteText.mock.calls[0]?.[0] ?? '')).toContain('Result ID: mem-mission-1')
    expect(sonnerMocks.success).toHaveBeenCalledWith('Mem0 capture summary copied.')

    clipboardWriteText.mockRejectedValueOnce(new Error('clipboard write failed'))

    await act(async () => {
      await result.current.copyVisibleActivitySummaries()
    })

    expect(sonnerMocks.error).toHaveBeenCalledWith('Failed to copy visible Mem0 summaries.')

    Object.defineProperty(window.navigator, 'clipboard', {
      configurable: true,
      value: undefined,
    })

    await act(async () => {
      await result.current.copyActivitySummary(result.current.activityTrail[0]!)
    })

    expect(sonnerMocks.error).toHaveBeenCalledWith('Failed to copy Mem0 capture summary.')
  })
})
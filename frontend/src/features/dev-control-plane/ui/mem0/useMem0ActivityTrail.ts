import { useEffect, useState } from 'react'

import { toast } from 'sonner'

import {
  buildActivitySummary,
  buildVisibleActivitySummaries,
  MEM0_ACTIVITY_STORAGE_KEY,
  type Mem0ActivityEntry,
  type Mem0ActivityFilter,
} from './activityTrail'

function isMem0ActivityEntry(value: unknown): value is Mem0ActivityEntry {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as { id?: unknown }).id === 'string' &&
    typeof (value as { kind?: unknown }).kind === 'string' &&
    typeof (value as { title?: unknown }).title === 'string' &&
    typeof (value as { summary?: unknown }).summary === 'string' &&
    typeof (value as { scopeLabel?: unknown }).scopeLabel === 'string' &&
    typeof (value as { recordedAt?: unknown }).recordedAt === 'string'
  )
}

export function useMem0ActivityTrail() {
  const [activityTrail, setActivityTrail] = useState<Mem0ActivityEntry[]>([])
  const [activityTrailHydrated, setActivityTrailHydrated] = useState(false)
  const [activityFilter, setActivityFilter] = useState<Mem0ActivityFilter>('all')

  useEffect(() => {
    try {
      const rawValue = window.sessionStorage.getItem(MEM0_ACTIVITY_STORAGE_KEY)
      if (!rawValue) {
        setActivityTrailHydrated(true)
        return
      }

      const parsed = JSON.parse(rawValue)
      if (!Array.isArray(parsed)) {
        setActivityTrailHydrated(true)
        return
      }

      setActivityTrail(parsed.filter(isMem0ActivityEntry))
    } catch {
      setActivityTrail([])
    } finally {
      setActivityTrailHydrated(true)
    }
  }, [])

  useEffect(() => {
    if (!activityTrailHydrated) {
      return
    }

    try {
      window.sessionStorage.setItem(MEM0_ACTIVITY_STORAGE_KEY, JSON.stringify(activityTrail))
    } catch {
      // Ignore sessionStorage write failures in the hidden developer surface.
    }
  }, [activityTrail, activityTrailHydrated])

  const filteredActivityTrail = activityTrail.filter(
    (entry) => activityFilter === 'all' || entry.kind === activityFilter
  )

  const recordActivity = (entry: Omit<Mem0ActivityEntry, 'id' | 'recordedAt'>) => {
    setActivityTrail((current) => [
      {
        ...entry,
        id: `${entry.kind}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        recordedAt: new Date().toISOString(),
      },
      ...current,
    ].slice(0, 8))
  }

  const clearActivityTrail = () => {
    setActivityTrail([])
  }

  const copyActivitySummary = async (entry: Mem0ActivityEntry) => {
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error('Clipboard is not available in this environment.')
      }

      await navigator.clipboard.writeText(buildActivitySummary(entry))
      toast.success('Mem0 capture summary copied.')
    } catch {
      toast.error('Failed to copy Mem0 capture summary.')
    }
  }

  const copyVisibleActivitySummaries = async () => {
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error('Clipboard is not available in this environment.')
      }

      await navigator.clipboard.writeText(
        buildVisibleActivitySummaries(filteredActivityTrail, activityFilter)
      )
      toast.success('Visible Mem0 summaries copied.')
    } catch {
      toast.error('Failed to copy visible Mem0 summaries.')
    }
  }

  return {
    activityTrail,
    filteredActivityTrail,
    activityFilter,
    setActivityFilter,
    recordActivity,
    clearActivityTrail,
    copyActivitySummary,
    copyVisibleActivitySummaries,
  }
}
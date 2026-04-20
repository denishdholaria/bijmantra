import { useEffect, useState } from 'react'

import {
  fetchDeveloperControlPlaneLearnings,
  getDeveloperControlPlanePersistenceErrorMessage,
  type DeveloperControlPlaneLearningLedgerResponse,
} from '../../api/activeBoard'

export type DecisionMemoryState = 'idle' | 'loading' | 'ready' | 'error'

export type DecisionMemoryScope = {
  sourceLaneId: string | null
  queueJobId: string | null
  linkedMissionId: string | null
}

export type DecisionMemoryMatchMode =
  | 'exact-runtime'
  | 'lane-and-mission'
  | 'lane-only'
  | 'mission-only'
  | 'queue-only'
  | 'none'

export type DecisionMemoryResolution = {
  matchMode: DecisionMemoryMatchMode
  fallbackUsed: boolean
}

type UseDecisionMemoryInput = {
  enabled: boolean
  sourceLaneId?: string | null
  queueJobId?: string | null
  linkedMissionId?: string | null
}

type UseDecisionMemoryResult = {
  state: DecisionMemoryState
  record: DeveloperControlPlaneLearningLedgerResponse | null
  error: string | null
  lastCheckedAt: string | null
  scope: DecisionMemoryScope
  resolution: DecisionMemoryResolution
}

type DecisionMemoryQuery = NonNullable<Parameters<typeof fetchDeveloperControlPlaneLearnings>[0]>
type DecisionMemoryQueryDescriptor = {
  matchMode: Exclude<DecisionMemoryMatchMode, 'none'>
  query: DecisionMemoryQuery
}

function normalizeDecisionMemoryQuery(query: DecisionMemoryQuery): DecisionMemoryQuery {
  return Object.fromEntries(
    Object.entries(query).filter(([, value]) => value !== null && value !== undefined)
  ) as DecisionMemoryQuery
}

function buildDecisionMemoryQueries(scope: DecisionMemoryScope): DecisionMemoryQueryDescriptor[] {
  const queries: DecisionMemoryQueryDescriptor[] = []
  const seen = new Set<string>()

  const pushQuery = (
    matchMode: DecisionMemoryQueryDescriptor['matchMode'],
    query: DecisionMemoryQuery
  ) => {
    const normalizedQuery = normalizeDecisionMemoryQuery(query)
    const queryKey = JSON.stringify(normalizedQuery)
    if (seen.has(queryKey)) {
      return
    }

    seen.add(queryKey)
    queries.push({ matchMode, query: normalizedQuery })
  }

  pushQuery('exact-runtime', {
    limit: 3,
    sourceLaneId: scope.sourceLaneId,
    queueJobId: scope.queueJobId,
    linkedMissionId: scope.linkedMissionId,
  })

  if (scope.sourceLaneId && scope.queueJobId && scope.linkedMissionId) {
    pushQuery('lane-and-mission', {
      limit: 3,
      sourceLaneId: scope.sourceLaneId,
      linkedMissionId: scope.linkedMissionId,
    })
  }

  if (scope.sourceLaneId) {
    pushQuery('lane-only', {
      limit: 3,
      sourceLaneId: scope.sourceLaneId,
    })
  }

  if (!scope.sourceLaneId && scope.linkedMissionId) {
    pushQuery('mission-only', {
      limit: 3,
      linkedMissionId: scope.linkedMissionId,
    })
  }

  if (!scope.sourceLaneId && scope.queueJobId) {
    pushQuery('queue-only', {
      limit: 3,
      queueJobId: scope.queueJobId,
    })
  }

  return queries
}

export function useDecisionMemory({
  enabled,
  sourceLaneId = null,
  queueJobId = null,
  linkedMissionId = null,
}: UseDecisionMemoryInput): UseDecisionMemoryResult {
  const [state, setState] = useState<DecisionMemoryState>('idle')
  const [record, setRecord] = useState<DeveloperControlPlaneLearningLedgerResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastCheckedAt, setLastCheckedAt] = useState<string | null>(null)
  const [resolution, setResolution] = useState<DecisionMemoryResolution>({
    matchMode: 'none',
    fallbackUsed: false,
  })

  useEffect(() => {
    const hasScope = Boolean(sourceLaneId || queueJobId || linkedMissionId)
    if (!enabled || !hasScope) {
      setState('idle')
      setRecord(null)
      setError(null)
      setLastCheckedAt(null)
      setResolution({
        matchMode: 'none',
        fallbackUsed: false,
      })
      return
    }

    let cancelled = false

    const loadDecisionMemory = async () => {
      setState('loading')
      setError(null)

      try {
        const queries = buildDecisionMemoryQueries({
          sourceLaneId,
          queueJobId,
          linkedMissionId,
        })
        const primaryMatchMode = queries[0]?.matchMode ?? 'none'
        let response: DeveloperControlPlaneLearningLedgerResponse = {
          total_count: 0,
          entries: [],
        }
        let resolvedMatchMode: DecisionMemoryMatchMode = primaryMatchMode

        for (const queryDescriptor of queries) {
          resolvedMatchMode = queryDescriptor.matchMode
          response = await fetchDeveloperControlPlaneLearnings(queryDescriptor.query)
          if (response.entries.length > 0) {
            break
          }
        }

        if (cancelled) {
          return
        }

        setRecord(response)
        setState('ready')
        setLastCheckedAt(new Date().toISOString())
        setResolution({
          matchMode: resolvedMatchMode,
          fallbackUsed:
            response.entries.length > 0 &&
            primaryMatchMode !== 'none' &&
            resolvedMatchMode !== primaryMatchMode,
        })
      } catch (loadError) {
        if (cancelled) {
          return
        }

        setRecord(null)
        setState('error')
        setError(getDeveloperControlPlanePersistenceErrorMessage(loadError))
        setLastCheckedAt(new Date().toISOString())
        setResolution({
          matchMode: 'none',
          fallbackUsed: false,
        })
      }
    }

    void loadDecisionMemory()

    return () => {
      cancelled = true
    }
  }, [enabled, linkedMissionId, queueJobId, sourceLaneId])

  return {
    state,
    record,
    error,
    lastCheckedAt,
    scope: {
      sourceLaneId,
      queueJobId,
      linkedMissionId,
    },
    resolution,
  }
}